import json

with open('assets/today_unapplied_candidates.json', 'r', encoding='utf-8') as f:
    jobs = json.load(f)

categories = {
    '大厂与高潜独角兽（实习/校招）': [],
    'AI Agent 与大模型应用核心开发': [],
    'Python 后端与研发助理': [],
    'FDE 前沿部署与交付工程师': [],
    '评测、标注与专项研究': []
}

for j in jobs:
    title = j['title']
    company = j['company']
    if any(k in company for k in ['阿里', '百度', '京东', 'VAST', '非凸', '多益网络']):
        categories['大厂与高潜独角兽（实习/校招）'].append(j)
    elif 'FDE' in title or '交付' in title:
        categories['FDE 前沿部署与交付工程师'].append(j)
    elif any(k in title for k in ['后端', 'Python', '开发工程师助理']):
        categories['Python 后端与研发助理'].append(j)
    elif any(k in title for k in ['评测', '标注', '质检', '研究员', '测试']):
        categories['评测、标注与专项研究'].append(j)
    else:
        categories['AI Agent 与大模型应用核心开发'].append(j)

for cat, items in categories.items():
    print(f"=== {cat} ({len(items)}家) ===")
    for i, it in enumerate(items, 1):
        hr = f"{it['hr_name']}({it['hr_active']})" if it['hr_name'] and it['hr_name'] != '未采集' else '待在线探测'
        print(f"  {i}. [{it['company']}] {it['title']} | {it['city']} | {it['salary']} | 匹配度: {it['score']} | HR: {hr}")
