# verify —— 模型有没有凭空造技能？

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**整轮带 `--verify`、或起点设成 `--from verify` 时先读这里。**

**默认关闭**：整轮 `--to render` 不会自动查材料。要查就显式加 `--verify`，或把起点设成它（`--from verify` 本身就带查的意图）。一条带核查的整轮：

```bash
python scripts/pipeline.py {简历.pdf} --to render --verify     # 整轮连材料核查一起跑
python scripts/pipeline.py --from verify                        # 只查这一环（自检，不拦下游）
```

它既做字符串比对，也调模型处理缩写 / 同义词 / 中英等价这些比对做不到的语义问题——所以按词烧模型，才默认关闭。它收集真正会被送出去的文本里的每个技术术语——`optimized_resume` 和招呼语——并报告那些在 `resume_text.txt` / `profile.json` 里没有依据的。一次悄悄加进 PyTorch 或 Kubernetes 的简历改写是本 skill 最糟糕的失败模式：用户带着它去面试，却答不上来。

**退出 1 表示它发现了问题，不是它坏了。** 流水线故意在 `render` 之前停下——长图一旦存在，材料读起来就是定稿。每个命中都带着周围上下文打印出来，好让人判断；然后选两条路之一：

```bash
# 确系编造 → 重新生成那些岗位
python scripts/stages/gen_materials.py {run_dir} --only 1,3 --force
# 站得住脚（它*确实*在简历里，只是措辞不同）→ 加白名单并继续
python scripts/pipeline.py --run-dir {run_dir} --from verify --to render --allow PyTorch,nginx
```

**不要自作主张打开 `--verify` 或传 `--allow`**——两者都是用户的决定：前者让这文件 1 道闸门真的去烧模型拦 render，后者以材料出门告终。把列表展示出来并询问。（`apply.py` 有一个不相关又同名充满歧义的 `--skip-verify`，用于*图片*健康检查；别把关于一个的决定搬到另一个身上。）

它抓不到的：夸大其词。「了解」被改写为「精通」、三个月实习被拉长到一年、一种不像用户的语气——任何术语匹配都发现不了这些，所以 `gate:send` 仍然意味着要读材料。还有两个值得知道的局限：它只评估拉丁字母词（像 多智能体面试系统 这样的中文短语永远不登记），而且 `optimization_suggestions` 刻意排除在外，因为给一份简历提出它缺的技能正是那个字段的全部工作。

退出码：`0` 干净 · `1` 有发现，或没有基准 / 没有可检查的材料（没检查不等于干净）· `2` 坏的 `--only` · `3` 跑完了但有些材料不可读——那些从没被检查过，所以你自己读。

它写 `verify_report.json`，记录它检查了哪些文件以及什么 mtime，这正是 `where_am_i.py` 知道该阶段跑没跑过的方式——也在一份材料被重新生成时知道某个 `✅` 已经过期。一次 `--only` 运行不写报告（子集结果会把没检查过的文件标记成已检查）。