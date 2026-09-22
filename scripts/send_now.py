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
    print("🌐 正在连接聊天窗口...", flush=True)
    dp.get('https://www.zhipin.com/web/geek/chat')
    time.sleep(3)

    # 1. 激活左侧第一项（刘女士）
    print("🖱️ 正在点击激活顶部会话...", flush=True)
    dp.run_js("""
        const el = document.elementFromPoint(200, 210);
        if (el) el.click();
        const textNodes = document.querySelectorAll('.friend-content .text, .friend-content-warp, div.user-list li');
        if (textNodes.length > 0) textNodes[0].click();
    """)
    time.sleep(2)

    # 2. 定位输入框并输入第二条定制招呼语
    inp = None
    for _ in range(6):
        cand = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
        if cand and cand.rect.size[0] > 50:
            inp = cand
            break
        time.sleep(1)

    if not inp:
        print("❌ 未找到输入框", flush=True)
        dp.get_screenshot(path='assets/failed_input_screen.png')
        sys.exit(1)
    print(f"🎯 成功锁定富文本输入框 (宽度: {inp.rect.size[0]}px)", flush=True)

    greeting_text = (
        "【随时到岗/可实习6个月/周5天】自动化大三夏子聪，看到咱们在招这个FDE岗位，感觉跟我现在折腾的方向特别合拍。\n\n"
        "我自己动手做过几个完整的AI项目。比如一个GraphRAG教研问答系统，把真实对白的检索引用精度做到了97.5%，响应不到1秒。另一个是AI Agent平台，我用FastAPI搭后端，做了完整的安全沙箱、虚拟文件系统和中间件管线，把LLM的输出约束成可执行、可验证的工作流。平时写Python和搞部署脚本很顺手，解决问题也快。\n\n"
        "简历长图已经贴上啦，方便的时候帮我看一眼？希望能有机会跟您深入交流！"
    )

    print(f"📝 正在输入针对 JD 的深度定制招呼语 ({len(greeting_text)} 字)...", flush=True)
    inp.click()
    time.sleep(0.3)
    inp.input(greeting_text)
    time.sleep(1)

    # 点击发送
    print("📤 正在发送招呼语...", flush=True)
    dp.run_js("""
        const btn = document.querySelector('.chat-op .btn-send, button.btn-send, [class*="btn-send"], button:not([disabled])');
        // 查找文案为 发送 的按钮
        const btns = Array.from(document.querySelectorAll('button, .btn'));
        const send = btns.find(b => b.innerText && b.innerText.includes('发送'));
        if (send) {
            send.click();
        } else {
            const ev = new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, which: 13, bubbles: true });
            document.querySelector('#chat-input').dispatchEvent(ev);
        }
    """)
    time.sleep(2)
    print("✓ 招呼语发送完毕，等待回读气泡...", flush=True)

    # 3. 发送简历长图附件
    image_path = os.path.abspath(r"assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#14-北京众互意联技术-FDE（前沿部署工程师）应届生_实习生/夏子聪-FDE（前沿部署工程师）应届生_实习生.png")
    print(f"📎 正在上传简历长图附件: {image_path}...", flush=True)

    # 查找图片 input
    file_input = dp.ele('css:input[type="file"]') or dp.ele('css:.btn-sendimg input')
    if file_input:
        file_input.input(image_path)
        print("✓ 长图文件已通过 input 接口提交，等待渲染...", flush=True)
    else:
        print("⚠️ 未找到原生 file input，尝试通过注入上传组件提交...", flush=True)
        # 点击图片图标
        dp.run_js("""
            const icon = document.querySelector('.icon-chat-img, [class*="sendimg"], [class*="image"]');
            if (icon) icon.click();
        """)
        time.sleep(1)
        fi = dp.ele('css:input[type="file"]')
        if fi:
            fi.input(image_path)

    time.sleep(4)

    # 4. 截图保存实测结果
    final_shot = os.path.abspath('assets/job14_final_delivered.png')
    dp.get_screenshot(path=final_shot)
    print(f"\n📸 终局截图已保存到: {final_shot}", flush=True)

finally:
    dp.quit()
