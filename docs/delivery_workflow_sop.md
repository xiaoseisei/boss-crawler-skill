# BOSS 自动化投递 Workflow SOP

> 状态：第一版已验证，可用于日常后台批量投递  
> 入口：`scripts/delivery_workflow/runner.py`  
> 成功账本：`assets/applied_history.json`  
> 运行日志：`<run_dir>/delivery_workflow.jsonl`

## 1. 工作流做什么

```text
读取候选岗位
→ 查询成功账本
→ 打开岗位详情
→ 点击“立即沟通”或“继续沟通”
→ 接管 BOSS 自动打开的目标会话
→ 校验公司身份
→ 核对已有文字和图片
→ 只发送缺失的材料
→ 确认文字气泡送达
→ 确认简历图片送达
→ 写入成功账本
→ 随机等待 5–10 秒
→ 下一个岗位
```

workflow 使用普通 Chrome 最小化运行，登录状态保存在：

```text
assets/workflow_chrome_user_data
```

不需要截图。所有判断依赖详情页状态、聊天身份、消息气泡和成功账本。

## 2. 环境约定

- 项目目录：`E:\PIAgent\10-projects\AgentLearn\简历投递`
- Python：`.venv\Scripts\python.exe`
- Chrome DevTools：`http://127.0.0.1:9224`
- 每次只允许一个 workflow 实例运行。
- 候选 JSON 中每个岗位必须包含链接、公司、职位、招呼语和 PNG 简历路径。

进入项目目录：

```powershell
Set-Location 'E:\PIAgent\10-projects\AgentLearn\简历投递'
```

## 3. 首次登录或登录失效

启动可见 Chrome 并等待登录：

```powershell
.venv\Scripts\python.exe scripts/delivery_workflow/runner.py `
  assets/2026-09-20_small_lowest_salary_batch `
  --jobs assets/today_unapplied_candidates.json `
  --login-only `
  --cdp http://127.0.0.1:9224
```

在打开的 Chrome 中完成 BOSS 登录。登录信息会保存到 `assets/workflow_chrome_user_data`，后续不需要保持 Chrome 常驻。

验证登录状态：

```powershell
.venv\Scripts\python.exe scripts/delivery_workflow/runner.py `
  assets/2026-09-20_small_lowest_salary_batch `
  --jobs assets/today_unapplied_candidates.json `
  --health-only `
  --background `
  --cdp http://127.0.0.1:9224
```

通过标准：

```json
{"status":"ready","url":"https://www.zhipin.com/web/geek/chat","page_responsive":true}
```

页面文本不能包含“当前登录状态已失效”。

## 4. 准备候选岗位

从现有材料目录重新生成未成功投递候选池：

```powershell
.venv\Scripts\python.exe scripts/parse_unapplied_candidates.py
```

产物：

```text
assets/today_unapplied_candidates.json
```

去重规则：

- 有岗位链接时，以链接为唯一键；
- 没有链接时，才使用“公司 + 职位”；
- 已存在于 `applied_history.json` 的岗位不会再次投递；
- 同一公司不同岗位可以分别投递。

候选最小结构：

```json
{
  "company": "公司名",
  "title": "岗位名",
  "url": "https://www.zhipin.com/job_detail/...html",
  "greeting": "针对 JD 生成的招呼语",
  "png": "assets/.../姓名-岗位.png"
}
```

## 5. 投递前预演

预演只检查候选数量和序号，不启动浏览器、不发送：

```powershell
.venv\Scripts\python.exe scripts/delivery_workflow/runner.py `
  assets/2026-09-20_small_lowest_salary_batch `
  --jobs assets/today_unapplied_candidates.json `
  --only 1,2,3,4,5 `
  --dry-run
```

投递前确认：

- 序号正确；
- URL 存在；
- `greeting` 非空；
- PNG 文件存在；
- 没有另一个 workflow 正在运行。

## 6. 正式后台投递

投递指定岗位：

```powershell
.venv\Scripts\python.exe scripts/delivery_workflow/runner.py `
  assets/2026-09-20_small_lowest_salary_batch `
  --jobs assets/today_unapplied_candidates.json `
  --only 1,2,3,4,5 `
  --background `
  --cdp http://127.0.0.1:9224
```

投递流程中：

- Chrome 使用普通浏览器模式并最小化运行；
- 点击详情页的“立即沟通”或“继续沟通”；
- 优先使用 BOSS 自动激活的目标会话；
- 自动会话不匹配时才搜索联系人；
- 当前会话公司身份验证通过后才允许输入；
- 优先点击 `.btn-send` 发送文字，真实 Enter 仅作备用；
- 文字送达后才允许上传图片；
- 图片最多轮询 5 秒确认；
- 岗位之间随机等待 5–10 秒；
- 最后一个岗位不等待。

