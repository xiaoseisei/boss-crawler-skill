# -*- coding: utf-8 -*-
"""5家企业小步快跑投递测试脚本 (完全对齐 send_now.py 验证生效逻辑)
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
        'idx': 15,
        'company': '深圳丰禾创业投资咨询',
        'position': '融资顾问与投资行业FDE',
        'link': 'https://www.zhipin.com/job_detail/364be0bd4acb03c30nJz2tW_E1pU.html',
        'greeting': (
            "【随时到岗/可实习6个月/周5天】您好！我是自动化专业大三夏子聪。"
            "看到咱们在招投资行业FDE，我对知识库组织、行业数据分析与现场交付非常感兴趣。"
            "我独立做过垂直领域的GraphRAG智能问答系统，把复杂对白数据的精准召回做到98.3%、响应0.82秒；"
            "曾获数模国奖，擅长复杂数据处理、逻辑结构化分析与Python自动化。动手能力强，能快速适应现场业务需求。"
            "简历长图已在下方贴上，方便时帮我过目一下？期待能与您交流！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#15-深圳丰禾创业投资咨询-融资顾问与投资行业FDE/夏子聪-融资顾问与投资行业FDE.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 16,
        'company': '知时致和',
        'position': 'FDE 前端部署工程师',
        'link': 'https://www.zhipin.com/job_detail/f56a25fe0d9ba55a0nF82Nm4FlFR.html',
        'greeting': (
            "【随时到岗/可实习6个月/周5天】您好！我是自动化专业大三夏子聪。"
            "我平时做过不少逆向工程与抓包协议分析（熟练用Frida、JADX还原加密网关与动态Token），"
            "同时自己动手搭建过端到端可交付的AI智能体工作流与GraphRAG问答系统。"
            "写Python、搞交付部署和排查现场Bug很顺手。简历长图已经发在下面啦，方便的话帮我看一眼？期待能跟您交流！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#16-知时致和-FDE 前端部署工程师/夏子聪-FDE 前端部署工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 17,
        'company': '英诺曼人工智能',
        'position': 'FDE 前沿部署工程师（AI交付/现场研发）',
        'link': 'https://www.zhipin.com/job_detail/4bd782294fad794f0nN62tW-GFdW.html',
        'greeting': (
            "【随时到岗/可实习6个月/周5天】您好！我是自动化大三夏子聪，看到咱们在招FDE现场研发交付，特别契合我的实践方向。"
            "我自己动手做过完整的GraphRAG教研问答系统，把检索召回做到98.3%、响应不到1秒；"
            "也搭建过包含多智能体流水线和自愈机制的Agent平台。平时写Python做部署、跑脚本和现场解决实际工程问题都很顺手，抗压能力强。"
            "简历长图在下方，方便时帮我过目一下？希望能有机会深入交流！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#17-英诺曼人工智能-FDE 前沿部署工程师（AI交付_现场研发）/夏子聪-FDE 前沿部署工程师（AI交付_现场研发）.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 19,
        'company': '深圳市搭班子智能科技',
        'position': 'FDE前端部署工程师',
        'link': 'https://www.zhipin.com/job_detail/e4bc086dca108c600nJ62tu6FlpR.html',
        'greeting': (
            "【随时到岗/可实习6个月/周5天】您好！我是自动化大三夏子聪。平时写Python和Java比较熟，有完整的Docker容器化和Linux服务部署经验。"
            "在之前的Agent平台项目中，我用FastAPI搭后端，实现了安全沙箱、中间件管线和多Agent工作流，把大模型能力封装成稳定可交付的工具。"
            "工程落地和排查部署问题很顺手，学习上手快。超清简历长图已发在下方，方便帮我看一眼吗？期待能有机会交流！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#19-深圳市搭班子智能科技-FDE前端部署工程师/夏子聪-FDE前端部署工程师.png'),
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    },
    {
        'idx': 23,
        'company': '宜飞科技',
        'position': 'AI Agent 全栈开发工程师',
        'link': 'https://www.zhipin.com/job_detail/d94630221600e99d0nF-2968E1VU.html',
        'greeting': (
            "【随时到岗/可实习6个月/周5天】您好！我是自动化大三夏子聪，看到贵司的AI Agent全栈开发岗位非常契合。"
            "我自己动手做过完整的AI项目：一个GraphRAG智能问答系统，真实长对话引用精度做到97.5%，首字响应不到1秒；"
            "另一个Agent平台用FastAPI实现，搭建了多智能体协同流水线和安全执行环境。平时写前后端、调Prompt、写自动化部署脚本都比较熟练。"
            "简历长图已在下方贴上，方便时帮我看一眼？期待能跟您深入聊聊！"
        ),
        'image': os.path.abspath(r'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#23-宜飞科技-AI Agent 全栈开发工程师/夏子聪-AI Agent 全栈开发工程师.png'),
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
            # 适度停顿防频控
            if i < len(TARGET_JOBS) - 1:
                print("⏳ 停顿 6 秒进入下一家...", flush=True)
                time.sleep(6)
    finally:
        dp.quit()

    print("\n========================================================", flush=True)
    print("📊 5家企业小测试执行总结:", flush=True)
    for k, v in results.items():
        print(f"  {k}: {v}", flush=True)
    print("========================================================", flush=True)

if __name__ == '__main__':
    main()
