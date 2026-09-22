"""投递审计日志与历史记录账本模块。

负责在投递过程中以 JSON Lines 格式追加写入详细事件流，
并在投递成功后同步更新全局已投递历史库，避免后续任务产生重复投递。
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


class Ledger:
    """投递工作流记账与审计日志管理器。"""

    def __init__(self, run_dir: str):
        """初始化账本实例。
        
        Args:
            run_dir: 当前批次运行输出目录，事件日志将保存在该目录下的 delivery_workflow.jsonl 中。
        """
        self.run_dir = run_dir
        self.log_path = os.path.join(run_dir, 'delivery_workflow.jsonl')
        self.history_path = os.path.join(os.path.dirname(run_dir), 'applied_history.json')

    def event(self, **data: Any) -> None:
        """追加记录一条审计事件到 jsonl 日志文件。
        
        自动补充当前本地时间戳（ISO 格式，精确到秒）。
        
        Args:
            **data: 事件键值对数据（例如 event, status, company, stage, error 等）。
        """
        os.makedirs(self.run_dir, exist_ok=True)
        data.setdefault('time', datetime.now().isoformat(timespec='seconds'))
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

    def success(self, job: Dict[str, Any], greeting: str, image_path: Optional[str]) -> None:
        """记录岗位投递成功事件，并同步持久化到全局已投递历史库。
        
        若为测试链接（以 https://example.test/ 开头），则仅记录日志而不污染真实历史记录库。
        
        Args:
            job: 原始岗位数据字典。
            greeting: 实际发送的打招呼语。
            image_path: 发送的简历图片路径（如有）。
        """
        # 记录本次批次的本地 JSONL 审计事件
        self.event(event='applied', status='applied', job=job, greeting_sent=True, image_sent=bool(image_path))
        
        link = str(job.get('link') or job.get('url') or '')
        # 忽略测试用的 Mock 链接，不写入正式历史库
        if link.startswith('https://example.test/'):
            return
            
        import sys
        # 动态将 scripts 根目录加入模块搜索路径以导入 resume_matcher
        scripts_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if scripts_root not in sys.path:
            sys.path.insert(0, scripts_root)
            
        from resume_matcher.history import record_applied_job
        
        # 规范化岗位关键字段并记录至全局历史
        normalized = dict(job)
        normalized['link'] = normalized.get('link') or normalized.get('url') or ''
        normalized['position'] = normalized.get('position') or normalized.get('title') or ''
        record_applied_job(normalized, status='applied', greeting=greeting, image=image_path, run_dir=self.run_dir)

