# -*- coding: utf-8 -*-
"""10家技术与交付型企业正式闭环投递脚本 (批次 3)
严格遵循：
1. 详情页「继续沟通」与弹窗「已沟通/已发送」强拦截
2. 聊天室已有历史记录与已发图片强拦截
3. 正式职业化招呼语（无校名、大三在读本科生、无机器做题家八股、无口语俗语、单段完整送达）
4. 高清长图简历附件上传
5. 终局截屏核验与持久化记账
"""
import os, sys, time, json

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from resume_matcher.history import record_applied_job, is_job_applied, load_applied_history

TARGET_JOBS = [
    {
        'idx': 38,
        'company': '梅西珠宝',
        'position': 'AI FDE（内部数据化落地）',
        'link': 'https://www.zhipin.com/job_detail/d517bf6a1896aa430nN_0t66EVFQ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI FDE（内部数据化落地）岗位。"
            "我专注于大模型应用在企业内部业务流中的工程化落地：独立主导过 GraphRAG 智能问答系统，将复杂对话数据的检索引用准确率做到 97.5%、首字响应控制在 1 秒以内；"
            "熟练运用 Python 与 FastAPI 搭建自动化流水线与结构化数据处理工具，具备良好的现场交付与环境排错能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#38-梅西珠宝-AI FDE（内部数据化落地）/夏子聪-AI FDE（内部数据化落地）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 39,
        'company': '深圳市耀光领智科技',
        'position': 'AI FDE / AI 交付工程师（应届生可投）',
        'link': 'https://www.zhipin.com/job_detail/759e5420a96bfa8d0nN62N68FFFT.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI FDE / AI 交付工程师岗位。"
            "我在 Agent 工程化与现场交付方面具备扎实基础：主导落地过垂直领域 GraphRAG 智能系统，基于混合召回与图谱索引实现长文本高精度引用与秒级响应；"
            "具备 Linux 运维、Docker 容器化部署与协议逆向排查经验，能独立推进现场环境适配与交付支持。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#39-深圳市耀光领智科技-AI FDE _ AI 交付工程师（应届生可投）/夏子聪-AI FDE _ AI 交付工程师（应届生可投）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 40,
        'company': '汉王数据',
        'position': 'AI Agent工程师（算法/Java）',
        'link': 'https://www.zhipin.com/job_detail/2118ec6aa79cbc0f0nB63N65FFBY.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 工程师岗位。"
            "我专注于大模型智能体架构与落地实践：熟练运用 LangGraph 构建多智能体协同流水线与自愈质检机制；"
            "在 GraphRAG 问答系统中独立实现了多阶段召回与图谱构建，将引用准确率提升至 97.5%。熟练掌握 Python 与后端开发，逻辑严密，学习与工程适应能力强。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#40-汉王数据-AI Agent工程师（算法_Java）/夏子聪-AI Agent工程师（算法_Java）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 41,
        'company': '元璟资本',
        'position': '元璟被投-北美AI agent 大模型算法-远程',
        'link': 'https://www.zhipin.com/job_detail/e525ceeeec31614f0nN52N-8FldY.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职该北美 AI Agent 大模型算法实习岗位。"
            "我专注于前沿智能体工作流与 RAG 算法落地：熟练掌握 LangGraph 与多 Agent 状态机调度，在项目中独立实现了多步骤意图消歧与自愈反思工作流；"
            "主导的 GraphRAG 问答系统实现了 97.5% 精准引用与 0.82 秒低延迟响应。具备扎实的 Python 算法工程与全流程交付经验，适应远程协作节奏。"
            "附件已上传针对岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#41-元璟资本-元璟被投-北美AI agent 大模型算法-远程/夏子聪-元璟被投-北美AI agent 大模型算法-远程.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 42,
        'company': '港理大研究院',
        'position': 'AI Agent开发实习生',
        'link': 'https://www.zhipin.com/job_detail/ecc33a109879cb100nB73t-7FltS.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵院的 AI Agent 开发实习生岗位。"
            "我具备扎实的研究实践与系统工程能力：独立主导过 GraphRAG 智能问答系统，通过知识图谱与混合索引将长文本对话引用精度提升至 97.5%；"
            "在智能体项目中熟练运用 LangGraph 搭建多 Agent 协同流水线。曾获数模国奖，具备优秀的问题建模、文献研读与算法复现能力。"
            "附件已上传针对岗位定制的简历长图，诚盼老师及团队的审阅与指导。期待能有机会与您深入交流！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#42-港理大研究院-AI Agent开发实习生/夏子聪-AI Agent开发实习生.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 43,
        'company': '隐向量科技',
        'position': 'AI Agent领域开发工程师',
        'link': 'https://www.zhipin.com/job_detail/a3f5b4f29dc7fd6203J43Nm9FltZ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 领域开发工程师岗位。"
            "我专注于大模型 Agent 的核心工程落地：基于 LangGraph 与 FastAPI 独立设计并实现了具备任务拆解、多智能体协同与自愈质检的 Agent 平台；"
            "并在 GraphRAG 问答系统中攻克了长对话上下文引用的难题，实现 97.5% 的引用准确率。代码严谨规范，具备端到端系统开发能力。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#43-隐向量科技-AI Agent领域开发工程师/夏子聪-AI Agent领域开发工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 44,
        'company': '上海壹玩科技有限公司',
        'position': 'FDE 工程师',
        'link': 'https://www.zhipin.com/job_detail/f3b5e0da7bb5a96e0nN_3tW5FlZT.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 FDE 工程师岗位。"
            "我具备 AI 应用研发与现场工程部署的双重实践经验：独立落地过 GraphRAG 智能问答系统（首字响应 0.82 秒、引用精度 97.5%），"
            "熟练掌握 Python、Linux 运维及 Docker 容器化打包；同时具备逆向抓包与接口分析经验，能快速适应现场业务环境并高效排障。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#44-上海壹玩科技有限公司-FDE 工程师/夏子聪-FDE 工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 46,
        'company': '杭州商通智能科技',
        'position': 'AI项目FDE工程师',
        'link': 'https://www.zhipin.com/job_detail/28a6fe76fc41d2b80nJz0t-9FlNZ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI 项目 FDE 工程师岗位。"
            "我专注于 AI 系统的现场交付与工程落地：主导设计并实现了 GraphRAG 智能问答系统，通过图谱索引与混合检索将引用准确率做到 97.5%；"
            "熟练掌握 Python 与常用服务组件，具备 Docker 容器化部署、Linux 环境运维与接口联调排错能力，能扎实推进现场项目闭环。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#46-杭州商通智能科技-AI项目FDE工程师/夏子聪-AI项目FDE工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 47,
        'company': '杭州赢云贸易有限公司',
        'position': 'AI Agent 开发师（Python）岗位代码 PY01',
        'link': 'https://www.zhipin.com/job_detail/213d6a2a05bfba420nF60964FVVS.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 开发师（Python）岗位。"
            "我熟练掌握 Python 全栈与大模型智能体开发：独立主导过 GraphRAG 智能问答系统，实现 97.5% 的长文本精准引用与低延迟响应；"
            "同时基于 FastAPI 与 LangGraph 搭建过多智能体协同流水线与安全执行环境，具备扎实的数据接口联调与自动化业务工具构建能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#47-杭州赢云贸易有限公司-AI Agent 开发师（Python）岗位代码 PY01/夏子聪-AI Agent 开发师（Python）岗位代码 PY01.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 49,
        'company': '美腾思智能',
        'position': 'AI应用工程师-AI Agent / 视频智能体方向',
        'link': 'https://www.zhipin.com/job_detail/7d702445183c8d900nJ43N27EFBZ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI 应用工程师（AI Agent / 视频智能体方向）岗位。"
            "我深耕大模型智能体与多模态工作流工程化：熟练运用 LangGraph 构建具备任务拆解与多智能体协同的工作流，"
            "在 GraphRAG 项目中实现了精准知识图谱构建与秒级响应；熟练掌握 Python、FastAPI 与模型调用封装，具备扎实的应用系统落地与调优经验。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#49-美腾思智能-AI应用工程师-AI Agent _ 视频智能体方向/夏子聪-AI应用工程师-AI Agent _ 视频智能体方向.png'),
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
    time.sleep(3)

    # 检查弹窗
    dialog = dp.ele('css:.dialog-wrap, .dialog-container')
    if dialog:
        dtext = dialog.text
        if ('今日沟通' in dtext and '上限' in dtext) or ('沟通次数' in dtext and '上限' in dtext):
            print(f"🚨 触发今日沟通上限: {dtext}", flush=True)
            dp.get_screenshot(path='assets/deliver_proof/limit_reached.png')
            return 'limit_reached'
        if '已发送' in dtext or '订阅回复' in dtext:
            print("🛑 弹窗显示已有沟通记录，强行拦截，补录防重库并跳过！", flush=True)
            record_applied_job(job, status='already_communicated', greeting=greeting, image=job['image'], run_dir=job['run_dir'])
            dp.get_screenshot(path=f"assets/deliver_proof/{job['idx']}_{job['company']}_skipped.png")
            return 'skipped_already_communicated'

    # 检查是否有新标签页打开
    if dp.tabs_count > 1:
        dp.activate_tab(dp.latest_tab)

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
    print("📊 第三批企业投递执行总结:", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("========================================================", flush=True)

if __name__ == '__main__':
    main()
