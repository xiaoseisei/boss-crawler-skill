---
name: boss-crawler
description: 用 DrissionPage 爬取 BOSS 直聘职位，解析简历，用规则打分 + LLM 语义分析做岗位匹配，生成 HTML 可视化报告，自动投递匹配岗位，并启动内嵌的 Markdown 简历编辑器（ShowCV）。当用户想搜索 BOSS 直聘职位、上传简历做岗位匹配、生成岗位匹配报告、自动投递匹配岗位、针对特定 JD 优化简历，或打开简历编辑器写/改简历（"打开简历编辑器"、"启动 ShowCV"、"写一份简历"、"预览简历"）时使用。
---

# BOSS 直聘 爬取与匹配

> **⚠️ 语言强制要求（最高优先级）**：本 skill 面向中文用户。所有对用户的输出——包括提问（AskUserQuestion 的 question/header/option 文案）、说明、进度、报告、确认、错误提示——**一律使用简体中文**。术语、命令、脚本名、文件路径、代码片段可保留英文；除此之外的用户可见文本必须为中文。与用户的任何对话都不允许用英文正文。

一条流水线、九个阶段、一个驱动程序。每个阶段都是一条命令——你运行它，读最后几行，自己决定是否继续。**所有模型推断都发生在这些命令内部**，对着用户自己的 OpenAI 兼容端点调用；你从不自己填提示词模板，也不派子代理去做推断。

```
parse → infer → crawl → match → deep → merge → materials → verify → render        [ apply ]
```

`scripts/pipeline.py` 是驱动程序。所有脚本都位于相对本 skill 目录的 `scripts/` 下。**[references/cli.md](references/cli.md)** 保存完整的参数表和每个阶段的故障排查——当一条命令以本文件或某阶段参考无法解释的方式失败时打开它，而不是当作例行阅读。

**所有脚本共用同一套四个退出码。在判定某个阶段失败之前先读它们：**

| 码 | 含义 | 该怎么处理 |
|---|---|---|
| `0` | 成功 | 继续 |
| `1` | 前置条件未满足 / 输入缺失 / 全部失败——通常什么都没写 | 停下，排查，告诉用户 |
| `2` | 用法错误（argparse）。*唯一的例外是 `llm_check.py`，其中 `2` = 配置没问题但端点不可达* | 修正命令 |
| `3` | **部分成功——产物已在磁盘上，部分条目缺失** | 检查缺了什么，只补齐那部分；**不要**重跑整个阶段 |

`3` 是最容易被误读成失败的那个。`deep`、`materials` 和 `render` 都会常规性地走到它，因为它们按岗位逐个处理。

有一个阶段弯曲了 `1`：对 `verify` 来说，退出 `1` 表示检查**成功并发现了问题**。没有坏任何东西，重跑也不会改变什么——动手之前先读 [references/stages/10-verify.md](references/stages/10-verify.md)。

**一次只驱动一个阶段。** `pipeline.py --from <stage>` 只运行那一个阶段（`match` 还会连带 `deep`+`merge`，因为停在 `match` 会留下一个下游谁也读不了的半成品），然后停下并打印下一条命令。**别用一条 `--to render` 把整轮一口气跑完**：下面的几道闸门处在阶段之间，而一口气跑到底会直接冲过去，把用户的 token 花在一份他们还没看到的岗位列表上。

## 前置条件：LLM 配置

每个推断阶段都需要 API key。**pipeline 会在计划里含任何 LLM 阶段时自动跑预检**（`llm_check.py --no-call`，紧跟运行目录之后、`parse` 之前），所以不用单独敲这条命令——预检退出 1 会停掉整次运行，把三种配置方式打给你看。单独跑仍然可用，当你只想查配置、不想走整条流水线时：

```bash
python scripts/utils/llm_check.py --no-call        # 退出 0 = 可用，1 = 配置缺失/非法
```

