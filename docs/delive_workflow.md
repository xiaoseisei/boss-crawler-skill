# BOSS 直聘自动化投递健壮工作流架构方案 (Delivery Workflow Architecture)

> 日常操作请直接阅读 [delivery_workflow_sop.md](./delivery_workflow_sop.md)。本文件保留架构设计背景，SOP 反映当前已验证实现。

> **文档状态**：待评审 / 实施设计方案  
> **文档位置**：`E:\PIAgent\10-projects\AgentLearn\简历投递\docs\delive_workflow.md`  
> **制定时间**：2026-09-20  

---

## 一、 背景与痛点复盘

### 1.1 历史教训（Dumb Script 的缺陷）
过去的投递脚本采用典型的**线性顺序执行模式**（无反馈盲跑）：
1. 缺少环境可用性前置检查，依赖手工保证登录态和浏览器窗口正常；
2. 填入开场白后，仅尝试点击一次页面按钮，**从未校验输入框是否清空、文字气泡是否真正生成**；
3. 一旦页面出现不可预期的 DOM 遮挡（例如 BOSS 登录后自动弹出的 `.guide-download-app` 二维码浮层），点击事件被上层截断，文字卡在输入框成为未发送草稿；
4. 脚本在文字未发出的情况下，盲目执行下一行上传图片，导致 HR 仅收到单张图片而丢失开场白，且脚本在留证日志中依然错误汇报为 `success`。

### 1.2 核心改造目标
彻底淘汰盲目执行的简单脚本，建立具备**前置门禁检查、状态机硬断言校验、快速失败（Fail-Fast）与异常熔断机制**的标准化工作流（Workflow Engine）。

---

## 二、 工作流总体设计原则

```mermaid
flowchart TD
    Init([启动工作流]) --> EnvGate{阶段 0: 投递环境就绪门禁<br/>Browser / Session / Viewport / Auth}
    EnvGate -- 校验失败 --> TerminateEnv[💥 抛出 EnvironmentNotReadyError<br/>立即安全终止, 绝不盲目进入投递]
    EnvGate -- 校验通过 --> NextJob[从待投队列获取下一岗位]

    NextJob --> DetailGate{阶段 1: 详情页沟通门禁<br/>按钮状态: 立即沟通 vs 继续沟通}
    DetailGate -- 显示继续沟通/已沟通 --> BreakSession[🛑 检测到继续沟通<br/>Break 当前会话, 记录跳过, 切换下一岗位]
    DetailGate -- 岗位下线/无按钮 --> SkipOffline[记录下线, 切换下一岗位]
    DetailGate -- 显示立即沟通 --> ClickChat[点击立即沟通]

    ClickChat --> LimitCheck{检测每日沟通上限弹窗}
    LimitCheck -- 触发上限 --> DailyLimit[🚨 抛出 DailyLimitReachedError<br/>保存凭证, 终止整批任务]
    LimitCheck -- 正常 --> EnterChat[阶段 2: 进入聊天工作台]

    EnterChat --> ClearOverlay[阶段 3: 强制浮层清障<br/>移除.guide-download-app等一切遮挡]
    ClearOverlay --> ChatDeduplicate{会话防重校验<br/>会话内是否已有简历图片?}
    ChatDeduplicate -- 已有简历 --> PreventDup[防重拦截, 补录账本, 跳过]
    ChatDeduplicate -- 新会话 --> StageGreeting[阶段 4: 开场白发送与双重硬断言]

    StageGreeting --> ActionSendText[填入文字 -> 触发发送]
    ActionSendText --> AssertText{双重强断言校验:<br/>1. 输入框文本是否清空?<br/>2. 我方文本气泡数是否增加?}
    
    AssertText -- 断言失败 --> RetryText{重试 1 次 (Enter/Focus)}
    RetryText -- 依然失败 --> RaiseGreetingErr[💥 抛出 GreetingSendFailedError<br/>案发现场截图 + 强制熔断<br/>⚠️ 严禁进入图片上传环节!]
    
    AssertText -- 断言成功 --> StageImage[阶段 5: 简历长图上传与强断言]
    StageImage --> ActionUploadImg[底层文件注入上传]
    ActionUploadImg --> AssertImage{图片强断言校验:<br/>最新一条消息是否确实为图片?}
    
    AssertImage -- 断言失败 --> RaiseImgErr[💥 抛出 ImageUploadFailedError<br/>案发现场截图 + 记录不完整异常]
    AssertImage -- 断言成功 --> StageAudit[阶段 6: 终局存证与记账<br/>双重成功截图 + 写入applied_history.json]
    
    StageAudit --> CheckRemaining{是否还有后续岗位?}
    CheckRemaining -- 是 --> NextJob
    CheckRemaining -- 否 --> CompleteAll([整批投递圆满完成])
    BreakSession --> CheckRemaining
    PreventDup --> CheckRemaining
```

