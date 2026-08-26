# parse —— 简历文件 → profile.json

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**驱动 parse 前先读这里。**

先问简历文件路径，然后一条命令：

```bash
python scripts/pipeline.py "简历.pdf"
```

PDF / Word / md / markdown / txt。它把 `resume_text.txt`、`profile.json` 和 `profile_validation.json` 写进一个全新的运行目录。**不要为了"检查"一次干净的 parse 而去读简历**——校验器已经做过了，而这段文本只会为毫无新信息地花掉上下文。只有当校验器退出 1、某条 hint 看起来像真实的遗漏、或用户要求彻底检查时，才去读 `resume_text.txt`。

`profile_validation.json` 就是那个校验器的输出。parse 阶段退出码 1 表示简历里出现了一个已知的技术术语却没进 profile——那是一次字典查找（`KNOWN_TECH_TERMS`），是这里唯一不依赖产生 JSON 的那个模型的信号。它在 `hints` 下打印的任何东西（未匹配的项目/公司名、稀薄的技能类别）都来自宽松的正则：读 hints，别照做，也别让某一条变成闸门。单独重跑它：

```bash
python scripts/stages/validate_profile.py {run_dir}/resume_text.txt {run_dir}/profile.json
```

需要确认某个具体字段时用 `read_thin.py --kind profile`。**你绝不手写 `profile.json`。**