#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动投递模块：使用 DrissionPage 控制浏览器完成 BOSS 直聘投递操作

流程：
  1. 打开岗位详情 URL
  2. 点击「立即沟通」
  3. 如有弹窗，关闭弹窗
  4. 点击「继续沟通」
  5. 根据简历和岗位要求生成招呼语，输入聊天框
  6. 点击发送按钮
  7. 发送简历附件（可选，通过「发送图片」上传简历文件）
"""

import os
import sys
import json
import re
import time
import random
import functools
from typing import List, Dict, Any, Optional, Union

from .config import ResumeProfile, OUTPUT_DIR, get_latest_run_dir, create_run_dir
from .paths import apply_log_path
from .utils import ensure_output_dir
from .scoring import hr_activity_rank, hr_activity_sort_key

# 登录状态检测复用 boss_crawler.auth，不在本模块内嵌 copy（旧 copy 缺
# check_login_elements 回退，已漂移）。这里只把 scripts/ 塞进 sys.path，不能顶层
# import boss_crawler.auth：auth → resume_matcher.paths → 本包 __init__ → auto_apply
# 会构成循环引用（auth 在 import 中途拿不到 check_login_status）。真正的 import 延到
# 调用时，见下方 check_login_status 的懒加载包装。
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

# 计时埋点：stage_timer 在 scripts/ 下（本模块是 scripts/resume_matcher/）。
# 导入失败一律退化成不计时，绝不影响投递。
try:
    import stage_timer
except ImportError:                                          # pragma: no cover
    import os as _os
    import sys as _sys
    _sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
    try:
        import stage_timer
    except ImportError:
        stage_timer = None

# 浏览器可执行文件定位：本模块是 resume_matcher 包，browser_finder 在 scripts/ 根，
# 同样靠把父目录塞进 sys.path（与上面 stage_timer 同款做法）。找不到也不碍事，
# 找不到浏览器时下方投递代码自然退化成「不显式 set_browser_path」。
_STAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # scripts/
if _STAGE_DIR not in sys.path:
    sys.path.insert(0, _STAGE_DIR)
try:
    from browser_finder import find_chrome_browser
except ImportError:                                          # pragma: no cover
    find_chrome_browser = None

# 尝试导入浏览器自动化库
try:
    from DrissionPage import WebPage, ChromiumOptions
    HAS_DRISSION = True
except ImportError:
    HAS_DRISSION = False


# ==================== XPath 常量 ====================

# 立即沟通按钮
XPATH_START_CHAT = (
    "//div[@class='btn-container']"
    "//a[@class='btn btn-startchat']"
    "[contains(text(),'立即沟通')]"
)

# 继续沟通按钮（点击「立即沟通」后可能出现）
XPATH_CONTINUE_CHAT = (
    "//div[@class='btn-container']"
    "//a[@class='btn btn-startchat']"
    "[contains(text(),'继续沟通')]"
)

# 弹窗关闭按钮
XPATH_POPUP_CLOSE = "//i[@class='icon-close']"

# 聊天输入框
XPATH_CHAT_INPUT = "//div[@id='chat-input']"

# 发送按钮
XPATH_SEND_BUTTON = "//button[@type='send']"

# 备用：投递简历按钮
XPATH_DELIVER_RESUME = "//div[@class='btn-container']//a[contains(text(),'投递简历')]"

# 发送图片按钮（聊天工具栏）
XPATH_SEND_IMAGE = "//div[@aria-label='发送图片']"

# 图片上传后的 file input
CSS_FILE_INPUT = "css:input[type='file']"

# 备用：发送简历按钮（聊天面板中）
XPATH_SEND_RESUME = "//span[contains(text(),'发简历')]"


# BOSS 直聘消息列表的预览框只显示前 15 个字（含标点）。HR 是在一屏几十条未读里扫
# 这 15 个字决定点不点开，所以它是标题、不是开场白 —— 「您好，我是XXX」开头等于把
# 整个预览框让给客套话，HR 划过去看不到任何有效信息。
#
# 分场景的前 15 字公式（实习看到岗时间、社招看成果数字、校招看学校奖项）在
# prompts/greeting.st 里，那是 AI 模式的口径。这里只做模板模式能做的那件机械事：
# 把事实顶到最前面，问候语挪到 15 字之后。改口径时两处一起改。
PREVIEW_LEN = 15

# 出现在开头就等于浪费预览框的词。
_WASTED_OPENERS = ('您好', '你好', '我是', '我对', '还招', '虽然', '尊敬的', '贵公司', '贵司')


def preview(text: str) -> str:
    """消息在 HR 列表里露出的那一截。"""
    return (text or '').strip().replace('\n', '')[:PREVIEW_LEN]


def has_wasted_preview(text: str) -> bool:
    """前 15 个字是不是被客套话占掉了。自检用，也给生成出来的招呼语做校验。"""
    return preview(text).startswith(_WASTED_OPENERS)


def _lead(profile: ResumeProfile, key_skills: List[str]) -> str:
    """拼前 15 个字：只用简历里确有的事实，按场景把最硬的一条顶到最前面。

    到岗日期 / 可实习时长 / 每周出勤这三样，是对方会照着安排工位和排期的**承诺**，
    简历没写就不能替用户猜一个 —— 猜错了是失信，不是文案问题。所以只在
    basic_info.availability 里明确给了才用，否则退到年限/学校/技能的公式。
    """
    avail = (profile.basic_info or {}).get('availability')
    if not isinstance(avail, dict):
        avail = {}
    can_start = str(avail.get('can_start') or '').strip()
    duration = str(avail.get('duration') or '').strip()
    days = str(avail.get('days_per_week') or '').strip()

    edu = profile.education or {}
    school = str(edu.get('school') or '').strip()
    degree = str(edu.get('degree') or '').strip()
    grad = str(edu.get('graduation_year') or '').strip()
    top = key_skills[0] if key_skills else ''

    # `or 0` 而非 get 的默认值：应届简历里 total_years 是显式 null（见本文件 142 行）
    try:
        years = int(float(profile.experience.get('total_years') or 0))
    except (TypeError, ValueError):
        years = 0

    # 实习岗：到岗时间 > 时长/出勤 > 学校。实习生技能大多差不多，HR 最怕招到随时
    # 跑路的人，谁能最快补上缺口谁占先 —— 学校只在极好时才值得占这 15 个字。
    if can_start:
        return f"【{can_start}到岗】{school or degree}"
    if duration or days:
        parts = []
        if duration:
            parts.append(f"可实习{duration}")
        if days:
            parts.append(f"周{days}")
        return "/".join(parts) + (f" {school}" if school and len("/".join(parts)) < 10 else "")

    if years > 0:                                  # 社招：年限 + 最匹配的那项技能
        lead = f"{years}年{top}经验" if top else f"{years}年工作经验"
    elif grad and school:                          # 校招：届别 + 学校学历
        lead = f"{grad[-2:]}届{school}{degree}"
    elif top:                                      # 兜底：技能顶上去，也比「您好」强
        lead = f"{top}方向"
    else:
        return ""

    # 预览框还有空位就再塞一项技能，但必须整个塞得进 15 个字 —— 被截断的半个技能名
    # （「/Pyt」）比留白更难读，那还不如让「，应聘「」自然占掉尾巴。
    if top and top not in lead and len(lead) + 1 + len(top) <= PREVIEW_LEN:
        lead = f"{lead}/{top}"
    return lead


def generate_greeting(
    profile: Optional[ResumeProfile] = None,
    job: Optional[Dict[str, Any]] = None,
    custom_greeting: Optional[str] = None
) -> str:
    """
    生成个性化招呼语。

    优先使用 custom_greeting（Claude 预生成的），
    其次根据 profile + job 模板生成。

    Args:
        profile: 简历结构化信息
        job: 岗位字典
        custom_greeting: 自定义招呼语（由 Claude 预生成）

    Returns:
        招呼语字符串
    """
    if custom_greeting:
        return custom_greeting

    if profile is None or job is None:
        return _default_greeting(job)

    # 从 profile 和 job 中提取信息生成模板招呼语
    name = profile.basic_info.get('name', '')
    position = job.get('职位', '')
    company = job.get('公司', '')

    # 提取核心技能匹配
    # `or []` 逐项兜底：某类技能为空时值是 null 而非缺键，get 的默认值不生效，
    # None + list 直接 TypeError 带崩招呼语生成（同本文件 128 行的坑）
    skills = profile.skills or {}
    all_skills = (
        (skills.get('programming') or [])
        + (skills.get('frameworks') or [])
        + (skills.get('tools') or [])
        + (skills.get('other') or [])
    )

    # 提取关键技能词（取前 5 个最有辨识度的）
    key_skills = _pick_key_skills(all_skills, job)

    # 提取相关项目经验
    # 只看 projects：experience.companies 的 name 是公司名，
    # 套进下面「曾主导 XX」的句式会变成病句
    relevant_project = _pick_relevant_project(profile.projects, job)

    # 学历
    education = profile.education
    degree = education.get('degree', '')
    major = education.get('major', '')
    school = education.get('school', '')

    # 经验年限 —— 用 `or` 兜底：应届简历里 total_years 是 null 而非缺键，
    # get 的默认值不生效，`None > 0` 直接 TypeError（同 scoring.py:674 的坑）
    total_years = profile.experience.get('total_years') or 0
    exp_desc = f"{total_years}年" if total_years > 0 else "实习"

    # 构建招呼语
    lines = []

    # 开头 —— 事实顶到最前面，问候语跟在后面。顺序是有意的：这一行的前 15 个字
    # 就是 HR 在列表里唯一看得到的东西。
    lead = _lead(profile, key_skills)
    if lead:
        lines.append(f"{lead}，应聘「{position}」。您好，我是{name}。")
    else:
        lines.append(f"您好，我是{name}，应聘贵公司「{position}」。")

    # 学历 + 专业（隐去具体二本校名，突出专业与届别）
    lines.append(f"我是自动化专业{degree}（27届），有{exp_desc}开发经验。")

    # 技能匹配
    if key_skills:
        skills_str = "、".join(key_skills[:6])
        lines.append(f"技术栈方面，熟练掌握{skills_str}。")

    # 项目亮点
    if relevant_project:
        lines.append(f"做过{relevant_project}，具备实际项目落地经验。")

    # 收尾
    lines.append("已附简历长图，方便看一下吗？期待与您交流！")

    greeting = "\n".join(lines)

    # 如果超长则精简
    if len(greeting) > 500:
        greeting = _compact_greeting(greeting, name, position, key_skills)

    return greeting


def validate_greeting_content(greeting: Optional[str]) -> Tuple[bool, str]:
    """
    路由审查：投递内容得体性门禁。
    严格审查要发送的招呼语，杜绝校名泄露、错误届别、AI 套话及违背求职策略的内容。
    """
    if not greeting or not greeting.strip():
        return False, "招呼语为空"

    text = greeting.strip()

    # 1. 校名红线审查
    forbidden_schools = ["湖北文理", "文理学院", "文理本科"]
    for s in forbidden_schools:
        if s in text:
            return False, f"包含禁用校名字样「{s}」（必须使用「自动化专业本科」或「大三」）"

    # 2. 错误届别红线审查（候选人明确为 27 届本科生）
    wrong_grads = ["23届", "24届", "25届", "26届", "28届"]
    for g in wrong_grads:
        if g in text:
            return False, f"包含错误届别「{g}」（候选人实为27届本科生）"

    # 3. 机械做题家 / 一眼 AI 套话审查
    if "岗位关键词" in text and ("支撑" in text or "匹配" in text):
        return False, "包含机械套话「岗位关键词...均有对应支撑」"

    if "涵盖VFS" in text:
        return False, "包含晦涩生硬架构词「涵盖VFS」"

    if "不仅熟悉" in text and "掌握独立设计" in text:
        return False, "包含机械八股套话句式"

    # 4. 长度与完整性审查
    if len(text) < 25:
        return False, f"招呼语过短（仅 {len(text)} 字，缺乏实质内容）"

    if len(text) > 450:
        return False, f"招呼语过长（共 {len(text)} 字，超过HR阅读舒适度）"

    return True, "得体合格"


def _pick_key_skills(all_skills: List[str], job: Dict[str, Any]) -> List[str]:
    """从技能列表中选出与岗位最相关的关键词

    排序依据（依次）：
      1. 技能标签命中 > 岗位职责正文命中 > 未命中
      2. 在 JD 中首次出现的位置越靠前，说明越是核心要求
      3. 简历中的原始顺序（稳定排序，简历自己的优先级）
    """
    tags = job.get('技能标签', '') or ''
    body = job.get('岗位要求和职责', '') or ''
    tags_lower = tags.lower()
    jd_lower = (tags + body).lower()

    scored = []
    for idx, skill in enumerate(all_skills):
        if not skill or len(skill) < 2:
            continue
        if len(skill) > 15 or skill.startswith("传统") or "开发" in skill:
            continue

        s = skill.lower()
        if s in tags_lower:
            score = 200          # 招聘方自己打的标签，最能代表岗位画像
        elif s in jd_lower:
            score = 100
        else:
            score = 0

        # 未命中的技能没有位置信息，排到最后
        pos = jd_lower.find(s) if score else len(jd_lower)
        scored.append((-score, pos, idx, skill))

    scored.sort()

    # 去重优先，取前 8 个
    seen = set()
    result = []
    for _, _, _, s in scored:
        if s.lower() not in seen:
            seen.add(s.lower())
            result.append(s)
        if len(result) >= 8:
            break

    return result


_TOKEN_RE = re.compile(r'[A-Za-z][A-Za-z0-9+#.]*|[一-龥]{2,}')


def _tokenize(text: str) -> List[str]:
    """把中英文混排文本切成可匹配的词元

    英文按连续字母数字串切；中文没有分词库，用 2-4 字滑动窗口，
    足以覆盖「向量检索」「推荐系统」这类技术名词。
    """
    tokens = []
    for m in _TOKEN_RE.finditer(text or ''):
        t = m.group()
        if t[0].isascii():
            if len(t) >= 2:
                tokens.append(t.lower())
        else:
            for n in (4, 3, 2):
                for i in range(len(t) - n + 1):
                    tokens.append(t[i:i + n])
    return tokens


def _pick_relevant_project(projects: List[Dict], job: Dict[str, Any]) -> Optional[str]:
    """选出与岗位最相关的项目名

    按命中的**不同词元数**打分，技术栈命中权重更高（技术栈是硬匹配，
    项目描述里的词更可能是巧合）。
    """
    jd = (
        (job.get('技能标签', '') or '')
        + (job.get('岗位要求和职责', '') or '')
        + (job.get('职位', '') or '')
    )
    jd_lower = jd.lower()

    best = None
    best_score = 0

    for proj in projects:
        if not isinstance(proj, dict):
            continue
        name = proj.get('name', '') or ''
        desc = proj.get('description', '') or ''
        tech_stack = proj.get('tech_stack', []) or []

        score = 0
        for token in set(_tokenize(name + ' ' + desc)):
            if token in jd_lower:
                score += 1
        for tech in tech_stack:
            if tech and str(tech).lower() in jd_lower:
                score += 3

        if score > best_score:
            best_score = score
            best = name

    return best


def _default_greeting(job: Optional[Dict[str, Any]] = None) -> str:
    """默认招呼语（连 profile 都没有时的兜底）

    没有简历事实可用，就把岗位名顶到最前面 —— 至少预览框里露出的是「应聘XXX」，
    HR 知道你在说哪个岗，而不是一句 15 个字的客套话。
    """
    position = job.get('职位', '该岗位') if job else '该岗位'
    return (
        f"应聘「{position}」，技术背景与岗位要求匹配。"
        f"您好，我看到贵公司这个岗位，已附简历，方便看一下吗？"
    )


def _compact_greeting(greeting: str, name: str, position: str, skills: List[str]) -> str:
    """精简招呼语到 300 字以内

    同样保持事实前置。原来这里硬编码了「AI应用项目落地经验」—— 那是从某次实跑里
    带出来的领域词，投任何非 AI 岗都会变成一句假话，已去掉。
    """
    skills_str = "、".join(skills[:4])
    head = f"熟练{skills_str}" if skills_str else "技术栈匹配"
    return (
        f"{head}，应聘「{position}」，与岗位要求高度匹配。"
        f"您好，我是{name}，已附简历，方便看一下吗？"
    )


def send_resume_attachment(
    dp: WebPage,
    resume_file_path: str,
    timeout: float = 10.0
) -> bool:
    """
    在聊天窗口中发送简历附件（图片/文件）。

    策略（按优先级尝试）：
        A. 先查找页面所有隐藏 <input type="file">，对匹配图片/PDF 的直接 input()
           → 绕过原生文件对话框
        B. 如果找不到合适的 file input，通过 JS 注入一个来接收文件
        C. 最后兜底：点击「发送图片」div + CDP 拦截文件对话框

    Args:
        dp: DrissionPage WebPage 实例（需已在聊天页面）
        resume_file_path: 简历文件路径（支持图片、PDF等）
        timeout: 操作超时

    Returns:
        是否成功发送
    """
    if not resume_file_path or not os.path.exists(resume_file_path):
        print(f"  ⚠ 简历文件不存在: {resume_file_path}")
        return False

    print(f"  📎 准备发送简历附件: {os.path.basename(resume_file_path)}")

    ext = os.path.splitext(resume_file_path)[1].lower()
    is_image = ext in ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

    # ── 送达校验基线：记录发送前的图片消息数量 ──
    # ⚠ 图片消息在 innerText 中不可见，只能数 img.message-image 元素。
    #   基线为 -1 表示读不到消息列表，此时无法校验，退化为「上传即返回」。
    baseline = _count_chat_images(dp) if is_image else -1
    can_verify = is_image and baseline >= 0
    if can_verify:
        print(f"  📐 校验基线: 当前 {baseline} 张图片消息")

    def _verify_sent() -> bool:
        """确认图片消息数量增加了 —— 这是唯一可信的送达证据"""
        if not can_verify:
            return True
        for _ in range(int(timeout)):
            time.sleep(1)
            if _count_chat_images(dp) > baseline:
                return True
        return False

    # ── 策略 0：优先直接使用聊天工具栏专属图片 file input ──
    try:
        tool_img_input = dp.ele('css:.btn-sendimg input[type="file"]', timeout=1) or dp.ele('css:input[type="file"][accept*="image"]', timeout=1)
        if tool_img_input:
            tool_img_input.input(resume_file_path)
            if _verify_sent():
                after = _count_chat_images(dp) if can_verify else -1
                suffix = f"，图片消息 {baseline} → {after}" if can_verify else ""
                print(f"  ✅ 简历长图已送达 (聊天工具栏上传){suffix}")
                return True
    except Exception as e:
        print(f"  ⚠ 工具栏图片上传尝试失败: {e}")

    # ── 策略 A：直接找隐藏 file input（不点击按钮，绕过原生对话框）──
    # ⚠ 每次只投递一个 input 并立即校验，成功即停 ——
    #   历史上「往所有 file input 都塞文件」会导致重复发送。
    file_inputs = _find_all_file_inputs(dp)
    if file_inputs:
        print(f"  🔍 找到 {len(file_inputs)} 个 file input，逐个尝试并校验...")
        ordered = []
        fallback = []
        for fi in file_inputs:
            try:
                accept = (fi.attr('accept') or '').lower()
            except Exception:
                accept = ''
            matched = (
                (is_image and 'image' in accept)
                or (not is_image and ext.lstrip('.') in accept)
            )
            (ordered if matched else fallback).append((fi, accept))

        for fi, accept in ordered + fallback:
            try:
                fi.input(resume_file_path)
            except Exception as e:
                print(f"  ⚠ input(accept={accept[:30]!r}) 失败: {e}")
                continue

            if _verify_sent():
                after = _count_chat_images(dp) if can_verify else -1
                suffix = f"，图片消息 {baseline} → {after}" if can_verify else "（无法校验）"
                print(f"  ✅ 简历附件已送达 (策略A: file input){suffix}")
                return True
            print(f"  ⚠ 该 input 未产生新图片消息，尝试下一个")

    # ── 策略 B：JS 注入 file input → 设置文件 → 触发 change 事件 ──
    print(f"  🔄 尝试策略B: JS 注入 file input...")
    if _upload_via_js_injection(dp, resume_file_path):
        if _verify_sent():
            print(f"  ✅ 简历附件已送达 (策略B)")
            return True
        print(f"  ⚠ 策略B 未产生新图片消息")

    # ── 策略 C：点击「发送图片」div（兜底，会弹出原生对话框需手动处理）──
    print(f"  🔄 尝试策略C: 点击「发送图片」按钮...")
    img_btn = _find_element(dp, [
        XPATH_SEND_IMAGE,
        "css:[aria-label='发送图片']",
        "css:.icon-send-image",
    ], timeout=3)

    if not img_btn:
        print(f"  ⚠ 未找到「发送图片」按钮")
        return False

    try:
        # 点击前先尝试用 CDP 拦截文件对话框
        _auto_accept_file_dialog(dp, resume_file_path)
        img_btn.click()
        time.sleep(3)
        if _verify_sent():
            print(f"  ✅ 简历附件已送达 (策略C)")
            return True
        print(f"  ⚠ 策略C: 未确认送达，如弹出对话框请手动选择文件")
        return False
    except Exception as e:
        print(f"  ❌ 策略C失败: {e}")
        return False


def _find_all_file_inputs(dp: WebPage) -> list:
    """查找页面上所有 <input type='file'>（包括隐藏的），返回元素列表"""
    try:
        # 用 JS 查找所有 file input（绕过 Selenium 不可见限制）
        result = dp.run_js("""
            const inputs = document.querySelectorAll('input[type="file"]');
            return inputs.length;
        """)
        count = int(result) if result else 0

        if count == 0:
            return []

        # 逐个获取
        inputs = []
        for i in range(count):
            try:
                el = dp.ele(f'css:input[type="file"]', index=i + 1, timeout=1)
                if el:
                    inputs.append(el)
            except Exception:
                continue
        return inputs
    except Exception:
        return []


def _upload_via_js_injection(dp: WebPage, file_path: str) -> bool:
    """
    通过 JS 注入一个 file input 元素，
    用 DrissionPage 设置文件值，再派发 change 事件触发上传。
    """
    try:
        # 1. 注入隐藏的 file input 到 body
        injected_id = '__auto_apply_file_input__'
        dp.run_js(f"""
            if (!document.getElementById('{injected_id}')) {{
                const input = document.createElement('input');
                input.type = 'file';
                input.id = '{injected_id}';
                input.style.display = 'none';
                input.accept = 'image/*,.pdf';
                document.body.appendChild(input);

                // 监听 change：找到原生的上传组件并派发文件
                input.addEventListener('change', (e) => {{
                    const file = e.target.files[0];
                    if (!file) return;
                    // 尝试找到页面上的 paste/drop 区域并派发 DataTransfer
                    const dt = new DataTransfer();
                    dt.items.add(file);
                    const pasteEvent = new ClipboardEvent('paste', {{
                        clipboardData: dt, bubbles: true, cancelable: true
                    }});
                    document.dispatchEvent(pasteEvent);
                }});
            }}
        """)
        time.sleep(0.5)

        # 2. 找到注入的 input 并设置文件
        injected = dp.ele(f'#{injected_id}', timeout=2)
        if injected:
            injected.input(file_path)
            time.sleep(2)
            print(f"  ✅ 简历附件已上传 (策略B: JS 注入)")
            return True
    except Exception as e:
        print(f"  ⚠ 策略B异常: {e}")

    return False


def _auto_accept_file_dialog(dp: WebPage, file_path: str) -> None:
    """通过 CDP 设置文件对话框自动选择文件"""
    try:
        cdp = dp._control_browser
        if cdp:
            cdp.Page.setInterceptFileChooserDialog({'enabled': True})
            # 注册回调：当对话框打开时自动选择文件
            # 注意：这是预先设置，下次文件对话框打开时自动生效
            dp.set.upload_files(file_path)
    except Exception:
        pass  # 静默失败，回退到手动


def _ensure_login(dp: WebPage, max_wait: int = 300) -> bool:
    """
    确保浏览器已登录 BOSS 直聘。

    1. 先快速检测是否已登录
    2. 未登录则进入轮询等待（每 3s 刷新），最长 max_wait 秒

    Returns:
        True 已登录，False 超时
    """
    # 先导航到首页检查
    dp.get('https://www.zhipin.com/web/geek/recommend')
    time.sleep(2)

    if check_login_status(dp):
        print(f"  [LOGIN_OK] 检测到已登录")
        return True

    print(f"  [需要登录] 请在浏览器窗口中完成登录...")
    print(f"  [需要登录] 脚本将每 3s 自动检测，最长等待 {max_wait}s...")

    elapsed = 0
    interval = 3
    while elapsed < max_wait:
        mins = elapsed // 60
        secs = elapsed % 60
        if elapsed > 0:
            print(f"  [等待登录] {mins}m{secs}s / {max_wait//60}m ...")
        time.sleep(interval)
        elapsed += interval

        try:
            dp.refresh()
            time.sleep(1)
        except Exception:
            pass

        if check_login_status(dp):
            print(f"  [LOGIN_OK] 检测到登录成功！（耗时 {elapsed}s）")
            return True

    print(f"  [LOGIN_FAIL] 登录超时（{max_wait}s）")
    return False


def check_login_status(page) -> bool:
    """检测 BOSS 直聘登录状态，委托给 boss_crawler.auth（与 crawler 共用同一份判定）。

    模块加载期 auto_apply ←→ boss_crawler.auth 循环引用（auth 经 resume_matcher.paths
    触发本包 __init__ 再回到 auto_apply），所以这里懒加载，第一次调用时才 import。
    """
    from boss_crawler.auth import check_login_status as _impl
    return _impl(page)


def auto_apply_jobs(*args, **kwargs):
    """`_auto_apply_jobs_impl` 的计时包装。

    只有显式传了 output_dir 才计时：impl 在 output_dir 为空时会自行定位最近运行目录
    或新建一个，在这里重复那套逻辑有可能多建一个空目录 —— 宁可不计时，也不让埋点
    产生副作用。

    崩了也要留下耗时：stage_timer.stage 会照抛异常但落盘 status=error。投递是整个
    流程里唯一不可逆的一步，「投到第几个崩的、崩之前跑了多久」是复盘时最要紧的信息。
    """
    run_dir = kwargs.get('output_dir')
    if run_dir is None and len(args) >= 7:
        run_dir = args[6]                    # 第 7 个位置参数就是 output_dir
    if not run_dir or stage_timer is None:
        return _auto_apply_jobs_impl(*args, **kwargs)
    with stage_timer.stage(run_dir, 'apply'):
        return _auto_apply_jobs_impl(*args, **kwargs)


def _auto_apply_jobs_impl(
    qualified_jobs: List[Dict[str, Any]],
    _profile: ResumeProfile,
    max_applications: int = 10,
    headless: bool = False,
    greetings: Optional[Dict[str, str]] = None,
    resume_file_path: Optional[Union[str, Dict[str, str]]] = None,
    output_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    自动投递简历到匹配岗位。

    流程：
        1. 打开岗位详情页
        2. 点击「立即沟通」
        3. 关闭弹窗（如有）
        4. 点击「继续沟通」
        5. 输入招呼语 → 发送
        6. 发送简历附件（如提供 resume_file_path）

    Args:
        qualified_jobs: 符合条件的岗位列表
        _profile: 简历结构化信息（用于生成招呼语）
        max_applications: 最大投递数量
        headless: 是否无头模式
        greetings: 预生成的招呼语字典 {job_link: greeting_text}，优先使用
        resume_file_path: 简历文件路径（图片/PDF），用于「发送图片」上传附件。
                    传字符串则整批共用一个文件；传 {job_link: path} 则按岗位
                    各发各的（分岗位定制简历走这条）。
        output_dir: 输出目录（投递日志保存位置）。
                    默认自动定位最近运行目录或创建新目录。

    Returns:
        投递结果列表
    """
    # Windows 控制台默认 GBK，打印 emoji 会抛 UnicodeEncodeError；统一重配为 UTF-8。
    # check_artifacts.py / write_application_md.py 都这么干，本模块此前漏了，导致投递在
    # 打印 emoji 时崩掉一次。reconfigure 失败（如非标准 stdout）不阻断投递。
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, ValueError, OSError):
            pass

    if not HAS_DRISSION:
        print("错误: DrissionPage 未安装，无法自动投递。pip install DrissionPage")
        return []

    if not qualified_jobs:
        print("没有可投递的岗位")
        return []

    # 按优先级排序：HR 活跃度优先，匹配分次之
    #
    # 活跃度作主键是有意的：到这一步的岗位都已通过硬门禁、又经用户在投递范围那道门禁
    # 手工确认，都是值得投的 —— 那么先投会回复的那个。未采集活跃度（无 -d）时全部折成 -1，
    # 排序自动退化成纯匹配分排序。
    #
    # 注意 max_applications 的截断发生在排序之后：当选中岗位数超过上限时，
    # 活跃度高但匹配分低的岗位会挤掉匹配分高但 HR 不活跃的岗位。
    # 若要改成匹配分优先、活跃度只做同分裁决，把前两个键对调即可。
    sorted_jobs = sorted(
        qualified_jobs,
        key=lambda j: (
            -hr_activity_sort_key(j),
            -j.get('match_score', 0),
            j.get('company', '')
        )
    )
    jobs_to_apply = sorted_jobs[:max_applications]

    ranked = [hr_activity_rank(j) for j in jobs_to_apply]
    if any(r is not None for r in ranked):
        hr_order = '活跃度优先'
    else:
        hr_order = '活跃度未采集，按匹配分排序'

    print(f"\n{'='*60}")
    print(f"  🤖 自动投递模式")
    print(f"  目标岗位: {len(jobs_to_apply)} 个")
    print(f"  投递顺序: {hr_order}")
    print(f"  招呼语来源: {'Claude 预生成' if greetings else '模板自动生成'}")
    print(f"{'='*60}")

    # 配置浏览器（复用 Chrome 用户数据，保留登录态）。
    # 浏览器可执行文件走 browser_finder 分层探测（env → PATH → 注册表 → 拼路径），
    # 探测不到就跳过 set_browser_path，交给 DrissionPage 默认逻辑。
    co = ChromiumOptions()
    if find_chrome_browser:
        chrome_path = find_chrome_browser()
        if chrome_path:
            co.set_browser_path(chrome_path)

    # 持久化 Chrome Profile（复用登录状态，位于 assets/chrome_user_data）
    user_data_dir = os.path.join(OUTPUT_DIR, 'chrome_user_data')
    os.makedirs(user_data_dir, exist_ok=True)
    co.set_argument(f'--user-data-dir={user_data_dir}')

    if headless:
        co.headless(True)

    dp = WebPage(chromium_options=co)
    results = []

    # ── 确保登录 ──
    if not _ensure_login(dp, max_wait=300):
        print("❌ 登录失败，无法继续投递")
        dp.quit()
        return results

    try:
        for i, job in enumerate(jobs_to_apply):
            position = job.get('职位', job.get('position', '未知'))
            company = job.get('公司', job.get('company', '未知'))
            link = job.get('link', '')

            print(f"\n--- [{i+1}/{len(jobs_to_apply)}] {company} - {position} ---")

            result = {
                'job': job,
                'status': 'unknown',
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'error': None,
                'greeting_used': None
            }

            if not link:
                result['status'] = 'skipped'
                result['error'] = '无岗位链接'
                print(f"  ⏭ 跳过: 无链接")
                results.append(result)
                continue

            # 校验全局历史投递账本，杜绝重复投递
            from .history import is_job_applied, record_applied_job
            already_applied, prev_record = is_job_applied(job)
            if already_applied:
                prev_time = (prev_record or {}).get('applied_at', '之前')
                result['status'] = 'skipped'
                result['error'] = f'历史已投递过 ({prev_time})'
                print(f"  ⏭ 跳过: 该岗位已在历史账本中成功投递 ({prev_time})，避免重复投递！")
                results.append(result)
                continue

            try:
                # === 步骤 1：打开岗位详情页 ===
                print(f"  🌐 打开详情页...")
                dp.get(link)
                time.sleep(3)

                # === 步骤 2：点击沟通按钮 ===
                print(f"  🔍 查找沟通按钮...")
                start_btn = _find_element(dp, [
                    XPATH_START_CHAT,
                    XPATH_DELIVER_RESUME,
                    'css:.btn-startchat',
                    'css:.btn-startchat-wrap a',
                    'xpath://a[contains(@class, "btn-startchat")]',
                ])

                if start_btn:
                    btn_text = (start_btn.text or '').strip()
                    # 强安全门禁：如果按钮是「继续沟通」或「已沟通」，说明历史已投递过，坚决不二次打扰！
                    if any(kw in btn_text for kw in ["继续", "已沟通", "已投递"]):
                        print(f"  🛑 路由拦截: 页面按钮为「{btn_text}」，说明该岗位此前已沟通，绝对禁止重复打扰！")
                        result['status'] = 'skipped'
                        result['error'] = f'页面显示已沟通过({btn_text})'
                        try:
                            from .history import record_applied_job
                            record_applied_job(job=job, status='applied', greeting=None, image=None, run_dir=output_dir)
                        except Exception:
                            pass
                        results.append(result)
                        continue

                    start_btn.click()
                    print(f"  ✅ 已点击「{btn_text}」")
                    time.sleep(2.5)
                else:
                    # 如果没找到正常沟通按钮，检查页面是否存在「继续沟通」或「已沟通」
                    already_chat = dp.ele('xpath://*[contains(text(), "继续沟通") or contains(text(), "已沟通") or contains(text(), "已投递")]', timeout=1)
                    if already_chat:
                        print(f"  🛑 路由拦截: 页面发现「{already_chat.text}」，此前已沟通过，立即跳过！")
                        result['status'] = 'skipped'
                        result['error'] = '页面显示已沟通'
                        try:
                            from .history import record_applied_job
                            record_applied_job(job=job, status='applied', greeting=None, image=None, run_dir=output_dir)
                        except Exception:
                            pass
                        results.append(result)
                        continue
                    print(f"  ⚠ 未找到沟通按钮，尝试进入聊天页面...")

                # === 步骤 3：关闭弹窗（如有） ===
                _close_popup(dp)

                # === 步骤 4：确保进入聊天页并激活会话 ===
                if len(dp.tab_ids) > 1:
                    dp.to_tab(dp.tab_ids[-1])

                if "/web/geek/chat" not in dp.url:
                    dp.get("https://www.zhipin.com/web/geek/chat")
                    time.sleep(3)

                _close_popup(dp)

                # 确保在聊天页激活当前会话并等待输入框挂载
                for _ in range(6):
                    try:
                        if "/web/geek/chat" in dp.url:
                            dp.run_js("""
                            const active = document.querySelector('.geek-chat-list .chat-item.active, .chat-user-list li.selected');
                            if (!active) {
                                const first = document.querySelector('.geek-chat-list .chat-item, .chat-user-list li, [class*="chat-item"]');
                                if (first) first.click();
                            }
                            """)
                            inp = dp.ele('css:#chat-input', timeout=0.5) or dp.ele('css:[contenteditable="true"]', timeout=0.5)
                            if inp and inp.rect.size[0] > 50:
                                break
                    except Exception:
                        pass
                    time.sleep(1)

                # 强安全门禁：检查当前聊天窗口是否已经存在历史对话记录（除刚点击后系统秒发的那 1 条外）
                chat_history_state = dp.run_js("""
                    const msgs = document.querySelectorAll('.chat-message-list .message-item, .chat-record .message-item, .chat-record li');
                    const imgs = document.querySelectorAll('.chat-message-list img.message-image, .chat-record img.message-image');
                    const timeHeaders = document.querySelectorAll('.chat-message-list .message-time, .chat-record .time, .chat-message-list .time');
                    return {
                        msgCount: msgs.length,
                        imgCount: imgs.length,
                        hasMultiTimes: timeHeaders.length > 1
                    };
                """)
                if chat_history_state and (chat_history_state.get('imgCount', 0) > 0 or chat_history_state.get('msgCount', 0) >= 2 or chat_history_state.get('hasMultiTimes')):
                    print(f"  🛑 路由拦截: 聊天窗口检测到已有历史对话或已发送过简历长图（消息数: {chat_history_state.get('msgCount')}，图片数: {chat_history_state.get('imgCount')}），坚决不重复发送！")
                    result['status'] = 'skipped'
                    result['error'] = '聊天记录已存在历史对话或图片'
                    try:
                        from .history import record_applied_job
                        record_applied_job(job=job, status='applied', greeting=None, image=None, run_dir=output_dir)
                    except Exception:
                        pass
                    results.append(result)
                    continue

                # === 步骤 5：路由审查招呼语得体性 ===
                greeting = _get_greeting(job, _profile, greetings)
                result['greeting_used'] = greeting

                is_appropriate, reason = validate_greeting_content(greeting)
                if not is_appropriate:
                    print(f"  ❌ 招呼语得体性路由拦截不通过: {reason}")
                    print(f"     拦截内容: {greeting[:60]}...")
                    result['status'] = 'rejected_content'
                    result['error'] = f'招呼语得体性拦截: {reason}'
                    results.append(result)
                    continue

                greeting_ok = False
                if greeting and _input_greeting(dp, greeting):
                    print(f"  📝 已输入定制招呼语")
                    time.sleep(0.5)

                    # === 步骤 6：发送并回读聊天记录校验 ===
                    if _click_send(dp, greeting):
                        print(f"  📤 定制招呼语已发送（已校验气泡）")
                        greeting_ok = True
                        result['greeting_verified'] = True
                    else:
                        print(f"  ⚠ 招呼语发送后未检测到新气泡")
                        result['greeting_verified'] = False
                else:
                    result['greeting_verified'] = False
                    print(f"  ⚠ 无法输入定制招呼语（可能已自动发送默认问候）")

                # === 步骤 7：发送简历附件（独立强保障）===
                job_resume = _get_resume_file(job, resume_file_path)
                attachment_ok = False
                if job_resume:
                    time.sleep(1)
                    attachment_ok = send_resume_attachment(dp, job_resume)
                    result['attachment_sent'] = attachment_ok
                    if attachment_ok:
                        print(f"  ✅ 简历长图附件已送达（已校验）！")
                    else:
                        print(f"  ⚠ 简历长图未确认送达")

                if greeting_ok or attachment_ok:
                    result['status'] = 'applied'
                    print(f"  ✅ 投递达成（招呼语: {'✓' if greeting_ok else '系统默认'}, 长图: {'✓' if attachment_ok else '无'}）")
                else:
                    result['status'] = 'no_chat'
                    result['error'] = '招呼语与简历长图均未能确认送达'

            except Exception as e:
                result['status'] = 'error'
                result['error'] = str(e)
                print(f"  ❌ 异常: {e}")

            results.append(result)
            if result['status'] in ('applied', 'partial'):
                try:
                    record_applied_job(
                        job=job,
                        status=result['status'],
                        greeting=result.get('greeting_used'),
                        image=job_resume if 'job_resume' in locals() else None,
                        run_dir=output_dir
                    )
                except Exception as ex:
                    print(f"  ⚠️ 保存全局投递账本失败: {ex}")

            # 间隔等待（模拟人类操作，3-8 秒随机）
            if i < len(jobs_to_apply) - 1:
                wait = random.uniform(3, 8)
                print(f"  ⏳ 等待 {wait:.1f}s...")
                time.sleep(wait)

    finally:
        dp.quit()

    # === 保存投递记录 ===
    if output_dir is None:
        output_dir = get_latest_run_dir() or create_run_dir()
    log_path = apply_log_path(output_dir)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    applied_count = sum(1 for r in results if r['status'] == 'applied')
    partial_count = sum(1 for r in results if r['status'] == 'partial')
    failed_count = sum(1 for r in results if r['status'] in ('error', 'no_chat', 'no_button'))
    skipped_count = sum(1 for r in results if r['status'] == 'skipped')

    log_data = {
        'applied_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_attempts': len(jobs_to_apply),
        'results': results,
        'summary': {
            'applied': applied_count,
            'partial': partial_count,
            'failed': failed_count,
            'skipped': skipped_count,
        }
    }

    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)

    # === 打印汇总 ===
    print(f"\n{'='*60}")
    print(f"  📊 投递汇总")
    print(f"  成功(含招呼): {applied_count}")
    print(f"  部分成功:      {partial_count}")
    print(f"  失败:          {failed_count}")
    print(f"  跳过:          {skipped_count}")
    print(f"  记录已保存:    {log_path}")
    print(f"{'='*60}")

    return results


