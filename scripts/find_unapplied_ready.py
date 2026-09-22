# -*- coding: utf-8 -*-
import json, os, glob

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_jobs = hist.get('applied_jobs', [])
applied_links = set(hist.get('applied_links', []))
applied_companies = set()
for aj in applied_jobs:
    if aj.get('link'): applied_links.add(aj['link'].strip())
    if aj.get('company'): applied_companies.add(aj['company'].strip())

runs = [
    'assets/2026-09-18_00-21-59',
    'assets/2026-09-18_10-17-37_batch2',
    'assets/2026-09-18_11-31-40_fde_agent_sme'
]

unapplied = []

for r in runs:
    deliver_dirs = sorted(glob.glob(os.path.join(r, 'deliver', '*')))
    for d in deliver_dirs:
        pngs = glob.glob(os.path.join(d, '*.png'))
        if not pngs:
            continue
        
        md_file = os.path.join(d, '岗位信息+招呼语.md')
        company, title, link, salary, city, match_score = '', '', '', '', '', ''
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if '| 职位 |' in line: title = line.split('|')[2].strip()
                    elif '| 公司 |' in line: company = line.split('|')[2].strip()
                    elif '| 薪资 |' in line: salary = line.split('|')[2].strip()
                    elif '| 城市 |' in line: city = line.split('|')[2].strip()
                    elif '| 链接 |' in line: link = line.split('|')[2].strip()
                    elif '| 匹配度 |' in line: match_score = line.split('|')[2].strip()

        if not company:
            base = os.path.basename(d)
            parts = base.split('-')
            if len(parts) >= 3:
                company = parts[1].strip()
                title = parts[2].strip()

        is_applied = False
        if link and link in applied_links:
            is_applied = True
        if company and company in applied_companies:
            is_applied = True
            
        if not is_applied:
            unapplied.append({
                'run': os.path.basename(r),
                'dir_name': os.path.basename(d),
                'dir_path': d,
                'company': company,
                'title': title,
                'salary': salary,
                'city': city,
                'match_score': match_score,
                'link': link,
                'png': pngs[0]
            })

print(f"Total ready and completely unapplied jobs across runs: {len(unapplied)}")
for i, item in enumerate(unapplied, 1):
    print(f"{i}. [{item['run']}] {item['company']} | {item['title']} | {item['city']} | {item['salary']} | 匹配度:{item['match_score']}")
    print(f"   Link: {item['link']}")
    print(f"   PNG: {os.path.basename(item['png'])}")
