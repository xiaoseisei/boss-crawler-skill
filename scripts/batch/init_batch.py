#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化后续批次的投递运行目录。

从 post_data 原始岗位池中读取全部数据，做权威规则打分与分层，
自动过滤全局历史账本（assets/applied_history.json）中已投递过的岗位，
按对口度评分从高到低精选 Top N 个未投递岗位，生成专属运行目录。
"""

import os
import sys
import json
import time
import argparse
import shutil

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from resume_matcher import (
    ResumeProfile, load_job_data, list_available_job_files,
    classify_jobs_advanced, qualified_jobs_path, profile_path, resume_text_path
)
from resume_matcher.requirements import enrich
from resume_matcher.history import load_applied_history

_SKILL_ROOT = os.path.dirname(_SCRIPTS)


def main():
    parser = argparse.ArgumentParser(description="初始化新投递批次")
    parser.add_argument("--base-run-dir", default="assets/2026-09-18_00-21-59", help="基础运行目录（提取profile和resume_text）")
    parser.add_argument("--target-run-dir", help="目标运行目录，默认按时间戳生成")
    parser.add_argument("--limit", type=int, default=50, help="本批次选取的岗位数量")
    parser.add_argument("--offset", type=int, default=0, help="在未投递岗位中的起始偏移量")
    args = parser.parse_args()

    base_dir = os.path.abspath(args.base_run_dir)
    base_profile_path = os.path.join(base_dir, 'state', 'profile.json')
    base_resume_text_path = os.path.join(base_dir, 'state', 'resume_text.txt')

    if not os.path.exists(base_profile_path):
        print(f"❌ 找不到基础 profile: {base_profile_path}")
        sys.exit(1)

    with open(base_profile_path, 'r', encoding='utf-8') as f:
        pdata = json.load(f)

    profile = ResumeProfile(
        basic_info=pdata.get('basic_info', {}),
        education=pdata.get('education', {}),
        experience=pdata.get('experience', {}),
        skills=pdata.get('skills', {}),
        projects=pdata.get('projects', []),
        awards=pdata.get('awards', []),
        publications=pdata.get('publications', []),
        social_links=pdata.get('social_links', {}),
        salary_expectation=pdata.get('salary_expectation', {}),
        keywords=pdata.get('keywords', []),
        raw_text=pdata.get('raw_text', ''),
    )

    print("🔍 正在扫描原始岗位库并加载权威要求...")
    job_files = list_available_job_files()
    csv_paths = [jf['path'] for jf in job_files]
    jobs = load_job_data(csv_paths)
    enrich(jobs)

    print(f"📊 正在执行 6 维度规则综合评分（共 {len(jobs)} 个岗位）...")
    t1, t2, t3, t4 = classify_jobs_advanced(profile, jobs)
    candidates = t1 + t2

    # 加载已投递历史防重
    history = load_applied_history()
    applied_links = set(history.get('applied_links', []))
    applied_keys = set(history.get('applied_keys', []))

    unapplied = []
    for j in candidates:
        link = j.get('link', '')
        key = f"{j.get('公司', '')}__{j.get('职位', '')}"
        if link in applied_links or key in applied_keys:
            continue
        unapplied.append(j)

    # 按匹配得分降序排序
    unapplied.sort(key=lambda x: x.get('match_score', 0), reverse=True)
    print(f"🎯 筛选完成：初筛合格岗位共 {len(candidates)} 个，已剔除历史已投递，剩余未投递合格岗位 {len(unapplied)} 个")

    if not unapplied:
        print("⚠️ 没有剩余的未投递合格岗位！")
        sys.exit(0)

    selected = unapplied[args.offset:args.offset + args.limit]
    print(f"✨ 本批次选定 Top {len(selected)} 个岗位（偏移 {args.offset} ~ {args.offset + len(selected)}）")

    # 创建目标目录
    if args.target_run_dir:
        target_dir = os.path.abspath(args.target_run_dir)
    else:
        stamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        target_dir = os.path.join(_SKILL_ROOT, 'assets', f"{stamp}_batch2")

    state_dir = os.path.join(target_dir, 'state')
    os.makedirs(state_dir, exist_ok=True)

    # 写入 profile.json 与 resume_text.txt
    shutil.copyfile(base_profile_path, os.path.join(state_dir, 'profile.json'))
    if os.path.exists(base_resume_text_path):
        shutil.copyfile(base_resume_text_path, os.path.join(state_dir, 'resume_text.txt'))

    # 规范化写入 qualified_jobs.json
    q_path = os.path.join(state_dir, 'qualified_jobs.json')
    with open(q_path, 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    # 打印前 10 个入选岗位
    print("\n📋 本批次重点投递目标概览（前 10 家）：")
    for idx, j in enumerate(selected[:10], 1):
        score = j.get('match_score', 0)
        c = j.get('公司', '')
        t = j.get('职位', '')
        city = j.get('城市', '')
        sal = j.get('薪资', '')
        print(f"  [{idx:2d}] [{score:2d}分] {c} · {t} ({city} | {sal})")

    # 写入 LATEST.txt
    latest_file = os.path.join(_SKILL_ROOT, 'assets', 'LATEST.txt')
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(os.path.relpath(target_dir, _SKILL_ROOT))

    print(f"\n✅ 批次目录初始化完成: {target_dir}")
    print(f"   已就绪合格岗位: {len(selected)} 个")


if __name__ == '__main__':
    main()
