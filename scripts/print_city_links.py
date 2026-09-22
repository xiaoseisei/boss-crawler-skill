import json

with open('assets/post_data/2026-09-20_small_company_agent_fde_internships.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

for city in ['上海', '深圳', '广州', '杭州', '武汉']:
    c_jobs = [j for j in jobs if j.get('城市') == city and ('实习' in j.get('职位','') or '元/天' in j.get('薪资',''))]
    print(f"=== {city} 实习岗位 ({len(c_jobs)}个) ===")
    for j in c_jobs[:4]:
        c = j.get('公司', '')
        p = j.get('职位', '')
        s = j.get('薪资', '')
        link = j.get('link', '')
        print(f"  [{c}] {p} | {s}")
        print(f"   链接: {link}")
