# -*- coding: utf-8 -*-
import os, sys, time, json
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
    time.sleep(4)
    print('Page Title:', dp.title)
    print('Page URL:', dp.url)

    dp.get_screenshot(path='assets/chat_debug.png')
    print('Screenshot saved to assets/chat_debug.png')

    res = dp.run_js("""
        const els = Array.from(document.querySelectorAll('input, textarea, [contenteditable="true"], [id*="chat"], [class*="chat-input"]'));
        return els.map(e => ({
            tag: e.tagName,
            id: e.id,
            className: e.className,
            width: e.offsetWidth,
            height: e.offsetHeight,
            editable: e.getAttribute('contenteditable'),
            visible: e.offsetWidth > 0 && e.offsetHeight > 0
        }));
    """)
    print('Found input elements:')
    for item in res:
        print('  ', item)

    # 检查左侧会话项
    items = dp.run_js("""
        const list = Array.from(document.querySelectorAll('.chat-user-list li, .geek-chat-list .chat-item, [class*="chat-item"]'));
        return list.map(e => ({
            className: e.className,
            text: e.innerText.split('\\n')[0],
            active: e.className.includes('active') || e.className.includes('selected')
        }));
    """)
    print('Found chat list items:')
    for it in items[:5]:
        print('  ', it)

finally:
    dp.quit()
