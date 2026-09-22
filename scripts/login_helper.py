# -*- coding: utf-8 -*-
"""BOSS 直聘扫码登录助手
打开可见浏览器窗口并访问 BOSS 登录/聊天页面，自动轮询检测登录状态。
用户扫码成功后自动保存并提示，无需手动在终端回车。
"""
import os
import sys
import time

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from boss_crawler.auth import check_login_status

def main():
    co = ChromiumOptions()
    chrome_path = find_chrome_browser()
    if chrome_path:
        co.set_browser_path(chrome_path)
    user_data_dir = os.path.abspath('assets/chrome_user_data')
    co.set_argument(f'--user-data-dir={user_data_dir}')
    
    print("🚀 正在拉起 Chrome 浏览器窗口...", flush=True)
    dp = WebPage(chromium_options=co)
    
    login_url = 'https://www.zhipin.com/web/user/?ka=header-login'
    print(f"🌐 正在打开 BOSS 登录页面: {login_url}", flush=True)
    dp.get(login_url)
    time.sleep(2)
    
    print("\n========================================================", flush=True)
    print("📱 浏览器窗口已打开，请在弹出的 Chrome 窗口中使用 微信 或 BOSS直聘APP 扫码登录！", flush=True)
    print("⏳ 系统正在自动实时检测登录状态（最长等待 180 秒）...", flush=True)
    print("========================================================\n", flush=True)
    
    start_time = time.time()
    logged_in = False
    
    while time.time() - start_time < 180:
        elapsed = int(time.time() - start_time)
        try:
            # 1. 检查是否跳到了登录后页面
            current_url = dp.url.lower()
            if 'web/geek/' in current_url or 'web/user/' not in current_url:
                if check_login_status(dp):
                    logged_in = True
                    break
            # 2. 检查头像或用户名元素
            if dp.ele('css:.user-nav .nav-figure, .header-login-btn', timeout=1):
                if check_login_status(dp):
                    logged_in = True
                    break
        except Exception:
            pass
            
        if elapsed % 10 == 0 and elapsed > 0:
            print(f"⏳ 等待扫码中... 已等待 {elapsed} 秒 / 180 秒", flush=True)
            
        time.sleep(2)
        
    if logged_in:
        print("\n🎉 [LOGIN_SUCCESS] 检测到登录成功！", flush=True)
        time.sleep(2)
        proof_path = os.path.abspath('assets/deliver_proof/login_success.png')
        dp.get_screenshot(path=proof_path)
        print(f"📸 登录成功存证已保存: {proof_path}", flush=True)
        print("💾 登录态已自动持久化保存到 assets/chrome_user_data/ 目录！", flush=True)
        dp.quit()
        return 0
    else:
        print("\n⚠️ 等待扫码超时（180秒），请重试。", flush=True)
        dp.quit()
        return 1

if __name__ == '__main__':
    sys.exit(main())
