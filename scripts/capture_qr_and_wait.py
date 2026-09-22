# -*- coding: utf-8 -*-
"""实时抓取登录二维码截图并保持监听
1. 启动浏览器访问登录页面
2. 保存二维码全屏/特写截图至 assets/login_qr.png 及 artifact 目录
3. 在后台持续轮询 180 秒等待扫码完成
4. 检测到成功后自动持久化并退出
"""
import os
import sys
import time
import shutil

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from boss_crawler.auth import check_login_status

ARTIFACT_DIR = r'C:\Users\seisei\.gemini\antigravity-cli\brain\60739b44-1bc1-4fa6-b1d6-e7846aa09f0a'

def main():
    co = ChromiumOptions()
    chrome_path = find_chrome_browser()
    if chrome_path:
        co.set_browser_path(chrome_path)
    user_data_dir = os.path.abspath('assets/chrome_user_data')
    co.set_argument(f'--user-data-dir={user_data_dir}')
    
    print("🚀 启动浏览器...", flush=True)
    dp = WebPage(chromium_options=co)
    
    login_url = 'https://www.zhipin.com/web/user/?ka=header-login'
    dp.get(login_url)
    time.sleep(2.5)
    
    # 保存二维码截图
    local_qr = os.path.abspath('assets/login_qr.png')
    artifact_qr = os.path.join(ARTIFACT_DIR, 'login_qr.png')
    
    dp.get_screenshot(path=local_qr)
    shutil.copyfile(local_qr, artifact_qr)
    
    with open('assets/QR_READY.txt', 'w', encoding='utf-8') as f:
        f.write(str(time.time()))
        
    print(f"📸 二维码截图已生成: {local_qr}", flush=True)
    print("⏳ 开始轮询监听扫码结果（最长等待 180 秒）...", flush=True)
    
    start_time = time.time()
    logged_in = False
    
    while time.time() - start_time < 180:
        elapsed = int(time.time() - start_time)
        try:
            current_url = dp.url.lower()
            if 'web/geek/' in current_url or ('web/user/' not in current_url and 'login' not in current_url):
                if check_login_status(dp):
                    logged_in = True
                    break
            if dp.ele('css:.user-nav .nav-figure, .header-login-btn', timeout=1):
                if check_login_status(dp):
                    logged_in = True
                    break
        except Exception:
            pass
            
        time.sleep(2)
        
    if logged_in:
        print("\n🎉 [LOGIN_SUCCESS] 检测到扫码登录成功！", flush=True)
        time.sleep(2)
        dp.get_screenshot(path='assets/deliver_proof/login_success.png')
        dp.quit()
        return 0
    else:
        print("\n⚠️ 等待扫码超时", flush=True)
        dp.quit()
        return 1

if __name__ == '__main__':
    sys.exit(main())
