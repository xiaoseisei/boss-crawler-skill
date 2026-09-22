"""独立、无截图依赖的招聘投递工作流执行器模块。

核心架构与设计原则：
1. 依赖注入（Dependency Injection）：
   核心调度函数 ``run_jobs`` 与 ``run_one`` 接收抽象的 ``BrowserOps`` 实例，
   模块本身仅拥有业务状态机、安全守卫（Safety Gates）与异常审计逻辑，便于进行单测与多引擎替换。
2. 细粒度状态机与安全守卫（Safety Gates）：
   - precheck（前置检查）：链接有效性校验；
   - history_guard（历史排重）：基于已投递数据库排重；
   - detail_guard（详情页守卫）：岗位下线检测、当日上限熔断检测；
   - session_guard（会话身份守卫）：验证当前激活的会话是否属于目标公司，杜绝串会话误发；
   - send_greeting（招呼语发送）：清空输入框、输入文本、点击/回车双保险发送及消息送达确认；
   - upload_image（简历上传）：文件上传控件注入及图片消息确认；
   - audit（审计结账）：写入本地 JSONL 审计事件并更新全局历史库。
3. 自动化环境管控：
   提供独立的命令行接口，支持 Chrome 进程拉起、登录检测、健康探针与多参数执行。
"""
import argparse
import json
import os
import sys
import time
import random
import subprocess
import urllib.request
from typing import Iterable, Optional

# 兼容作为独立脚本执行或作为包模块导入两种运行模式
if __package__ in (None, ''):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from delivery_workflow.assertions import assert_greeting_sent, assert_image_sent, assert_overlay_clear
    from delivery_workflow.exceptions import DailyLimitReachedError, GreetingSendFailedError, TargetSessionNotFoundError
    from delivery_workflow.ledger import Ledger
    from delivery_workflow.models import JobContext, JobResult
    from delivery_workflow.observers import classify_chat_button, has_resume_image, has_matching_greeting
    from delivery_workflow.lock import WorkflowLock
else:
    from .assertions import assert_greeting_sent, assert_image_sent, assert_overlay_clear
    from .exceptions import DailyLimitReachedError, GreetingSendFailedError, TargetSessionNotFoundError
    from .ledger import Ledger
    from .models import JobContext, JobResult
    from .observers import classify_chat_button, has_resume_image, has_matching_greeting
    from .lock import WorkflowLock


