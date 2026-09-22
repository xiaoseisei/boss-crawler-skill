"""原子浏览器操作适配层模块。

定义并实现了所有与浏览器交互的原语操作（打开页面、点击按钮、提取 DOM、输入文本、上传附件等）。
遵循关注点分离原则：本模块内的所有方法仅执行纯粹的页面操作或只读提取，不包含任何业务决策或状态机流转。
业务决策与控制流均统一交由 runner 模块负责。
"""
import time
from typing import Any, List, Optional

# ----------------- 超时与轮询常量定义 -----------------
# 岗位详情页加载导航超时时间（秒）
DETAIL_TIMEOUT = 8
# 聊天页面加载超时时间（秒）
CHAT_TIMEOUT = 8
# 轮询等待目标聊天会话就绪的最大重试次数
CHAT_READY_POLLS = 6
# 轮询检查聊天会话就绪的时间间隔（秒）
CHAT_READY_INTERVAL = 0.35
# 聊天富文本输入框（composer）渲染挂载的最大等待超时时间（秒）
COMPOSER_TIMEOUT = 10.0


class BrowserOps:
    """浏览器原子操作适配器接口抽象基类。
    
    定义了工作流所需的所有浏览器操作接口。
    在单元测试或仿真环境中，可直接基于该基类创建 Mock 实现，无需启动真实浏览器。
    """

    def open_job_detail(self, url: str) -> None:
        """导航并打开指定的岗位详情页。"""
        raise NotImplementedError

    def read_job_chat_button(self) -> str:
        """读取岗位详情页中沟通按钮的文本内容（如'立即沟通'、'继续沟通'等）。"""
        raise NotImplementedError

    def click_start_chat(self) -> None:
        """点击岗位详情页中的沟通按钮以发起或继续聊天。"""
        raise NotImplementedError

    def read_daily_limit_dialog(self) -> bool:
        """检测当前页面是否弹出或展示了触达每日沟通上限的提示。"""
        raise NotImplementedError

    def open_chat_workspace(self) -> None:
        """打开或切换到 /web/geek/chat 聊天工作台标签页。"""
        raise NotImplementedError

    def remove_overlay(self) -> bool:
        """检测并移除页面中可能遮挡操作的下载引导或弹窗遮罩层。"""
        raise NotImplementedError

    def select_chat_session(self, company: str = '', position: str = '') -> None:
        """在聊天列表中检索并选中匹配目标公司/职位的会话。"""
        raise NotImplementedError

    def read_messages(self) -> List[Any]:
        """读取当前激活会话窗口内的所有聊天记录。"""
        raise NotImplementedError

    def read_input_value(self) -> str:
        """读取聊天输入框当前尚未发送的输入草稿内容。"""
        raise NotImplementedError

    def focus_input(self) -> None:
        """将焦点聚焦到聊天输入框元素上。"""
        raise NotImplementedError

    def fill_input(self, text: str) -> None:
        """清空当前输入框并将指定文本输入到聊天框中。"""
        raise NotImplementedError

    def press_enter(self) -> None:
        """模拟键盘回车（Enter）键以触发快捷发送。"""
        raise NotImplementedError

    def click_send_button(self) -> None:
        """定位并点击聊天工作台中的“发送”按钮。"""
        raise NotImplementedError

    def upload_file(self, path: str) -> None:
        """通过隐藏的文件上传 input 控件上传本地附件（如简历图片）。"""
        raise NotImplementedError


