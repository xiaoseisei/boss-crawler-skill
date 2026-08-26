# match → deep → merge —— 打分与报告

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**驱动 match（路径 A、B、C）前先读这里。**

一条命令覆盖全部三个；quick 模式下 `deep`/`merge` 是空操作：

```bash
python scripts/pipeline.py --from match          # deep 模式：后台任务，每个岗位一次请求
```

- **quick** —— 基于规则的 6 维打分（0-115 分），数秒，零 token 成本。
- **deep** —— 规则预筛到 Top-N，然后每个候选一次模型请求，再做一次合并，把规则分（40%）与模型分（60%）融合、重新分类并重新生成报告。

两者都写 `matching_report.html` 和 `qualified_jobs.json`（投递池 = 符合 + 需优化，用原始爬取字段）。**绝不手写 `qualified_jobs.json`。** 也别自己调 `generate_html_report()`——脚本已经调过了，而且 CLI 运行之后你手里也没有它需要的那个对象。

为用户打开报告：`Invoke-Item {run_dir}\matching_report.html`（PowerShell）或 `start {run_dir}/matching_report.html`（Bash）。**你消费 `application_category` 和 `match_score`，你绝不去重算它们。**

每个岗位带三个 `application_category` 值之一——枚举是英文，报告是中文，而 `read_thin.py --kind jobs` 和 `--kind ranked` 都打印原始枚举，所以跟用户说话时你自己翻译：

| 枚举 | 中文 | 含义 |
|---|---|---|
| `qualified` | 符合 | 没碰到硬闸门，技能和经验已在 |
| `need_optimization` | 需优化 | 没碰到硬闸门，差距可弥合——包括 经验差 1–3 年 / 薪资差 3–8K |
| `cannot_apply` | 不可投递 | **打中了硬闸门** |

只有三件事会落到 `cannot_apply`，而且总分永远盖不过它们（`resume_matcher/scoring.py:320-354`）：学历低于 JD 的要求、经验差距 ≥ 3 年、或薪资差距 > 8K。绝不要把中档岗位说成 不可投递。

**deep 模式每个岗位发一次请求，所以部分失败是常态。** `deep` 退出 **3** 表示结果文件已写但部分 rank 缺失——用 `--resume` 补齐，而不是重跑整个阶段：

```bash
python scripts/stages/deep_analyze.py <run_dir> --resume    # 跳过 deep_results.json 里已有的 rank
```

`deep_results.json` 靠 **`rank`** 映射回候选，而不是靠 `job_id` 或 link——那是唯一的对齐键，一旦 rank 错位，就会把某岗位的分析安到另一个岗位上而没有任何地方报错。`read_thin.py --kind ranked` 已经做这个连接了；用它而不是自己重建。