---

## 三、 六大阶段详细设计与契约约束

### 阶段 0：投递环境可用性前置门禁（Pre-flight Environment Gate）
在对任何岗位发起请求前，必须执行全套环境健康体检。只要有任一指标不达标，立刻抛错终止，严禁带着不健全环境运行：

| 校验项 | 校验标准 | 失败动作 |
| :--- | :--- | :--- |
| **浏览器二进制** | `find_chrome_browser()` 必须返回有效存在路径 | 抛出 `EnvironmentNotReadyError("Chrome 可执行文件缺失")` |
| **User Data 目录** | `assets/chrome_user_data` 目录必须存在且无 SingletonLock 锁死 | 抛出 `EnvironmentNotReadyError("浏览器数据目录被外部占用或损坏")` |
| **视口分辨率规范** | 强制设置浏览器视口为标准化尺寸（`1920x1080`），严禁窄屏启动 | 防止响应式布局断点导致按钮折叠或 DOM 重叠 |
| **登录 Session 有效性** | 访问 `https://www.zhipin.com/web/geek/chat`，断言是否包含用户信息元素（如 `.header-user-info`、`.user-name`） | 抛出 `EnvironmentNotReadyError("登录态已失效，请重新扫码登录")` |
| **物料完整性** | 检查当前批次绑定的所有长图文件是否全部在磁盘真实存在 | 抛出 `EnvironmentNotReadyError("简历长图附件丢失")` |

---

### 阶段 1：详情页沟通门禁与 Session 隔离（Detail Page Session Guard）
打开目标岗位链接 `job_detail/xxx.html` 后，执行严格的意图判定：
1. **定位按钮**：检索包含“沟通”字样的交互元素（`[ka="job-detail-chat"]`、`.btn-startchat` 等）。
2. **按钮文本强校验**：
   - **情况 A（继续沟通 / 已沟通）**：
     - **行为**：**立刻 break 退出当前 session**，严禁点击！
     - **处理**：补录一条 `status: 'already_communicated'` 至历史账本，保存当前页面截图，直接 `return 'skipped_already_communicated'` 进入下一家。
   - **情况 B（立即沟通）**：
     - **行为**：符合首投条件，执行点击动作。
     - **上限校验**：点击后必须在 2 秒内检索是否有今日沟通上限弹窗（`dialog-container` 含“上限”）。若命中，立即抛出 `DailyLimitReachedError`，安全中止整批任务。
   - **情况 C（岗位已下线 / 按钮不存在）**：
     - **行为**：记录 `job_offline`，保存截图存证，安全跳到下一家。

---

### 阶段 2：聊天工作台进入与常驻浮层清障（Chat Overlay Purge）
进入 `https://www.zhipin.com/web/geek/chat` 后的预备动作：
1. **单标签页保障**：关闭所有多余 Tab，保持单一激活页面。
2. **清除一切悬浮遮挡物（强制清障）**：
   - 执行脚本主动探测并销毁页面注入的所有遮挡层，重点针对 BOSS 直聘的右下角二维码浮层：
     ```javascript
     document.querySelectorAll('.guide-download-app, [class*="guide-download"], [class*="download-app"]').forEach(el => el.remove());
     ```
   - 若浮层存在且通过 JS 无法移除，且检测到物理覆盖了聊天输入/发送区域，直接抛出 `OverlayBlockedError`。
3. **激活首个聊天会话**：点击左侧用户列表中最新一条会话项，等待 2 秒确保右侧主工作台完全渲染。

---

### 阶段 3：聊天窗口历史防重安全拦截
在向输入框输入任何文字前，检查当前聊天室右侧的历史气泡：
- 扫描 `.chat-record .item-myself`：
  - 如果历史消息中已经存在图片气泡（`img` 标签），说明历史上有过长图交付记录；
  - **拦截规则**：立即终止后续输入和发送动作，补录账本并截图留证，防止对 HR 进行二次图片轰炸。

---

### 阶段 4：开场白发送与双重硬断言（Greeting Dispatch & Dual Hard Assertions）

这是杜绝“只发图片不发文字”的核心关键。**开场白发送必须通过严格的验收断言（Assertions），未通过前绝对禁止执行后续任何步骤！**

#### 步骤 1：记录基准
- 获取发送前我方文本消息数：`text_count_before = len(dp.eles('css:.chat-record .item-myself .text'))`

