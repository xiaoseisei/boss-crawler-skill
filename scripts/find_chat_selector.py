# -*- coding: utf-8 -*-
import os, sys, time
sys.path.insert(0, 'scripts')
from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser

co = ChromiumOptions()
chrome_path = find_chrome_browser()
if chrome_path:
    co.set_browser_path(chrome_path)
user_data_dir = os.path.abspath('assets/chrome_user_data')
co.set_argument(f'--user-data-dir={user_data_dir}')

dp = WebPage(chromium_options=co)
try:
    dp.get('https://www.zhipin.com/web/geek/chat')
    time.sleep(3)
    info = dp.run_js("""
        // 查找包含刘女士的元素
        const all = Array.from(document.querySelectorAll('*'));
        for (const el of all) {
            if (el.innerText && el.innerText.includes('刘女士') && el.children.length > 2 && el.offsetWidth > 150) {
                return {
                    tag: el.tagName,
                    className: el.className,
                    html: el.outerHTML.slice(0, 300)
                };
            }
        }
        return null;
    """)
    print("刘女士 container:", info)

    # 尝试点击第一项
    click_res = dp.run_js("""
        const candidates = document.querySelectorAll('li, [class*="chat-item"], [class*="conversation-item"], [class*="user-item"]');
        for (const c of candidates) {
            if (c.innerText && (c.innerText.includes('刘女士') || c.innerText.includes('人力行政'))) {
                c.click();
                return 'Clicked: ' + c.className;
            }
        }
        return 'Not found';
    """)
    print("Click result:", click_res)
    time.sleep(2)

    # 检查点击后右侧输入框是否出现
    inp_info = dp.run_js("""
        const inp = document.querySelector('#chat-input, [contenteditable="true"], textarea.input');
        if (inp) {
            return {
                id: inp.id,
                className: inp.className,
                w: inp.offsetWidth,
                h: inp.offsetHeight,
                visible: inp.offsetWidth > 50
            };
        }
        return null;
    """)
    print("Input after click:", inp_info)

    dp.get_screenshot(path='assets/after_click_chat.png')
    print("Screenshot saved to assets/after_click_chat.png")
finally:
    dp.quit()