class DrissionBrowserOps(BrowserOps):
    """基于 DrissionPage 实现的真实浏览器操作适配器。
    
    封装具体的 CSS/XPath 选择器、JavaScript 脚本注入及 CDP 键鼠动作，
    保证每个公共方法只执行单一且明确的操作或读取。
    """
    def __init__(self, page: Any, sleep: float = 0.2):
        """初始化操作适配器。
        
        Args:
            page: DrissionPage 的 ChromiumPage 对象。
            sleep: 操作间的默认微等待时间（秒）。
        """
        self.page = page
        self.sleep = sleep
        self.chat_page = None
        self.metrics = {'chat_page_creations': 0}

    def _chat(self):
        """获取当前绑定的聊天工作台标签页对象。
        
        Raises:
            RuntimeError: 当尚未调用 open_chat_workspace 时抛出。
        """
        if self.chat_page is None:
            raise RuntimeError('聊天工作台尚未初始化')
        return self.chat_page

    def open_job_detail(self, url: str) -> None:
        """打开指定的岗位详情页并统计导航耗时。
        
        Args:
            url: 岗位详情页链接。
        """
        started = time.perf_counter()
        self.page.get(url, timeout=DETAIL_TIMEOUT)
        self.metrics['detail_navigation_ms'] = round((time.perf_counter() - started) * 1000, 1)

    def read_job_chat_button(self) -> str:
        """通过多种候选选择器提取详情页沟通按钮的文本。
        
        Returns:
            str: 按钮文本（去除首尾空白），未定位到则返回空字符串。
        """
        selectors = [
            'css:.btn-startchat',
            'xpath://a[contains(@class,"btn-startchat")]',
            'xpath://*[contains(text(),"立即沟通") or contains(text(),"继续沟通") or contains(text(),"已沟通")]'
        ]
        for selector in selectors:
            try:
                el = self.page.ele(selector, timeout=1)
                if el:
                    return (el.text or '').strip()
            except Exception:
                continue
        return ''

    def click_start_chat(self) -> None:
        """点击岗位详情页上的“立即沟通”/“继续沟通”按钮。
        
        Raises:
            RuntimeError: 当页面上找不到可见的沟通按钮时抛出。
        """
        el = None
        # 依次尝试 class 选择器与文本匹配选择器（覆盖“立即沟通”与“继续沟通”）
        for selector in (
            'css:.btn-startchat',
            'css:.btn-startchat-wrap a',
            'xpath://a[contains(@class,"btn-startchat")]',
            'xpath://*[contains(@class,"btn-startchat") or contains(text(),"立即沟通") or contains(text(),"继续沟通")]'
        ):
            try:
                candidate = self.page.ele(selector, timeout=1)
                if candidate and candidate.rect.size[0] > 0:
                    el = candidate
                    break
            except Exception:
                pass
        if not el:
            raise RuntimeError('沟通按钮不存在')
            
        # 记录按钮绑定的 href 属性（如有有效链接），供后续直接跳转兜底使用
        # 针对新岗位的“立即沟通”DOM 常为 <a href="javascript:;">，需清洗过滤伪协议与锚点
        raw_href = (el.attr('href') or '').strip()
        if not raw_href or 'javascript' in raw_href.lower() or raw_href.startswith('#'):
            self.target_chat_href = ''
        else:
            self.target_chat_href = raw_href
        el.click()
        # 点击后等待 1 秒以触发页面跳转或自动开启聊天会话
        time.sleep(1)

    def read_daily_limit_dialog(self) -> bool:
        """通过注入 JS 检测页面 body 中是否存在当日沟通上限关键字。
        
        Returns:
            bool: 若检测到“上限”且包含“沟通”或“次数”则返回 True。
        """
        try:
            text = self.page.run_js("""return document.body ? document.body.innerText : '';""") or ''
            return '上限' in text and ('沟通' in text or '次数' in text)
        except Exception:
            return False

    def open_chat_workspace(self) -> None:
        """定位或新建 /web/geek/chat 聊天工作台。
        
        确保当前操作对象确实位于聊天工作台。
        修复原先仅在 chat_page 为 None 时才检查的缺陷，防止在 job_detail 页面盲跑后续逻辑。
        """
        # 1. 轮询检测当前页面或新标签页是否已经进入 /web/geek/chat
        deadline = time.perf_counter() + 3
        while time.perf_counter() < deadline:
            try:
                if '/web/geek/chat' in (self.page.url or ''):
                    self.chat_page = self.page
                    return
                tab = self.page.get_tab(url='web/geek/chat')
                if tab:
                    self.chat_page = tab
                    return
            except Exception:
                pass
            time.sleep(0.2)

        # 2. 若未自动跳转（常见于首投岗位或点击“继续沟通”未弹出新窗口，页面仍停留在 job_detail）
        raw_target = getattr(self, 'target_chat_href', '') or ''
        if not raw_target or 'javascript' in raw_target.lower() or raw_target.startswith('#'):
            target_url = 'https://www.zhipin.com/web/geek/chat'
        elif raw_target.startswith('http'):
            target_url = raw_target
        else:
            target_url = 'https://www.zhipin.com' + (raw_target if raw_target.startswith('/') else '/' + raw_target)

        # 检查是否已有缓存的历史聊天标签页可用
        if self.chat_page and self.chat_page != self.page:
            try:
                if '/web/geek/chat' in (self.chat_page.url or ''):
                    return
                self.chat_page.get(target_url)
                time.sleep(0.8)
                return
            except Exception:
                self.chat_page = None

        # 兜底：直接让当前页面导航进入聊天工作台
        started = time.perf_counter()
        try:
            self.page.get(target_url)
            self.chat_page = self.page
            time.sleep(0.8)
        except Exception:
            self.chat_page = self.page.new_tab(target_url, background=False)
            time.sleep(0.8)
        self.metrics['chat_page_creations'] = self.metrics.get('chat_page_creations', 0) + 1
        self.metrics['chat_page_creation_ms'] = round((time.perf_counter() - started) * 1000, 1)

        # 3. 终验：严格确保进入了聊天工作台
        current_url = (self.chat_page.url if self.chat_page else self.page.url) or ''
        if '/web/geek/chat' not in current_url:
            raise RuntimeError(f'未能跳转到聊天工作台，页面仍停留在: {current_url}')

    def remove_overlay(self) -> bool:
        """注入 JS 移除 APP 下载引导弹窗及全屏遮罩元素。
        
        Returns:
            bool: 若成功找到并移除了遮罩层则返回 True。
        """
        try:
            return bool(self._chat().run_js("""
                const s = '.guide-download-app,[class*="guide-download"],[class*="download-app"]';
                const e = [...document.querySelectorAll(s)];
                e.forEach(x => x.remove());
                return e.length;
            """))
        except Exception:
            return False

    def select_chat_session(self, company: str = '', position: str = '') -> None:
        """在聊天工作台左侧列表中搜索并定位目标公司与职位的会话。
        
        Args:
            company: 目标公司名称。
            position: 目标职位名称（可选）。
            
        Raises:
            RuntimeError: 在指定轮询次数内未找到目标会话或会话未就绪时抛出。
        """
        started = time.perf_counter()
        chat = self._chat()
        
        # 1. 若存在搜索框且指定了公司名称，在搜索框中键入关键词并点击搜索按钮
        search = chat.ele('css:input.boss-search-input', timeout=1)
        if search and company:
            search_term = company.replace('…', '').replace('...', '').strip()
            # 限制搜索词长度不超过 10 个字，提高匹配容错率
            if len(search_term) > 10:
                search_term = search_term[:10]
            try:
                search.clear()
            except Exception:
                pass
            search.input(search_term)
            
            # 关键修复：BOSS 搜索框仅按回车无效，必须鼠标点击搜索图标
            clicked_search = False
            try:
                search_btn = (
                    search.parent().ele('css:.icon-search, i, span[class*="search"], [class*="search-btn"], svg', timeout=0.8)
                    or chat.ele('css:.boss-search-input-wrap .icon-search, .search-box .icon-search, .icon-search', timeout=0.8)
                )
                if search_btn:
                    search_btn.click()
                    clicked_search = True
            except Exception:
                pass
                
            if not clicked_search:
                # 兜底：通过 JS 派发 input/change 事件并点击父级中的搜索图标
                chat.run_js("""
                    const inp = document.querySelector('input.boss-search-input');
                    if (inp) {
                        inp.dispatchEvent(new Event('input', { bubbles: true }));
                        inp.dispatchEvent(new Event('change', { bubbles: true }));
                        const icon = inp.parentElement ? inp.parentElement.querySelector('i, span, [class*="search"], svg') : null;
                        if (icon) icon.click();
                    }
                """)
                
            # 补充回车作为辅助按键
            try:
                chat.actions.key_down('ENTER')
                chat.actions.key_up('ENTER')
            except Exception:
                pass
            time.sleep(1.0)
            
        # 2. 轮询查找匹配目标公司/职位的列表项并执行点击激活
        for _ in range(CHAT_READY_POLLS):
            try:
                found = chat.run_js("""
                    const company = %s, position = %s;
                    const active = document.querySelector('.geek-chat-list .chat-item.active, .chat-user-list li.selected, li[role="listitem"].active');
                    const items = [...document.querySelectorAll('li[role="listitem"], .user-list li, .user-list-content li, .friend-content-warp, .geek-chat-list .chat-item, .chat-user-list li, [class*="chat-item"]')];
                    const target = items.find(x => (x.innerText || '').includes(company));
                    if (target) {
                        target.scrollIntoView({ block: 'nearest' });
                        target.click();
                        const inner = target.querySelector('.chat-content, .title-box, a') || target;
                        if (inner !== target) { inner.click(); }
                        return true;
                    }
                    if (!active && !company) {
                        const first = items[0];
                        if (first) {
                            first.scrollIntoView({ block: 'nearest' });
                            first.click();
                            return true;
                        }
                    }
                    return false;
                """ % (repr(company), repr(position)))
                if not found:
                    time.sleep(CHAT_READY_INTERVAL)
                    continue
                # 目标会话已被点击选中，等待 0.5 秒让右侧主会话及输入框完成挂载渲染
                time.sleep(0.5)
                self.metrics['chat_search_ms'] = round((time.perf_counter() - started) * 1000, 1)
                return
            except Exception:
                pass
            time.sleep(CHAT_READY_INTERVAL)
            
        # 若轮询耗尽仍未就绪，采集当前页面诊断信息后抛出异常
        try:
            state = chat.run_js("""
                return {
                    url: location.href,
                    body: (document.body && document.body.innerText || '').slice(0, 120),
                    inputs: [...document.querySelectorAll('[contenteditable="true"],textarea,input')].slice(0, 20).map(e => ({
                        tag: e.tagName, cls: e.className, id: e.id, ph: e.getAttribute('placeholder')
                    })),
                    iframes: document.querySelectorAll('iframe').length
                };
            """)
        except Exception as exc:
            state = {'error': str(exc)}
        self.metrics['chat_search_ms'] = round((time.perf_counter() - started) * 1000, 1)
        raise RuntimeError('聊天会话未就绪: ' + str(state))

    def read_active_chat_identity(self) -> str:
        """读取当前右侧聊天窗口顶部的会话标题（通常包含沟通对象姓名及公司名）。
        
        严格限定在右侧主会话容器 .chat-conversation 内部，杜绝误读左侧联系人列表。
        若右侧处于未激活或空白状态（如包含 .chat-no-data），则必然返回空字符串。
        
        Returns:
            str: 标题文本内容，未获取到或未激活时返回空字符串。
        """
        return self._chat().run_js("""
            // 1. 严格定位右侧主会话容器，绝不抓取左侧列表
            const conv = document.querySelector('.chat-conversation');
            if (!conv) return '';
            
            // 2. 若右侧处于无数据/未激活状态，返回空字符串
            if (conv.querySelector('.chat-no-data, .chat-empty')) return '';
            
            // 3. 从右侧会话头部提取当前会话对象与公司名
            const e = conv.querySelector('.top-info-content, .base-info, .name-content, .title-box, [class*="top-info"], [class*="base-info"], [class*="name-wrap"]');
            return e ? (e.innerText || '').trim() : '';
        """) or ''

    @staticmethod
    def identity_matches(identity: str, company: str) -> bool:
        """检查会话身份标识字符串与目标公司名是否吻合。
        
        清洗省略号等特殊标点后做子串包含判断。
        
        Args:
            identity: 从页面读取到的会话身份文本。
            company: 预期的公司名称。
            
        Returns:
            bool: 匹配成功返回 True，否则返回 False。
        """
        key = (company or '').replace('…', '').replace('...', '').strip()
        return bool(key) and key in (identity or '')

    def wait_for_active_identity(self, company: str, timeout: float = 1.5) -> str:
        """快速路径：等待由 BOSS 点击沟通后系统自动激活的目标会话标题。
        
        若在超时时间内当前激活的会话正是目标公司，则无需再经过左侧列表搜索。
        
        Args:
            company: 目标公司名称。
            timeout: 等待超时时间（默认 1.5 秒）。
            
        Returns:
            str: 匹配成功的会话标题文本；若超时未匹配则返回空字符串。
        """
        deadline = time.perf_counter() + timeout
        identity = ''
        while time.perf_counter() < deadline:
            identity = self.read_active_chat_identity()
            if self.identity_matches(identity, company):
                return identity
            time.sleep(0.2)
        return ''

    def read_messages(self) -> List[dict]:
        """注入 JS 读取当前聊天记录列表中的所有气泡。
        
        自动判别消息是否由我方发送（mine）以及是否包含图片元素（has_image）。
        
        Returns:
            List[dict]: 格式为 [{'text': str, 'mine': bool, 'has_image': bool}, ...] 的列表。
        """
        return self._chat().run_js("""
            const selectors = [
              '.chat-record .item-myself .text',
              '.chat-record .item-myself .item-image',
              '.chat-message-list .item-myself .text',
              '.chat-message-list .item-myself .item-image',
              '[class*="message-list"] [class*="myself"] .text',
              '[class*="message-list"] [class*="mine"] .text',
              '.chat-record .message-item', '.chat-record li', '[class*="message-item"]', '.message-image-content'
            ];
            const seen = new Set(), out = [];
            for (const s of selectors) for (const x of document.querySelectorAll(s)) {
              if (seen.has(x)) continue; seen.add(x);
              // 严格筛选正文图片气泡，排除系统推荐卡片图标、模糊头像及表情
              const chatImgs = Array.from(x.querySelectorAll('img, .message-image')).filter(img => {
                const cls = ((img.className || '') + ' ' + (img.parentElement?.className || '')).toLowerCase();
                return !cls.includes('avatar') && !cls.includes('msg-blur') && !cls.includes('message-card') && !cls.includes('figure') && !cls.includes('emotion');
              });
              const hasChatImg = chatImgs.length > 0 || !!x.querySelector('img.message-image, .item-image img, .message-image-content img');

              out.push({
                text: x.innerText || '',
                mine: !!x.closest('.item-myself,[class*="myself"],[class*="mine"]'),
                has_image: hasChatImg
              });
            }
            return out;
        """) or []

    def read_input_value(self) -> str:
        """读取当前输入框内可见的草稿文本内容。
        
        Returns:
            str: 输入框内部文本或 value；未找到有效输入框时返回空字符串。
        """
        return self._chat().run_js("""
            const es = document.querySelectorAll('#chat-input,[contenteditable="true"],.chat-input,textarea.input,textarea');
            for (const e of es) {
                if (e.offsetWidth > 50 && e.offsetHeight > 20) return e.innerText || e.value || '';
            }
            return '';
        """) or ''

    def _composer(self):
        """寻找当前聊天窗口中可见且尺寸合规的输入框控件（contenteditable 或 textarea）。
        
        Raises:
            RuntimeError: 当找不到尺寸大于 50x20 的输入控件时抛出。
        """
        chat = self._chat()
        selectors = (
            'css:#chat-input',
            'css:[contenteditable="true"]',
            'css:.chat-input',
            'css:textarea.input',
            'css:textarea'
        )
        for selector in selectors:
            try:
                for el in chat.eles(selector, timeout=0.5):
                    try:
                        if el.rect.size[0] > 50 and el.rect.size[1] > 20:
                            return el
                    except Exception:
                        continue
            except Exception:
                continue
        raise RuntimeError('聊天输入框未就绪：可见 contenteditable/textarea 均不存在')

    def wait_for_composer(self, timeout: float = COMPOSER_TIMEOUT):
        """轮询等待聊天输入框渲染就绪。
        
        Args:
            timeout: 超时等待时间（秒）。
            
        Returns:
            ChromiumElement: 找到的输入框元素。
            
        Raises:
            RuntimeError: 超时仍未找到可用输入框时抛出。
        """
        deadline = time.perf_counter() + timeout
        last = None
        while time.perf_counter() < deadline:
            try:
                return self._composer()
            except Exception as exc:
                last = exc
                time.sleep(0.25)
        raise RuntimeError(str(last or '聊天输入框未就绪'))

    def focus_input(self) -> None:
        """点击聊天输入框以聚焦并激活光标。"""
        self._composer().click()

    def fill_input(self, text: str) -> None:
        """清空输入框并输入指定文本内容。
        
        Args:
            text: 待输入的文字内容。
        """
        el = self._composer()
        try:
            el.clear()
        except Exception:
            pass
        el.input(text)

    def press_enter(self) -> None:
        """使用 CDP Action 模拟按下并弹起 Enter 回车键以发送消息。"""
        actions = self._chat().actions
        actions.key_down('ENTER')
        actions.key_up('ENTER')

    def click_send_button(self) -> None:
        """查找并点击聊天界面上的发送按钮。
        
        Raises:
            RuntimeError: 当找不到发送按钮时抛出。
        """
        chat = self._chat()
        el = chat.ele('css:.btn-send', timeout=2) or chat.ele('css:.btn-sure-v2', timeout=2)
        if not el:
            raise RuntimeError('发送按钮不存在')
        el.click()

    def upload_file(self, path: str) -> None:
        """通过注入文件路径到 input[type=file] 控件触发图片/简历上传。
        
        Args:
            path: 本地待上传文件的绝对路径。
            
        Raises:
            RuntimeError: 页面未找到文件上传控件时抛出。
        """
        chat = self._chat()
        el = (chat.ele('css:.btn-sendimg input[type="file"]', timeout=2)
              or chat.ele('css:input[type="file"][accept*="image"]', timeout=2)
              or chat.ele('css:input[type="file"]', timeout=2))
        if not el:
            raise RuntimeError('文件上传控件不存在')
        el.input(path)


