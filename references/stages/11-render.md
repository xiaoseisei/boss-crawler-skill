# render —— 简历长图 + 自动落盘 + 图检

> 本文是 [SKILL.md](../../SKILL.md) 的阶段参考。**驱动 render 前先读这里。**

```bash
python scripts/pipeline.py --from render --only 1,3,5
```

**设计上就是串行——没有 `--workers`。** 所有简历共用一个浏览器、一个 origin 和一个 `localStorage`；并发只会让它们互相踩踏。脚本在调试端口 9333 被一个 `--user-data-dir` 不是 `assets/showcv_profile` 的浏览器占住时拒绝运行——那个端口可能是持有用户真实简历的*被接管的*浏览器。绝不要替用户传 `--adopt-browser`。

当用户选了 不发送 时，用 `--no-images` 整个跳过该阶段。

**附件文件名是 `<姓名>-<应聘岗位>`，所以这个阶段需要一个真名。** 当 `profile.json` 的 `basic_info.name` 为空或占位符（`未提取` / `未知` / `无` / …）时，脚本退出 1，而不是渲染一张 `未提取-Python工程师.png`——HR 会看到那个字符串。传 `--name "真实姓名"`（`apply.py` 上有同一个 flag）。这里的退出码：`0` 每张图都渲染了，`1` 前置条件失败且什么都没跑，`3` 阶段跑完但部分岗位没有图——在 `gate:send` 之前检查是哪些。

## 岗位信息+招呼语.md 自动落盘，然后看一眼

`岗位信息+招呼语.md` **不需要你动手** —— `materials` 阶段跑完会自动跑 `write_application_md.py`，为本次 `--only` 选中的岗位写 `deliver/{company}-{position}/岗位信息+招呼语.md`（所有爬取字段加招呼语；绝不手写），同时落盘 `优化建议.md` 和优化简历正文 md（`<姓名>-<岗位>.md`，取自该岗位 `materials/resume_#.json` 的 `optimized_resume`，与 render 出的长图同名同目录）。**只给要投的岗位建 deliver 文件夹**：`--only` 给了就只建那几家；没给才退回 `--all` 写全部 qualified 岗位。它挂在 materials 而非 render 上，所以 `--resume-mode skip` / `--no-images` 跳过渲染时也照写。简历正文想看薄格式就用 `read_thin.py` 读 `materials/resume_#.json`。

长图检查也不用你动手 —— `render` 阶段跑完会自动跑 `verify_image.py "{run_dir}/deliver" --all`，把十几行数字打到屏幕上给你读。单独跑仍然可用（不用走整条流水线时）：

```bash
python scripts/verify/verify_image.py "{run_dir}/deliver" --all
```

`verify_image.py` 是你检查图片的方式：它返回十几行数字，而不是一张 639k token 的截图。如果用户想看某一张，把路径给他们，让他们自己打开。