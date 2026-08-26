# crawl —— → assets/post_data/**.csv（路径 A、C）＋ 路径 E 公司定向采集

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**驱动 crawl（路径 A、C）或路径 E 前先读这里。**

## crawl（路径 A、C）

先登录。这一步天然是交互式的，跑在前台：

```bash
python scripts/stages/boss_post_interactive.py --ensure-login
```

`[LOGIN_OK]` → 浏览器关闭，继续。`[LOGIN_NEEDED]` → 浏览器保持打开，用户登录后告诉你 已登录，然后重跑。登录状态保存在 `assets/chrome_user_data/`。

然后爬取——**后台任务，几十分钟**，argv 由 `crawl_params.json` 构建：

```bash
python scripts/pipeline.py --from crawl
```

之后下限检查自己跑：阈值来自 `crawl_params.json` 里的 `min_count`，`--min-jobs N` 只覆盖它。缺失 `crawl_summary.json` 意味着**什么都没爬到**——爬虫在检测到已登出会话时会以 0 退出，所以光靠退出码看不出来。当下限触发时，**停下问用户**——换关键词 / 放宽筛选 / 接受现状（继续，`--min-jobs 0`）——而不是拿着稀薄的池子硬往下走。小城市爬取可以合理地提前结束；这正是这个检查要暴露的情况，而不是要覆盖掉。

行数只是岗位数的上界，而且它数的是**整个 `assets/post_data/` 池子**，不只是本次运行：一个命中三个关键词的岗位会被写三次，加载时去重。你需要的每个筛选值见 [03-infer.md](03-infer.md) 的取值表。

## 路径 E：公司定向采集 —— 手动输入公司名 → 某公司全部在招岗 CSV

想定向抓**某几家公司的全部在招岗**（而不是关键词搜到什么算什么）时用路径 E。**这套不碰简历、不经 parse、不走九阶段流水线**——只走公司爬虫，靠 `brandName` 精确过滤出目标公司的岗位。

**① 输入公司名（纯文本停点，不用 AskUserQuestion）**：公司名是自由文本、无法列选项，照路径选择的规矩让用户用文字敲定。要问齐三样：公司名（可多个，逗号分隔）、城市（默认 `全国`，或给分公司所在城市）、条数上限（默认 30，`-n`）。

**② 登录**（登录态已持久化；`[OK]` 直接跳过，`[LOGIN_NEEDED]` 浏览器保持打开、用户登录后重跑）：

```bash
python scripts/stages/boss_post_interactive.py --ensure-login
```

**③ 后台跑公司爬取**（`-d` 连详情让 `公司信息` 列由详情接口的 `brandComInfo` 回填公司简介；`-y` 跳过确认才能非交互）：

```bash
python scripts/stages/boss_post_interactive.py -m company -p "字节跳动,腾讯" -c "全国" -n 30 -d -y
```

**④ 核查落盘**：读 `assets/post_data/company/` 下对应 `{公司}_{城市}.csv`，逐家确认存在且行数非空。缺哪家只补哪家，不要重跑全家。

**⑤ 后继**：这些 CSV 字段与关键词爬完全同构（`CSV_FIELDS`），**就是喂给「路径 B」的现成数据**。用户有简历 → 接路径 B 匹配侧（`parse` → `infer` → 跳过 crawl → `--from match` → match/deep/merge → `gate:jobs` → `materials` → `render` → `gate:send` → `apply.py --yes`），匹配/投递侧零改动；没简历 → 纯采集到这里就停。

实现用搜索接口 + `brandName` 精确过滤（无需联网校准、即时可用）；「品牌主页逐页抓满」的精确增强见 [../cli.md](../cli.md) 公司定向节。