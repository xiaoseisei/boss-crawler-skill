#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""全局持久化投递历史记录管理（assets/applied_history.json）。

记录所有已成功投递的岗位信息，支持：
1. 跨轮次持久化存储投递历史（时间、公司、岗位、链接、招呼语等）
2. 快速判断某岗位是否已投递过（按链接 link 或 公司+岗位 组合去重）
3. 提供已投递链接集合，供爬虫和匹配阶段快速去重，防止二次投递。
"""

import json
import os
import time
from typing import Any, Dict, List, Optional, Set, Tuple

_SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HISTORY_FILE = os.path.join(_SKILL_ROOT, 'assets', 'applied_history.json')


def get_history_file() -> str:
    return HISTORY_FILE


def load_applied_history() -> Dict[str, Any]:
    """读取已投递历史账本。若文件不存在则初始化空结构。"""
    if not os.path.exists(HISTORY_FILE):
        return {
            'updated_at': '',
            'total_applied': 0,
            'applied_jobs': [],
            'applied_links': [],
            'applied_keys': []
        }
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not isinstance(data, dict):
                data = {}
            data.setdefault('applied_jobs', [])
            data.setdefault('applied_links', [])
            data.setdefault('applied_keys', [])
            return data
    except Exception as exc:
        print(f"⚠️ 读取已投递历史记录失败 ({exc})，使用空记录")
        return {
            'updated_at': '',
            'total_applied': 0,
            'applied_jobs': [],
            'applied_links': [],
            'applied_keys': []
        }


def save_applied_history(history: Dict[str, Any]) -> None:
    """持久化保存投递历史。"""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    history['updated_at'] = time.strftime('%Y-%m-%d %H:%M:%S')
    history['total_applied'] = len(history.get('applied_jobs', []))
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def get_applied_links() -> Set[str]:
    """获取所有已投递过的链接集合。"""
    hist = load_applied_history()
    return set(hist.get('applied_links', []))


def make_job_key(job: Dict[str, Any]) -> str:
    company = str(job.get('公司') or job.get('company') or '').strip()
    position = str(job.get('职位') or job.get('position') or '').strip()
    return f"{company}__{position}"


def is_job_applied(job: Dict[str, Any], history: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """检查某个岗位是否已投递过。

    Returns:
        (True, record) 如果已投递过；否则 (False, None)
    """
    if history is None:
        history = load_applied_history()

    link = (job.get('link') or '').strip()
    if link and link in history.get('applied_links', []):
        for item in history.get('applied_jobs', []):
            if item.get('link') == link:
                return True, item
        return True, {'link': link}

    key = make_job_key(job)
    if key and key != '__' and key in history.get('applied_keys', []):
        for item in history.get('applied_jobs', []):
            if item.get('key') == key:
                return True, item
        return True, {'key': key}

    return False, None


def record_applied_job(job: Dict[str, Any], status: str = 'applied',
                       greeting: Optional[str] = None,
                       image: Optional[str] = None,
                       run_dir: Optional[str] = None) -> None:
    """记录一次成功的岗位投递。"""
    history = load_applied_history()
    link = (job.get('link') or '').strip()
    key = make_job_key(job)

    already, _ = is_job_applied(job, history)
    if already:
        return

    record = {
        'company': job.get('公司') or job.get('company') or '未知',
        'position': job.get('职位') or job.get('position') or '未知',
        'city': job.get('城市') or job.get('city') or '',
        'salary': job.get('薪资') or job.get('salary') or '',
        'link': link,
        'key': key,
        'applied_at': time.strftime('%Y-%m-%d %H:%M:%S'),
        'status': status,
        'greeting': greeting or '',
        'image': image or '',
        'run_dir': run_dir or ''
    }

    history['applied_jobs'].append(record)
    if link and link not in history['applied_links']:
        history['applied_links'].append(link)
    if key and key != '__' and key not in history['applied_keys']:
        history['applied_keys'].append(key)

    save_applied_history(history)
