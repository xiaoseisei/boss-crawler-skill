# gate:jobs —— 一个问题，三个轴

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**过 gate:jobs 前先读这里。**

先展示表格（`read_thin.py --kind ranked` 把分数 + 判定 + 公司 + 职位放一张表，或 `--kind jobs` 拿爬取列——绝不 `Read` 文件），然后**一次** `AskUserQuestion` 覆盖三个互相独立的抉择：

`--kind jobs` 打印的三列是决策信号，不是细节——把它们放进表格里，而不是让用户在死岗位上瞎选：

- `已失效=是` —— BOSS 返回了 `invalidStatus=true`；投了也白投，把它从范围里拿掉
- `代招=是`，或 `HR公司` ≠ `公司` —— 联系人是猎头/外包，不是雇主自己的 HR
- 三者都是**三态**：空值表示 未采集（爬取是没带 `-d` 跑的），绝不是 否

| 轴 | 选项 |
|---|---|
| 投递范围 | 投哪些岗位（岗位选择不影响另外两个） |
| 招呼语生成方式 | 自定义 / 默认模板 / AI生成 |
| 是否发送图片 | 自定义上传 / AI调整（渲染长图） / 不发送 |

把答案映射成 flag，而不是事后编辑文件：

| 答案 | 如何执行 |
|---|---|
| 投递范围 = 子集 | 在 `materials` **和** `render` 上用 `--only 1,3,5-7`（对 `qualified_jobs.json` 从 1 开始计数的下标）——别去改文件 |
| 招呼语 **自定义** | 把文字写进每个选中的 `i` 的 `{run_dir}/materials/greeting_{i}_custom.txt`，然后用 `--greeting-mode skip` 跑 materials…或把模式留在 `ai`：已存在的非空产物会被跳过，绝不覆盖 |
| 招呼语 **默认模板** | `--greeting-mode default`（规则模板，不调模型） |
| 招呼语 **AI生成** | `--greeting-mode ai`（默认） |
| 图片 **自定义上传** | 校验路径，`--resume-mode skip`，发送时 `apply.py --image <path>`。`skip` 也会抑制 `render`——生成的 PNG 反正不会被发送 |
| 图片 **AI调整** | 默认：`materials` 写简历 JSON，`render` 把它变成长图 |
| 图片 **不发送** | `pipeline.py --no-images`，发送时 `apply.py --no-image` |

**招呼语的前 15 个字是大多数 HR 唯一会看到的部分。** BOSS 的消息列表预览在那里截断，所以 `您好，我是…` 把整个窗口都浪费在废话上了。规则和各场景公式在 `scripts/prompts/greeting.st`——唯一来源，别转述。

`materials` 已经守住了 **AI** 路径：它跑检查，花一次额外调用把糟糕的开头重新前置，并打印 `N 条招呼语的前 15 字被客套话占掉，已重写：…`。别再去复查那些。有三种情况留着没守住——你自己查，从包里导入（不是裸 `auto_apply`）：

```bash
python -c "from resume_matcher.auto_apply import has_wasted_preview; print(has_wasted_preview(open('X.txt',encoding='utf-8').read()))"
```

- `--greeting-mode default` —— 离线模板路径从不检查
- 用户手动打的一段自定义文字 —— 从不检查
- 一段重试也失败了的 AI 招呼语 —— 原样保留，且**不会**出现在那行打印里

如果检查失败，说出来并提供重新前置，但**绝不静默改写用户提供的招呼语。**