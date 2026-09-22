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
    print("🌐 打开聊天工作台...", flush=True)
    dp.get('https://www.zhipin.com/web/geek/chat')
    time.sleep(3)

    # 找到美腾思智能或第一个没有发过消息的会话
    user_items = dp.eles('css:.user-list li, .friend-content')
    print(f"找到会话项数量: {len(user_items)}")
    
    # 点击最新会话（第1项）
    user_items[0].click()
    time.sleep(2)

    my_msgs = dp.eles('css:.chat-record .item-myself')
    print(f"当前会话我方消息数: {len(my_msgs)}")

    # 尝试找到输入框
    inp = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
    if inp:
        print(f"找到输入框: {inp.tag}")
        greeting = (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI 应用工程师（AI Agent / 视频智能体方向）岗位。"
            "我深耕大模型智能体与多模态工作流工程化：熟练运用 LangGraph 构建具备任务拆解与多智能体协同的工作流，"
            "在 GraphRAG 项目中实现了精准知识图谱构建与秒级响应；熟练掌握 Python、FastAPI 与模型调用封装，具备扎实的应用系统落地与调优经验。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        )
        inp.click()
        inp.input(greeting)
        time.sleep(1)
        
        # 点击发送
        send_btn = dp.ele('css:.btn-send') or dp.ele('text:发送')
        if send_btn:
            send_btn.click()
            print("✓ 招呼语已点击发送")
            time.sleep(2)
        
        # 上传图片
        img_path = os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#49-美腾思智能-AI应用工程师-AI Agent _ 视频智能体方向/夏子聪-AI应用工程师-AI Agent _ 视频智能体方向.png')
        fi = dp.ele('css:input[type="file"]')
        if fi and os.path.exists(img_path):
            fi.input(img_path)
            print("✓ 简历长图已提交上传")
            time.sleep(4)
            
        dp.get_screenshot(path='assets/deliver_proof/test_send_success.png')
        print("📸 终局截图已保存到 assets/deliver_proof/test_send_success.png")
        
        my_msgs_after = dp.eles('css:.chat-record .item-myself')
        print(f"发送后我方消息数: {len(my_msgs_after)}")
finally:
    dp.quit()
