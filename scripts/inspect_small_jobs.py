import glob, os, csv

files = glob.glob('assets/post_data/custom/*.csv')
small_jobs = []
seen = set()

for f in files:
    with open(f, 'r', encoding='utf-8-sig') as fp:
        rows = list(csv.DictReader(fp))
        for r in rows:
            scale = r.get('规模', '')
            link = r.get('link', '').split('?')[0]
            if scale in ['0-20人', '20-99人'] and link and link not in seen:
                seen.add(link)
                small_jobs.append(r)

print(f"=== Total Unique Small Company (0-99 people) Jobs: {len(small_jobs)} ===")
agent_cnt = sum(1 for j in small_jobs if 'agent' in j.get('职位','').lower() or '智能体' in j.get('职位',''))
fde_cnt = sum(1 for j in small_jobs if 'fde' in j.get('职位','').lower() or '交付' in j.get('职位',''))

print(f"AI Agent / 智能体 方向: {agent_cnt} 个")
print(f"FDE / 交付 方向: {fde_cnt} 个")

print("\nLatest 10 crawled small company positions:")
for j in small_jobs[-10:]:
    c = j.get('公司', '')
    scale = j.get('规模', '')
    p = j.get('职位', '')
    s = j.get('薪资', '')
    city = j.get('城市', '')
    hr = f"{j.get('HR姓名', '')}({j.get('HR活跃度', '')})"
    print(f"[{city}] {c} ({scale}) - {p} | {s} | HR: {hr}")
