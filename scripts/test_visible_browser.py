#!/usr/bin/env python3
import time
import os
from DrissionPage import WebPage, ChromiumOptions

co = ChromiumOptions()
co.no_imgs(False)
user_data = os.path.abspath("assets/chrome_user_data")
os.makedirs(user_data, exist_ok=True)
co.set_argument(f'--user-data-dir={user_data}')
co.set_argument('--disable-blink-features=AutomationControlled')

print("[+] 正在通过 DrissionPage WebPage 启动浏览器...")
dp = WebPage(chromium_options=co)
dp.get("https://app.mokahr.com/campus_apply/transwarp/3196#/job/4add3fe2-7f73-4790-9488-283586fd7a49")
print("[+] 页面已加载，标题:", dp.title)
print("[+] 保持窗口打开 15 秒...")
time.sleep(15)
dp.quit()
print("[+] 退出完成。")
