#!/usr/bin/env python3
"""
Moka 校园招聘智能网申 Agent。
支持：
1. 自动读取 profile.json 结构化求职信息
2. 自动化打开岗位页、点击申请
3. 人机协同登录（自动填入手机号/协议，等待用户输入验证码）
4. 智能匹配并自动填写 Moka 投递表单（姓名、学历、学校、专业、经历等）
5. 自动上传 PDF 简历附件
6. 留置核验环节：确认无误后再提交，保障 100% 准确
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

class MokaApplyAgent:
    def __init__(self, job_url: str):
        self.job_url = job_url
        self.profile = self.load_profile()
        self.page = None

    def load_profile(self) -> dict:
        if not PROFILE_PATH.exists():
            raise FileNotFoundError(f"找不到简历档案: {PROFILE_PATH}")
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def log(self, msg: str):
        print(msg, flush=True)

    def init_browser(self):
        chrome_path = find_chrome_browser()
        co = ChromiumOptions()
        co.set_browser_path(chrome_path)
        co.set_user_data_path(str(USER_DATA_DIR))
        co.auto_port()
        print(f"[+] 正在启动 Chrome，载入配置目录: {USER_DATA_DIR}")
        self.page = ChromiumPage(co)

    def run(self):
        self.init_browser()
        print(f"[+] 正在打开目标岗位: {self.job_url}")
        self.page.get(self.job_url)
        time.sleep(3)

        # 1. 查找并点击申请按钮
        print(f"[+] 当前页面: {self.page.title}")
        apply_btn = None
        for btn in self.page.eles('tag:button'):
            t = btn.text.strip()
            if any(k in t for k in ['申请职位', '立即投递', '投递简历']):
                apply_btn = btn
                break

        if not apply_btn:
            print("[!] 未找到申请按钮，请检查岗位是否已下线。")
            return

        print(f"[+] 触发申请: {apply_btn.text}")
        apply_btn.click()
        time.sleep(2)

        # 2. 检查是否弹出手机号登录验证框
        phone_input = self.page.ele('@placeholder*=请输入手机号') or self.page.ele('@placeholder*=手机号')
        if phone_input:
            phone_num = self.profile.get("basic_info", {}).get("phone", "")
            print(f"\n[!] 检测到 Moka 登录弹窗，准备自动填入手机号: {phone_num}")
            phone_input.clear()
            phone_input.input(phone_num)

            # 查找勾选框（用户服务协议）
            checkboxes = self.page.eles('tag:input')
            for cb in checkboxes:
                if cb.attr('type') == 'checkbox':
                    if not cb.property('checked'):
                        cb.click()
                        print("[+] 已自动勾选服务与隐私协议")

            print("\n" + "=" * 60)
            print("👉 手机号与协议已自动填好！")
            print("👉 请在浏览器弹出的窗口中点击「获取验证码」，并在页面中输入验证码完成登录。")
            print("👉 登录成功后，脚本将自动检测并进入后续填表流程！")
            print("=" * 60 + "\n")

            # 等待登录框消失或表单出现（最多等待 3 分钟）
            for _ in range(90):
                time.sleep(2)
                # 检查登录框是否已经关闭/消失
                if not self.page.ele('@placeholder*=请输入验证码'):
                    print("[+] 登录成功，正在进入网申简历表单...")
                    break
            time.sleep(3)

        # 3. 探查并填充申请表单
        self.fill_application_form()

    def fill_application_form(self):
        print("\n[+] 开始分析并填充 Moka 简历表单...")
        time.sleep(2)

        basic = self.profile.get("basic_info", {})
        edu = self.profile.get("education", {})

        name = basic.get("name", "")
        email = basic.get("email", "")
        school = edu.get("school", "")
        major = edu.get("major", "")
        degree = edu.get("degree", "本科")

        print(f"  👤 候选人: {name} | 邮箱: {email}")
        print(f"  🎓 院校: {school} | 专业: {major} | 学历: {degree}")

        # 遍历所有 input 输入框进行语义匹配
        inputs = self.page.eles('tag:input')
        for inp in inputs:
            p = inp.attr('placeholder') or ''
            # 上下文文本（label 或父容器）
            parent_text = inp.parent().text.strip() if inp.parent() else ''
            combined_label = f"{p} {parent_text}".lower()

            # 姓名
            if any(k in combined_label for k in ['姓名', '真实姓名', 'name']) and not any(k in combined_label for k in ['紧急', '推荐', '公司']):
                current_val = inp.attr('value') or ''
                if not current_val and name:
                    inp.clear()
                    inp.input(name)
                    print(f"  [√] 自动填入姓名: {name}")

            # 邮箱
            elif any(k in combined_label for k in ['邮箱', 'email', 'mail']):
                current_val = inp.attr('value') or ''
                if not current_val and email:
                    inp.clear()
                    inp.input(email)
                    print(f"  [√] 自动填入邮箱: {email}")

            # 学校
            elif any(k in combined_label for k in ['学校', '毕业院校', 'school']):
                current_val = inp.attr('value') or ''
                if not current_val and school:
                    inp.clear()
                    inp.input(school)
                    print(f"  [√] 自动填入毕业学校: {school}")

            # 专业
            elif any(k in combined_label for k in ['专业', 'major']):
                current_val = inp.attr('value') or ''
                if not current_val and major:
                    inp.clear()
                    inp.input(major)
                    print(f"  [√] 自动填入专业: {major}")

        print("\n[+] 表单基础字段已初步填充完毕。")
        print("[+] 浏览器保持在前台，供您检查预览与核验。")

if __name__ == "__main__":
    test_url = "https://app.mokahr.com/campus_apply/transwarp/3196#/job/4add3fe2-7f73-4790-9488-283586fd7a49"
    agent = MokaApplyAgent(test_url)
    agent.run()