def run_one(ops, ctx: JobContext, ledger=None, dry_run=False) -> JobResult:
    """执行单个岗位的完整投递状态机。
    
    依次通过前置检查、历史库排重、详情页导航、会话匹配校验、
    招呼语发送、图片上传以及审计日志写入。
    
    Args:
        ops: BrowserOps 浏览器原子操作接口实例。
        ctx: JobContext 当前岗位的投递上下文。
        ledger: Ledger 记账器实例（可选）。
        dry_run: 是否为干运行模式（仅探测页面与按钮状态，不执行实质性发送）。
        
    Returns:
        JobResult: 投递结果对象，记录最终状态、停留阶段、各环节耗时及错误详情。
        
    Raises:
        DailyLimitReachedError: 当检测到平台今日沟通次数上限时向上抛出，触发外层熔断。
    """
    job_started = time.perf_counter()
    result = JobResult(ctx.index, ctx.company, ctx.position, 'failed', 'precheck')
    
    # 阶段 1：前置检查（precheck）——验证岗位是否具备有效链接
    if not ctx.link:
        result.status, result.stage, result.error = 'skipped', 'precheck', '无岗位链接'
        result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
        return result
        
    try:
        # 阶段 2：历史排重守卫（history_guard）——比对全局已投递库
        scripts_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if scripts_root not in sys.path:
            sys.path.insert(0, scripts_root)
        from resume_matcher.history import is_job_applied
        
        history_job = dict(ctx.job)
        history_job['link'] = ctx.link
        history_job['position'] = ctx.position
        applied, _record = is_job_applied(history_job)
        if applied:
            result.status, result.stage = 'skipped_history', 'history_guard'
            result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
            return result
            
        # 阶段 3：详情页守卫（detail_guard）——打开详情页并判断沟通按钮状态
        ops.open_job_detail(ctx.link)
        button = classify_chat_button(ops.read_job_chat_button())
        already_communicated = button == 'already_communicated'
        
        # 岗位已下线或不可沟通
        if button == 'offline':
            result.status, result.stage = 'skipped_offline', 'detail_guard'
            result.timings.update(getattr(ops, 'metrics', {}))
            result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
            return result
            
        # 若开启了 dry-run 演练模式，在此提前终止并记录演练成功
        if dry_run:
            result.status, result.stage = 'dry_run', 'detail_guard'
            result.timings.update(getattr(ops, 'metrics', {}))
            result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
            return result

        # 阶段 4：点击沟通并进行每日上限探测
        # “立即沟通”与“继续沟通”均能让 BOSS 后台在聊天工作台精准激活对应会话
        result.stage = 'start_chat'
        ops.click_start_chat()
        if not already_communicated and ops.read_daily_limit_dialog():
            raise DailyLimitReachedError('触发每日沟通上限')
            
        # 阶段 5：打开聊天工作台并清除遮罩
        result.stage = 'open_chat'
        ops.open_chat_workspace()
        removed = ops.remove_overlay()
        assert_overlay_clear(removed)
        
        # 阶段 6：会话身份守卫（session_guard）——防串会话安全校验
        result.stage = 'session_guard'
        # 优先使用快速路径（自动激活的目标身份），若未就绪则在左侧列表检索并点击
        identity = ops.wait_for_active_identity(ctx.company) if hasattr(ops, 'wait_for_active_identity') else ''
        if not identity:
            ops.select_chat_session(ctx.company, ctx.position)
            # 点击激活后进行短轮询，等待右侧主会话身份与 DOM 渲染就绪
            if hasattr(ops, 'wait_for_active_identity'):
                identity = ops.wait_for_active_identity(ctx.company, timeout=3.0)
            else:
                identity = ops.read_active_chat_identity()
            
        matcher = getattr(ops, 'identity_matches', lambda value, company: company in value)
        if not matcher(identity, ctx.company):
            raise TargetSessionNotFoundError('无法证明当前聊天会话属于目标公司: %r' % identity)
            
        # 阶段 7：状态对齐与幂等性检查（audit reconciliation）
        # 检查是否历史已投递过（例如人工已发过招呼语与简历）
        before = ops.read_messages()
        existing_text = has_matching_greeting(before, ctx.greeting)
        existing_image = has_resume_image(before)
        if existing_text and existing_image:
            result.status, result.stage = 'reconciled_applied', 'audit'
            result.greeting_sent, result.image_sent = True, True
            result.timings.update(getattr(ops, 'metrics', {}))
            result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
            if ledger:
                ledger.success(ctx.job, ctx.greeting, ctx.image_path)
            return result

        # 阶段 8：发送打招呼语（send_greeting）
        result.stage = 'send_greeting'
        result.retries = 0
        after = before
        if not existing_text:
            # 等待富文本输入框挂载可用
            if hasattr(ops, 'wait_for_composer'):
                ops.wait_for_composer(timeout=10)
            # 聚焦并清空输入框，写入打招呼语
            ops.focus_input()
            ops.fill_input(ctx.greeting)
            # 优先使用点击“发送”按钮
            ops.focus_input()
            ops.click_send_button()
            
            # 轮询 6 次检查输入框是否已清空或消息数是否增加
            input_value = ''
            for _ in range(6):
                time.sleep(0.5)
                input_value = ops.read_input_value()
                after = ops.read_messages()
                if len(after) > len(before) or not input_value.strip():
                    break
                    
            # 双保险：若消息数未增加且输入框仍有文本残留，尝试回车发送
            if len(after) == len(before) and input_value.strip():
                ops.focus_input()
                ops.press_enter()
                for _ in range(6):
                    time.sleep(0.5)
                    input_value = ops.read_input_value()
                    after = ops.read_messages()
                    if len(after) > len(before) or not input_value.strip():
                        break
                        
            # 断言打招呼语确实送达且内容匹配
            assert_greeting_sent(before, after, input_value, ctx.greeting)
        result.greeting_sent = True

        # 阶段 9：上传并发送简历图片（upload_image）
        if ctx.image_path:
            result.stage = 'upload_image'
            if not existing_image:
                ops.upload_file(ctx.image_path)
                image_after = after
                # 轮询 10 次等待图片上传并出现在聊天气泡中
                for _ in range(10):
                    time.sleep(0.5)
                    image_after = ops.read_messages()
                    try:
                        assert_image_sent(after, image_after)
                        result.image_sent = True
                        break
                    except Exception:
                        if _ == 9:
                            raise
            else:
                result.image_sent = True
            
        # 阶段 10：最终审计与持久化（audit）
        result.status, result.stage = 'applied', 'audit'
        result.timings.update(getattr(ops, 'metrics', {}))
        result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
        if ledger:
            ledger.success(ctx.job, ctx.greeting, ctx.image_path)
        return result
        
    except DailyLimitReachedError:
        # 每日上限属于全局阻断性异常，记录结果后直接向上重新抛出以终止批次
        result.status, result.error = 'daily_limit', '触发每日沟通上限'
        raise
    except TargetSessionNotFoundError as exc:
        # 会话身份不匹配时安全跳过当前岗位，不进行误发
        result.status, result.stage, result.error = 'skipped_session_unverified', 'session_guard', str(exc)
        result.timings.update(getattr(ops, 'metrics', {}))
        result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
        if ledger:
            ledger.event(event='job_skipped', index=ctx.index, company=ctx.company,
                         stage=result.stage, reason=str(exc))
        return result
    except Exception as exc:
        # 其他未预期的单岗位执行异常，记录日志并标记失败
        result.error = str(exc)
        result.timings.update(getattr(ops, 'metrics', {}))
        result.timings['job_total_ms'] = round((time.perf_counter() - job_started) * 1000, 1)
        if ledger:
            ledger.event(event='job_failed', index=ctx.index, company=ctx.company, stage=result.stage,
                         error=type(exc).__name__, reason=str(exc), retries=result.retries)
        return result


