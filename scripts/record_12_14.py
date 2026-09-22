# -*- coding: utf-8 -*-
import json, os, time

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_jobs = hist.setdefault('applied_jobs', [])
applied_links = hist.setdefault('applied_links', [])
applied_keys = hist.setdefault('applied_keys', [])

to_add = [
    {
        'company': '软通众擎',
        'position': 'FDE前沿部署工程师',
        'link': 'https://www.zhipin.com/job_detail/65aa41b2a082071e0nB83N60E1RZ.html',
        'key': '软通众擎__FDE前沿部署工程师',
        'applied_at': '2026-09-18 14:07:00',
        'status': 'applied',
        'greeting': '27届本科，掌握agent开发...',
        'image': '',
        'run_dir': ''
    },
    {
        'company': '北京众互意联技术',
        'position': 'FDE（前沿部署工程师）应届生/实习生',
        'link': 'https://www.zhipin.com/job_detail/21f0013317e42fea0nF93tm5FVRT.html',
        'key': '北京众互意联技术__FDE（前沿部署工程师）应届生/实习生',
        'applied_at': '2026-09-18 14:21:00',
        'status': 'applied',
        'greeting': '我自己动手做过几个完整的AI项目。比如一个GraphRAG教研问答系统...',
        'image': 'assets/2026-09-18_11-31-40_fde_agent_sme/deliver/#14-北京众互意联技术-FDE（前沿部署工程师）应届生_实习生/夏子聪-FDE（前沿部署工程师）应届生_实习生.png',
        'run_dir': 'assets/2026-09-18_11-31-40_fde_agent_sme'
    }
]

for item in to_add:
    if item['link'] not in applied_links:
        applied_links.append(item['link'])
    if item['key'] not in applied_keys:
        applied_keys.append(item['key'])
    # check if in applied_jobs
    if not any(j.get('company') == item['company'] for j in applied_jobs):
        applied_jobs.append(item)

hist['total_applied'] = len(applied_jobs)
hist['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')

with open('assets/applied_history.json', 'w', encoding='utf-8') as f:
    json.dump(hist, f, ensure_ascii=False, indent=2)

print(f"Updated applied_history.json. Total applied: {len(applied_jobs)}")
