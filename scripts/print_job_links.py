import json

with open('assets/post_data/2026-09-20_small_company_agent_fde_internships.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

agent_jobs = [j for j in jobs if j.get('方向') == 'AI Agent']
fde_jobs = [j for j in jobs if j.get('方向') == 'FDE / 交付']

print("=== TOP 10 AGENT JOBS ===")
for i, j in enumerate(agent_jobs[:10], 1):
    c = j.get('公司', '')
    p = j.get('职位', '')
    s = j.get('薪资', '')
    city = j.get('城市', '')
    scale = j.get('规模', '')
    link = j.get('link', '')
    print(f"{i}. [{city}] {c} ({scale}) - {p} | {s}")
    print(f"   直达链接: {link}")

print("\n=== TOP 10 FDE JOBS ===")
for i, j in enumerate(fde_jobs[:10], 1):
    c = j.get('公司', '')
    p = j.get('职位', '')
    s = j.get('薪资', '')
    city = j.get('城市', '')
    scale = j.get('规模', '')
    link = j.get('link', '')
    print(f"{i}. [{city}] {c} ({scale}) - {p} | {s}")
    print(f"   直达链接: {link}")