def run_jobs(ops, jobs: Iterable[dict], run_dir: str, image_path: Optional[str] = None,
             only=None, dry_run=False, manage_lock=True):
    """批量执行岗位投递任务的主调度器。
    
    具备进程互斥锁管理、按序号过滤（only）、每日上限熔断终止、
    岗位间随机延时防风控等机制。
    
    Args:
        ops: BrowserOps 浏览器操作实例。
        jobs: 待投递岗位列表。
        run_dir: 本次运行产物输出目录。
        image_path: 默认的简历图片文件路径。
        only: 可选的岗位序号集合或列表（1-based），仅执行指定序号的岗位。
        dry_run: 是否为干运行模式。
        manage_lock: 是否由本函数负责管理 WorkflowLock 互斥锁。
        
    Returns:
        List[JobResult]: 所有已处理岗位的执行结果列表。
    """
    lock = WorkflowLock(run_dir) if manage_lock else None
    if lock:
        lock.acquire()
    try:
        ledger = Ledger(run_dir)
        selected = set(only or [])
        results = []
        # 筛选符合指定条件的岗位
        selected_jobs = [(index, job) for index, job in enumerate(jobs, 1)
                         if not selected or index in selected]
                         
        for offset, (index, job) in enumerate(selected_jobs):
            # 获取打招呼语（优先使用岗位自带的特定招呼语，否则使用通用招呼语）
            greeting = job.get('greeting') or job.get('招呼语') or '你好，看到岗位和我的经历比较匹配，希望有机会进一步沟通。'
            # 解析简历图片路径（支持绝对与相对路径）
            job_image = job.get('image') or job.get('png') or image_path
            if job_image and not os.path.isabs(job_image):
                job_image = os.path.abspath(job_image)
                
            ctx = JobContext(job=job, greeting=greeting, image_path=job_image, index=index)
            try:
                result = run_one(ops, ctx, ledger=ledger, dry_run=dry_run)
            except DailyLimitReachedError:
                # 捕获每日上限异常，记录熔断状态并立即中断后续岗位的投递
                results.append(JobResult(index, ctx.company, ctx.position, 'daily_limit', 'limit'))
                break
                
            results.append(result)
            
            # 岗位间随机等待 5~10 秒，模拟人类操作节奏以防反爬风控
            if offset < len(selected_jobs) - 1:
                delay = random.uniform(5, 10)
                print('  ⏳ 岗位间随机等待 %.1f 秒...' % delay, flush=True)
                time.sleep(delay)
                
        return results
    finally:
        if lock:
            lock.release()


