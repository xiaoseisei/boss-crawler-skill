#!/usr/bin/env python3
"""
Moka 智能网申 Agent (V2 增强版)
- 保持浏览器持久打开，支持人机协同核对
- 深度解析 Moka 表单控件与联动组件
- 自动填充候选人基础信息、学历教育、实习项目与附件简历
"""

import os
import sys
import time
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from DrissionPage import ChromiumPage, ChromiumOptions
from scripts.browser_finder import find_chrome_browser

PROFILE_PATH = PROJECT_ROOT / "assets" / "2026-09-18_00-21-59" / "state" / "profile.json"
USER_DATA_DIR = PROJECT_ROOT / "assets" / "chrome_profile"

class MokaApplyAgentV2:
    def __init__(self, job_url: str):
        self.job_url = job_url
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            self.profile = json.load(f)
        self.page = None

    def log(self, msg: str):
        print(msg, flush=True)

    def init_browser(self):
        chrome_path = find_chrome_browser()
        co = ChromiumOptions()
        co.set_browser_path(chrome_path)
        co.set_user_data_path(str(USER_DATA_DIR))
        co.auto_port()
        self.log(f"[+] 启动 Chrome (Profile: {USER_DATA_DIR})")
        self.page = ChromiumPage(co)

    def run(self):
        self.init_browser()
        self.log(f"[+] 打开目标岗位页面: {self.job_url}")
        self.page.get(self.job_url)
        time.sleep(3)

        # 查找「申请职位」
        apply_btn = None
        for btn in self.page.eles('tag:button'):
            t = btn.text.strip()
            if any(k in t for k in ['申请职位', '立即投递', '投递简历']):
                apply_btn = btn
                break

        if apply_btn:
            self.log(f"[+] 点击申请按钮: {apply_btn.text}")
            apply_btn.click()
            time.sleep(3)

        # 检查是否还在验证码弹窗中
        if self.page.ele('@placeholder*=请输入手机号'):
            self.log("[!] 检测到尚未登录，正在等待登录完成...")
            for _ in range(60):
                time.sleep(2)
                if not self.page.ele('@placeholder*=请输入手机号'):
                    break
            time.sleep(2)

        # 进入正式填表
        self.log("\n" + "=" * 50)
        self.log("🚀 开始智能填充网申简历表单...")
        self.log("=" * 50)

        basic = self.profile.get("basic_info", {})
        edu = self.profile.get("education", {})

        name = basic.get("name", "夏子聪")
        phone = basic.get("phone", "18971817011")
        email = basic.get("email", "2646428831@qq.com")
        school = edu.get("school", "湖北文理学院")
        major = edu.get("major", "自动化")
        degree = edu.get("degree", "本科")
        grad_year = edu.get("graduation_year", "2027")

        self.log(f"  [👤 个人] 姓名: {name} | 手机: {phone} | 邮箱: {email}")
        self.log(f"  [🎓 学历] 学校: {school} | 专业: {major} | 学历: {degree} | 毕业: {grad_year}")

        # 1. 遍历所有 input 元素并打印探查
        all_inputs = self.page.eles('tag:input')
        self.log(f"\n[+] 页面检测到 {len(all_inputs)} 个输入控件，逐项匹配中:")

        for idx, inp in enumerate(all_inputs):
            t = inp.attr('type') or 'text'
            p = inp.attr('placeholder') or ''
            val = inp.attr('value') or ''
            
            # 提取容器所有可读文本
            ctx = ""
            curr = inp
            for _ in range(3):
                if curr.parent():
                    curr = curr.parent()
                    ctx = f"{ctx} {curr.text.strip()}"
            ctx_clean = " ".join(ctx.split())[:60]

            self.log(f"  控件 #{idx+1:02d}: type={t:6} | placeholder={p:15} | val={val:10} | context={ctx_clean}")

            # 智能判定并填入
            if t in ['text', 'tel', 'email']:
                # 姓名
                if any(k in ctx_clean for k in ['姓名', '真实姓名']) and not any(k in ctx_clean for k in ['紧急', '推荐', '联系人']):
                    if not val:
                        inp.clear()
                        inp.input(name)
                        self.log(f"    👉 [填入] 姓名 -> {name}")

                # 手机
                elif any(k in ctx_clean for k in ['手机号', '联系电话', '手机号码']):
                    if not val:
                        inp.clear()
                        inp.input(phone)
                        self.log(f"    👉 [填入] 手机号 -> {phone}")

                # 邮箱
                elif any(k in ctx_clean for k in ['邮箱', '电子邮箱', 'email']):
                    if not val:
                        inp.clear()
                        inp.input(email)
                        self.log(f"    👉 [填入] 邮箱 -> {email}")

                # 学校
                elif any(k in ctx_clean for k in ['学校', '毕业院校', '就读院校']):
                    if not val:
                        inp.clear()
                        inp.input(school)
                        self.log(f"    👉 [填入] 毕业院校 -> {school}")

                # 专业
                elif any(k in ctx_clean for k in ['专业', '所学专业']):
                    if not val:
                        inp.clear()
                        inp.input(major)
                        self.log(f"    👉 [填入] 所学专业 -> {major}")

                # 毕业年份
                elif any(k in ctx_clean for k in ['毕业年份', '毕业时间', '届别']):
                    if not val:
                        inp.clear()
                        inp.input(grad_year)
                        self.log(f"    👉 [填入] 毕业年份 -> {grad_year}")

        # 2. 检查多行输入框 (自我评价/项目经历)
        textareas = self.page.eles('tag:textarea')
        if textareas:
            self.log(f"\n[+] 发现 {len(textareas)} 个多行文本域 (Textarea):")
            for idx, ta in enumerate(textareas):
                p = ta.attr('placeholder') or ''
                ctx = ta.parent().text.strip()[:40] if ta.parent() else ''
                self.log(f"  文本域 #{idx+1}: placeholder={p} | 上下文={ctx}")
                if any(k in ctx for k in ['自我评价', '个人优势', '个人陈述']):
                    summary = self.profile.get("skills", {}).get("summary", "")
                    if summary and not ta.text:
                        ta.input(summary)
                        self.log("    👉 [填入] 自我评价 / 个人技术摘要")

        # 3. 检查附件上传
        file_inputs = self.page.eles('@type=file')
        if file_inputs:
            self.log(f"\n[+] 发现 {len(file_inputs)} 个文件上传控件。")

        self.log("\n" + "=" * 60)
        self.log("🎉 当前页面自动填表阶段完成！")
        self.log("👉 浏览器将持续保持在前台，请直接查看浏览器中的表单内容并核对。")
        self.log("=" * 60 + "\n")

        # 保持运行，避免 Python 退出关掉 Chrome
        while True:
            time.sleep(10)

if __name__ == "__main__":
    job_url = "https://app.mokahr.com/campus_apply/transwarp/3196#/job/4add3fe2-7f73-4790-9488-283586fd7a49"
    agent = MokaApplyAgentV2(job_url)
    agent.run()
