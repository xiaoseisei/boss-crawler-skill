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
    link = 'https://www.zhipin.com/job_detail/8592031be97390530nV-3d60FVBQ.html'
    dp.get(link)
    time.sleep(3)
    btns = dp.eles('css:.btn-startchat, [ka="job-detail-chat"], .btn-container a, a.btn')
    chat_btn = [b for b in btns if '沟通' in b.text]
    if chat_btn:
        print('Initial button text:', chat_btn[0].text)
        chat_btn[0].click()
        time.sleep(2)
        dialogs = dp.eles('css:.dialog-wrap, .dialog-container, [class*="dialog"]')
        for i, d in enumerate(dialogs):
            print(f'Dialog {i} text:', repr(d.text))
        print('URL after click:', dp.url)
finally:
    dp.quit()