`--no-call` 不花任何钱。退出 1 → 把三种配置方式展示给用户（脚本会打印它们）然后停下；不要启动一场会在 `match` 处死掉的爬取。加 `--stage deep` 看单个阶段被解析成什么，或去掉 `--no-call` 顺便发一个最小请求——**那一条路径会多出第三个码，`2` = 配置完整但端点不可达**（这个脚本是仓库范围内 `2 = 用法错误` 的唯一例外；是网络或 base-URL 的问题，不是配置问题）。**绝不打印、记录或回显 `api_key`**——脚本会把它打码，所以只传路径和阶段名，别传 key。

## 路径选择

**每次调用开始都必须让用户定一条路径**——但这一停点**不用 `AskUserQuestion`**。你直接以普通文本输出「推荐用法」：默认推荐路径 A，附上下面那张 A/B/C/D/E 简表让用户对表选，然后**停下等用户用文字回复**——敲 `A`/`B`/`C`/`D`/`E`、@ 一个简历文件、或贴一句需求都行。不要从保存过的预设或磁盘上恰好存在的东西自动选路径；预设是在路径确定*之后*才提供参数。

**路径一旦被用户文字确定，就按字面执行，绝不绕回去。** 比如用户只敲了 `A` 或 @ 了一份简历，接下来唯一该做的是停下、按该路径的下一问继续——需要简历路径时，停下来等用户给路径，**不要**自己跑 `ls`/`find` 去磁盘搜简历文件、再列几个候选让用户重选一遍，那等于把用户刚做的选择又抹掉了。磁盘搜索只发生在用户明确要求之后。定完就别再自作主张地"提前帮忙"。

| 选项 | 何时用 | 流程 |
|------|------|------|
| **A: 简历驱动** ✨ | 有简历，想要精确 | parse → infer → crawl → match… → apply |
| **B: 已有岗位数据** | 有简历，且 `assets/post_data/` 里已有 CSV（含 `company/` 子目录的公司定向采集结果） | parse → infer → *(跳过 crawl)* → match… → apply |
| **C: 预设重放** | 用保存的预设重跑，不用重新声明 | preset → parse → infer *(预设值)* → crawl → match… |
| **D: 仅编辑简历** | 还没有简历文件，想写或改一份 | 启动简历编辑器 → **到此为止** |
| **E: 公司定向采集** | 想定向抓某几家公司的**全部在招岗**，只要公司名、无需简历 | 输入公司名 → 公司定向爬取 → `company/` CSV → **到此为止**（有简历可再接路径 B 匹配） |

**每条路径都从 `parse` 开始。** `infer` 读 `profile.json`，`crawl` 读 `infer` 写出的 `crawl_params.json`——所以"先爬后解析"不是受支持的顺序。路径 B 与 A 只差一件事：跳过 `crawl` 阶段（`infer` 之后直接 `--from match`）。**路径 E 是唯一例外**：它不从 `parse` 起，也不经过九个阶段任何一环——直接跑公司爬虫产 CSV，纯采集用（四大码 / 流水线 / run 目录那一套对它都不适用）。

**AskUserQuestion 选项上限（本 skill 每个用该工具的提问都一样；路径选择那一停点不用该工具，不在此列）：** 每个问题最多 4 个选项。当某个选择有更多候选——薪资档、关键词选择——取最相关的 4 个，把推荐默认值放第一个，让自动加的「其他」兜住其余。绝不发出第 5 个选项；工具会拒绝该调用。与其让调用失败，不如把一个过长的提问拆成后续问题。

**每个阶段一轮 `AskUserQuestion`，而不是每个字段一轮。** 该工具接受一个问题列表；把一个阶段需要的所有决定都打包进那一次调用（最多 4 个问题）。本 skill 恰好有三个用 `AskUserQuestion` 的停点——`infer` 确认、`gate:jobs`、`gate:send`——每个都**恰好一次**调用（路径选择那一步是纯文本推荐的停点，不在其列）。绝不要单独问一个字段：那正是 9 轮爬取参数会话的由来，而每一轮大约耗掉用户 1.5 分钟的注意力。

**推荐路径 A**：简历会告诉你搜什么——技能、城市、薪资区间——所以爬到的岗位跟候选人的背景对齐，而不是跟瞎猜的关键词对齐。

