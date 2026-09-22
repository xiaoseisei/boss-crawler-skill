# -*- coding: utf-8 -*-
"""2026-09-20 薪资由低到高投递执行脚本（第一批：100-150元/天 最低薪资小微/初创团队）
候选名单：
1. 深圳行为先教育科技 - AI Agent实习生（深圳 · 100-110元/天 · 0-20人）
2. 广州先途人工智能 - Java后端开发实习生（AI Agent方向|27届）（广州 · 100-110元/天 · 0-20人）
3. 兴合基金 - FDE部署（北京 · 100-110元/天 · 20-99人）
4. 北京水山识流科技 - 初级FDE / Forward Deployed Engineer（北京 · 100-150元/天 · 0-20人）
5. 深圳华大涌生智能科技 - AI Agent 实习生（生物工艺方向）（深圳 · 100-150元/天 · 20-99人）

执行规范：
- 正式职业化招呼语（黄金前15字到岗承诺、无校名漏洞、无口语俚语、单段完整送达）
- 详情页沟通状态强检测（继续沟通/已沟通自动拦截防重）
- 自适应忽略微信扫码订阅弹窗，直达聊天工作台
- 聊天室简历图片防重检测
- 发送招呼语 + 上传对应方向高清长图简历
- 截图存证至 assets/deliver_proof/ 并更新持久化历史账本
"""
import os, sys, time, json

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from resume_matcher.history import record_applied_job, is_job_applied, load_applied_history

AGENT_RESUME_IMG = os.path.abspath(r'assets/2026-09-18_00-21-59/deliver/#1-湖北地心智能科技-AI智能体（Agent）开发实习生/夏子聪-AI智能体（Agent）开发实习生.png')
FDE_RESUME_IMG = os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#27-拾新未来-AI Agent实习生（FDE方向丨可留用）/夏子聪-AI Agent实习生（FDE方向丨可留用）.png')

LOWEST_SALARY_JOBS = [
    {
        'idx': 1,
        'company': '深圳行为先教育科技',
        'position': 'AI Agent实习生',
        'salary': '100-110元/天',
        'link': 'https://www.zhipin.com/job_detail/bd0f541eb0762c4f0nB_2d65FVNQ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 实习生岗位。"
            "我专注于大模型智能体与实际业务场景落地：独立负责过场景生成智能体平台，运用 LangGraph 搭建多 Agent 协同流水线并实现任务反思与自愈质检；"
            "同时主导开发了 GraphRAG 智能问答系统，将复杂长文本检索准确率提升至 97.5%。熟练使用 Python，具备扎实的工程落地与技术文档撰写能力。"
            "附件已上传针对智能体开发定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': AGENT_RESUME_IMG,
        'run_dir': 'assets/2026-09-18_00-21-59'
    },
    {
        'idx': 2,
        'company': '广州先途人工智能',
        'position': 'Java后端开发实习生（AI Agent方向|27届）',
        'salary': '100-110元/天',
        'link': 'https://www.zhipin.com/job_detail/f11f5d23d0e627dd0nJ80t-9FFBS.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是2027届自动化专业本科生夏子聪，求职贵司的后端开发实习生（AI Agent方向）岗位。"
            "我具备扎实的后端工程底子与 AI Agent 落地实战：熟悉 Controller/Service/DTO 分层架构与数据库设计规范，能熟练完成 CRUD 与接口开发；"
            "并在项目中深度实践了基于图谱的 RAG 检索与智能体工作流编排，曾获数模国奖，逻辑严谨。接受线下面试，期待长期实习培养与转正。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': AGENT_RESUME_IMG,
        'run_dir': 'assets/2026-09-18_00-21-59'
    },
    {
        'idx': 3,
        'company': '兴合基金',
        'position': 'FDE部署',
        'salary': '100-110元/天',
        'link': 'https://www.zhipin.com/job_detail/607474203de17fca0nJy3929E1tT.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 FDE 部署实习岗位。"
            "我具备大模型工程部署与现场交付实践：熟练掌握 Linux 环境与服务容器化部署，主导过 GraphRAG 智能系统与多 Agent 流水线的高性能交付；"
            "能熟练利用大模型协同完成技术文档编写与服务运维，具备良好的系统排错排障能力与严谨的团队协作精神。"
            "附件已上传针对交付部署定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': FDE_RESUME_IMG,
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 4,
        'company': '北京水山识流科技',
        'position': '初级FDE / Forward Deployed Engineer',
        'salary': '100-150元/天',
        'link': 'https://www.zhipin.com/job_detail/a9ecaab36165afc60nN_3Ni4ElNS.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的初级 FDE（Forward Deployed Engineer）岗位。"
            "我具备前沿部署工程师所需的技术交付与客户场景落地能力：主导过垂直领域的 GraphRAG 系统，将复杂场景检索准确率提升至 97.5%、响应低至 0.82 秒；"
            "并基于 FastAPI 与 LangGraph 完成从场景需求拆解到智能体交付的完整闭环，熟练使用 Python，抗压与解决实际工程问题能力强。"
            "附件已上传针对 FDE 岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': FDE_RESUME_IMG,
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 5,
        'company': '深圳华大涌生智能科技',
        'position': 'AI Agent 实习生（生物工艺方向）',
        'salary': '100-150元/天',
        'link': 'https://www.zhipin.com/job_detail/8ce02d0154eeeea10nN829q7FFJR.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 实习生岗位。"
            "我专注于复杂垂类领域中大模型智能体的设计与研发：基于 LangGraph 构建过多智能体协同流水线与安全沙箱执行环境，实现任务反思与多阶段自愈；"
            "在数据检索上主导过 GraphRAG 认知图谱问答系统，攻克了长文本长链路精准引用的难题，数模国奖算法功底扎实，学习适应能力极强。"
            "附件已上传针对智能体开发定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': AGENT_RESUME_IMG,
        'run_dir': 'assets/2026-09-18_00-21-59'
    }
]

