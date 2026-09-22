#!/usr/bin/env python3
"""
根据用户指定的 5 大求职方向对 7,222 条校招岗位进行精准分类与筛选。
求职方向：
1. Agent 方向 (AI Agent / 大模型 / 智能体)
2. 后端方向 (Backend / Java / Go / C++ / 服务端)
3. 嵌入式方向 (Embedded / 单片机 / 固件 / FPGA / DSP / 驱动)
4. FDE 方向 (Forward Deployed Engineer / 现场开发 / 交付研发 / 解决方案)
5. 电气方向 (电气工程 / 自动化 / 电力 / PLC / 控制)
"""

import json
import re
import csv
from pathlib import Path
from collections import defaultdict

INPUT_JSON = Path("assets/feishu_data/campus_jobs.json")
OUTPUT_DIR = Path("assets/feishu_data/categorized")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 规则与关键词定义 (使用小写匹配)
CATEGORIES = {
    "agent方向": {
        "keywords": [
            r"agent", r"智能体", r"大模型", r"llm", r"aigc", r"具身智能", 
            r"rag", r"多模态", r"生成式ai", r"提示词", r"算法.*(agent|模型|nlp)"
        ],
        "exclude": [r"保险代理人", r"销售agent"]
    },
    "后端方向": {
        "keywords": [
            r"后端", r"后台", r"服务端", r"java", r"golang", r"\bgo\b(开发|工程师)?", 
            r"c\+\+", r"python(开发|工程师)?", r"软件开发(工程师)?", r"研发工程师", 
            r"分布式", r"数据库", r"微服务"
        ],
        "exclude": [r"前端", r"ui", r"交互设计", r"采购", r"行政", r"财务"]
    },
    "嵌入式方向": {
        "keywords": [
            r"嵌入式", r"单片机", r"固件", r"firmware", r"arm", r"dsp", 
            r"fpga", r"rtos", r"驱动", r"bsp", r"底层开发", r"soc", r"板级"
        ],
        "exclude": [r"机械", r"建筑"]
    },
    "fde方向": {
        "keywords": [
            r"\bfde\b", r"forward deployed", r"前线", r"现场开发", r"现场研发", 
            r"交付研发", r"驻场研发", r"解决方案工程师", r"解决方案专家", 
            r"\bfae\b", r"现场应用", r"技术支持工程师", r"实施开发"
        ],
        "exclude": [r"物业", r"客服"]
    },
    "电气方向": {
        "keywords": [
            r"电气", r"自动化", r"电力", r"plc", r"电机", r"电路", 
            r"配电", r"继电保护", r"变电", r"电气工程", r"控制工程", 
            r"工控", r"强电", r"弱电", r"机电"
        ],
        "exclude": [r"电气焊", r"普工"]
    }
}

def match_category(job_text):
    text_lower = job_text.lower()
    matched = []
    
    for cat_name, rule in CATEGORIES.items():
        # 检查是否命中关键词
        hit = False
        for kw in rule["keywords"]:
            if re.search(kw, text_lower):
                hit = True
                break
        if not hit:
            continue
            
        # 检查是否包含排除词
        exclude_hit = False
        for ex in rule.get("exclude", []):
            if re.search(ex, text_lower):
                exclude_hit = True
                break
        
        if hit and not exclude_hit:
            matched.append(cat_name)
            
    return matched

def main():
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    categorized_jobs = defaultdict(list)
    all_target_jobs = []
    seen_target_ids = set()

    for idx, job in enumerate(jobs):
        # 搜索文本主要包含：招聘岗位、招聘公告标题、行业
        job_title = job.get("招聘岗位", "")
        company = job.get("公司名称", "")
        notice = job.get("招聘公告", "")
        
        combined_text = f"{job_title} {notice}"
        cats = match_category(combined_text)
        
        if cats:
            job_copy = dict(job)
            job_copy["matched_categories"] = cats
            job_copy["id"] = idx
            
            for c in cats:
                categorized_jobs[c].append(job_copy)
                
            if idx not in seen_target_ids:
                seen_target_ids.add(idx)
                all_target_jobs.append(job_copy)

    print("=" * 60)
    print("🎯 各目标求职方向岗位命中统计:")
    print("=" * 60)
    
    summary_report = {}
    for cat_name in CATEGORIES.keys():
        job_list = categorized_jobs[cat_name]
        valid_link_count = sum(1 for j in job_list if j.get("岗位链接") and j.get("岗位链接").startswith("http"))
        summary_report[cat_name] = {
            "total": len(job_list),
            "valid_links": valid_link_count
        }
        print(f"📌 【{cat_name.upper()}】: 命中 {len(job_list)} 个岗位 (其中有效网申链接: {valid_link_count} 条)")

        # 保存各自独立的分类文件
        cat_file_json = OUTPUT_DIR / f"{cat_name}.json"
        cat_file_csv = OUTPUT_DIR / f"{cat_name}.csv"
        with open(cat_file_json, "w", encoding="utf-8") as f:
            json.dump(job_list, f, ensure_ascii=False, indent=2)
            
        if job_list:
            headers = list(job_list[0].keys())
            with open(cat_file_csv, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(job_list)

    print(f"\n✨ 去重后总计命中目标岗位: {len(all_target_jobs)} 个！")
    
    # 保存所有目标岗位的全集
    all_target_file = OUTPUT_DIR / "all_target_jobs.json"
    with open(all_target_file, "w", encoding="utf-8") as f:
        json.dump(all_target_jobs, f, ensure_ascii=False, indent=2)

    all_target_csv = OUTPUT_DIR / "all_target_jobs.csv"
    if all_target_jobs:
        headers = list(all_target_jobs[0].keys())
        with open(all_target_csv, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(all_target_jobs)

    # 打印每个类别的典型样本
    print("\n" + "=" * 60)
    print("📋 各方向典型岗位样本展示:")
    print("=" * 60)
    for cat_name in CATEGORIES.keys():
        print(f"\n>>> 方向: 【{cat_name.upper()}】(展示前 2 条):")
        sample_shown = 0
        for j in categorized_jobs[cat_name]:
            link = j.get("岗位链接", "")
            if link.startswith("http"):
                print(f"  🏢 公司: {j.get('公司名称')} | 💼 岗位: {j.get('招聘岗位')}")
                print(f"     📍 地点: {j.get('工作地点')} | 🎓 届别: {j.get('招聘届别')}")
                print(f"     🔗 链接: {link}")
                print("-" * 50)
                sample_shown += 1
                if sample_shown >= 2:
                    break

if __name__ == "__main__":
    main()
