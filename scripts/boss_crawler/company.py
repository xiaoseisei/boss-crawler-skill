#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
公司定向采集核心
================

给爬虫加第三种模式 `company`：输入公司名 → 定向抓取该公司全部在招岗。

**实现思路——复用已验证的搜索接口，不猜品牌页结构。** BOSS 的品牌页在招列表接口、
返回字段这些离线确定不了（想进品牌页抓"主页上的全部岗"，需要先联网探针校准那张
契约，而这又需要一次登录）。但**搜索接口**（`/web/geek/jobs?query=…`）是现有爬取
已经在用、字段键名已经被 `process_job_list` 证实过的（`brandName` / `salaryDesc` /
`encryptJobId` …）。所以公司模式用 `query=公司全名` 翻页搜索，把返回结果按
`brandName` 精确过滤掉别的公司，就得到该公司的全部在招岗 —— 无需猜任何新接口。

代价是这是"搜索接口物理上限内的全部"（BOSS 搜索对全名公司名通常能翻很多页）；若
某岗位因公司名写法不同而没被这个 query 命中，或候选页数超出 BOSS 搜索分页上限，
就可能漏。绝大多数公司远够用；真要做"品牌主页逐页抓满"，需要契约增强，见
`company_probe.py` 的说明。

每岗的完整详情（JD / HR / 公司简介）由上层在 with_detail 时复用 `crawl_job_details`
回填 —— 公司简介（`公司信息` 列）来自详情接口的 brandComInfo，正好覆盖用户要的
"公司简介"，不需要额外进品牌页。

流程（对每个 公司 × 城市）：
  1. crawl_company_jobs: 搜索翻页 + brandName 过滤 + 复用 process_job_list 写 CSV
  2. （with_detail）crawl_job_details 回填详情
"""
import os
import re
import urllib.parse

from .config import COMPANY_OUTPUT_DIR
from .crawler import _crawl_paginated
from .data_loader import init_csv_file, load_existing_links


def company_output_path(company, city):
    """公司模式的落盘路径：assets/post_data/company/{公司}_{城市}.csv。

    公司/城市名清掉 Windows 文件系统非法字符，避免直接抛 OSError。
    全国模式的 city 传入 '全国'，占位符文件名；行内城市列仍取各岗实际 cityName。
    """
    safe = lambda s: re.sub(r'[\\/:*?"<>|]', '_', s.strip())
    return os.path.join(COMPANY_OUTPUT_DIR, '%s_%s.csv' % (safe(company), safe(city)))


def crawl_company_jobs(dp, company, city_code, file_path, count_limit, existing_links,
                       run_seen=None):
    """
    按公司全名搜索 + 翻页 + brandName 精确过滤，抓该公司的全部在招岗。

    Reuses _crawl_paginated（翻页去重到底判定）并把非本公司的岗位滤掉。
    Returns: (total_processed, total_written, total_skipped, total_run_dups)，与
             execute_crawl_iteration 里每个小桶同构。
    """
    init_csv_file(file_path)
    encoded = urllib.parse.quote(company)
    url = 'https://www.zhipin.com/web/geek/jobs?city=%s&query=%s' % (city_code, encoded)

    def _only_company(job):
        return str(job.get('brandName', '')).strip() == company

    print('  访问: %s' % url)
    return _crawl_paginated(dp, url, file_path, count_limit, existing_links,
                            run_seen, job_filter=_only_company)


def crawl_company(dp, company, city_name, city_code, count_limit, with_detail,
                  detail_existing_links=None):
    """
    单个 公司×城市 的完整采集：搜索过滤翻页 →（可选）详情回填。

    返回统计 dict（与 execute_crawl_iteration 每个小桶同构），供汇总。
    """
    file_path = company_output_path(company, city_name)
    existing_links = load_existing_links(file_path)
    stats = crawl_company_jobs(dp, company, city_code, file_path, count_limit,
                               existing_links)

    if with_detail and stats[1] > 0:   # stats[1] = written
        from .crawler import crawl_job_details
        detail_existing_links = detail_existing_links if detail_existing_links is not None else set()
        crawl_job_details(dp, file_path, detail_existing_links)

    return {
        'total': stats[0],
        'written': stats[1],
        'skipped': stats[2],
        'run_dups': stats[3],
    }