os.makedirs('assets/deliver_proof', exist_ok=True)

def deliver_one_job(dp, job):
    print(f"\n========================================================", flush=True)
    print(f"🚀 开始处理 #{job['idx']} [{job['company']}] {job['position']} ({job['salary']})", flush=True)
    print(f"🔗 链接: {job['link']}", flush=True)
    print(f"========================================================", flush=True)

    # 1. 检查本地防重库
    hist = load_applied_history()
    applied, rec = is_job_applied(job, hist)
    if applied:
        print(f"⏭️ 本地历史库已记录过该岗位 (applied_at: {rec.get('applied_at')})，跳过！", flush=True)
        return 'already_in_history'

    # 2. 检查招呼语合规性
    greeting = job['greeting']
    for bad in ['湖北文理', '文理学院', '24届', '关键词均有对应支撑', 'VFS安全沙箱', '看一眼', '贴上啦', '咱们的', '很顺手', '啦', '哈', '呢', '呀']:
        if bad in greeting:
            print(f"❌ 招呼语命中违禁词: {bad}，拒绝发送！", flush=True)
            return 'greeting_rejected'
    if not os.path.exists(job['image']):
        print(f"❌ 简历长图不存在: {job['image']}，拒绝发送！", flush=True)
        return 'image_missing'

    # 保持单一标签页
    if dp.tabs_count > 1:
        dp.close_tabs(others=True)

    # 3. 访问详情页
    print("🌐 正在打开岗位详情页...", flush=True)
    dp.get(job['link'])
    time.sleep(3)

    # 4. 详情页按钮防重门禁
    btns = dp.eles('css:.btn-startchat, [ka="job-detail-chat"], .btn-container a, a.btn')
    chat_btn = None
    for b in btns:
        if '沟通' in b.text:
            chat_btn = b
            break

    if not chat_btn:
        print("⚠️ 未找到沟通按钮，可能岗位已下线或结构变动", flush=True)
        dp.get_screenshot(path=f"assets/deliver_proof/salary_{job['idx']}_{job['company']}_no_btn.png")
        return 'no_btn'

    btn_text = chat_btn.text.strip()
    print(f"🔘 详情页沟通按钮状态: [{btn_text}]", flush=True)

    if '继续' in btn_text or '已沟通' in btn_text:
        print(f"🛑 详情页显示 [{btn_text}]，已被HR开聊或历史沟通！强行拦截，补录防重库并跳过。", flush=True)
        record_applied_job(job, status='already_communicated', greeting=greeting, image=job['image'], run_dir=job['run_dir'])
        dp.get_screenshot(path=f"assets/deliver_proof/salary_{job['idx']}_{job['company']}_skipped.png")
        return 'skipped_already_communicated'

    # 5. 点击立即沟通
    print(f"👉 点击 [{btn_text}] 按钮...", flush=True)
    chat_btn.click()
    time.sleep(2)

    # 检查是否有今日上限弹窗
    dialog = dp.ele('css:.dialog-wrap, .dialog-container')
    if dialog:
        dtext = dialog.text
        if ('今日沟通' in dtext and '上限' in dtext) or ('沟通次数' in dtext and '上限' in dtext):
            print(f"🚨 触发今日沟通上限: {dtext}", flush=True)
            dp.get_screenshot(path='assets/deliver_proof/limit_reached.png')
            return 'limit_reached'

    # 6. 进入聊天中心
    print("🌐 前往聊天工作台...", flush=True)
    dp.get('https://www.zhipin.com/web/geek/chat')
    time.sleep(3)

    # 7. 激活左侧最新会话（第1项）
    print("🖱️ 激活最新会话...", flush=True)
    user_items = dp.eles('css:.user-list li, .friend-content')
    if user_items:
        user_items[0].click()
        time.sleep(2)

    # 8. 聊天窗口防重检查
    my_msgs = dp.eles('css:.chat-record .item-myself')
    print(f"💬 当前会话我方已有消息数: {len(my_msgs)}", flush=True)
    has_image = False
    for m in my_msgs:
        if m.ele('css:img'):
            has_image = True
            break
    if has_image:
        print("🛑 检测到当前会话中已经发送过简历图片，强行拦截，避免重复打扰！", flush=True)
        record_applied_job(job, status='applied', greeting=greeting, image=job['image'], run_dir=job['run_dir'])
        dp.get_screenshot(path=f"assets/deliver_proof/salary_{job['idx']}_{job['company']}_duplicate_prevented.png")
        return 'duplicate_prevented'

    # 9. 定位输入框并输入正式招呼语
    inp = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
    if not inp:
        for _ in range(5):
            time.sleep(1)
            inp = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
            if inp: break

    if not inp:
        print("❌ 未找到聊天输入框", flush=True)
        dp.get_screenshot(path=f"assets/deliver_proof/salary_{job['idx']}_{job['company']}_no_input.png")
        return 'no_input'

    print(f"📝 正在填入定制正式招呼语 ({len(greeting)} 字)...", flush=True)
    inp.click()
    time.sleep(0.3)
    inp.input(greeting)
    time.sleep(1)

    # 10. 点击发送招呼语
    print("📤 发送招呼语...", flush=True)
    send_btn = dp.ele('css:.btn-send') or dp.ele('text:发送')
    if send_btn:
        send_btn.click()
    else:
        dp.run_js("""
            const btns = Array.from(document.querySelectorAll('button, .btn'));
            const send = btns.find(b => b.innerText && b.innerText.trim() === '发送');
            if (send) send.click();
        """)
    time.sleep(2)

    # 11. 上传简历高清长图附件
    print(f"📎 正在上传简历高清长图: {os.path.basename(job['image'])}...", flush=True)
    fi = dp.ele('css:input[type="file"]') or dp.ele('css:.btn-sendimg input')
    if fi:
        fi.input(job['image'])
        print("✓ 长图已通过原生 input 提交，等待上传完成...", flush=True)
    else:
        print("⚠️ 尝试激活图片上传按钮...", flush=True)
        dp.run_js("""
            const icon = document.querySelector('.icon-chat-img, [class*="sendimg"], [class*="image"]');
            if (icon) icon.click();
        """)
        time.sleep(1)
        fi = dp.ele('css:input[type="file"]')
        if fi:
            fi.input(job['image'])

    time.sleep(4)

    # 12. 截图留证与核验消息数
    proof_path = os.path.abspath(f"assets/deliver_proof/salary_{job['idx']}_{job['company']}_delivered.png")
    dp.get_screenshot(path=proof_path)
    print(f"📸 终局截图已保存: {proof_path}", flush=True)

    my_msgs_after = dp.eles('css:.chat-record .item-myself')
    print(f"✅ 发送完毕，当前会话我方消息数: {len(my_msgs_after)}", flush=True)

    # 13. 写入全局持久化防重历史账本
    record_applied_job(job, status='applied', greeting=greeting, image=job['image'], run_dir=job['run_dir'])
    print(f"🎉 #{job['idx']} {job['company']} 投递成功并成功记账！", flush=True)
    return 'success'

