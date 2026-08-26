# materials —— 招呼语 + 优化后简历

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**驱动 materials 前先读这里。**

```bash
python scripts/pipeline.py --from materials --only 1,3,5     # 后台任务
```

每个岗位两次模型请求（招呼语 + 简历改写），所以这是对用户刚批准的岗位列表花钱的阶段——这正是 `gate:jobs` 先行的原因。产物是 `materials/greeting_{i}_{company}.txt` 和 `materials/resume_{i}_{company}.json`，其中 `{i}` 是 `qualified_jobs.json` 里从 1 开始计数的下标。**这个下标是下游一切的对齐键**，所以一个失败的岗位会留下空隙，而不是把后面的都错位。

部分成功退出 3，不是 1。检查并只补齐缺失的——已存在的非空产物会被跳过，绝不覆盖（`--force` 才覆盖）：

```bash
python scripts/check_artifacts.py {run_dir}
python scripts/stages/gen_materials.py {run_dir} --only 4        # 只补那个失败的
```

**材料失败的岗位会从批次里剔除，而不是无限重试。** 把它从 `render` 和投递列表里排除，并在 `gate:send` 告诉用户。

> **自动落盘**：materials 跑完会自动跑 `write_application_md.py`，为本次 `--only` 选中的岗位写 `deliver/{company}-{position}/岗位信息+招呼语.md`（所有爬取字段加招呼语；绝不手写），同时落盘 `优化建议.md` 和优化简历正文 md（`<姓名>-<岗位>.md`，取自该岗位 `materials/resume_#.json` 的 `optimized_resume`）。这份自动落盘的机制说明见 [11-render.md](11-render.md)。