#### 步骤 2：填入并触发发送
- 聚焦输入框并填入完整定制开场白。
- 采用多重组合触发方式发送：
  1. 优先模拟键盘 Enter 回车事件（`inp.input('\n')` 或 CDP 模拟按键）；
  2. 若输入框仍有文本，执行备用方案：显式点击 `.btn-send:not(.disabled)` 按钮。

#### 步骤 3：双重硬断言校验（Hard Assertions）
- 等待最多 3 秒，执行以下两个断言条件：
  - **断言 A（输入框清空断言）**：`inp.text.strip() == ''`（确保草稿已经被清空发送）。
  - **断言 B（消息数量与内容断言）**：
    - `text_count_after = len(dp.eles('css:.chat-record .item-myself .text'))`
    - 断言 `text_count_after == text_count_before + 1`，且最新气泡文本命中开场白的核心特征字符。

#### 步骤 4：失败熔断处理（Fail-Fast）
- **如果重试 2 次后断言依然不满足**：
  - **绝对严禁**执行下一步的图片上传！
  - 保存当前案发现场截图命名为 `salary_{idx}_{company}_greeting_FAILED.png`；
  - **立即抛出异常 `GreetingSendFailedError(f"[{company}] 开场白发送断言失败，文字未上屏送达！")`**；
  - 该岗位标记为失败，不会被伪造为 `applied` 成功记录。

---

### 阶段 5：简历长图上传与送达断言（Resume Image Upload & Hard Assertion）

只有在【阶段 4】双重硬断言 100% 成立后，工作流才允许放行进入图片上传。

1. **底层上传**：向 `<input type="file">` 传入对应方向的高清简历长图路径。
2. **硬断言校验**：
   - 等待最多 6 秒，检索最新一条消息元素；
   - 断言最新一条消息包含有效的 `img` 标签，或状态出现“送达”回执；
   - 若断言失败，抛出 `ImageUploadFailedError` 并保存错误截图。

---

### 阶段 6：终局审计与持久化存证（Audit & Ledger）
双重断言全部通过后：
1. 截取全屏终局凭证图保存至 `assets/deliver_proof/salary_{idx}_{company}_delivered.png`；
2. 调用 `record_applied_job()` 写入全局防重账本 `assets/applied_history.json`；
3. 输出结构化成功日志，设置安全防频控停顿（7 秒），平滑过渡至下一岗位。

---

## 四、 异常体系定义（Exception Hierarchy）

定义在 `scripts/delivery_workflow/exceptions.py` 中的标准异常类：

```python
class DeliveryWorkflowError(Exception):
    """投递工作流基类异常"""
    pass

class EnvironmentNotReadyError(DeliveryWorkflowError):
    """环境不可用（浏览器缺失/Cookie失效/目录锁死/长图不存在）"""
    pass

class JobDetailInvalidError(DeliveryWorkflowError):
    """详情页结构异常或解析失败"""
    pass

class DailyLimitReachedError(DeliveryWorkflowError):
    """触发平台每日沟通上限，工作流安全熔断"""
    pass

class OverlayBlockedError(DeliveryWorkflowError):
    """页面浮层遮挡且无法清除"""
    pass

class GreetingSendFailedError(DeliveryWorkflowError):
    """开场白文字发送断言失败（文字未送达，熔断中止）"""
    pass

class ImageUploadFailedError(DeliveryWorkflowError):
    """简历长图附件上传断言失败"""
    pass
```

---


---

## 五、 代码目录与工程落地结构规划

```text
scripts/
├── delivery_workflow/
│   ├── __init__.py
│   ├── exceptions.py          # 异常类层级定义
│   ├── environment.py         # 阶段 0: 环境体检与标准化视口配置
│   ├── detail_guard.py        # 阶段 1: 详情页立即沟通 vs 继续沟通门禁
│   ├── overlay_cleaner.py     # 阶段 2: DOM 浮层扫描与强力清除
│   ├── chat_assertions.py     # 阶段 4 & 5: 消息发送、输入框清空与消息气泡硬断言
│   ├── runner.py              # 工作流总引擎 (串联各阶段与重试熔断)
│   └── repair_drafts.py       # 历史草稿补发与修复独立工具
```

---

## 七、 实施落地步骤与验收标准

1. **Step 1（代码构建）**：建立 `scripts/delivery_workflow/` 目录，编写纯净解耦的各个模块与断言逻辑。
2. **Step 2（单点测试验收）**：选择单一测试会话运行，验证当出现浮层、输入框未清空等异常时，工作流是否能**精确抛错并停止后续传图**。
3. **Step 3（执行修复）**：运行 `repair_drafts.py` 修复刚才 10 家卡在草稿框中的开场白，确认文字全部送达。
4. **Step 4（正式投递）**：后续投递（如第 11~15 家）全部由 `runner.py` 接管，以工业级标准稳定推进。
