#!/usr/bin/env python3
"""
打开具体岗位详情页，探查「立即投递」点击后的申请表单字段与交互逻辑。
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from DrissionPage import ChromiumPage, ChromiumOptions
from scripts.browser_finder import find_chrome_browser

JOB_URL = "https://app.mokahr.com/campus_apply/transwarp/3196#/job/4add3fe2-7f73-4790-9488-283586fd7a49"
USER_DATA_DIR = PROJECT_ROOT / "assets" / "chrome_profile"

def main():
    chrome_path = find_chrome_browser()
    co = ChromiumOptions()
    co.set_browser_path(chrome_path)
    co.set_user_data_path(str(USER_DATA_DIR))
    co.auto_port()

    print(f"[+] 启动浏览器打开目标岗位: {JOB_URL}")
    page = ChromiumPage(co)
    page.get(JOB_URL)

    time.sleep(3)
    print(f"[+] 页面标题: {page.title}")

    # 查找「立即投递」或「申请」按钮
    apply_btn = None
    for btn in page.eles('tag:button'):
        t = btn.text.strip()
        if any(k in t for k in ['立即投递', '申请', '投递简历']):
            apply_btn = btn
            print(f"[+] 找到申请按钮: {t}")
            break

    if apply_btn:
        print("[+] 模拟点击申请按钮...")
        apply_btn.click()
        time.sleep(3)

        # 检查当前是否弹出了登录浮层或者直接进入了申请表单
        print(f"[+] 当前 URL: {page.url}")
        
        # 查找表单元素
        inputs = page.eles('tag:input')
        print(f"[+] 发现输入框数量: {len(inputs)}")
        for inp in inputs:
            p = inp.attr('placeholder') or ''
            n = inp.attr('name') or ''
            t = inp.attr('type') or 'text'
            # 向上寻找 label 文本
            parent_text = inp.parent().text.strip() if inp.parent() else ''
            print(f"  - Input [type={t}, name={n}, placeholder={p}] | 上下文: {parent_text[:30]}")

        # 查找所有文本域 textarea
        textareas = page.eles('tag:textarea')
        print(f"[+] 发现多行文本框数量: {len(textareas)}")
        for ta in textareas:
            p = ta.attr('placeholder') or ''
            print(f"  - Textarea [placeholder={p}]")

        # 检查是否有文件上传 input
        files = page.eles('@type=file')
        print(f"[+] 发现附件上传输入框: {len(files)}")

    # 等待几秒
    time.sleep(5)

if __name__ == "__main__":
    main()
