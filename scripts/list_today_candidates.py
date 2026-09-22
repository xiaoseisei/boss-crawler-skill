import json
import os
import glob

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

applied_keys = set()
for item in history.get('applied_jobs', []):
    key = item.get('key') or f"{item.get('company')}__{item.get('position')}"
    applied_keys.add(key)
    # also normalized key
    c = item.get('company', '').strip()
    p = item.get('position', '').strip()
    applied_keys.add(f"{c}__{p}")

batches = [
    'assets/2026-09-18_00-21-59',
    'assets/2026-09-18_10-17-37_batch2',
    'assets/2026-09-18_11-31-40_fde_agent_sme'
]

ready_jobs = []

for b in batches:
    deliver_dir = os.path.join(b, 'deliver')
    search_dir = deliver_dir if os.path.exists(deliver_dir) else b
    if not os.path.exists(search_dir):
        continue
    for folder in os.listdir(search_dir):
        fpath = os.path.join(search_dir, folder)
        if not os.path.isdir(fpath):
            continue
        info_file = os.path.join(fpath, '岗位信息+招呼语.md')
        png_files = glob.glob(os.path.join(fpath, '*.png'))
        if os.path.exists(info_file) and png_files:
            content = open(info_file, 'r', encoding='utf-8').read()
            url = ''
            company = ''
            title = ''
            salary = ''
            city = ''
            score = ''
            greeting = ''
            lines = content.splitlines()
            for i, line in enumerate(lines):
                line_str = line.strip()
                if ('岗位链接' in line_str or 'URL' in line_str or 'https://' in line_str) and not url:
                    if 'http' in line_str:
                        raw_url = line_str[line_str.find('http'):].split(')')[0].split(' ')[0].strip()
                        url = raw_url
                elif '公司' in line_str and not company:
                    parts = line_str.split(':', 1) if ':' in line_str else line_str.split('：', 1)
                    if len(parts) > 1: company = parts[1].strip()
                elif '岗位' in line_str and not title:
                    parts = line_str.split(':', 1) if ':' in line_str else line_str.split('：', 1)
                    if len(parts) > 1: title = parts[1].strip()
                elif '薪资' in line_str and not salary:
                    parts = line_str.split(':', 1) if ':' in line_str else line_str.split('：', 1)
                    if len(parts) > 1: salary = parts[1].strip()
                elif '城市' in line_str and not city:
                    parts = line_str.split(':', 1) if ':' in line_str else line_str.split('：', 1)
                    if len(parts) > 1: city = parts[1].strip()
                elif '匹配度' in line_str and not score:
                    parts = line_str.split(':', 1) if ':' in line_str else line_str.split('：', 1)
                    if len(parts) > 1: score = parts[1].strip()
                elif '招呼语' in line_str and not greeting:
                    greeting = "\n".join(lines[i+1:]).strip()

            key = f"{company}__{title}"
            # Check if applied
            is_applied = False
            for ak in applied_keys:
                if key == ak or (company and company in ak and title and title in ak):
                    is_applied = True
                    break
            
            if not is_applied:
                ready_jobs.append({
                    'batch': b,
                    'folder': folder,
                    'fpath': fpath,
                    'company': company,
                    'title': title,
                    'salary': salary,
                    'city': city,
                    'score': score,
                    'url': url,
                    'png': png_files[0],
                    'greeting': greeting
                })

print(f"Total ready unapplied: {len(ready_jobs)}")
for idx, j in enumerate(ready_jobs, 1):
    print(f"{idx}. [{j['company']}] {j['title']} | {j['city']} | {j['salary']} | 匹配度: {j['score']}")
    print(f"   路径: {j['folder']}")
    print(f"   URL: {j['url']}")