**路径 D 以启动告终。** 它打开编辑器、报告 URL，仅此而已。它通常作为前奏：用户写一份简历，然后从 A/B/C 重新进入。编辑器里存的 Markdown 可以直接喂给 `parse`——但只在用户要求时。

**路径 E 是唯一不碰简历的采集路径**——整套只有公司爬虫，产出落在 `assets/post_data/company/`，正是路径 B 认的现成数据。它通常作为前奏：先定向抓几家目标公司的在招岗，回头再凭简历走路径 B 做匹配/投递。用户已有简历时，采集完可接路径 B 的匹配侧；没有简历就止步于 CSV。

**路径 C 是预设路径。** `preferences.py show` 打印已存的参数，`preferences.py missing` 点名预设缺了哪些可问字段（薪资/规模/最低岗位数 以及同类）。只问**恰好**那些，用 `preferences.py save` 合并回去，再把整组作为 flag 传给 `infer`。如果 `show` 退出 1，说明没有预设——退回路径 A 的全新确认，而不是报错。

`save` 是**合并**——只传你刚问过的字段；其余都保留。只有在要整体重写预设时才传 `--replace`（这正是 `infer --save` 在打印完整组待确认之后做的事）。合并模式下，你无法通过省略某个字段来清除它：用 `--replace` 重写，或用 `clear` 全部清空。

> **两道闸门，都必须过。** `gate:jobs`（投哪些岗位，以及材料怎么做）和 `gate:send`（批准真正落到磁盘的东西）。缺了任何一道都不投递。
>
> **预设永远到不了这两道闸门。** `assets/preferences.json` 只覆盖爬取和匹配参数——它没有"投哪些岗位、用什么招呼语、是否发送"这些字段，`load()` 会丢弃白名单之外的任何键。

## 运行目录

`parse` 在 `assets/` 下创建带时间戳的运行目录（例如 `assets/2026-08-16_14-30-00/`）并把 `assets/LATEST.txt` 指向它。之后每个阶段都会自动找到它；要显式指定就传 `--run-dir`。路径 D 不产生运行产物，也不需要运行目录；路径 E 直接写 `assets/post_data/company/`，同样不建运行目录、不碰 `LATEST.txt`。

---

## 工作流

复制这份清单，完成一项就在前头打勾：

```
进度：
- [ ] 前置：LLM 配置预检（pipeline 会自动跑 llm_check.py --no-call，退出 1 会停掉整次运行）
- [ ] 路径选择：直接输出推荐用法（默认 A）+ A/B/C/D/E 简表，停下等用户文字输入
- [ ] 阶段 0：启动简历编辑器（路径 D——终止步骤）→ 读 [01-showcv.md](references/stages/01-showcv.md)
- [ ] parse:     简历文件 → profile.json → 读 [02-parse.md](references/stages/02-parse.md)
- [ ] infer:     确认参数（2 次打包提问 + min_count）→ crawl_params.json → 读 [03-infer.md](references/stages/03-infer.md)
- [ ] crawl:     后台运行，然后检查下限（路径 A、C）→ 读 [04-crawl.md](references/stages/04-crawl.md)
- [ ] match:     → deep → merge → matching_report.html + qualified_jobs.json → 读 [05-match.md](references/stages/05-match.md)
- [ ] gate:jobs  一次 AskUserQuestion：投哪些 + 招呼语方式 + 图片方式 → 读 [06-gate-jobs.md](references/stages/06-gate-jobs.md)
- [ ] availability  到岗三样，缺就问（条件停点）→ 读 [07-availability.md](references/stages/07-availability.md)
- [ ] 计划征询:   简历怎么改，用户先点头（条件停点；写 plan_+decision_ JSON）→ 读 [08-plan.md](references/stages/08-plan.md)
- [ ] materials: 招呼语 + 优化后简历（后自动落盘 岗位信息+招呼语.md）→ 读 [09-materials.md](references/stages/09-materials.md)
- [ ] verify:    没有凭空造技能（退出 1 = 发现了——停下给用户看）→ 读 [10-verify.md](references/stages/10-verify.md)
- [ ] render:    简历长图（用 --no-images 跳过；后自动 verify_image 图检）→ 读 [11-render.md](references/stages/11-render.md)
- [ ] gate:send  一次 AskUserQuestion → apply.py --yes → 读 [12-gate-send.md](references/stages/12-gate-send.md)
```

