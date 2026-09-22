import json
import datetime

with open('assets/applied_history.json', 'r', encoding='utf-8') as f:
    hist = json.load(f)

intercepted = hist.setdefault('intercepted_jobs', [])
# check if already there
exists = any(j.get('company') == '京东集团' for j in intercepted)
if not exists:
    intercepted.append({
        'company': '京东集团',
        'position': '多模态大模型算法工程师',
        'link': 'https://www.zhipin.com/job_detail/f2a78cfeb79282500nN_2NW4EVdS.html',
        'key': '京东集团__多模态大模型算法工程师',
        'intercepted_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'position_closed',
        'reason': '职位已关闭（无立即沟通按钮）',
        'proof': 'assets/deliver_proof/1_京东集团_no_btn.png'
    })
    hist['updated_at'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open('assets/applied_history.json', 'w', encoding='utf-8') as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)
    print("Recorded 京东集团 as position_closed.")
else:
    print("京东集团 already recorded.")
