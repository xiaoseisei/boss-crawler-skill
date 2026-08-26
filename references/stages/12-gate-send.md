# gate:send —— 批准，然后投递

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**过 gate:send 前先读这里。**

一次 `AskUserQuestion`：全部投递 / 返回修改 / 取消投递。然后，也只有在这之后：

```bash
python scripts/deliver/apply.py "{run_dir}"                # 干跑：打印列表，不碰浏览器
python scripts/deliver/apply.py "{run_dir}" --yes          # 发送
```

**`--yes` 是本 skill 里唯一不可撤销的一步**——一条已发送的消息瞬间到达、无法撤回。永远先干跑并把那份列表展示出来。`gate:send` **不可合并、不可预设**：它必须看到实际落到磁盘的材料，所以不能提前，任何保存的偏好都不能替代它。`pipeline.py` 从不运行 `apply.py`，即使带 `--to render` 也不。

有用的参数：`--only 1,3,5`、`--company 百度,棱镜数聚`、`--max N`、`--image <path>`、`--greeting <文本>`、`--greeting-file <文件>`、`--no-image`、`--name 张三`。`--image` / `--greeting` / `--greeting-file` 都是**整批统一一份**：给了就对选中的每个岗位用它，覆盖各自的长图和招呼语；不逐岗位给不同值。结果落在 `{run_dir}/apply_log.json`。三个检查拒绝发送而不是警告——缺招呼语、缺/空附件图片、运行目录不可读。

其中两个参数会咬人：

- **`--company` 是全有或全无。** 一个匹配不到任何东西的名字（拼写错误、池子里存的是简称却给了全名）会退出 1 并发送给*零个人*，包括那些确实匹配上的公司。名字对池子做子串匹配；干跑会打印一份你能传的确切菜单。
- **`--max N` 取 `qualified_jobs.json` 顺序的前 N 个，而那个顺序是 符合 在前、需优化 在后，每组内部不按分数排序**（`deep_analysis.py:377` 写的是原始列表；只有报告里的副本会被排序）。所以 `--max 5` 不是"最好的 5 个"。如果用户要最好的 N 个，传从报告读出来的显式 `--only` 下标。HR 活跃优先的排序属于库的入口点 `auto_apply.apply_to_jobs(max_applications=…)`，**不属于**这个 CLI。