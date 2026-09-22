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
    print('URL:', dp.url)

    # Click first chat
    user_items = dp.eles('css:.user-list li, .friend-content')
    if user_items:
        user_items[0].click()
        time.sleep(2)

    inp = dp.ele('css:#chat-input') or dp.ele('css:[contenteditable="true"]')
    print('Input found:', bool(inp))
    if inp:
        print('Input text current:', repr(inp.text[:60]))

    btn_send = dp.eles('css:.btn-send')
    print('btn-send count:', len(btn_send))
    for i, b in enumerate(btn_send):
        print(f'btn-send [{i}]: tag={b.tag}, text={repr(b.text)}, html={repr(b.html[:150])}')

    send_text = dp.eles('text:发送')
    print('text:发送 count:', len(send_text))
    for i, b in enumerate(send_text):
        print(f'text:发送 [{i}]: tag={b.tag}, text={repr(b.text)}, html={repr(b.html[:150])}')

    # Check footer or chat-op
    chat_op = dp.ele('css:.chat-op, .chat-editor, .chat-input')
    if chat_op:
        print('chat_op html:', repr(chat_op.html[:500]))

finally:
    dp.quit()