def main():
    co = ChromiumOptions()
    chrome_path = find_chrome_browser()
    if chrome_path:
        co.set_browser_path(chrome_path)
    user_data_dir = os.path.abspath('assets/chrome_user_data')
    co.set_argument(f'--user-data-dir={user_data_dir}')

    print(f"🚀 初始化浏览器环境... (User Data: {user_data_dir})", flush=True)
    dp = WebPage(chromium_options=co)

    results = {}
    try:
        for i, job in enumerate(LOWEST_SALARY_JOBS):
            print(f"\n>>> 正在推进薪资从低到高第 {i+1} / {len(LOWEST_SALARY_JOBS)} 家企业...", flush=True)
            res = deliver_one_job(dp, job)
            results[f"#{job['idx']} {job['company']} ({job['salary']})"] = res
            if res == 'limit_reached':
                print("🚨 达到每日沟通上限，安全终止当前批次！", flush=True)
                break
            # 停顿防频控 (7秒)
            if i < len(LOWEST_SALARY_JOBS) - 1:
                print("⏳ 停顿 7 秒进入下一家...", flush=True)
                time.sleep(7)
    finally:
        dp.quit()

    print("\n========================================================", flush=True)
    print("📊 最低薪资批次投递执行总结:", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("========================================================", flush=True)

if __name__ == '__main__':
    main()
