import glob, os, csv, json

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

applied_links = set()
for item in hist.get('applied_jobs', []) + hist.get('intercepted_jobs', []):
    l = item.get('link') or item.get('url')
    if l: applied_links.add(l.split('?')[0])

target_files = [
    'assets/post_data/custom/AI Agent_北京.csv',
    'assets/post_data/custom/AI Agent_上海.csv',
    'assets/post_data/custom/AI Agent_深圳.csv',
    'assets/post_data/custom/AI Agent_广州.csv',
    'assets/post_data/custom/AI Agent_杭州.csv',
    'assets/post_data/custom/AI Agent_武汉.csv',
    'assets/post_data/custom/AI Agent_成都.csv',
    'assets/post_data/custom/FDE_北京.csv',
    'assets/post_data/custom/FDE_上海.csv',
    'assets/post_data/custom/FDE_深圳.csv',
    'assets/post_data/custom/FDE_广州.csv',
    'assets/post_data/custom/FDE_杭州.csv',
    'assets/post_data/custom/FDE_武汉.csv',
    'assets/post_data/custom/FDE_成都.csv',
]

small_unapplied = []
seen = set()

for f in target_files:
    if not os.path.exists(f):
        continue
    with open(f, 'r', encoding='utf-8-sig') as fp:
        for r in csv.DictReader(fp):
            scale = r.get('规模', '')
            link = r.get('link', '').split('?')[0]
            if scale in ['0-20人', '20-99人'] and link and link not in seen:
                seen.add(link)
                if link not in applied_links:
                    # tag direction
                    title = r.get('职位', '').lower()
                    if 'fde' in title or '交付' in title:
                        r['方向'] = 'FDE / 交付'
                    elif 'agent' in title or '智能体' in title:
                        r['方向'] = 'AI Agent'
                    else:
                        r['方向'] = 'AI应用 / 综合'
                    small_unapplied.append(r)

out_csv = 'assets/post_data/2026-09-20_small_company_agent_fde_internships.csv'
out_json = 'assets/post_data/2026-09-20_small_company_agent_fde_internships.json'

fields = ['方向', '公司', '规模', '职位', '城市', '薪资', '经验', '学历', 'HR姓名', 'HR职位', 'HR活跃度', 'link', '技能标签', '岗位要求和职责', '公司信息']

with open(out_csv, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(small_unapplied)

with open(out_json, 'w', encoding='utf-8') as f:
    json.dump(small_unapplied, f, ensure_ascii=False, indent=2)

print(f"Exported {len(small_unapplied)} jobs to:")
print(f"CSV: {os.path.abspath(out_csv)}")
print(f"JSON: {os.path.abspath(out_json)}")