# 让计时包装对外表现得和实现一致：inspect.signature / help() / IDE 提示都能看到
# 真实参数表，而不是 (*args, **kwargs)。放在这里是因为 wraps 需要实现已定义。
# 副作用：包装函数的 __doc__ 被换成实现的 —— 这是想要的，计时是实现细节，
# 调用方该看到的是投递流程的说明。
functools.update_wrapper(auto_apply_jobs, _auto_apply_jobs_impl)


# ==================== 内部辅助函数 ====================

def _find_element(dp: WebPage, selectors: List[str], timeout: float = 2.0):
    """
    按优先级尝试多个选择器查找元素。
    支持 XPath 和 CSS 选择器。
    """
    for selector in selectors:
        try:
            el = dp.ele(selector, timeout=timeout)
            if el:
                return el
        except Exception:
            continue
    return None


def _close_popup(dp: WebPage) -> bool:
    """尝试关闭页面弹窗（含 BOSS 最新全屏模态遮罩）"""
    close_selectors = [
        XPATH_POPUP_CLOSE,
        'css:.dialog-wrap .close',
        'css:.dialog-wrap .icon-close',
        'css:.boss-dialog__close',
        'css:.boss-dialog .close',
        'css:.dialog-close',
        'css:.modal-close',
        'css:[class*="dialog"] .close',
        'css:[class*="dialog"] .icon-close',
        'css:[class*="dialog"] [class*="close"]',
        'css:.icon-close',
    ]
    closed = False
    for selector in close_selectors:
        try:
            el = dp.ele(selector, timeout=1)
            if el and el.rect.size[0] > 0:
                el.click()
                closed = True
                time.sleep(0.3)
        except Exception:
            continue
    try:
        dp.run_js("""
        const btns = document.querySelectorAll('.dialog-wrap .close, .dialog-wrap .icon-close, .boss-dialog__close, [class*="dialog"] [class*="close"]');
        btns.forEach(b => { if (b.offsetWidth > 0) b.click(); });
        """)
    except Exception:
        pass
    return closed


