# availability —— 到岗三样，缺就问（条件停点）

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**只在要给「AI 招呼语」送往岗时才走这一步。**

**只有要给「AI 招呼语」送往岗时才走这一步**（`gate:jobs` 里选了 AI 生成招呼语，即默认）；`--greeting-mode default` 和自定义招呼语不消费它，就别问。

到岗三样（可到岗 `can_start` / 可实习时长 `duration` / 每周出勤 `days_per_week`）是 HR 会照此排期入职的**承诺**，招呼语里不许编。`materials` 阶段的 AI 招呼语提示词是**动态组装**的：`profile.basic_info.availability` 有值才把到岗段拼进去，没值整段不出现——所以如果你简历原文没写、parse 又没提出来（三项 null），招呼语就一个都写不了，得靠你问用户补一次真值。

先用 thin 视图读，别 `Read` profile.json：

```bash
python scripts/utils/read_thin.py <run_dir>/state/profile.json --kind profile
```

若 `basic_info.availability` 的**三项全为 null/空** → 一次 `AskUserQuestion`（≤4 选项规矩照旧）问可到岗时间 / 可实习时长 / 每周可出勤天数；拿到答案后用 `set_availability.py` 写回 profile（**绝不手改 profile.json**——那是显式 null、get 默认值不生效的坑）：

```bash
python scripts/stages/set_availability.py <run_dir> \
    --can-start "随时" --duration "6个月" --days-per-week "5天"
```

三项任一句都不给就是允许 `materials` 一个到岗段都没有——那是用户自己的选择，尊重它，别再追着问。非 null（简历原文写了，parse 提出来了）→ 这一停点直接跳过，不打扰。