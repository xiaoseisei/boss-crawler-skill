# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, 'scripts')
from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser

co = ChromiumOptions()
chrome_path = find_chrome_browser()
if chrome_path:
    co.set_browser_path(chrome_path)
co.set_argument(f'--user-data-dir={os.path.abspath("assets/chrome_user_data")}')

dp = WebPage(chromium_options=co)
try:
    print("Page URL:", dp.url)
    items = dp.eles('css:.chat-record .item-myself')
    print(f"Total my messages: {len(items)}")
    for i, it in enumerate(items):
        print(f"--- Item {i} ---")
        print(it.text.strip())
        img = it.ele('css:img')
        if img:
            print("[Image attached]:", img.attr('src')[:60] if img.attr('src') else 'image')
finally:
    dp.quit()
