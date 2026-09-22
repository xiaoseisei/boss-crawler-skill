import os
import json

with open('assets/today_unapplied_candidates.json', 'r', encoding='utf-8') as f:
    all_jobs = json.load(f)

# Find top jobs by company name
job_map = {}
for j in all_jobs:
    for target in ['京东集团', '阿里巴巴集团', '百度', 'VAST', '多益网络', '非凸科技', '深圳市智元数创科技', '澳斯顿电子商务']:
        if target in j['company'] and target not in job_map:
            job_map[target] = j

print(f"Found {len(job_map)} target companies from unapplied candidates:")
for comp, data in job_map.items():
    p = data['png']
    exists = os.path.exists(p)
    size = os.path.getsize(p) if exists else 0
    print(f"[{comp}] {data['title']}")
    print(f"  Folder: {data['folder']}")
    print(f"  PNG: {p} (Exists: {exists}, {size} bytes)")
    print(f"  URL: {data['url']}")
