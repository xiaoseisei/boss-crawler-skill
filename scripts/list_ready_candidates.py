# -*- coding: utf-8 -*-
import json, glob, os

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_jobs = hist.get('applied_jobs', [])
applied_links = set(hist.get('applied_links', []))
applied_companies = set()
for aj in applied_jobs:
    if aj.get('link'): applied_links.add(aj['link'])
    if aj.get('company'): applied_companies.add(aj['company'])

runs = sorted(glob.glob('assets/2026-*'))

candidates = []
for r in runs:
    deliver_dirs = glob.glob(os.path.join(r, 'deliver', '*'))
    for d in deliver_dirs:
        pngs = glob.glob(os.path.join(d, '*.png'))
        if not pngs:
            continue
        base = os.path.basename(d)
        
        md_file = os.path.join(d, '岗位信息+招呼语.md')
        link, company, title = '', '', ''
        if os.path.exists(md_file):
            with open(md_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if '| 职位 |' in line:
                        title = line.split('|')[2].strip()
                    elif '| 公司 |' in line:
                        company = line.split('|')[2].strip()
                    elif '| 链接 |' in line:
                        link = line.split('|')[2].strip()
        
        if not company:
            parts = base.split('-')
            if len(parts) >= 3:
                company = parts[1].strip()
                title = parts[2].strip()
                
        is_app = False
        if link and link in applied_links:
            is_app = True
        if company and company in applied_companies:
            is_app = True
            
        if not is_app:
            candidates.append({
                'run_dir': r,
                'deliver_dir': d,
                'company': company,
                'title': title,
                'link': link,
                'png': pngs[0]
            })

print(f"Total ready candidates with PNG across all runs: {len(candidates)}")
for idx, c in enumerate(candidates, 1):
    rd = os.path.basename(c['run_dir'])
    print(f"{idx}. [{rd}] {c['company']} | {c['title']} | {c['link']}")
