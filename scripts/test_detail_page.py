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
    test_url = 'https://www.zhipin.com/job_detail/364be0bd4acb03c30nJz2tW_E1pU.html' # #15
    print(f"Opening {test_url}...")
    dp.get(test_url)
    time.sleep(3)
    
    # check title and url
    print("Page Title:", dp.title)
    print("Page URL:", dp.url)
    
    # check startchat button
    btns = dp.eles('css:.btn-startchat, [ka="job-detail-chat"], .btn-container a, a.btn')
    for b in btns:
        if '沟通' in b.text:
            print(f"Found button: text='{b.text}', class='{b.attr('class')}'")
            
    dp.get_screenshot(path='assets/test_job15_detail.png')
    print("Screenshot saved to assets/test_job15_detail.png")
finally:
    dp.quit()
