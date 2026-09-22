# -*- coding: utf-8 -*-
"""单步实操调试器：用于一步一步手工操作 BOSS 直聘投递流程"""
import os
import sys
import time
from DrissionPage import ChromiumPage, ChromiumOptions

def get_page():
    co = ChromiumOptions()
    co.set_address('127.0.0.1:9222')
    return ChromiumPage(co)

def step1_open(url):
    page = get_page()
    print(f"🌐 正在打开岗位详情页: {url}")
    page.get(url)
    time.sleep(3)
    print(f"  当前页面标题: {page.title}")
    print(f"  当前 URL: {page.url}")
    btn = page.ele('css:.btn-startchat') or page.ele('xpath://a[contains(@class, "btn-startchat")]')
    if btn:
        text = (btn.text or '').strip()
        print(f"  🔍 沟通按钮已找到: 「{text}」")
        return text
    else:
        print("  ⚠️ 未找到 .btn-startchat 按钮")
        return None

def step2_click_and_enter_chat():
    page = get_page()
    print("🖱️ 正在执行第 2 步：点击「立即沟通」...")
    btn = page.ele('css:.btn-startchat') or page.ele('xpath://a[contains(@class, "btn-startchat")]')
    if not btn:
        print("  ❌ 未找到沟通按钮")
        return False
    
    text = (btn.text or '').strip()
    if "立即沟通" not in text:
        print(f"  🛑 安全拦截：按钮文本不是「立即沟通」，而是「{text}」，中止操作！")
        return False
        
    btn.click()
    print(f"  ✅ 已点击「{text}」按钮！等待页面响应...")
    time.sleep(3)
    
    # 关闭弹窗
    for sel in ['.dialog-wrap .close', '.boss-dialog__close', '[class*="dialog"] [class*="close"]']:
        try:
            for c in page.eles(f'css:{sel}'):
                if c.is_displayed():
                    c.click()
                    print(f"  ✓ 已关闭遮罩弹窗: {sel}")
        except Exception:
            pass
            
    # 检查新标签页
    if len(page.tab_ids) > 1:
        page.to_tab(page.tab_ids[-1])
        print(f"  🔀 已切换到最新标签页: {page.url}")
        
    if "/web/geek/chat" not in page.url:
        print(f"  🌐 正在跳转进入聊天中心...")
        page.get("https://www.zhipin.com/web/geek/chat")
        time.sleep(3)
        
    # 等待输入框出现
    for _ in range(5):
        inp = page.ele('css:#chat-input', timeout=1) or page.ele('css:[contenteditable="true"]', timeout=1)
        if inp and inp.rect.size[0] > 50:
            print(f"  🎯 聊天输入框已定位就绪！(宽度: {inp.rect.size[0]}px)")
            break
        time.sleep(1)
        
    # 读取当前聊天记录中的首条消息
    chat_text = page.run_js("""
        const m = document.querySelector('[class*="chat-message-list"], [class*="message-list"], .chat-record');
        return m ? m.innerText : '';
    """) or ''
    print(f"  📜 当前聊天窗口已有内容:\n{chat_text.strip()}")
    return True

if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) > 1 else 'step1'
    if action == 'step1':
        url = sys.argv[2] if len(sys.argv) > 2 else 'https://www.zhipin.com/job_detail/21f0013317e42fea0nF93tm5FVRT.html'
        step1_open(url)
    elif action == 'step2':
        step2_click_and_enter_chat()