def _get_greeting(
    job: Dict[str, Any],
    profile: Optional[ResumeProfile],
    greetings: Optional[Dict[str, str]]
) -> Optional[str]:
    """获取招呼语：优先使用预生成的，否则模板生成"""
    if greetings:
        link = job.get('link', '')
        if link in greetings:
            return greetings[link]

    return generate_greeting(profile=profile, job=job)


def _get_resume_file(
    job: Dict[str, Any],
    resume_file_path: Optional[Union[str, Dict[str, str]]]
) -> Optional[str]:
    """取该岗位要发的简历附件：dict 按 job_link 取，字符串则整批共用"""
    if isinstance(resume_file_path, dict):
        return resume_file_path.get(job.get('link', ''))

    return resume_file_path


def _norm(text: str) -> str:
    """归一化：去掉所有空白，便于跨 DOM 渲染比对文本"""
    return re.sub(r'\s+', '', text or '')


def _greeting_probe(greeting: str, length: int = 14) -> str:
    """
    从招呼语中取一段稳定的特征串，用于回读聊天记录时判定是否真的发出去了。
    跳过开头的括号类标点（BOSS 渲染时可能改写），取正文前 length 个字符。
    """
    s = _norm(greeting)
    core = re.sub(r'^[【\[（(“"\'’‘]+', '', s)
    return core[:length] if len(core) >= length else core


