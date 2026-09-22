"""独立、无截图依赖的招聘投递自动化工作流模块。

本模块提供基于 DOM 与 CDP（Chrome DevTools Protocol）的稳健投递方案：
- 采用确定性的 DOM/接口探测替代脆弱的视觉/截图比对；
- 具备完善的投递状态机、幂等性校验、会话身份证明及防并发机制；
- 暴露标准化的数据模型、异常体系与执行器接口。
"""

# 导出核心异常类型，便于上层调用方进行精确捕获与风控处理
from .exceptions import (
    DeliveryWorkflowError, EnvironmentNotReadyError, DailyLimitReachedError,
    GreetingSendFailedError, ImageUploadFailedError, OverlayBlockedError,
)
# 导出核心数据结构，包括岗位上下文、执行结果及消息快照
from .models import JobContext, JobResult, Message, ChatSnapshot

__all__ = [
    # 异常体系
    'DeliveryWorkflowError',
    'EnvironmentNotReadyError',
    'DailyLimitReachedError',
    'GreetingSendFailedError',
    'ImageUploadFailedError',
    'OverlayBlockedError',
    # 数据模型
    'JobContext',
    'JobResult',
    'Message',
    'ChatSnapshot',
]

