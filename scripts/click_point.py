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

    el_info = dp.run_js("""
        const el = document.elementFromPoint(200, 210);
        if (!el) return null;
        let curr = el;
        const chain = [];
        while (curr && curr.tagName !== 'BODY') {
            chain.push(curr.tagName + '.' + Array.from(curr.classList).join('.'));
            curr = curr.parentElement;
        }
        el.click();
        return {
            pointEl: el.tagName + '.' + Array.from(el.classList).join('.'),
            chain: chain
        };
    """)
    print("Point element and chain:", el_info)
    time.sleep(2)
    dp.get_screenshot(path='assets/after_point_click.png')
    print("Screenshot saved to assets/after_point_click.png")

    # 查看输入框
    inp = dp.run_js("""
        const inp = document.querySelector('#chat-input, [contenteditable="true"]');
        return inp ? { tag: inp.tagName, id: inp.id, cls: inp.className, w: inp.offsetWidth, h: inp.offsetHeight } : null;
    """)
    print("Input after click:", inp)
finally:
    dp.quit()
