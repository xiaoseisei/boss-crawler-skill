#!/usr/bin/env python3
"""
探查 Moka 招聘官网的页面结构、岗位列表与投递表单 DOM。
"""

import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from DrissionPage import ChromiumPage, ChromiumOptions
from scripts.browser_finder import find_chrome_browser

# 测试目标：星环科技 Moka 校园招聘（包含：智能体开发工程师、大模型算法工程师、AI前线部署工程师）
TEST_URL = "https://app.mokahr.com/campus_apply/transwarp/3196#/jobs"
USER_DATA_DIR = PROJECT_ROOT / "assets" / "chrome_profile"

def main():
    chrome_path = find_chrome_browser()
    co = ChromiumOptions()
    co.set_browser_path(chrome_path)
    co.set_user_data_path(str(USER_DATA_DIR))
    co.auto_port()

    print(f"[+] 启动浏览器探查: {TEST_URL}")
    page = ChromiumPage(co)
    page.get(TEST_URL)

    # 等待页面加载（Moka 为 SPA 客户端渲染）
    print("[+] 等待岗位列表加载完成...")
    time.sleep(4)

    # 打印页面标题
    print(f"[+] 页面标题: {page.title}")

    # 查找包含 '智能体' 或 '大模型' 或 'Agent' 的岗位元素
    found_jobs = []
    # Moka 的岗位卡片通常有 job-title、link 或 a 标签
    for a in page.eles('tag:a'):
        text = a.text.strip()
        if any(k in text for k in ['智能体', '大模型', 'Agent', '算法', '部署']):
            href = a.attr('href')
            print(f"  🎯 发现目标岗位: {text} | href: {href}")
            found_jobs.append((a, text, href))

    if not found_jobs:
        print("[!] 当前列表暂未直接发现包含关键词的 a 标签，正在检查列表容器...")
        for div in page.eles('tag:div'):
            c = div.attr('class') or ''
            if 'job' in c.lower() or 'item' in c.lower() or 'title' in c.lower():
                t = div.text.strip()
                if any(k in t for k in ['智能体', '大模型', 'Agent']) and len(t) < 50:
                    print(f"  🎯 发现目标卡片/标题: {t}")

    print("\n[+] 页面主要输入框/按钮特征:")
    for btn in page.eles('tag:button'):
        t = btn.text.strip()
        if t:
            print(f"  - 按钮: {t}")

    # 保留浏览器 5 秒供观察
    time.sleep(3)

if __name__ == "__main__":
    main()
