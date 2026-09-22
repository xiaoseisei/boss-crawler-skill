# -*- coding: utf-8 -*-
import json, os, time
from resume_matcher.history import record_applied_job

job = {
    'company': '靖安科技',
    'position': 'FDE 全栈工程师',
    'link': 'https://www.zhipin.com/job_detail/980df8ecf473153a0nN62NW6GFFR.html',
    'key': '靖安科技__FDE 全栈工程师'
}

record_applied_job(job, status='already_communicated', greeting='王昊阳历史沟通', image='', run_dir='assets/2026-09-18_11-31-40_fde_agent_sme')
print("Recorded #26 靖安科技 as already_communicated.")