def _read_chat_record(dp: WebPage) -> str:
    """读取当前聊天记录的纯文本。注意：图片消息在 innerText 中不可见。"""
    try:
        return dp.run_js("""
            const m = document.querySelector(
                '[class*="chat-message-list"], [class*="message-list"], .chat-record');
            return m ? m.innerText : '';
        """) or ''
    except Exception:
        return ''


def _read_chat_input(dp: WebPage) -> str:
    """回读聊天输入框的当前内容，只读取真实可见的富文本输入框"""
    try:
        return dp.run_js("""
            const els = document.querySelectorAll('#chat-input, [contenteditable="true"], textarea.input, textarea');
            for (const el of els) {
                if (el.offsetWidth > 50 && el.offsetHeight > 20) {
                    const txt = el.innerText || el.value || '';
                    if (txt.trim().length > 0) return txt;
                }
            }
            return '';
        """) or ''
    except Exception:
        return ''


def _count_chat_images(dp: WebPage) -> int:
    """
    统计聊天记录中的图片消息数量。
    只数 img.message-image，排除界面图标（msg-blur）和头像。
    """
    try:
        n = dp.run_js("""
            const m = document.querySelector(
                '[class*="chat-message-list"], [class*="message-list"], .chat-record');
            if (!m) return -1;
            return m.querySelectorAll('img.message-image').length;
        """)
        return int(n) if n is not None else -1
    except Exception:
        return -1