def ensure_cdp_page(cdp_url: str = 'http://127.0.0.1:9223', target_url: str = 'https://www.zhipin.com/web/geek/chat'):
    """连接到现有 DevTools 调试浏览器，并确保存在可操作的目标页面。
    
    处理边界异常情况：
    - 若浏览器进程存活但所有标签页均被关闭（零标签），通过 CDP 的 /json/new 端点创建新标签，无需人工干预；
    - 若存在已关闭但残留的陈旧 target id，自动进行重试并拉起新页面。
    
    Args:
        cdp_url: Chrome 远程调试端口地址（如 http://127.0.0.1:9224）。
        target_url: 需要导航并驻留的目标网页 URL。
        
    Returns:
        ChromiumPage: 连接成功的 DrissionPage 页面实例。
    """
    import json
    from urllib.request import Request, urlopen
    from DrissionPage import ChromiumPage

    address = cdp_url.replace('http://', '').replace('https://', '')
    try:
        # 查询当前浏览器所有调试目标列表
        with urlopen(cdp_url.rstrip('/') + '/json/list', timeout=5) as response:
            targets = json.load(response)
    except Exception:
        targets = []
        
    pages = [t for t in targets if t.get('type') == 'page']
    target_id = next((t.get('id') for t in pages if 'zhipin.com' in (t.get('url') or '')), None)
    
    # 若当前没有任何 page 类型的标签页，调用 /json/new 接口主动开启一个
    if not pages:
        req = Request(cdp_url.rstrip('/') + '/json/new?' + target_url, method='PUT')
        with urlopen(req, timeout=10) as response:
            json.load(response)
        with urlopen(cdp_url.rstrip('/') + '/json/list', timeout=10) as response:
            pages = [t for t in json.load(response) if t.get('type') == 'page']
        target_id = next((t.get('id') for t in pages if 'zhipin.com' in (t.get('url') or '')), None)
        
    try:
        page = ChromiumPage(address, tab_id=target_id)
        page.get(target_url)
        return page
    except Exception:
        # 兜底：处理 target id 已失效的情况，通过刷新 target list 重新建页
        req = Request(cdp_url.rstrip('/') + '/json/new?' + target_url, method='PUT')
        with urlopen(req, timeout=10) as response:
            json.load(response)
        with urlopen(cdp_url.rstrip('/') + '/json/list', timeout=10) as response:
            fresh = [t for t in json.load(response) if t.get('type') == 'page']
        fresh_id = next((t.get('id') for t in fresh if target_url.split('/')[2] in (t.get('url') or '')), None)
        page = ChromiumPage(address, tab_id=fresh_id)
        page.get(target_url)
        return page

