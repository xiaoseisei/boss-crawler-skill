# -*- coding: utf-8 -*-
import json, os, glob, re

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_jobs = hist.get('applied_jobs', [])
applied_links = set(hist.get('applied_links', []))
applied_keys = set(hist.get('applied_keys', []))

fde_dirs = sorted(glob.glob('assets/2026-09-18_11-31-40_fde_agent_sme/deliver/*'), key=lambda x: int(re.search(r'#(\d+)', x).group(1)) if re.search(r'#(\d+)', x) else 999)

candidates = []
for d in fde_dirs:
    md_file = os.path.join(d, '岗位信息+招呼语.md')
    if not os.path.exists(md_file):
        continue
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    pos_m = re.search(r'\|\s*职位\s*\|\s*(.*?)\s*\|', content)
    pos = pos_m.group(1).strip() if pos_m else ''
    comp_m = re.search(r'\|\s*公司\s*\|\s*(.*?)\s*\|', content)
    comp = comp_m.group(1).strip() if comp_m else ''
    link_m = re.search(r'\|\s*链接\s*\|\s*(.*?)\s*\|', content)
    link = link_m.group(1).strip() if link_m else ''

    # greeting
    greeting = ''
    if '## 招呼语' in content:
        greeting_part = content.split('## 招呼语')[1].split('\n\n', 1)[-1].strip()
        greeting = re.sub(r'>.*?\n', '', greeting_part).strip()

    pngs = glob.glob(os.path.join(d, '*.png'))
    img = pngs[0] if pngs else ''

    dir_name = os.path.basename(d)
    key = f'{comp}__{pos}'

    is_app = False
    if link in applied_links or key in applied_keys:
        is_app = True
    for aj in applied_jobs:
        if aj.get('company') and aj.get('company') == comp:
            is_app = True
            break

    if not is_app and img and greeting:
        candidates.append({
            'dir_name': dir_name,
            'company': comp,
            'position': pos,
            'link': link,
            'greeting': greeting,
            'image': img,
            'dir': d
        })

print(f'Total valid candidates: {len(candidates)}')
for i, c in enumerate(candidates[:10]):
    dn = c['dir_name']
    cp = c['company']
    ps = c['position']
    gr = c['greeting']
    lk = c['link']
    print(f"{i+1}. [{dn}] {cp} - {ps}")
    print(f"   Link: {lk}")
    print(f"   Greeting ({len(gr)} chars): {gr[:70]}...")
    print()