def _input_greeting(dp: WebPage, greeting: str) -> bool:
    """
    在聊天输入框中输入招呼语，并**回读校验文字是否真的落地**。

    只使用 DrissionPage 的 .input()（底层走 CDP 真实输入事件，浏览器视为可信输入，
    BOSS 前端框架必然更新内部 state）。
    """
    if not greeting:
        return False

    probe = _greeting_probe(greeting)

    input_selectors = [
        'css:#chat-input',
        'css:[contenteditable="true"]',
        'css:.chat-input',
        XPATH_CHAT_INPUT,
        'css:textarea.input',
        'css:textarea',
    ]

    for attempt in range(8):
        candidates = []
        for selector in input_selectors:
            try:
                for el in dp.eles(selector, timeout=0.5):
                    if el not in candidates:
                        candidates.append(el)
            except Exception:
                continue

        for el in candidates:
            try:
                sz = el.rect.size
                if sz[0] <= 50 or sz[1] <= 20:
                    continue
            except Exception:
                continue

            try:
                el.click()
                time.sleep(0.3)
                try:
                    el.clear()
                    time.sleep(0.2)
                except Exception:
                    pass
                el.input(greeting)          # CDP 真实输入
                time.sleep(1.0)
            except Exception:
                continue

            # ── 回读校验：直接校验刚才输入的当前元素与页面 ──
            try:
                elem_txt = _norm(el.text or el.value or '')
            except Exception:
                elem_txt = ''
            typed = elem_txt or _norm(_read_chat_input(dp))
            if probe and (probe in typed or len(typed) >= len(probe)):
                print(f"  ✓ 输入框已确认落地 {len(typed)} 字")
                return True

        time.sleep(1)

    return False


