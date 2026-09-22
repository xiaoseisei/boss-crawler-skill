# -*- coding: utf-8 -*-
import json
with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    h = json.load(f)

applied = h.get('applied_jobs', [])
print(f"Total applied: {len(applied)}")
print("Last 7 entries:")
for it in applied[-7:]:
    print(f"  {it.get('applied_at')} | {it.get('company')} | {it.get('position')} | {it.get('status')}")
