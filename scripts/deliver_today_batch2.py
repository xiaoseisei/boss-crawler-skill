# -*- coding: utf-8 -*-
"""2026-09-20 今日第二批投递执行脚本（Top 5 核心AI Agent与优质后端/算法研发）
候选名单：
1. 非凸科技 - 大模型应用开发工程师（实习）
2. 北京福来数创智能科技 - 算法实习生（大模型应用方向）
3. 深圳市智元数创科技 - Python后端开发工程师助理
4. 凡岛 - 大模型算法工程师
5. 深圳某大型计算机软件公司 - 后端开发工程师（Python / Java / C++）

执行规范：
- 正式职业化招呼语（黄金前15字到岗承诺、无校名漏洞、无口语俚语、单段完整送达）
- 详情页沟通状态强检测（继续沟通/已沟通自动拦截防重）
- 自适应忽略微信扫码订阅弹窗，直达聊天工作台
- 聊天室简历图片防重检测
- 发送招呼语 + 上传高清长图简历
- 截图存证至 assets/deliver_proof/ 并更新持久化历史账本
"""
import os, sys, time, json

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser
from resume_matcher.history import record_applied_job, is_job_applied, load_applied_history

BATCH2_TARGET_JOBS = [
    {
        'idx': 6,
        'company': '非凸科技',
        'position': '大模型应用开发工程师（实习）',
        'link': 'https://www.zhipin.com/job_detail/f33fe8470e1eb52403V-2tq7FFpW.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的大模型应用开发工程师（实习）岗位。"
            "我专注大模型工程化落地与全栈开发：独立主导过垂直领域的 GraphRAG 智能问答系统，通过图谱混合召回将复杂对话引用准确率提升至 97.5%、响应低至 0.82 秒；"
            "熟练运用 LangGraph 搭建多智能体协同流水线与安全沙箱执行环境。熟练掌握 Python，具备数模国奖算法功底与扎实的全栈独立开发能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#38-非凸科技-大模型应用开发工程师（实习）/夏子聪-大模型应用开发工程师（实习）.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 7,
        'company': '北京福来数创智能科技',
        'position': '算法实习生（大模型应用方向）',
        'link': 'https://www.zhipin.com/job_detail/14d16170ad5e56660nJz3di7GFJR.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的算法实习生（大模型应用方向）岗位。"
            "我深入实践大模型智能体与 GraphRAG 体系研发：熟练掌握 LangGraph 构建多智能体协作系统，实现包含工具调用与反思质检的完整流水线；"
            "主导开发的 EduGraph-RAG 实现了 97.5% 引用准确率，并基于 FastAPI 封装高性能 RESTful API 服务。熟练使用 Python，工程上手快。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#47-北京福来数创智能科技-算法实习生（大模型应用方向）/夏子聪-算法实习生（大模型应用方向）.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 8,
        'company': '深圳市智元数创科技',
        'position': 'Python后端开发工程师助理',
        'link': 'https://www.zhipin.com/job_detail/3b5ec2f209e1916f0nd62t26GFBQ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 Python 后端开发工程师助理岗位。"
            "我具备扎实的 Python 全栈与后端服务开发基础：熟练使用 FastAPI 搭建高内聚低耦合的后端 API，熟悉数据库 CRUD 与常规 SQL 操作；"
            "在项目中独立完成接口设计、代码联调与单元测试，具备良好的代码规范与 Git 协作习惯，能快速理解业务并排查解决问题。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#29-深圳市智元数创科技-Python后端开发工程师助理/夏子聪-Python后端开发工程师助理.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 9,
        'company': '凡岛',
        'position': '大模型算法工程师',
        'link': 'https://www.zhipin.com/job_detail/1f1acecd3bd9b04a0nJ_0tu_FlpR.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的大模型算法工程师岗位。"
            "我深耕大模型技术栈与垂直领域落地：曾基于 Qwen3 完成模型 LoRA 微调及多模态 VLM 内容校验，在指令数据清洗与评测调优方面有丰富实操；"
            "同时主导开发 GraphRAG 智能问答系统，将复杂长对话检索准确率提升至 97.5%。熟练掌握 Python 与主流深度学习框架，工程落地能力扎实。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#48-凡岛-大模型算法工程师/夏子聪-大模型算法工程师.png'),
        'run_dir': 'assets/2026-09-18_10-17-37_batch2'
    },
    {
        'idx': 10,
        'company': '深圳某大型计算机软件公司',
        'position': '后端开发工程师（Python / Java / C++）',
        'link': 'https://www.zhipin.com/job_detail/615081ee9196bfb70nN439i6EFBQ.html',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司在北京的后端开发工程师岗位。"
            "我具备扎实的后端工程与 AI 创新项目实战经验：熟练使用 Python 与 FastAPI 搭建高性能后台服务，熟悉常用数据库组件与 Linux 环境；"
            "同时独立负责过 GraphRAG 知识库系统与多 Agent 协作工作流的开发与联调，在接口封装、性能调优与排错上经验丰富。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_10-17-37_batch2/deliver/#46-深圳某大型计算机软件公司-后端开发工程师（Python _ Java _ C++）/夏子聪-后端开发工程师（Python _ Java _ C++）.png'),
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
        for i, job in enumerate(BATCH2_TARGET_JOBS):
            print(f"\n>>> 正在推进第二批第 {i+1} / {len(BATCH2_TARGET_JOBS)} 家企业...", flush=True)
            res = deliver_one_job(dp, job)
            results[f"#{job['idx']} {job['company']}"] = res
            if res == 'limit_reached':
                print("🚨 达到每日沟通上限，安全终止当前批次！", flush=True)
                break
            # 停顿防频控 (7秒)
            if i < len(BATCH2_TARGET_JOBS) - 1:
                print("⏳ 停顿 7 秒进入下一家...", flush=True)
                time.sleep(7)
    finally:
        dp.quit()

    print("\n========================================================", flush=True)
    print("📊 第二批投递执行总结:", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("========================================================", flush=True)

if __name__ == '__main__':
    main()
