import json
import re
import os

with open('assets/post_data/2026-09-20_small_company_agent_fde_internships.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_links = set()
for item in hist.get('applied_jobs', []) + hist.get('intercepted_jobs', []):
    l = item.get('link') or item.get('url')
    if l: applied_links.add(l.split('?')[0])

def parse_salary_val(s):
    if not s: return 999999
    # Daily: e.g. 100-150元/天
    m_day = re.search(r'(\d+)(?:-(\d+))?元/天', s)
    if m_day:
        low = float(m_day.group(1))
        high = float(m_day.group(2)) if m_day.group(2) else low
        return (low + high) / 2
    # Monthly K: e.g. 3-5K, 4-6K
    m_k = re.search(r'(\d+)(?:-(\d+))?K', s, re.IGNORECASE)
    if m_k:
        low = float(m_k.group(1)) * 1000
        high = float(m_k.group(2)) * 1000 if m_k.group(2) else low
        return ((low + high) / 2) / 21.75
    # Monthly raw: e.g. 2000-3000
    m_raw = re.search(r'(\d+)-(\d+)', s)
    if m_raw:
        low = float(m_raw.group(1))
        high = float(m_raw.group(2))
        return ((low + high) / 2) / 21.75
    return 999999

unapplied_sorted = []
for j in jobs:
    link = j.get('link', '').split('?')[0]
    if link not in applied_links:
        j['salary_val'] = parse_salary_val(j.get('薪资', ''))
        unapplied_sorted.append(j)

# Sort by salary ascending (lowest to highest)
unapplied_sorted.sort(key=lambda x: x['salary_val'])

with open('assets/post_data/2026-09-20_small_jobs_sorted_lowest_salary.json', 'w', encoding='utf-8') as f:
    json.dump(unapplied_sorted, f, ensure_ascii=False, indent=2)

print(f"Total unapplied small company jobs: {len(unapplied_sorted)}")
print("\n=== TOP 15 LOWEST SALARY JOBS ===")
for idx, j in enumerate(unapplied_sorted[:15], 1):
    c = j.get('公司', '')
    scale = j.get('规模', '')
    p = j.get('职位', '')
    s = j.get('薪资', '')
    city = j.get('城市', '')
    direction = j.get('方向', '')
    hr = f"{j.get('HR姓名', '')}({j.get('HR活跃度', '')})"
    val = round(j['salary_val'])
    print(f"{idx}. [{city}] {c} ({scale}) - {p} | 薪资: {s} (约{val}元/天)")
    print(f"   方向: {direction} | HR: {hr}")
    print(f"   链接: {j.get('link')}")
