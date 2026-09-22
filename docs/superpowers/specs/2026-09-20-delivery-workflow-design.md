# 独立投递工作流与原子浏览器操作设计

## 目标

新增一套独立运行的投递 workflow，用于替代当前投递脚本中的盲目线性执行问题。第一阶段只新增独立入口，不修改或接管 `scripts/deliver/apply.py`；经过真实单岗位和小批量验证后，再考虑让 `apply.py` 委托给该 workflow。

workflow 不依赖截图进行判断，也不把截图作为必要产物。程序通过浏览器 DOM 状态、消息内容和结构化日志判断成功、跳过和失败；浏览器页面由用户实时观察。

## 架构边界

系统分为三层：

1. 原子浏览器操作层：每个函数只执行一个浏览器动作或一次状态读取，不做业务决策，不串联后续动作。
2. 观察与断言层：读取页面事实并判断是否满足阶段契约，不触发浏览器动作。
3. workflow runner：按状态机编排岗位流程，负责重试、跳过、熔断和账本写入。

原子操作层禁止出现跨阶段函数，例如 `send_greeting_and_upload_image`。文字发送和图片上传必须是两个独立阶段。

## 目录规划

```text
scripts/delivery_workflow/
├── __init__.py
├── exceptions.py
├── models.py
├── browser_ops.py
├── observers.py
├── assertions.py
├── ledger.py
└── runner.py
```

- `exceptions.py`：工作流异常层级。
- `models.py`：岗位上下文、消息快照、阶段结果和投递结果。
- `browser_ops.py`：从现有投递代码提取的原子浏览器动作。
- `observers.py`：按钮、输入框、消息列表、弹窗和图片状态读取。
- `assertions.py`：纯判断函数，不执行浏览器动作。
- `ledger.py`：结构化运行日志和 `applied_history.json` 写入。
- `runner.py`：独立 CLI 和状态机入口。

## 原子浏览器操作

操作函数统一使用清晰的动词命名，每次只完成一个动作：

```text
open_job_detail(url)
read_job_chat_button()
click_start_chat()
read_daily_limit_dialog()
open_chat_workspace()
remove_overlay()
select_chat_session()
read_chat_messages()
read_input_value()
focus_input()
fill_input(text)
press_enter()
click_send_button()
upload_file(path)
read_latest_message()
```

动作函数不负责判断动作是否达到业务目标；例如 `press_enter()` 不判断文字是否发送成功。动作执行失败时抛出底层浏览器异常，由 runner 转换为工作流阶段失败。

## 状态机

```text
PRECHECK
  -> OPEN_DETAIL
  -> READ_CHAT_BUTTON
     -> SKIPPED_ALREADY_COMMUNICATED
     -> SKIPPED_OFFLINE
     -> CLICK_START_CHAT
  -> CHECK_DAILY_LIMIT
  -> OPEN_CHAT_WORKSPACE
  -> REMOVE_OVERLAY
  -> SELECT_SESSION
  -> CHECK_DUPLICATE
     -> SKIPPED_DUPLICATE
     -> SEND_GREETING
  -> ASSERT_GREETING
     -> retry once
     -> FAILED_GREETING
     -> UPLOAD_IMAGE
  -> ASSERT_IMAGE
     -> FAILED_IMAGE
     -> WRITE_LEDGER
```

硬约束：

- `ASSERT_GREETING` 成功前禁止调用 `upload_file`。
- 文字断言检查输入框为空、我方文字消息数量增加、最新文字内容匹配。
- 图片断言检查最新消息包含有效图片元素或等价的已发送图片状态。
- 每日沟通上限是批次级熔断，立即停止剩余岗位。
- 已沟通、岗位下线和重复图片属于正常跳过，不写成功记录。
- 只有文字和图片断言都成功后才写入成功投递账本。

## 异常与记录

异常至少包括：

```text
DeliveryWorkflowError
EnvironmentNotReadyError
JobDetailInvalidError
DailyLimitReachedError
OverlayBlockedError
GreetingSendFailedError
ImageUploadFailedError
```

不保存截图。每个岗位记录结构化事件，包含岗位标识、公司、阶段、状态、错误类型、错误原因、重试次数和时间。成功账本记录 `greeting_sent`、`image_sent` 和最终状态。

## 独立入口

第一版入口为：

```text
python scripts/delivery_workflow/runner.py <run_dir> [--only 1,2,3]
```

入口默认支持演练和单岗位/小批量运行，必须显式选择真实发送模式。它复用现有浏览器初始化和页面操作能力，但不调用 `apply.py` 的批次控制流程。

## 测试与验收

1. 原子操作 mock 测试：确认函数只执行单一动作。
2. 观察器测试：覆盖立即沟通、继续沟通、无按钮、弹窗和消息列表状态。
3. 断言测试：覆盖输入框未清空、消息未增加、图片未出现。
4. runner 测试：确认文字失败时不会调用图片上传，图片失败时不会写成功账本。
5. 单岗位真实浏览器验收：用户可直接观察页面，程序只依赖 DOM 断言和日志。

第一阶段完成标准是：独立入口能够安全处理单岗位和小批次，失败时快速停止当前岗位或整批，且无截图依赖；`apply.py` 行为保持不变。
