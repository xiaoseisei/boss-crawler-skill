import json
import os
import glob
import re

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

applied_links = set()
applied_keys = set()

def clean_url(u):
    if not u: return ""
    return u.split('?')[0].strip()

for item in history.get('applied_jobs', []):
    l = clean_url(item.get('link') or item.get('url'))
    if l: applied_links.add(l)
    k = item.get('key')
    if k: applied_keys.add(k.strip())
    c = item.get('company', '').strip()
    p = item.get('position', '').strip()
    if c and p: applied_keys.add(f"{c}__{p}")

for item in history.get('intercepted_jobs', []):
    l = clean_url(item.get('link') or item.get('url'))
    if l: applied_links.add(l)
    k = item.get('key')
    if k: applied_keys.add(k.strip())
    c = item.get('company', '').strip()
    p = item.get('position', '').strip()
    if c and p: applied_keys.add(f"{c}__{p}")

batches = [
    'assets/2026-09-18_00-21-59',
    'assets/2026-09-18_10-17-37_batch2',
    'assets/2026-09-18_11-31-40_fde_agent_sme'
]

raw_candidates = []

for b in batches:
    deliver_dir = os.path.join(b, 'deliver')
    if not os.path.exists(deliver_dir):
        continue
    for folder in os.listdir(deliver_dir):
        fpath = os.path.join(deliver_dir, folder)
        if not os.path.isdir(fpath):
            continue
        info_file = os.path.join(fpath, '岗位信息+招呼语.md')
        png_files = glob.glob(os.path.join(fpath, '*.png'))
        if not (os.path.exists(info_file) and png_files):
            continue
            
        with open(info_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        def extract_table_field(pattern, text):
            m = re.search(pattern, text)
            return m.group(1).strip() if m else ""
            
        title = extract_table_field(r'\|\s*职位\s*\|\s*([^|]+)\|', content)
        company = extract_table_field(r'\|\s*公司\s*\|\s*([^|]+)\|', content)
        salary = extract_table_field(r'\|\s*薪资\s*\|\s*([^|]+)\|', content)
        city = extract_table_field(r'\|\s*城市\s*\|\s*([^|]+)\|', content)
        url = extract_table_field(r'\|\s*链接\s*\|\s*([^|]+)\|', content)
        score = extract_table_field(r'\|\s*匹配度\s*\|\s*([^|]+)\|', content)
        hr_name = extract_table_field(r'\|\s*HR姓名\s*\|\s*([^|]+)\|', content)
        hr_active = extract_table_field(r'\|\s*HR活跃度\s*\|\s*([^|]+)\|', content)
        
        greeting_match = re.search(r'## 招呼语.*?\n\n?(.*?)(?:\n##|\Z)', content, re.DOTALL)
        greeting = greeting_match.group(1).strip() if greeting_match else ""
        
        clean_u = clean_url(url)
        key = f"{company}__{title}"
        
        # Check against applied history
        is_applied = False
        if clean_u:
            is_applied = clean_u in applied_links
        elif key in applied_keys:
            is_applied = True
        if not clean_u:
            for ak in applied_keys:
                if company and title and (company in ak and title in ak):
                    is_applied = True
                    break
                
        if not is_applied:
            raw_candidates.append({
                'batch': b,
                'folder': folder,
                'folder_path': fpath,
                'company': company,
                'title': title,
                'salary': salary,
                'city': city,
                'score': score,
                'url': url,
                'png': png_files[0],
                'hr_name': hr_name,
                'hr_active': hr_active,
                'greeting': greeting
            })

# Deduplicate by clean URL and key
seen_urls = set()
seen_keys = set()
unique_candidates = []

for item in raw_candidates:
    u = clean_url(item['url'])
    k = f"{item['company']}__{item['title']}"
    if u and u in seen_urls:
        continue
    if k in seen_keys:
        continue
    if u: seen_urls.add(u)
    seen_keys.add(k)
    unique_candidates.append(item)

def parse_score(s):
    try:
        return float(s.replace('%', ''))
    except:
        return 0.0

unique_candidates.sort(key=lambda x: parse_score(x['score']), reverse=True)

with open('assets/today_unapplied_candidates.json', 'w', encoding='utf-8') as f:
    json.dump(unique_candidates, f, ensure_ascii=False, indent=2)

print(f"Total deduplicated unapplied candidates: {len(unique_candidates)}")
for idx, j in enumerate(unique_candidates, 1):
    hr_info = f"{j['hr_name']} ({j['hr_active']})" if j['hr_name'] and j['hr_name'] != '未采集' else "待探测"
    print(f"{idx}. [{j['company']}] {j['title']} | {j['city']} | {j['salary']} | 匹配度: {j['score']} | HR: {hr_info}")
