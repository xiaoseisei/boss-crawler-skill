#!/usr/bin/env python3
import json
import re
from urllib.parse import urlparse
from collections import Counter

with open("assets/feishu_data/campus_jobs.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

domain_counter = Counter()
ats_keywords = {
    "北森 (Beisen / zhiye)": ["zhiye.com", "italent.cn", "beisen"],
    "Moka (Mokahr)": ["mokahr.com", "moka"],
    "大易 (Dayee)": ["dayee.com", "dayee"],
    "飞书招聘 (Feishu)": ["feishu.cn", "bytedance.com"],
    "微信推文/长图": ["mp.weixin.qq.com"],
    "前程无忧/智联专区": ["51job.com", "zhaopin.com", "liepin.com"],
    "牛客网": ["nowcoder.com"],
    "海投网": ["haitou.cc"]
}

ats_stats = Counter()

for j in jobs:
    text = f"{j.get('岗位链接', '')} {j.get('招聘公告', '')}"
    urls = re.findall(r'https?://([a-zA-Z0-9\-\.]+)', text)
    for host in urls:
        host = host.lower()
        domain_counter[host] += 1
        matched = False
        for ats_name, patterns in ats_keywords.items():
            if any(p in host for p in patterns):
                ats_stats[ats_name] += 1
                matched = True
                break
        if not matched:
            ats_stats["企业自建/独立官网"] += 1

print("=" * 50)
print("📊 招聘链接/系统类型分布统计:")
print("=" * 50)
for ats_name, count in ats_stats.most_common():
    print(f"{ats_name:25}: {count:5} 条")

print("\n" + "=" * 50)
print("🌐 访问频次最高的 Top 20 域名:")
print("=" * 50)
for host, count in domain_counter.most_common(20):
    print(f"{host:35}: {count:5} 次")
