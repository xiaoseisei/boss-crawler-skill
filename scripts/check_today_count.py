# -*- coding: utf-8 -*-
import json
from collections import Counter

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    h = json.load(f)

applied_jobs = h.get('applied_jobs', [])
today = '2026-09-18'

today_records = []
for j in applied_jobs:
    t = j.get('applied_at', '')
    if t.startswith(today):
        today_records.append(j)

statuses = Counter(j.get('status', 'unknown') for j in today_records)

print(f"Total in history: {len(applied_jobs)}")
print(f"Total recorded today ({today}): {len(today_records)}")
print("Status breakdown for today:")
for s, c in statuses.items():
    print(f"  {s}: {c}")

print(f"\nSuccessfully applied list (status == 'applied') count = {statuses.get('applied', 0)}:")
applied_list = [j for j in today_records if j.get('status') == 'applied']
for idx, j in enumerate(applied_list, 1):
    print(f"{idx}. [{j.get('applied_at')}] {j.get('company')} | {j.get('position')} | {j.get('city')}")
