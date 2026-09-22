#!/usr/bin/env python3
"""
使用本地 Chrome 浏览器登录并抓取飞书多维表格（Base）内容。
支持持久化登录：首次运行需扫码登录，后续可直接免登。
"""

import os
import sys
import time
import json
from pathlib import Path

# 添加工程根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from DrissionPage import ChromiumPage, ChromiumOptions
from scripts.browser_finder import find_chrome_browser

FEISHU_URL = "https://my.feishu.cn/base/Q6yQbgLiNa1y0as8QEtcOR6YnFb?table=tblO4VkZJBoMZRrV&view=vewQElU49w"
USER_DATA_DIR = PROJECT_ROOT / "assets" / "chrome_profile"
OUTPUT_DIR = PROJECT_ROOT / "assets" / "feishu_data"

def main():
    chrome_path = find_chrome_browser()
    if not chrome_path:
        print("[-] 未检测到 Chrome 浏览器，请检查安装路径。")
        sys.exit(1)

    print(f"[+] 检测到浏览器: {chrome_path}")
    print(f"[+] 浏览器配置目录: {USER_DATA_DIR}")

    USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    co = ChromiumOptions()
    co.set_browser_path(chrome_path)
    co.set_user_data_path(str(USER_DATA_DIR))
    
    # 允许有界面运行，方便用户扫码
    co.auto_port()

    print("[+] 正在启动 Chrome 浏览器窗口...")
    page = ChromiumPage(co)

    # 启动网络监听，监听飞书的数据接口
    # 飞书多维表格常见数据接口特征: /space/api/ /bitable/ /stream/ /preload
    page.listen.start(targets=['space/api', 'bitable', 'records', 'view'])

    print(f"[+] 正在打开飞书多维表格页面: {FEISHU_URL}")
    page.get(FEISHU_URL)

    print("\n=======================================================")
    print("👉 请在弹出的 Chrome 窗口中完成登录（如需扫码/短信验证码）。")
    print("👉 登录成功并进入多维表格后，脚本将自动捕获表格数据！")
    print("=======================================================\n")

    # 循环检测是否已成功进入表格
    max_wait = 180  # 最多等待 3 分钟
    start_time = time.time()
    captured_data = []

    while time.time() - start_time < max_wait:
        current_url = page.url
        # 如果还在登录页面 accounts.feishu.cn，等待
        if "accounts.feishu.cn" in current_url:
            print("⏳ 等待用户完成登录...", end="\r", flush=True)
            time.sleep(2)
            continue

        # 检查是否有网络包捕获
        res = page.listen.steps(timeout=2)
        if res:
            for packet in res:
                try:
                    url = packet.url
                    # 过滤可能包含记录数据的接口
                    if any(k in url for k in ['records', 'view', 'bitable', 'table', 'client_vars', 'preload']):
                        body = packet.response.body
                        if isinstance(body, dict):
                            print(f"\n[+] 捕获到数据接口: {url[:80]}...")
                            captured_data.append({"url": url, "data": body})
                        elif isinstance(body, str) and (body.startswith("{") or body.startswith("[")):
                            parsed = json.loads(body)
                            print(f"\n[+] 捕获到数据接口: {url[:80]}...")
                            captured_data.append({"url": url, "data": parsed})
                except Exception as e:
                    pass

        # 检查页面是否加载出表格内容元素
        # 飞书表格常有 grid / canvas / table-container
        if "base" in current_url:
            # 稍作等待让页面把接口请求发完
            time.sleep(1)
            # 如果已经拿到有效数据，或者检测到页面特定元素
            if len(captured_data) > 0:
                print(f"\n[+] 已捕获到 {len(captured_data)} 个关键数据包，正在保存...")
                break

    # 保存捕获到的原始数据
    save_path = OUTPUT_DIR / "feishu_raw_data.json"
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(captured_data, f, ensure_ascii=False, indent=2)
    print(f"[+] 原始数据已暂存至: {save_path}")

    # 同时尝试读取当前页面的 text / HTML 以备解析
    page_title = page.title
    print(f"[+] 页面标题: {page_title}")

    # 尝试提取页面所有的链接（<a> 标签）
    links = []
    for a in page.eles('tag:a'):
        href = a.attr('href')
        text = a.text
        if href and (href.startswith('http://') or href.startswith('https://')):
            links.append({'text': text, 'href': href})

    print(f"[+] 页面中提取到 {len(links)} 个超链接。")
    links_path = OUTPUT_DIR / "extracted_links.json"
    with open(links_path, "w", encoding="utf-8") as f:
        json.dump(links, f, ensure_ascii=False, indent=2)
    print(f"[+] 链接已保存至: {links_path}")

    # 保持浏览器打开，不要立即关闭，让用户也能手动查看
    print("\n[+] 抓取流程完成，浏览器保持当前状态供后续使用。")

if __name__ == "__main__":
    main()
