#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""初始化 0-99人 中小企业【AI Agent & FDE】专属投递批次。

从刚刚采集的 FDE、AI Agent、大模型应用开发岗位库中，
筛选 0-20人 及 20-99人 的中小初创企业，
使用大模型技术简历做 6 维度规则匹配，排除历史已投递，
精选 Top 50 个高对口度岗位，生成专属运行目录。
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
    parser = argparse.ArgumentParser(description="初始化 SME AI Agent & FDE 投递批次")
    parser.add_argument("--base-run-dir", default="assets/2026-09-18_00-21-59", help="基础 profile 目录")
    parser.add_argument("--target-run-dir", help="目标运行目录")
    parser.add_argument("--limit", type=int, default=50, help="本批次选取的岗位数量")
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

    custom_dir = os.path.join(_SKILL_ROOT, 'assets', 'post_data', 'custom')
    target_files = []
    for fname in os.listdir(custom_dir):
        if fname.endswith('.csv') and any(k in fname for k in ['FDE', 'AI Agent', '大模型应用开发']):
            target_files.append(os.path.join(custom_dir, fname))

    print(f"🔍 正在加载 {len(target_files)} 个 FDE / AI Agent / 大模型岗位数据文件...")
    raw_jobs = load_job_data(target_files)

    # 严格限定规模为 0-20人 或 20-99人
    sme_jobs = [j for j in raw_jobs if (j.get('规模') or '').strip() in ('0-20人', '20-99人')]
    print(f"🏢 过滤后纯 0-99 人中小企业岗位数: {len(sme_jobs)} 个")

    # 规则评分
    print("📊 正在执行 Agent/FDE 综合对口度评分...")
    t1, t2, t3, t4 = classify_jobs_advanced(profile, sme_jobs)
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

    # 额外对标题含 FDE、Agent、智能体 的岗位做前置加权
    def sort_key(job):
        score = job.get('match_score', 0)
        title = (job.get('职位') or '').lower()
        if 'fde' in title or 'forward deployed' in title:
            score += 15
        elif 'agent' in title or '智能体' in title:
            score += 10
        return score

    unapplied.sort(key=sort_key, reverse=True)
    print(f"🎯 筛选完成：初筛合格岗位共 {len(candidates)} 个，已剔除历史已投递，剩余未投递合格岗位 {len(unapplied)} 个")

    if not unapplied:
        print("⚠️ 没有剩余的未投递合格岗位！")
        sys.exit(0)

    selected = unapplied[:args.limit]
    print(f"✨ 本批次精选 Top {len(selected)} 个纯中小企业 (0-99人) 岗位")

    # 创建目标目录
    if args.target_run_dir:
        target_dir = os.path.abspath(args.target_run_dir)
    else:
        stamp = time.strftime('%Y-%m-%d_%H-%M-%S')
        target_dir = os.path.join(_SKILL_ROOT, 'assets', f"{stamp}_fde_agent_sme")

    state_dir = os.path.join(target_dir, 'state')
    os.makedirs(state_dir, exist_ok=True)

    # 写入 profile.json 与 resume_text.txt
    shutil.copyfile(base_profile_path, os.path.join(state_dir, 'profile.json'))
    if os.path.exists(base_resume_text_path):
        shutil.copyfile(base_resume_text_path, os.path.join(state_dir, 'resume_text.txt'))

    # 写入 qualified_jobs.json
    q_path = os.path.join(state_dir, 'qualified_jobs.json')
    with open(q_path, 'w', encoding='utf-8') as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    # 打印前 15 个入选岗位
    print("\n📋 本批次【AI Agent & FDE 中小企业】重点投递目标（前 15 家）：")
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
