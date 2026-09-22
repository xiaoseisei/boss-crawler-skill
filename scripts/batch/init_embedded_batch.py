#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化中小企业嵌入式/电气自动化专属投递批次。

从刚刚采集的 169 个中小企业（0-20人、20-99人）嵌入式与电气岗位中，
使用嵌入式专属简历（assets/resumes/embedded）做多维规则匹配，
自动排除已投递历史，按匹配得分排序精选 Top N 个岗位，
生成独立的运行目录供下游材料生成与批量投递。
"""

import os
import sys
import json
import time
import glob
import shutil
import argparse

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from resume_matcher import (
    ResumeProfile, load_job_data, classify_jobs_advanced
)
from resume_matcher.history import load_applied_history

_SKILL_ROOT = os.path.dirname(_SCRIPTS)


def main():
    parser = argparse.ArgumentParser(description="初始化中小企业嵌入式投递批次")
    parser.add_argument("--profile-dir", default="assets/resumes/embedded", help="嵌入式简历profile目录")
    parser.add_argument("--target-run-dir", help="目标运行目录，默认按时间戳生成")
    parser.add_argument("--limit", type=int, default=50, help="本批次选取的岗位数量")
    args = parser.parse_args()

    profile_dir = os.path.abspath(args.profile_dir)
    profile_path = os.path.join(profile_dir, 'state', 'profile.json')
    resume_text_path = os.path.join(profile_dir, 'state', 'resume_text.txt')

    if not os.path.exists(profile_path):
        print(f"❌ 找不到嵌入式 profile: {profile_path}")
        sys.exit(1)

    with open(profile_path, 'r', encoding='utf-8') as f:
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

    # 扫描中小企业嵌入式/单片机/电气相关 CSV
    patterns = ['*嵌入式*.csv', '*单片机*.csv', '*STM32*.csv', '*电气*.csv']
    files = []
    for p in patterns:
        files.extend(glob.glob(os.path.join(_SKILL_ROOT, 'assets', 'post_data', 'custom', p)))
    files = sorted(list(set(files)))

    print(f"🔍 正在加载 {len(files)} 个中小企业嵌入式与电气岗位数据文件...")
    jobs = load_job_data(files)

    print(f"📊 正在执行嵌入式专业能力综合评分（共 {len(jobs)} 个岗位）...")
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

    selected = unapplied[:args.limit]
    print(f"✨ 本批次选定 Top {len(selected)} 个优质中小企业岗位")

    # 创建目标目录
    if args.target_run_dir:
        target_dir = os.path.abspath(args.target_run_dir)
    else:
        stamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        target_dir = os.path.join(_SKILL_ROOT, 'assets', f"{stamp}_embedded_sme")

    state_dir = os.path.join(target_dir, 'state')
    os.makedirs(state_dir, exist_ok=True)

    # 写入 profile.json 与 resume_text.txt
    shutil.copyfile(profile_path, os.path.join(state_dir, 'profile.json'))
    if os.path.exists(resume_text_path):
        shutil.copyfile(resume_text_path, os.path.join(state_dir, 'resume_text.txt'))

    # 写入 qualified_jobs.json
    q_path = os.path.join(state_dir, 'qualified_jobs.json')
    with open(q_path, 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    # 打印前 15 个入选岗位
    print("\n📋 中小企业嵌入式重点投递目标概览（前 15 家）：")
    for idx, j in enumerate(selected[:15], 1):
        score = j.get('match_score', 0)
        c = j.get('公司', '')
        t = j.get('职位', '')
        city = j.get('城市', '')
        sal = j.get('薪资', '')
        sc = j.get('规模', '')
        print(f"  [{idx:2d}] [{score:2d}分] {c} · {t} ({city} | {sal} | {sc})")

    # 写入 LATEST.txt
    latest_file = os.path.join(_SKILL_ROOT, 'assets', 'LATEST.txt')
    with open(latest_file, 'w', encoding='utf-8') as f:
        f.write(os.path.relpath(target_dir, _SKILL_ROOT))

    print(f"\n✅ 批次目录初始化完成: {target_dir}")
    print(f"   已就绪合格岗位: {len(selected)} 个")


if __name__ == '__main__':
    main()