**路径 E（公司定向纯采集）清单** —— 只走公司爬虫，不碰 parse / 简历 / 流水线；全程读 [04-crawl.md](references/stages/04-crawl.md) 的路径 E 一节：

```
- [ ] 输入公司名 + 城市 + 条数（纯文本停点，不用 AskUserQuestion）
- [ ] 登录（--ensure-login，无登录态时；登录态持久化，已有则跳过）
- [ ] 后台跑 boss_post_interactive.py -m company -p 公司名 -c 城市 -n N -d -y
- [ ] 核查 assets/post_data/company/ 下各家 CSV 是否落盘、行数非空
- [ ] 用户有简历 → 接路径 B 匹配侧；无 → 到此为止
```

**停点。** 路径选择（纯文本：输出推荐用法后停下等用户输入）、路径 E 的公司名输入（纯文本：问公司名+城市+条数后停下）、`infer` 确认（两次打包的 `AskUserQuestion` 调用加一次小小的 `min_count` 后续——当路径 C 复用完整预设时跳过）、`gate:jobs`、`gate:send`。外加三个条件停点：爬取下限（只在池子来得太稀薄时）、`availability`（只在该 run 要 AI 招呼语且到岗三样为 null 时）、`计划征询`（只在 `gate:jobs` 选了图片=待 AI 调整、走 AI 简历优化时）。

**迷失了位置（例如在上下文压缩之后）？不要重读文档来重建状态。** 问文件系统：

```bash
python scripts/utils/where_am_i.py           # 或传一个显式的 <run_dir>
```

它会根据磁盘上的产物推断出当前阶段，并用约 1k 字符打印下一条命令。只在它指向的那*一个*阶段参考文件去查详情。

## 让一次运行保持廉价的三个习惯

1. **绝不 `Read` 一张渲染好的简历图片。** 用 `scripts/verify/verify_image.py`。一张 0.5 MB 的 PNG 花掉 638,960 个输入 token——单次工具调用就占了那个会话 79% 的新鲜输入。
2. **绝不 `Read` 完整数据文件——用 `read_thin.py`**，它是唯一能回答"我该挑几号岗位"的视图（`--kind ranked` 的 `index` 就是 `--only`、`materials_*_N` 和 `apply --max` 用的同一个从 1 开始计数的编号）：

   ```bash
   python scripts/utils/read_thin.py {run_dir}/qualified_jobs.json --kind jobs     # → 表格字段
   python scripts/utils/read_thin.py {run_dir}/profile.json --kind profile         # → 汇总统计
   python scripts/utils/read_thin.py {run_dir}/deep_results.json --kind deep       # → 只看判定
   python scripts/utils/read_thin.py {run_dir} --kind ranked                       # → 序号+公司+职位+分数+判定
   ```

3. **在后台跑长阶段并用 grep 过滤输出。** `crawl` 要几十分钟，`deep`/`materials` 每个岗位打印一行——把全部输出灌进你的上下文正是触发压缩的原因。用 `run_in_background` 启动它们，然后只读关键部分：

   ```bash
   grep -E "✅|❌|⚠|阶段|失败|写入" <后台任务输出文件> | tail -20
   ```

耗时自动落在 `{run_dir}/intermediate/run_timings.jsonl`——每个阶段都会自我埋点，所以不用手工标记。`python scripts/stage_timer.py report <run_dir>` 给它们排序。

## 阶段参考 —— 驱动某一阶段前，必须先读它

**阶段细节已拆到 `references/stages/` 下，按需加载，不常驻。** 规则：**在你准备驱动某个阶段、执行它的命令之前，必须先 Read 它对应的参考文件**，再动手。绝不凭记忆或凭下面这句摘要就执行——摘要只够你判断「该不该停」，不够你安全运行。下方每个阶段旁的链接就是你要读的那份。