def _click_send(dp: WebPage, greeting: Optional[str] = None) -> bool:
    """
    发送聊天框内已输入的内容，并**回读聊天记录校验消息气泡是否出现**。
    优先点击 BOSS 直聘现代 UI 发送按钮（.btn-send / .btn-sure-v2），备选回车。
    """
    probe = _greeting_probe(greeting) if greeting else ''

    def _verify() -> bool:
        if not probe:
            return True          # 无法校验时不谎报，由调用方决定
        return probe in _norm(_read_chat_record(dp))

    # 已经发出去了（重试场景），直接返回
    if probe and _verify():
        return True

    # ── 方式 1：点击现代发送按钮（实测最稳）──
    send_selectors = [
        'css:.btn-send',
        'css:.btn-sure-v2',
        'xpath://button[contains(@class, "btn-send")]',
        'xpath://button[contains(text(), "发送")]',
        'xpath://div[contains(@class, "btn-sure-v2")]',
        XPATH_SEND_BUTTON,
    ]
    for selector in send_selectors:
        try:
            el = dp.ele(selector, timeout=1)
            if el and el.rect.size[0] > 0:
                # 等待 disabled 类消失
                for _ in range(5):
                    cls = el.attr('class') or ''
                    if 'disabled' not in cls:
                        break
                    time.sleep(0.3)
                el.click()
                time.sleep(2.5)
                if _verify():
                    print(f"  ✓ 发送已校验（按钮 {selector}）")
                    return True
        except Exception:
            continue

    # ── 方式 2：键盘回车 ──
    try:
        input_el = dp.ele('css:#chat-input', timeout=1) or dp.ele('css:[contenteditable="true"]', timeout=1)
        if input_el:
            input_el.click()
            time.sleep(0.2)
        dp.actions.type('\n')
        time.sleep(2.5)
        if _verify():
            print(f"  ✓ 发送已校验（回车）")
            return True
        print(f"  ⚠ 回车后未见消息气泡，尝试发送按钮")
    except Exception as e:
        print(f"  ⚠ 回车发送异常: {e}")

    return False

