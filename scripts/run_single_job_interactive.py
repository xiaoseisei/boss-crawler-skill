# -*- coding: utf-8 -*-
"""单岗位全流程交互式实操与验证脚本"""
import os
import sys
import time
from DrissionPage import WebPage, ChromiumOptions

sys.path.insert(0, 'scripts')
sys.path.insert(0, 'scripts/deliver')
from browser_finder import find_chrome_browser
from resume_matcher.auto_apply import (
    validate_greeting_content, _count_chat_images, _greeting_probe, 
    _norm, check_login_status
)
from write_application_md import load_jobs
from apply import find_greeting, find_image, job_dir_name

def run_job(run_dir, job_index):
    print(f"\n{'='*60}", flush=True)
    print(f"🚀 开始对岗位 #{job_index} 执行全流程单步实操与校验", flush=True)
    print(f"{'='*60}", flush=True)

    # 1. 加载岗位与物料
    jobs = load_jobs(run_dir)
    if job_index < 1 or job_index > len(jobs):
        print(f"❌ 岗位序号 #{job_index} 超出范围 (1~{len(jobs)})", flush=True)
        return False
    job = jobs[job_index - 1]
    dir_name, pos = job_dir_name(job, job_index)
    company = job.get('公司', '未知公司')
    link = job.get('link', '')

    print(f"📌 目标公司: {company}", flush=True)
    print(f"📌 目标岗位: {pos}", flush=True)
    print(f"📌 岗位链接: {link}", flush=True)

    greeting, greeting_src = find_greeting(run_dir, job_index, dir_name)
    image_path = find_image(run_dir, job, '夏子聪', job_index)

    print(f"\n--- [审查阶段 1：招呼语与物料审查] ---", flush=True)
    ok, reason = validate_greeting_content(greeting)
    if not ok:
        print(f"❌ 招呼语得体性审查失败: {reason}", flush=True)
        return False
    print(f"✅ 招呼语审查通过 ({len(greeting)} 字，来源: {os.path.basename(greeting_src)})", flush=True)
    print(f"   招呼语预览:\n   {greeting[:120]}...\n", flush=True)

    if not image_path or not os.path.exists(image_path) or os.path.getsize(image_path) == 0:
        print(f"❌ 简历长图不存在或为空: {image_path}", flush=True)
        return False
    print(f"✅ 简历长图已就绪: {os.path.basename(image_path)} ({os.path.getsize(image_path) // 1024} KB)", flush=True)

    # 2. 启动浏览器
    print(f"\n--- [执行阶段 1：启动浏览器与登录态核对] ---", flush=True)
    co = ChromiumOptions()
    chrome_path = find_chrome_browser()
    if chrome_path:
        co.set_browser_path(chrome_path)
    user_data_dir = os.path.abspath('assets/chrome_user_data')
    co.set_argument(f'--user-data-dir={user_data_dir}')
    dp = WebPage(chromium_options=co)

    try:
        dp.get('https://www.zhipin.com/web/geek/recommend')
        time.sleep(2)
        if not check_login_status(dp):
            print("❌ 未检测到登录状态，请先在浏览器登录！", flush=True)
            return False
        print("✅ 登录状态验证通过！", flush=True)

        # 3. 打开岗位详情页并防重检查
        print(f"\n--- [执行阶段 2：打开详情页与防重门禁] ---", flush=True)
        print(f"🌐 正在导航至: {link}", flush=True)
        dp.get(link)
        time.sleep(3)

        btn = dp.ele('css:.btn-startchat') or dp.ele('xpath://a[contains(@class, "btn-startchat")]')
        if not btn:
            print("❌ 未找到沟通按钮", flush=True)
            return False

        btn_text = (btn.text or '').strip()
        print(f"🔍 页面按钮文本为: 「{btn_text}」", flush=True)
        if any(kw in btn_text for kw in ["继续", "已沟通", "已投递"]):
            print(f"🛑 路由安全拦截生效：按钮是「{btn_text}」，说明此前已沟通，坚决不二次打扰！", flush=True)
            return False
        if "立即沟通" not in btn_text:
            print(f"⚠️ 按钮不是「立即沟通」，为安全起见停止: 「{btn_text}」", flush=True)
            return False

        # 4. 点击立即沟通
        print(f"\n--- [执行阶段 3：点击立即沟通进入会话] ---", flush=True)
        btn.click()
        print(f"🖱️ 已点击「立即沟通」，等待进入聊天...", flush=True)
        time.sleep(3)

        # 关闭弹窗
        for sel in ['.dialog-wrap .close', '.boss-dialog__close', '[class*="dialog"] [class*="close"]']:
            try:
                for c in dp.eles(f'css:{sel}'):
                    if c.is_displayed():
                        c.click()
                        print(f"  ✓ 已关闭遮罩弹窗: {sel}", flush=True)
            except Exception:
                pass

        if len(dp.tab_ids) > 1:
            dp.to_tab(dp.tab_ids[-1])
            print(f"🔀 已切换到最新聊天标签页: {dp.url}", flush=True)

        if "/web/geek/chat" not in dp.url:
            dp.get("https://www.zhipin.com/web/geek/chat")
            time.sleep(3)

        # 激活左侧第一个会话项
        for _ in range(6):
            try:
                dp.run_js("""
                    const active = document.querySelector('.geek-chat-list .chat-item.active, .chat-user-list li.selected');
                    if (!active) {
                        const first = document.querySelector('.geek-chat-list .chat-item, .chat-user-list li, [class*="chat-item"]');
                        if (first) first.click();
                    }
                """)
                inp = dp.ele('css:#chat-input', timeout=0.5) or dp.ele('css:[contenteditable="true"]', timeout=0.5)
                if inp and inp.rect.size[0] > 50:
                    print(f"🎯 聊天输入框已就绪 (宽度: {inp.rect.size[0]}px)", flush=True)
                    break
            except Exception:
                pass
            time.sleep(1)

        inp = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
        if not inp:
            print("❌ 未找到输入框", flush=True)
            return False

        # 5. 输入定制招呼语并发送
        print(f"\n--- [执行阶段 4：发送定制 AI 招呼语] ---", flush=True)
        inp.click()
        time.sleep(0.3)
        inp.input(greeting)
        print(f"📝 招呼语已输入到富文本框 (长度: {len(greeting)} 字)", flush=True)
        time.sleep(1)

        send_btn = dp.ele('css:button.btn-send, button.btn-sure-v2') or dp.ele('xpath://button[contains(@class, "btn-send") or contains(text(), "发送")]')
        if send_btn:
            send_btn.click()
            print("📤 已点击发送按钮", flush=True)
        else:
            inp.input('\n')
            print("📤 已按回车发送", flush=True)
        time.sleep(2)

        # 校验文字气泡
        probe = _greeting_probe(greeting, 10)
        current_chat = dp.run_js("""
            const m = document.querySelector('[class*="chat-message-list"], [class*="message-list"], .chat-record');
            return m ? m.innerText : '';
        """) or ''
        greeting_sent = probe in _norm(current_chat)
        print(f"✅ 招呼语送达校验: {'✓ 已成功送达上屏' if greeting_sent else '⚠️ 未直接命中特征码'}", flush=True)

        # 6. 发送简历长图附件
        print(f"\n--- [执行阶段 5：上传定制简历长图附件] ---", flush=True)
        initial_img_count = _count_chat_images(dp)
        print(f"🖼️ 当前图片气泡数: {initial_img_count}", flush=True)

        file_input = None
        for sel in ['css:.btn-sendimg input[type="file"]', 'css:input[type="file"][accept*="image"]', 'css:input[type="file"]']:
            try:
                fi = dp.ele(sel, timeout=1)
                if fi:
                    file_input = fi
                    print(f"📎 命中上传组件: {sel}", flush=True)
                    break
            except Exception:
                pass

        img_sent = False
        if file_input:
            print(f"📤 正在上传图片附件: {image_path}", flush=True)
            file_input.input(image_path)
            time.sleep(3)
            for attempt in range(8):
                new_count = _count_chat_images(dp)
                if new_count > initial_img_count:
                    print(f"✅ 简历长图气泡已成功渲染！({initial_img_count} → {new_count})", flush=True)
                    img_sent = True
                    break
                time.sleep(1)
        else:
            print("❌ 未找到图片上传 input", flush=True)

        # 7. 截图留证
        screenshot_path = os.path.abspath(os.path.join(run_dir, f'test_chat_job_{job_index}.png'))
        try:
            dp.get_screenshot(path=screenshot_path)
            print(f"\n📸 当前会话真实截图已落盘: {screenshot_path}", flush=True)
        except Exception as ex:
            print(f"⚠️ 截图失败: {ex}", flush=True)

        # 8. 记账
        from resume_matcher.history import record_applied_job
        if greeting_sent or img_sent:
            record_applied_job(job=job, status='applied', greeting=greeting, image=image_path, run_dir=run_dir)
            print(f"💾 该岗位已安全记入全局防重账本！", flush=True)

        print(f"\n{'='*60}", flush=True)
        print(f"🎉 岗位 #{job_index} {company} 完整流程单步实操完毕！", flush=True)
        print(f"   · 招呼语发送: {'✅ 成功' if greeting_sent else '❌ 失败'}", flush=True)
        print(f"   · 简历图附件: {'✅ 成功' if img_sent else '❌ 失败'}", flush=True)
        print(f"{'='*60}\n", flush=True)
        return True
    finally:
        dp.quit()

if __name__ == '__main__':
    run_dir = sys.argv[1] if len(sys.argv) > 1 else 'assets/2026-09-18_11-31-40_fde_agent_sme'
    idx = int(sys.argv[2]) if len(sys.argv) > 2 else 14
    run_job(run_dir, idx)
