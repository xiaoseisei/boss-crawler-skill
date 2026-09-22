import glob, os, csv

files = [
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

total_jobs = 0
all_jobs = []

for f in files:
    if os.path.exists(f):
        with open(f, 'r', encoding='utf-8-sig') as fp:
            rows = list(csv.DictReader(fp))
            total_jobs += len(rows)
            for r in rows:
                all_jobs.append((f, r))

print(f"Total rows in target CSVs: {total_jobs}")

# Deduplicate
unique_links = set()
unique_jobs = []
for fpath, r in all_jobs:
    l = r['link'].split('?')[0] if r.get('link') else ''
    if l and l not in unique_links:
        unique_links.add(l)
        unique_jobs.append((fpath, r))

print(f"Unique total jobs: {len(unique_jobs)}")

# Check internship jobs specifically
interns = []
for fpath, r in unique_jobs:
    salary = r.get('薪资', '')
    title = r.get('职位', '')
    exp = r.get('经验', '')
    if '元/天' in salary or '实习' in title or '实习' in exp or '校招' in title or '应届' in exp:
        interns.append(r)

print(f"Total internship / campus recruit jobs: {len(interns)}")

print("\n--- Latest 10 newly crawled jobs ---")
for fpath, r in unique_jobs[-10:]:
    c = r.get('公司', '')
    p = r.get('职位', '')
    s = r.get('薪资', '')
    city = r.get('城市', '')
    hr = f"{r.get('HR姓名', '')}({r.get('HR活跃度', '')})"
    print(f"[{city}] {c} - {p} | {s} | HR: {hr}")
