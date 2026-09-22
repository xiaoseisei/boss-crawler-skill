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
    link = 'https://www.zhipin.com/job_detail/d517bf6a1896aa430nN_0t66EVFQ.html'
    dp.get(link)
    time.sleep(3)
    btns = dp.eles('css:.btn-startchat, [ka="job-detail-chat"], .btn-container a, a.btn')
    chat_btn = [b for b in btns if '沟通' in b.text]
    if chat_btn:
        print('Button text:', chat_btn[0].text)
        chat_btn[0].click()
        time.sleep(2)
        dialog = dp.ele('css:.dialog-wrap, .dialog-container, [class*="dialog"]')
        if dialog:
            print('Dialog Text:', repr(dialog.text))
        else:
            print('No dialog found!')
        print('Current URL:', dp.url)
        print('Tabs count:', dp.tabs_count)
finally:
    dp.quit()