## 7. 已沟通岗位的处理

详情页显示“继续沟通/已沟通”不等于完整投递。workflow 会点击按钮进入目标聊天并核对：

| 聊天状态 | 动作 |
|---|---|
| 已有招呼语和图片 | 补录成功账本，不重复发送 |
| 只有招呼语 | 只补发图片 |
| 只有图片 | 只补发招呼语 |
| 两者都没有 | 完整发送文字和图片 |

重复运行同一序号可用于补偿。成功账本门禁和聊天内容检查会阻止重复投递。

## 8. 结果状态

| 状态 | 含义 | 是否继续下一个岗位 |
|---|---|---|
| `applied` | 文字、图片和账本全部成功 | 是 |
| `reconciled_applied` | 聊天中已完整送达，本次补录账本 | 是 |
| `skipped_history` | 成功账本已有记录 | 是 |
| `skipped_offline` | 岗位下线或无可用沟通入口 | 是 |
| `skipped_session_unverified` | 两条路径都无法证明目标会话 | 是 |
| `failed` | 当前岗位文字、图片或页面动作失败 | 是 |
| `daily_limit` | 触发每日沟通上限 | 否，终止整批 |

## 9. 批次级终止条件

只有下列问题会停止整批：

- 已有 workflow 持有 `.delivery_workflow.lock`；
- Chrome 无法启动；
- DevTools/CDP 无法连接；
- BOSS 登录态失效；
- 浏览器或页面连接彻底断开；
- 达到每日沟通上限；
- 成功账本无法安全读取或写入。

岗位下线、目标会话无法证明、单岗发送失败都只结束当前岗位。

## 10. 失败补偿

文字成功但图片未及时确认时，直接重跑原岗位序号：

```powershell
.venv\Scripts\python.exe scripts/delivery_workflow/runner.py `
  assets/2026-09-20_small_lowest_salary_batch `
  --jobs assets/today_unapplied_candidates.json `
  --only 5 `
  --background `
  --cdp http://127.0.0.1:9224
```

workflow 会先检查聊天：

- 图片已延迟出现：补录成功账本；
- 只有文字：只上传图片；
- 不会重复发送已存在的招呼语。

目标会话无法证明时，不要手工强制绕过身份校验。该岗位会返回 `skipped_session_unverified`，批次继续。

## 11. 账本与日志核对

查看成功总数：

```powershell
$h = Get-Content 'assets/applied_history.json' -Raw | ConvertFrom-Json
$h.total_applied
$h.updated_at
$h.applied_jobs | Select-Object -Last 10 company,position,status,applied_at
```

查看 workflow 事件：

```powershell
Get-Content 'assets/2026-09-20_small_lowest_salary_batch/delivery_workflow.jsonl' -Tail 30
```

锁文件正常情况下在任务结束后不存在：

```powershell
Test-Path 'assets/2026-09-20_small_lowest_salary_batch/.delivery_workflow.lock'
```

预期返回 `False`。

## 12. 常见故障

### 登录失效

表现：进入 `/web/user/`，或页面显示“当前登录状态已失效”。

处理：执行第 3 节的 `--login-only`，重新登录后再运行 `--health-only`。

### 输入框未就绪

workflow 只使用可见的输入控件，优先级为：

```text
#chat-input
[contenteditable="true"]
.chat-input
textarea.input（仅可见时）
```

隐藏 textarea 不会被当作当前输入框。目标会话身份验证成功后，发送阶段会单独等待输入框最多 5 秒。

### 当前会话与目标公司不匹配

workflow 会先点击详情页沟通按钮，等待 BOSS 自动激活目标会话；失败后才搜索联系人。两条路径都无法证明时跳过当前岗位，不阻塞后续批次。

### 图片实际送达但初次判定失败

重跑原岗位序号。workflow 会识别 `.item-image`、`.message-image-content` 和图片元素，核对后补录账本或只补发图片。

### 每日沟通上限

整批停止。次日重新生成未投递候选池后继续运行。

## 13. 验收基线

第一版已完成以下真实验证：

- 连续 5 个岗位全部完成文字、图片和账本；
- 单岗位完整投递约 9–12 秒；
- 聊天页复用，不重复加载；
- 目标会话身份错误时不会发送；
- 图片延迟可通过补偿重跑完成；
- 岗位间随机等待 5–10 秒；
- 专项测试 `4 passed`；
- 测试数据不会写入生产账本。

