import os, sys, time
sys.path.insert(0, 'scripts')
from DrissionPage import WebPage, ChromiumOptions
from browser_finder import find_chrome_browser

co = ChromiumOptions()
chrome_path = find_chrome_browser()
if chrome_path:
    co.set_browser_path(chrome_path)
user_data_dir = os.path.abspath('assets/chrome_user_data')
co.set_argument(f'--user-data-dir={user_data_dir}')
dp = WebPage(chromium_options=co)

try:
    dp.get('https://www.zhipin.com/web/geek/chat')
    time.sleep(3)
    user_items = dp.eles('css:.user-list li, .friend-content')
    if user_items:
        user_items[0].click()
        time.sleep(2)

    inp = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
    if inp:
        print('Input text:', repr(inp.text))
        print('Input loc:', inp.rect.location, 'size:', inp.rect.size)

    qr = dp.eles('text:下载App')
    print('QR text count:', len(qr))
    for q in qr:
        print('QR ele:', q.html[:100], 'loc:', q.rect.location, 'size:', q.rect.size)

    btn_send = dp.ele('css:.btn-send')
    if btn_send:
        print('btn_send html:', btn_send.html[:100], 'loc:', btn_send.rect.location, 'size:', btn_send.rect.size)
        print('btn_send class:', btn_send.attr('class'))

finally:
    dp.quit()
