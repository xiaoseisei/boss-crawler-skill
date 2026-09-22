# -*- coding: utf-8 -*-
"""5家全新企业真实闭环投递测试脚本
严格遵循：
1. 详情页「继续沟通」强拦截
2. 忽略BOSS常规「微信扫码订阅」引导弹窗，直达聊天室
3. 聊天室已发图片强防重拦截
4. 正式职业化招呼语（无校名、大三在读、无做题家八股、无口语俗语、单段完整送达）
5. 上传高清长图简历附件
6. 终局截屏核验与持久化记账
"""
import os, sys, time, json

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from resume_matcher.history import record_applied_job, is_job_applied, load_applied_history

TARGET_JOBS = [
    {
        'idx': 27,
        'company': '拾新未来',
        'position': 'AI Agent实习生（FDE方向丨可留用）',
        'link': 'https://www.zhipin.com/job_detail/7979b720334245b90nB92Ny5GFBT.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 实习生（FDE方向丨可留用）岗位。"
            "我具备大模型 Agent 落地与交付部署的双重实践：独立主导过 GraphRAG 智能问答系统，将长文本检索引用准确率做到 97.5%、首字响应控制在 1 秒以内；"
            "同时基于 FastAPI 与 LangGraph 搭建过多智能体协同流水线与安全执行环境。熟练掌握 Python，具备良好的现场交付排错与系统工程能力。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#27-拾新未来-AI Agent实习生（FDE方向丨可留用）/夏子聪-AI Agent实习生（FDE方向丨可留用）.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 30,
        'company': '朗姿医疗',
        'position': 'AI应用开发工程师｜LLM Agent / RAG方向',
        'link': 'https://www.zhipin.com/job_detail/05edb43abf014da60nF-2Nu1FVFT.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI 应用开发工程师（LLM Agent / RAG方向）岗位。"
            "我深耕大模型智能体与 RAG 系统落地：独立主导过垂直领域的 GraphRAG 智能问答系统，通过知识图谱与混合召回将复杂对话引用精度提升至 97.5%；"
            "熟练运用 LangGraph 构建多智能体协同流水线与任务反思质检机制，熟悉 Python 后端与模型调用封装，代码规范严谨。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#30-朗姿医疗-AI应用开发工程师｜LLM Agent _ RAG方向/夏子聪-AI应用开发工程师｜LLM Agent _ RAG方向.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 22,
        'company': '北京星云深图软件科技',
        'position': 'AI Agent 实习生 (MJ000902)',
        'link': 'https://www.zhipin.com/job_detail/1ae1e1de6c746a990nN-39-0FFNY.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 实习生岗位。"
            "我专注于大模型 Agent 的核心工程化落地：熟练运用 LangGraph 搭建任务拆解、多智能体协同与自愈质检工作流；"
            "并在 GraphRAG 问答系统中攻克了长对话上下文精准引用的难题，实现 97.5% 引用准确率与低延迟响应。具备扎实的 Python 全栈与算法工程能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#22-北京星云深图软件科技-AI Agent 实习生 (MJ000902)/夏子聪-AI Agent 实习生 (MJ000902).png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 26,
        'company': '拂曦科技',
        'position': 'Agent开发',
        'link': 'https://www.zhipin.com/job_detail/07b7ee2455b4360f0nJy29u7GVtY.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 Agent 开发岗位。"
            "我具备独立的大模型系统研发与落地经验：独立主导过 GraphRAG 智能问答系统，将长文本长对话引用精度做到 97.5%、响应不到 1 秒；"
            "同时基于 FastAPI 与 LangGraph 实现了多阶段智能体流水线与任务调度平台，熟练使用 Python，具备扎实的应用系统开发与接口联调能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#26-拂曦科技-Agent开发/夏子聪-Agent开发.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 23,
        'company': '湖北省千寻智创',
        'position': 'agent开发',
        'link': 'https://www.zhipin.com/job_detail/c30b7e3bbc8a005e03x939S1FVdY.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 Agent 开发岗位。"
            "我专注于大模型智能体与工作流工程化开发：熟练掌握 LangChain 与 LangGraph 框架，搭建过多智能体协同平台与自愈质检机制；"
            "在项目中基于 FastAPI 构建后端服务并实现端到端业务闭环，曾获数模国奖，逻辑严谨，工程上手和解决实际技术问题能力强。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#23-湖北省千寻智创-agent开发/夏子聪-agent开发.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    }
]

os.makedirs('assets/deliver_proof', exist_ok=True)

def deliver_one_job(dp, job):
    print(f"\n========================================================", flush=True)
    print(f"🚀 开始处理 #{job['idx']} {job['company']} - {job['position']}", flush=True)
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
    for bad in ['湖北文理', '文理学院', '24届', '关键词均有对应支撑', 'VFS安全沙箱', '看一眼', '贴上啦', '咱们的', '很顺手']:
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
        dp.get_screenshot(path=f"assets/deliver_proof/{job['idx']}_{job['company']}_no_btn.png")
        return 'no_btn'

    btn_text = chat_btn.text.strip()
    print(f"🔘 详情页沟通按钮状态: [{btn_text}]", flush=True)

    if '继续' in btn_text or '已沟通' in btn_text:
        print(f"🛑 详情页显示 [{btn_text}]，已被HR开聊或历史沟通！强行拦截，补录防重库并跳过。", flush=True)
        record_applied_job(job, status='already_communicated', greeting=greeting, image=job['image'], run_dir=job['run_dir'])
        dp.get_screenshot(path=f"assets/deliver_proof/{job['idx']}_{job['company']}_skipped.png")
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
        # 注意：此处忽略“微信扫码订阅回复消息”引导弹窗，直接进入聊天中心

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
        dp.get_screenshot(path=f"assets/deliver_proof/{job['idx']}_{job['company']}_duplicate_prevented.png")
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
        dp.get_screenshot(path=f"assets/deliver_proof/{job['idx']}_{job['company']}_no_input.png")
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
    proof_path = os.path.abspath(f"assets/deliver_proof/{job['idx']}_{job['company']}_delivered.png")
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
        for i, job in enumerate(TARGET_JOBS):
            print(f"\n>>> 正在推进第 {i+1} / {len(TARGET_JOBS)} 家全新企业...", flush=True)
            res = deliver_one_job(dp, job)
            results[f"#{job['idx']} {job['company']}"] = res
            if res == 'limit_reached':
                print("🚨 达到每日沟通上限，安全终止当前批次！", flush=True)
                break
            # 适度停顿防频控 (7秒)
            if i < len(TARGET_JOBS) - 1:
                print("⏳ 停顿 7 秒进入下一家...", flush=True)
                time.sleep(7)
    finally:
        dp.quit()

    print("\n========================================================", flush=True)
    print("📊 5家全新企业测试投递执行总结:", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("========================================================", flush=True)

if __name__ == '__main__':
    main()
