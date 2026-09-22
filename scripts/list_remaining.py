# -*- coding: utf-8 -*-
import json, os, glob, re

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_jobs = hist.get('applied_jobs', [])
applied_links = set(hist.get('applied_links', []))
applied_keys = set(hist.get('applied_keys', []))
applied_companies = set(j.get('company') for j in applied_jobs if j.get('company'))

fde_dirs = sorted(glob.glob('assets/2026-09-18_11-31-40_fde_agent_sme/deliver/*'), key=lambda x: int(re.search(r'#(\d+)', x).group(1)) if re.search(r'#(\d+)', x) else 999)

unapplied = []
for d in fde_dirs:
    idx_m = re.search(r'#(\d+)', d)
    idx = int(idx_m.group(1)) if idx_m else 0
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
    scale_m = re.search(r'\|\s*规模\s*\|\s*(.*?)\s*\|', content)
    scale = scale_m.group(1).strip() if scale_m else ''
    sal_m = re.search(r'\|\s*薪资\s*\|\s*(.*?)\s*\|', content)
    sal = sal_m.group(1).strip() if sal_m else ''

    # greeting
    greeting = ''
    if '## 招呼语' in content:
        greeting_part = content.split('## 招呼语')[1].split('\n\n', 1)[-1].strip()
        greeting = re.sub(r'>.*?\n', '', greeting_part).strip()

    pngs = glob.glob(os.path.join(d, '*.png'))
    img = pngs[0] if pngs else ''

    key = f'{comp}__{pos}'
    is_app = False
    if link in applied_links or key in applied_keys or comp in applied_companies:
        is_app = True

    if not is_app and img:
        unapplied.append({
            'idx': idx,
            'dir_name': os.path.basename(d),
            'company': comp,
            'position': pos,
            'scale': scale,
            'salary': sal,
            'link': link,
            'greeting': greeting,
            'image': img,
            'dir': d
        })

print(f"Total unapplied SME jobs: {len(unapplied)}")
for i, u in enumerate(unapplied[:20]):
    print(f"{i+1}. #{u['idx']} {u['company']} ({u['scale']}) | {u['position']} | {u['salary']}")
    print(f"   Link: {u['link']}")
    print(f"   Img: {os.path.basename(u['image'])}")
    print(f"   Greeting: {u['greeting'][:70]}...")
    print()
