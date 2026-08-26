#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
公司定向采集 - 品牌页结构探针（可选增强）
========================================

公司定向的**基础能力**（`-m company`）不依赖本探针：它直接用已验证过的搜索接口
（`/web/geek/jobs?query=公司全名`）翻页 + `brandName` 精确过滤，就拿到该公司的在招
岗。本探针是关于**想在品牌主页逐页抓满全部岗**（搜索结果物理上限内的全部不够时）
需要先摸清的 BOSS 品牌页结构——搜索命中、品牌 id 字段名、品牌页 URL、在招列表翻页
接口。这些离线猜不出来，且 BOSS 结构会变，所以探针只负责**收集证据**不做假设。

目前是第一阶段，聚焦搜索侧证据：
  1. query=<公司名> 搜索一次，dump 第一个命中 job 的完整 dict ——
     从这里认 brandId / 品牌页 url / 公司名 的字段名。
  2. 列出"看起来像品牌标识"的候选键，供人核对。
拿到真实字段后，才据此补第二阶段：进品牌页 dump 在招列表接口，做「品牌页逐页抓满」
的精确增强。

用法:
    python scripts/stages/company_probe.py "<公司名>" [<城市>]
"""
import argparse
import json
import os
import re
import sys
import urllib.parse

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SCRIPTS)

from DrissionPage import WebPage                                  # noqa: E402
from boss_crawler.config import co                                # noqa: E402
from boss_crawler.auth import check_login_status                  # noqa: E402
from boss_crawler.data_loader import load_city_data, find_cities_by_name  # noqa: E402

PROBE_URL = 'https://www.zhipin.com/web/geek/jobs'


def _brand_candidates(job):
    """从单个 job dict 里挑出"可能是品牌标识"的候选键。

    规则故意放得很宽：键名含 brand/com/company/id、或键名含"公司"、
    或值像 zhipin.org 的品牌页 url、或值是纯长数字 id。产出给人在终端上核对，
    不自动下结论。
    """
    cands = []
    for k, v in job.items():
        vs = str(v)[:80]
        if re.search(r'brand|comId|company|gongsir|brandId|com_id|nullUrl', k, re.I):
            cands.append((k, vs))
        elif str(k).find('公司') >= 0:
            cands.append((k, vs))
        elif re.fullmatch(r'\d{3,}', str(v)) and re.search(r'id|code', k, re.I):
            cands.append((k, vs))
        elif 'zhipin.com' in vs or 'gongsir' in vs:
            cands.append((k, vs))
    return cands


def _search(dp, query, city_code):
    """跑一次公司名搜索，返回第一个命中 job，或 None。"""
    url = '%s?city=%s&query=%s' % (PROBE_URL, city_code, urllib.parse.quote(query))
    print('\n[搜索] %s' % url)
    dp.get(url)
    dp.listen.start('zpgeek/search/joblist.json')
    try:
        dp.scroll.to_bottom()
        r = dp.listen.wait(timeout=8)
    finally:
        dp.listen.stop()
    if not r:
        print('\n[搜索] 未捕获到 joblist.json（无结果或接口变了）。')
        return None
    job_list = r.response.body.get('zpData', {}).get('jobList', [])
    if not job_list:
        print('\n[搜索] 返回空 jobList。')
        return None
    return job_list[0]


def main():
    for _stream in (sys.stdout, sys.stderr):
        _stream.reconfigure(encoding='utf-8', errors='replace')

    ap = argparse.ArgumentParser(description='公司定向结构探针（第一段：搜索侧证据）')
    ap.add_argument('query', help='公司名')
    ap.add_argument('city', nargs='?', default='全国', help='城市名（默认全国）')
    args = ap.parse_args()

    dp = WebPage(chromium_options=co)
    try:
        dp.get(PROBE_URL)
        if not check_login_status(dp):
            print('\n[LOGIN_NEEDED] 未登录。请先登录后再跑探针：')
            print('  python scripts/stages/boss_post_interactive.py --ensure-login')
            return 1

        city_data = load_city_data()
        found = find_cities_by_name(city_data, [args.city])
        code = found[0][1] if found else '100010000'
        if not found:
            print('\n[警告] 城市 %s 未匹配，改用全国代码 %s' % (args.city, code))

        job = _search(dp, args.query, code)
        if job is None:
            print('\n[结论] 没搜到该公司的岗位 —— 品牌识别证据不足。'
                  '换一个确定有在招职位的公司名再试。')
            return 1

        print('\n[1/2] 搜索结果第一个命中 job 的完整字段（认 brandId / 品牌页 url 用）：')
        print(json.dumps(job, ensure_ascii=False, indent=2))

        cands = _brand_candidates(job)
        print('\n[2/2] 看起来像品牌标识的候选键：')
        if not cands:
            print('  （没认出来 —— 上面的完整 dump 里以下字段名随手可查）')
        for k, v in cands:
            print('   %-28s = %s' % (k, v))

        print('\n[说明] 先把上面 1 个完整 job + 候选键贴出来，人就能确定：')
        print('  · 哪几个键是 brandId / 品牌名 / 品牌页 url')
        print('  · 品牌页 url 长什么样（gongsir/… 还是别的）')
        print('拿到这些后再补探针第二段：进品牌页 dump 在招列表翻页接口。')
        return 0
    finally:
        try:
            dp.quit()
        except Exception:
            pass


if __name__ == '__main__':
    sys.exit(main())