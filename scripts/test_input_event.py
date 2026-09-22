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
    print('Initial input innerHTML:', repr(inp.inner_html))
    btn_send = dp.ele('css:.btn-send')
    print('Initial btn-send class:', btn_send.attr('class') if btn_send else 'None')

    # Test typing a single character or event
    inp.click()
    dp.run_js("""
        const el = arguments[0];
        console.log('Testing input dispatch');
    """, inp)

finally:
    dp.quit()