def _load_jobs(path: str) -> list:
    """从指定 JSON 文件加载岗位数据。
    
    兼容直接为列表格式或以 {"jobs": [...]} 字典包裹的两种格式。
    
    Args:
        path: JSON 文件路径。
        
    Returns:
        list: 岗位数据字典列表。
    """
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    return data if isinstance(data, list) else data.get('jobs', [])


def _read_page_body(page, attempts: int = 5) -> str:
    """带重试机制读取页面 document.body 纯文本内容。
    
    Args:
        page: ChromiumPage 实例。
        attempts: 最大重试次数。
        
    Returns:
        str: 页面 body 文本，若重试耗尽仍失败则返回空字符串。
    """
    for _ in range(attempts):
        try:
            time.sleep(0.5)
            return page.run_js("return document.body ? document.body.innerText : ''") or ''
        except Exception:
            continue
    return ''


def main(argv=None) -> int:
    """投递工作流命令行入口主函数。
    
    解析 CLI 参数、获取互斥锁、自动探测或拉起具备 CDP 调试端口的 Chrome 浏览器、
    处理登录与健康检查，最后调度执行投递批次。
    
    Returns:
        int: 退出状态码（0 表示成功，1 表示环境/登录异常，3 表示投递存在失败项）。
    """
    parser = argparse.ArgumentParser(description='独立、无截图依赖的投递 workflow')
    parser.add_argument('run_dir', help='批次输出目录路径')
    parser.add_argument('--jobs', required=True, help='待投递岗位 JSON 文件路径')
    parser.add_argument('--image', help='简历图片附件本地绝对路径')
    parser.add_argument('--only', default='', help='仅投递指定序号的岗位（逗号分隔，如 1,3,5）')
    parser.add_argument('--dry-run', action='store_true', help='演练模式，仅探测页面而不发送')
    parser.add_argument('--headless', action='store_true', help='使用 Chrome 无头模式')
    parser.add_argument('--background', action='store_true', help='使用普通 Chrome 最小化窗口运行，保留 Cookie 会话')
    parser.add_argument('--cdp', default='http://127.0.0.1:9224', help='Chrome 远程调试 CDP 地址')
    parser.add_argument('--health-only', action='store_true', help='仅探测环境与页面健康状态并输出 JSON')
    parser.add_argument('--login-only', action='store_true', help='启动可见 Chrome 登录并等待登录完成')
    args = parser.parse_args(argv)

    # 1. 加载岗位数据与解析过滤参数
    jobs = _load_jobs(args.jobs)
    chosen = {int(x) for x in args.only.split(',') if x.strip().isdigit()} or None
    
    # 纯 dry-run 且不启动浏览器时的快速输出响应
    if args.dry_run and not args.health_only:
        print(json.dumps({'run_dir': args.run_dir, 'jobs': len(jobs), 'only': sorted(chosen or []), 'dry_run': True}, ensure_ascii=False))
        return 0

    # 2. 抢占单实例文件互斥锁，防止并发执行
    workflow_lock = WorkflowLock(args.run_dir)
    workflow_lock.acquire()
    
    launched_here = False
    page = None
    try:
        from browser_finder import find_chrome_browser
        project_assets = os.path.dirname(os.path.abspath(args.run_dir))
        user_data = os.path.join(project_assets, 'workflow_chrome_user_data')
        os.makedirs(user_data, exist_ok=True)
        cdp = args.cdp.rstrip('/')
        
        # 3. 探测 CDP 端口是否已有存活的 Chrome；若无则自动启动浏览器
        try:
            urllib.request.urlopen(cdp + '/json/version', timeout=2).close()
        except Exception:
            chrome = os.environ.get('CHROME_PATH') or find_chrome_browser()
            if not chrome or 'chrome' not in os.path.basename(chrome).lower():
                chrome = r'C:\Program Files\Google\Chrome\Application\chrome.exe'
            launch = [
                chrome,
                '--remote-debugging-port=9224',
                '--remote-debugging-address=127.0.0.1',
                '--remote-allow-origins=*',
                f'--user-data-dir={user_data}',
                '--no-first-run',
                '--no-default-browser-check',
                '--disable-gpu',
                '--disable-gpu-sandbox',
                '--disable-gpu-compositing',
                '--use-angle=swiftshader'
            ]
            if args.headless:
                launch.append('--headless=new')
            elif args.background and not args.login_only:
                launch.append('--start-minimized')
            launch.append('about:blank')
            subprocess.Popen(launch, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            launched_here = True
            
            # 等待浏览器端口就绪（最多等待 20 秒）
            deadline = time.time() + 20
            while time.time() < deadline:
                try:
                    urllib.request.urlopen(cdp + '/json/version', timeout=1).close()
                    break
                except Exception:
                    time.sleep(0.5)
            else:
                print(json.dumps({'status': 'environment_not_ready', 'error': 'DevToolsUnavailable', 'jobs_started': 0}, ensure_ascii=False))
                workflow_lock.release()
                return 1

        # 4. 连接 CDP 页面
        if __package__ in (None, ''):
            from delivery_workflow.browser_ops import DrissionBrowserOps, ensure_cdp_page
        else:
            from .browser_ops import DrissionBrowserOps, ensure_cdp_page
        page = ensure_cdp_page(cdp)

        # 5. 仅登录模式（--login-only）：轮询等待用户扫码/账号登录完成
        if args.login_only:
            print(json.dumps({'status': 'login_page_ready', 'browser': 'chrome', 'cdp': cdp,
                              'url': page.url}, ensure_ascii=False))
            stable_reads = 0
            while True:
                time.sleep(1)
                try:
                    body = page.run_js("return document.body ? document.body.innerText : ''") or ''
                    logged_out = '/web/user/' in page.url or '当前登录状态已失效' in body or ('登录/注册' in body and '消息' not in body)
                    if not logged_out and len(body.strip()) > 20:
                        stable_reads += 1
                    else:
                        stable_reads = 0
                    # 连续两次读取确认登录态稳定
                    if stable_reads >= 2:
                        print(json.dumps({'status': 'login_detected', 'url': page.url}, ensure_ascii=False), flush=True)
                        launched_here = False
                        workflow_lock.release()
                        return 0
                except Exception:
                    continue

        # 6. 健康检查模式（--health-only）：检测页面连通性与登录态
        if args.health_only:
            body = _read_page_body(page)
            login_required = '/web/user/' in page.url or '当前登录状态已失效' in body
            print(json.dumps({
                'status': 'login_required' if login_required else 'ready',
                'browser': 'chrome',
                'cdp': cdp,
                'url': page.url,
                'title': page.title,
                'page_responsive': bool(body),
                'body_preview': body[:300]
            }, ensure_ascii=False))
            if launched_here and page:
                page.quit()
            workflow_lock.release()
            return 1 if login_required else 0

        # 7. 正式投递前的登录状态校验
        body = _read_page_body(page)
        if '/web/user/' in page.url or '当前登录状态已失效' in body:
            print(json.dumps({'status': 'login_required', 'url': page.url, 'jobs_started': 0}, ensure_ascii=False))
            if launched_here and page:
                page.quit()
            workflow_lock.release()
            return 1

        # 8. 调度执行批量投递
        results = run_jobs(DrissionBrowserOps(page), jobs, args.run_dir, args.image, chosen, manage_lock=False)
        if launched_here and page:
            page.quit()
        workflow_lock.release()
        
        # 输出 JSON 格式的结果明细
        print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))
        return 0 if all(r.status in ('applied', 'skipped_already_communicated', 'skipped_offline', 'skipped_duplicate') for r in results) else 3

    except ImportError as exc:
        if launched_here and page:
            page.quit()
        workflow_lock.release()
        parser.error(f'缺少浏览器依赖: {exc}')
    except Exception:
        if launched_here and page:
            page.quit()
        workflow_lock.release()
        raise
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