| 阶段 | 一句话摘要 | 参考文件 |
|---|---|---|
| 阶段 0 ＋辅助 | 启动 ShowCV 简历编辑器（路径 D）；0.5/0.6/0.7 导入/导出/删除 | [01-showcv.md](references/stages/01-showcv.md) |
| parse | 简历文件 → profile.json（不手写、不 Read 干净文本） | [02-parse.md](references/stages/02-parse.md) |
| infer | 确认爬取/匹配参数 → crawl_params.json（两次打包提问） | [03-infer.md](references/stages/03-infer.md) |
| crawl | 登录 + 后台爬取 + 下限检查（路径 A、C） | [04-crawl.md](references/stages/04-crawl.md) |
| 路径 E | 公司定向采集 → company/ CSV（不碰流水线） | 见 [04-crawl.md](references/stages/04-crawl.md) 路径 E 节 |
| match | → deep → merge → 报告 + qualified_jobs.json | [05-match.md](references/stages/05-match.md) |
| gate:jobs | 一个问题，三个轴：投哪些 / 招呼语 / 图片 | [06-gate-jobs.md](references/stages/06-gate-jobs.md) |
| availability | 到岗三样（条件停点，仅 AI 招呼语送往岗时） | [07-availability.md](references/stages/07-availability.md) |
| 计划征询 | 简历怎么改，用户先点头（条件停点） | [08-plan.md](references/stages/08-plan.md) |
| materials | 招呼语 + 优化后简历 | [09-materials.md](references/stages/09-materials.md) |
| verify | 模型有没有凭空造技能？(退出 1 = 发现了) | [10-verify.md](references/stages/10-verify.md) |
| render | 简历长图（串行，无 --workers） | [11-render.md](references/stages/11-render.md) |
| gate:send | 批准，然后 `apply.py`（唯一不可撤销一步） | [12-gate-send.md](references/stages/12-gate-send.md) |

> **只读你即将驱动的那个阶段参考**，别把它们一次全读完——读满 12 份就把拆分省下的上下文又填回去了。`where_am_i.py` 会告诉你当前该读哪一份。

## references/ —— 需要时才翻的文档

| 文件 | 读者 / 触发时机 |
|---|---|
| [cli.md](references/cli.md) | **故障排查。** 一条命令以本文件或某阶段参考无法解释的方式失败，或你需要一个上面没列出的 flag |
| [stage 参考](references/stages/01-showcv.md) | **阶段细节。** 驱动对应阶段前读（见上表）；不过只要你正在跑它就应该已经读过了 |

## 关键原则

1. **规则优先，然后才是 LLM**：Python 规则打分预筛；模型只对顶部候选做深度分析
2. **绝不编造**：简历优化不得发明经历或技能。三个 `basic_info.availability` 字段——到岗日期 / 可实习时长 / 每周出勤——更严格：它们是 HR 会据以行动的排期*承诺*，所以只能从简历复制。如果它们是 `null`，招呼语就什么也不说时间安排，并去问用户；绝不要从入学或毕业年份推导日期（`prompts/resume_parse.st:92`、`prompts/greeting.st:46`）
3. **安全投递**：每次投递间隔 3-5 秒，每次会话最多 10-20 个，验证码时暂停
4. **始终可视化**：每次运行都生成并打开 HTML 报告
5. **磁盘上的产物才是真相**：用文件和退出码判断一个阶段，而不是凭通知
6. **PDF 只用 `parse_pdf`（PyPDF2）解析，绝不另试别法**：任何上游给的 PDF —— 简历，或用户上传的含公司名称等数据的 PDF —— 一律走 `scripts/resume_matcher/parsers.py::parse_pdf` 的 PyPDF2 文本抽取。**不经 OCR**，不猜其它库，不为其发明新解析路径；扫描版/加密 PDF 抽不出文本是预期行为，按 `parse` 阶段的提示请用户另存为 `.md`/`.txt` 再跑。