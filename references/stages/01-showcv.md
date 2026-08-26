# 阶段 0 ＋ ShowCV 独立工具 · 简历编辑器

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**启动简历编辑器（路径 D）或调用 ShowCV 三个辅助工具前先读这里。**

## 阶段 0：启动简历编辑器（路径 D）

在本地提供内嵌的 ShowCV 构建（`app/`）并在一个隔离的 Chromium 里打开它。不需要 `pnpm install` 或 node。

**第 1 步——启动静态服务器**（后台任务）：

```bash
python scripts/showcv/serve.py
```

等待就绪信号并从它读出实际地址：

```bash
until grep -q "SHOWCV_READY" "<后台任务输出文件>"; do sleep 0.3; done
grep "SHOWCV_READY" "<后台任务输出文件>"
```

第一行永远是 `SHOWCV_READY http://127.0.0.1:<port>`，默认 3090。**如果那个后台进程立刻退出却仍打印了 `SHOWCV_READY`**：说明服务已经在运行，本次复用了它。用那个地址继续——**不要**重启它或另选端口；端口正是用户保存的简历的作用域。

**第 2 步——打开浏览器**（用第 1 步的地址，别假设是 3090）：

```bash
python scripts/showcv/launch.py http://127.0.0.1:3090
```

成功时打印 `url=` / `title=` / `profile=`，title 里有 `ShowCV`。**如果 title 里没有 `ShowCV` 脚本就退出 1**——构建不完整或服务器没起来。不要报告成功。可选参数：`--headless`、`--close`、`--browser <exe>`。

**第 3 步——向用户报告**:URL、浏览器已打开，以及**怎么停下它**——对第 1 步的后台任务执行 `TaskStop`；浏览器窗口由用户自己关。

然后停下。路径 D 到此结束。

## 阶段 0.5 / 0.6 / 0.7：ShowCV 独立工具（仅在要求时）

**刻意不接入任何路径，也不在工作流清单里。** 三个工具都假设阶段 0 已经跑过（服务器起来、浏览器打开），失败也不自己启动。从阶段 0 的 `SHOWCV_READY` 行读 URL——`--url` 故意没有默认值。

```bash
# 0.5 批量把 Markdown 导入编辑器的简历列表
python scripts/showcv/import_md.py --url http://127.0.0.1:3090 <文件或目录> [-r] [--dry-run]

# 0.6 把简历导出为图片（可重复的 --id，或 --all；一次调用覆盖一个批次）
python scripts/showcv/export_images.py --url http://127.0.0.1:3090 [--name N | --id I | --all] \
    [--mode paginated|flat] [--scale 1|2|3] [--out DIR] [--dry-run]

# 0.7 删除简历——破坏性操作，localStorage 是唯一副本
python scripts/showcv/delete_resumes.py --url http://127.0.0.1:3090 --name NAME --dry-run
python scripts/showcv/delete_resumes.py --url http://127.0.0.1:3090 --name NAME --yes
```

`export_images.py` 在本地把名字解析成 id，所以拼写错误会在导出任何东西之前就失败，而且它会确认文件真地落盘，而不是相信页面的"已下载"文字。`delete_resumes.py` 不带 `--yes` 只打印计划；带 `--yes` 先做备份（打印恢复命令），走站点自己的确认页，如果那里的名字与它解析出来的不一致就中止。与 `/export` 不同，缺失的 `id` 绝不会被当作"当前这份简历"。