# -*- coding: utf-8 -*-
import os, glob
from list_ready_candidates import candidates

target_names = [
    '科农优选', '星云深图', '千寻智创', '拂曦科技', '拾新未来',
    '智元数创', '朗姿医疗', 'VAST', '非凸科技', '福来数创'
]

selected = []
for tn in target_names:
    for c in candidates:
        if tn in c['company']:
            selected.append(c)
            break

print(f"Selected count: {len(selected)}")
for i, s in enumerate(selected, 1):
    png_name = os.path.basename(s['png'])
    print(f"{i}. {s['company']} | {s['title']} | PNG: {png_name}")
    print(f"   Link: {s['link']}")
    print(f"   RunDir: {s['run_dir']}")
    print(f"   PNG Path: {s['png']}")
