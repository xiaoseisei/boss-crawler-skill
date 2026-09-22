#!/usr/bin/env python3
"""
连接当前已登录的浏览器页面，深度探查 Moka 投递表单的所有字段、组件类型与已填内容。
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from DrissionPage import ChromiumPage, ChromiumOptions
from scripts.browser_finder import find_chrome_browser

USER_DATA_DIR = PROJECT_ROOT / "assets" / "chrome_profile"

def main():
    chrome_path = find_chrome_browser()
    co = ChromiumOptions()
    co.set_browser_path(chrome_path)
    co.set_user_data_path(str(USER_DATA_DIR))
    co.auto_port()

    page = ChromiumPage(co)
    print(f"[+] 当前页面标题: {page.title}")
    print(f"[+] 当前 URL: {page.url}")

    # 探查所有输入框与下拉框
    print("\n" + "=" * 50)
    print("📝 表单字段探查清单:")
    print("=" * 50)

    # 查找所有带有表单项特征的容器 (通常在 Moka 中是 .form-item 或 .field-wrapper 或包含 label 的 div)
    inputs = page.eles('tag:input')
    for idx, inp in enumerate(inputs):
        t = inp.attr('type') or 'text'
        p = inp.attr('placeholder') or ''
        v = inp.attr('value') or ''
        
        # 向上寻找 label 或描述
        label = ""
        parent = inp.parent()
        for _ in range(4):
            if not parent:
                break
            # 查找内部的 label 或 class 含有 label 的元素
            lbl_ele = parent.ele('tag:label') or parent.ele('@class*=label') or parent.ele('@class*=title')
            if lbl_ele and lbl_ele.text.strip():
                label = lbl_ele.text.strip()
                break
            parent = parent.parent()

        if not label:
            # 尝试直接取父容器文本的前 30 个字
            label = inp.parent().text.strip()[:30] if inp.parent() else ''

        print(f"[{idx+1}] 类型: {t:10} | Label: {label:20} | 占位: {p:20} | 当前值: {v}")

    # 探查附件上传组件
    print("\n" + "=" * 50)
    print("📎 附件/简历上传控件:")
    print("=" * 50)
    file_inputs = page.eles('@type=file')
    for f in file_inputs:
        print(f"  - 发现 file input: accept={f.attr('accept')} | id={f.attr('id')}")

    # 探查多行文本框
    print("\n" + "=" * 50)
    print("📄 多行输入框 (Textarea):")
    print("=" * 50)
    textareas = page.eles('tag:textarea')
    for idx, ta in enumerate(textareas):
        p = ta.attr('placeholder') or ''
        print(f"  [{idx+1}] 占位: {p} | 当前内容: {ta.text[:50]}")

if __name__ == "__main__":
    main()
