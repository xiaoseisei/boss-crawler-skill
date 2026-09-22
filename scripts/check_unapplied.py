# -*- coding: utf-8 -*-
import json, os, glob

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_jobs = hist.get('applied_jobs', [])
print(f'Total applied in history: {len(applied_jobs)}')
print('Latest 10 applied:')
for it in applied_jobs[-10:]:
    print(f"  {it.get('applied_at')} | {it.get('company')} | {it.get('position')} | {it.get('status')}")

fde_dirs = sorted(glob.glob('assets/2026-09-18_11-31-40_fde_agent_sme/deliver/*'))
print(f'\nTotal FDE SME dirs: {len(fde_dirs)}')

applied_links = set(hist.get('applied_links', []))
applied_keys = set(hist.get('applied_keys', []))

unapplied = []
for d in fde_dirs:
    md_file = os.path.join(d, '岗位信息+招呼语.md')
    if not os.path.exists(md_file):
        continue
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    link = ''
    company = ''
    pos = ''
    for line in content.splitlines():
        if line.startswith('岗位链接:'):
            link = line.replace('岗位链接:', '').strip()
        elif line.startswith('公司:'):
            company = line.replace('公司:', '').strip()
        elif line.startswith('岗位:'):
            pos = line.replace('岗位:', '').strip()

    key = f'{company}__{pos}'
    is_app = False
    if link and link in applied_links:
        is_app = True
    elif key in applied_keys:
        is_app = True

    dir_name = os.path.basename(d)
    for aj in applied_jobs:
        if aj.get('company') and aj.get('company') in dir_name:
            is_app = True
            break

    if not is_app:
        unapplied.append((dir_name, company, pos, link, d))

print(f'Unapplied count in 11-31-40: {len(unapplied)}')
print('\nFirst 10 unapplied:')
for i, (dn, c, p, l, d) in enumerate(unapplied[:10]):
    print(f'{i+1}. {dn} | {c} | {p} | {l}')
