# -*- coding: utf-8 -*-
"""10家中小企业全自动小步快跑投递测试脚本
严格遵循：
1. 详情页「继续沟通」强拦截
2. 聊天室已有历史记录强拦截
3. 定制人话招呼语（无校名、大三在读、无做题家八股、单段完整送达）
4. 高清长图简历附件上传
5. 终局截屏核验与持久化记账
"""
import os, sys, time, json
sys.path.insert(0, 'scripts')
from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from resume_matcher.history import record_applied_job, is_job_applied, load_applied_history

TARGET_JOBS = [
    {
        'idx': 18,
        'company': '某小型人工智能企业服务天使轮公司',
        'position': 'AI前沿部署工程师（FDE）',
        'link': 'https://www.zhipin.com/job_detail/6b13619b4a5316b00nN509-9EFZV.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI 前沿部署工程师（FDE）岗位。"
            "我在 Agent 工程化与交付部署方面有完整实践：独立设计并落地了 GraphRAG 系统，通过混合召回与图谱索引将长文本引用准确率做到 97.5%、首字响应在 1 秒以内；"
            "同时基于 FastAPI 搭建了端到端可交付的 Agent 流水线与安全执行环境。熟练掌握 Python 与常用组件，具备扎实的部署排错与现场问题解决能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#18-某小型人工智能企业服务天使轮公司-AI前沿部署工程师（FDE）/夏子聪-AI前沿部署工程师（FDE）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 24,
        'company': '语核科技',
        'position': 'FDE交付工程师',
        'link': 'https://www.zhipin.com/job_detail/c51220050f25cd6c0nN73Nm_GFFV.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 FDE 交付工程师岗位。"
            "我具备大模型应用研发与逆向分析双重实践：独立落地过 GraphRAG 教研问答系统（支持多智能体工作流与精准召回），"
            "同时具备协议分析与网络抓包经验，熟悉 Linux 环境运维与 Docker 容器化交付，具备扎实的现场环境部署与排错能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。期待能有机会与您深入沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#24-语核科技-FDE交付工程师/夏子聪-FDE交付工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 26,
        'company': '靖安科技',
        'position': 'FDE 全栈工程师',
        'link': 'https://www.zhipin.com/job_detail/980df8ecf473153a0nN62NW6GFFR.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 FDE 全栈工程师岗位。"
            "我熟练掌握 LangChain/LangGraph 与全栈开发：独立主导过 GraphRAG 智能问答系统（基于长对话实现 97.5% 精准引用与 0.82 秒低延迟响应），以及基于 FastAPI 搭建的多智能体协同平台。"
            "日常具备自动化部署工具交付经验，熟练掌握 Docker 部署与 Linux 运维，与贵司 FDE 全栈交付方向高度契合。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#26-靖安科技-FDE 全栈工程师/夏子聪-FDE 全栈工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 27,
        'company': '杭州铭予科技有限公司',
        'position': 'AI交付工程师/FDE（应届生培养方向）',
        'link': 'https://www.zhipin.com/job_detail/a813636565e9d5650nN53N-7E1FQ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI 交付工程师/FDE 岗位。"
            "我在 AI 项目落地与交付部署方面有完整实践：独立主导过 GraphRAG 智能问答系统，将引用准确率做到 97.5%、首字响应在 1 秒以内；"
            "同时搭建过多智能体工作流与自愈机制的 Agent 平台。熟练掌握 Python 与常用组件，具备扎实的部署环境排错与现场交付能力。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#27-杭州铭予科技有限公司-AI交付工程师_FDE（应届生培养方向）/夏子聪-AI交付工程师_FDE（应届生培养方向）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 28,
        'company': '领客深维',
        'position': 'AI -FDE工程师',
        'link': 'https://www.zhipin.com/job_detail/ca9bc0aac12300180nN82tW5FFNQ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI -FDE 工程师岗位。"
            "我具备大模型 Agent 落地与现场工程交付的双重实践：主导开发过 GraphRAG 系统（引用精度 97.5%、具备端到端低延迟）；"
            "同时熟练掌握从协议分析、逆向排查到自动化工具打包交付的全流程，熟悉 Python 后端与 MCP 通信机制，具备良好的工程抗压能力。"
            "附件已上传针对岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#28-领客深维-AI -FDE工程师/夏子聪-AI -FDE工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 31,
        'company': 'Muse/星檬',
        'position': 'AI Agent与工作流自动化实习生（可远程）',
        'link': 'https://www.zhipin.com/job_detail/845704fba377f3f30nF_2N-7GVZU.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 与工作流自动化岗位。"
            "我熟练掌握 LangGraph 与多 Agent 工作流工程化：在 GraphRAG 问答系统中设计了知识图谱与混合召回机制，意图消歧率达 87%；"
            "在场景生成 Agent 项目中基于 FastAPI 搭建了多智能体协同流水线与质检闭环，能稳定将模型输出转化为可执行成果，具备扎实的 Python 自动化能力。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与指导。期待能有机会与您深入交流！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#31-Muse_星檬-AI Agent与工作流自动化实习生（可远程）/夏子聪-AI Agent与工作流自动化实习生（可远程）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 32,
        'company': '次元跃动',
        'position': 'AI Agent 开发工程师',
        'link': 'https://www.zhipin.com/job_detail/952511ec57ee0f960nN53928E1BW.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 开发工程师岗位。"
            "我具备独立的大模型系统研发经验：独立主导过 GraphRAG 智能问答系统，实现真实长对话 97.5% 精准引用与低延迟响应；"
            "同时基于 FastAPI 搭建过多阶段智能体流水线与任务调度平台，熟练使用 Python 与 LangGraph 工作流开发，代码规范沉稳。"
            "附件已上传针对岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#32-次元跃动-AI Agent 开发工程师/夏子聪-AI Agent 开发工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 34,
        'company': '现象创新',
        'position': 'AI Agent 产品⼯程师 / 智能体应⽤⼯程师',
        'link': 'https://www.zhipin.com/job_detail/b0e1f5cc6a7b30410nZz2tu4F1ZW.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 应用工程师岗位。"
            "我专注于大模型 Agent 的落地开发与产品工程化：熟练运用 LangGraph 框架，主导落地过上下文召回率达 98.3% 的 GraphRAG 系统；"
            "在智能体平台中搭建过 FastAPI 异步服务、状态机机制与 MCP 接口，具备将复杂 Agent 技术稳定转化为业务工具的实践经验。"
            "附件已上传针对贵司定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#34-现象创新-AI Agent 产品⼯程师 _ 智能体应⽤⼯程师/夏子聪-AI Agent 产品⼯程师 _ 智能体应⽤⼯程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 35,
        'company': '深圳嘉策天晟数智科技',
        'position': 'AI Agent开发工程师（驻场交付方向）',
        'link': 'https://www.zhipin.com/job_detail/a83e7ec10bccdccb0nJ70t-0EFpR.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 开发工程师（驻场交付方向）岗位。"
            "我具备良好的工程适应力与现场排错能力：独立开发过 GraphRAG 问答系统（引用精度 97.5%、响应 0.82 秒），"
            "搭建过多智能体流水线与可自愈工作流平台。熟练掌握 Python、Docker 容器化部署与现场接口联调，能够稳步适应驻场业务节奏。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#35-深圳嘉策天晟数智科技-AI Agent开发工程师（驻场交付方向）/夏子聪-AI Agent开发工程师（驻场交付方向）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 36,
        'company': '小致科技',
        'position': '全栈工程师（FDE工程化方向）',
        'link': 'https://www.zhipin.com/job_detail/c162981a780e72ef0nJz29q5GFdZ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的全栈工程师（FDE工程化方向）岗位。"
            "我具备完整的大模型工程化落地实践：主导的 GraphRAG 系统实现 97.5% 精准引用与 606ms 低延迟，并在 Agent 平台中基于 FastAPI 实现了多智能体协同与安全执行环境。"
            "熟练掌握前后端交互、MCP 服务端通信与 Docker 交付部署，现场工程排查与解决问题能力扎实。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#36-小致科技-全栈工程师（FDE工程化方向）/夏子聪-全栈工程师（FDE工程化方向）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
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
    for bad in ['湖北文理', '文理学院', '24届', '关键词均有对应支撑', 'VFS安全沙箱']:
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
    time.sleep(3)

    # 检查是否有新标签页打开
    if dp.tabs_count > 1:
        dp.activate_tab(dp.latest_tab)

    # 检查是否有风控/上限弹窗
    dialog = dp.ele('css:.dialog-wrap, .dialog-container, [class*="dialog"]')
    if dialog and '上限' in dialog.text:
        print(f"🚨 触发今日沟通上限: {dialog.text}", flush=True)
        dp.get_screenshot(path='assets/deliver_proof/limit_reached.png')
        return 'limit_reached'

    # 6. 进入聊天中心
    if 'geek/chat' not in dp.url:
        print("🌐 前往聊天工作台...", flush=True)
        dp.get('https://www.zhipin.com/web/geek/chat')
        time.sleep(3)
    else:
        time.sleep(2)

    # 7. 激活左侧第一个会话
    print("🖱️ 激活最新会话...", flush=True)
    dp.run_js("""
        const el = document.elementFromPoint(200, 210);
        if (el) el.click();
        const textNodes = document.querySelectorAll('.friend-content .text, .friend-content-warp, div.user-list li');
        if (textNodes.length > 0) textNodes[0].click();
    """)
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

    # 9. 定位输入框并输入招呼语
    inp = None
    for _ in range(6):
        cand = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
        if cand and cand.rect.size[0] > 50:
            inp = cand
            break
        time.sleep(1)

    if not inp:
        print("❌ 未找到聊天输入框", flush=True)
        dp.get_screenshot(path=f"assets/deliver_proof/{job['idx']}_{job['company']}_no_input.png")
        return 'no_input'

    print(f"📝 正在填入定制招呼语 ({len(greeting)} 字)...", flush=True)
    inp.click()
    time.sleep(0.3)
    inp.input(greeting)
    time.sleep(1)

    # 10. 点击发送招呼语
    print("📤 发送招呼语...", flush=True)
    dp.run_js("""
        const btns = Array.from(document.querySelectorAll('button, .btn'));
        const send = btns.find(b => b.innerText && b.innerText.trim() === '发送');
        if (send) {
            send.click();
        } else {
            const ev = new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, which: 13, bubbles: true });
            document.querySelector('#chat-input').dispatchEvent(ev);
        }
    """)
    time.sleep(2)

    # 11. 上传简历高清长图附件
    print(f"📎 正在上传简历高清长图: {os.path.basename(job['image'])}...", flush=True)
    file_input = dp.ele('css:input[type="file"]') or dp.ele('css:.btn-sendimg input')
    if file_input:
        file_input.input(job['image'])
        print("✓ 长图已通过原生 input 接口提交，等待渲染...", flush=True)
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

    # 12. 截图落盘留证
    proof_path = os.path.abspath(f"assets/deliver_proof/{job['idx']}_{job['company']}_delivered.png")
    dp.get_screenshot(path=proof_path)
    print(f"📸 终局截图已保存: {proof_path}", flush=True)

    # 13. 写入全局持久化防重历史账本
    record_applied_job(job, status='applied', greeting=greeting, image=job['image'], run_dir=job['run_dir'])
    print(f"✅ #{job['idx']} {job['company']} 投递成功并成功记账！", flush=True)
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
            print(f"\n>>> 正在推进第 {i+1} / {len(TARGET_JOBS)} 家企业...", flush=True)
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
    print("📊 10家企业小测试执行总结:", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("========================================================", flush=True)

if __name__ == '__main__':
    main()
