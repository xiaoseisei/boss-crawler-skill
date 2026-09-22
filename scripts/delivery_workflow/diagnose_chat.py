"""BOSS直聘聊天工作台诊断工具脚本。

用于在网页结构变动、输入框定位失败或发送按钮失效时独立排查现场：
- 连接当前 CDP 调试端口（127.0.0.1:9224）；
- 探测聊天工作台中的输入框、发送按钮、最顶层点击命中元素；
- 抓取最近 5 条我方消息和页面警告文案（如频率限制、沟通上限）；
- 测试 DrissionPage 各种选择器的匹配与可见性情况。
"""
import json
from DrissionPage import ChromiumPage

# 连接运行在 9224 端口的 Chrome 浏览器实例
page = ChromiumPage('127.0.0.1:9224')

# 执行内嵌 JS 脚本，全景采集当前聊天页面的关键 DOM 结构与样式状态
state = page.run_js(r'''
// 1. 探测页面中所有潜在的输入控件（包括 contenteditable 富文本及 textarea 等）
const inputs = [...document.querySelectorAll('#chat-input,[contenteditable="true"],textarea,input')].map(e => ({
  tag:e.tagName, id:e.id, cls:String(e.className||''), value:e.value||'', text:e.innerText||'',
  disabled:!!e.disabled, readonly:!!e.readOnly, visible:!!(e.offsetWidth&&e.offsetHeight),
  outer:e.outerHTML.slice(0,500)
}));

// 2. 探测页面中的所有按钮控件（查找包含 send 或确定类名的按钮）
const buttons = [...document.querySelectorAll('button,[role="button"],.btn-send,.btn-sure-v2,[class*="send"]')].map(e => ({
  tag:e.tagName, id:e.id, cls:String(e.className||''), text:(e.innerText||'').slice(0,100),
  disabled:!!e.disabled, aria:e.getAttribute('aria-disabled'), visible:!!(e.offsetWidth&&e.offsetHeight),
  outer:e.outerHTML.slice(0,500)
}));

// 3. 检查发送按钮的物理位置与视口重叠情况，排查是否有不可见遮罩层挡住点击
const send = document.querySelector('button.btn-send');
const rect = send ? send.getBoundingClientRect() : null;
const top = rect ? document.elementFromPoint(rect.left + rect.width/2, rect.top + rect.height/2) : null;

// 4. 采集我方发送的最新 5 条历史聊天记录
const records = [...document.querySelectorAll('.chat-record .item-myself,.chat-message-list .item-myself,[class*="message-list"] [class*="myself"]')].slice(-5).map(e=>({text:(e.innerText||'').slice(0,200),html:e.outerHTML.slice(0,500)}));

// 5. 组装整体验断报告对象，并提取页面内可能出现的风控警告文本
return {
  url: location.href,
  title: document.title,
  inputs,
  buttons,
  send_rect: rect ? {x:rect.x, y:rect.y, w:rect.width, h:rect.height} : null,
  element_at_send: top ? {tag:top.tagName, cls:String(top.className||''), text:(top.innerText||'').slice(0,50)} : null,
  records,
  warnings: (document.body && document.body.innerText || '').match(/.{0,30}(上限|频繁|次数|稍后|限制|无法发送).{0,50}/g) || [],
  active: document.activeElement ? {tag:document.activeElement.tagName, id:document.activeElement.id, cls:String(document.activeElement.className||'')} : null,
  body: (document.body && document.body.innerText || '').slice(-1200)
};
''')

# 探测左侧用户/会话列表项的 DOM 结构
print('LISTS', page.run_js("return ['.user-list li','.user-list-content li','li[role=listitem]','.friend-content-warp'].map(s=>[s,[...document.querySelectorAll(s)].slice(0,10).map(e=>({text:(e.innerText||'').slice(0,100),cls:String(e.className||''),html:e.outerHTML.slice(0,180)}))])"))

# 测试 DrissionPage 原生元素选择器在当前页面上的定位能力与元素尺寸
for selector in ('css:#chat-input', 'css:[contenteditable="true"]', 'css:textarea.input', 'css:textarea'):
    try:
        el = page.ele(selector, timeout=1)
        print('DRISSION', selector, bool(el), el.rect.size if el else None)
    except Exception as exc:
        print('DRISSION', selector, 'ERROR', type(exc).__name__, str(exc))

# 格式化输出完整的状态诊断报告
print(json.dumps(state, ensure_ascii=False, indent=2))

