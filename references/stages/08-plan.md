# 计划征询 —— 简历怎么改，用户先点头（条件停点）

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**只有走 AI 简历优化时才走这一步。**

**只有走 AI 简历优化时才走这一步**（`gate:jobs` 里图片方式选了待 AI 调整，即默认）；图片=原简历、`--resume-mode skip`、自定义简历图都不消费它，直接进 `materials`。

把原本 `materials` 里「一口气做完的 AI 简历改写」拆成**先出计划、用户点头、再照点头的结果改写**两步。计划阶段的 `must_add`（简历缺、JD 又强烈要求的新内容）AI 严禁编造，只能由你本人补真内容——所以这一步是先问清楚，不是走过场。

一个岗位走完这一停点，会留下两类文件：`materials/plan_{i}_{公司}.json`（调整计划）和 `materials/decision_{i}.json`（你的决定）。`{i}` 是 `qualified_jobs.json` 里从 1 起的下标，和 `resume_`/`greeting_` 同一个对齐键。

**① 计划阶段**（headless，对刚批准的岗位跑，不写简历）：

```bash
python scripts/stages/gen_materials.py <run_dir> \
    --only 1,3,5 --greeting-mode skip --resume-mode plan
```

每岗位写一份 `plan_{i}_{公司}.json`，含 `chapter_plan`（章节保留/顺序）和 `optimization_suggestions`（`must_add`/`should_adjust`/`keywords_to_emphasize`/`format_suggestions`）。

**② 展示摘要**——用薄视图读，别 Read 计划原文件：

```bash
python scripts/utils/read_thin.py <run_dir> --kind plans
```

**③ 每岗位 `AskUserQuestion`（第一层摘要）**：给用户看 `index` + 公司 + 职位 + `must_add`/`should_adjust` 概览，问 **整套采纳 / 逐条细看 / 不用AI优化**（+ 其他）。

**④ 「逐条细看」才下钻（第二层）**：对 `must_add` 的每条，`AskUserQuestion` 问 **我补充真实内容（用"其他"贴内容）/ 放弃该条**；`should_adjust`、`keywords` 每条问 **按建议改 / 保留原样**。受一次 ≤4 问题、每问题 ≤4 选项的上限约束，点多就拆多轮。你补的内容必须是你真的做过、简历拿得出的——填不了就放弃，别让 AI 替你圆。

**⑤ 决定落盘**（CLI 原子写 `decision_{i}.json`，主循环绝不手改）：

```bash
python scripts/stages/set_plan_decisions.py <run_dir> --index 3 --approved
python scripts/stages/set_plan_decisions.py <run_dir> --index 3 \
    --suggestions '{"must_add":[{"section":"专业技能","content":"..."}],"should_adjust":[]}'
python scripts/stages/set_plan_decisions.py <run_dir> --index 3 --reject \
    --fallback-image "C:/my/简历.png"
```

`--approved` 整套采纳；`--suggestions` 传过滤/改写过（含你补的真内容）的；`--reject` 该岗位不用 AI 优化，可带回退图（自定义简历图或原上传简历，留给 `gate:send` 当附件）。

**⑥ 应用阶段**（headless，只对已批准岗位出简历）：

```bash
python scripts/stages/gen_materials.py <run_dir> \
    --only 1,3 --greeting-mode skip --resume-mode apply
```

被拒岗位（`decision_` 里 approved=false 或无 decision）**不生成** `resume_{i}.json`——这不是失败，是设计。它的招呼语照常生成，不受连坐。

**⑦ 顺着走**：`render --only <已批准>`（被拒岗位没有 resume json，别让它被当「部分缺图」退 3）；落盘 md 只建已投岗的 deliver 目录；到 `gate:send` 时被拒岗位的附件走 decision 里的 `fallback_image`。

`--resume-mode ai`（两阶段合并路径）保留作高级/评估用，不在常规流程里走它。