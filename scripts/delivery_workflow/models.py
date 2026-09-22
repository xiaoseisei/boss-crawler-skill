"""投递工作流核心数据模型定义。

包含消息实体、聊天状态快照、岗位上下文及投递执行结果等数据类。
所有数据类均采用 dataclass 规范，兼顾易用性与类型安全性。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Message:
    """聊天气泡/消息实体。
    
    Attributes:
        text: 消息正文文本内容。
        kind: 消息类别，如 'text'（文本）或 'image'（图片）。
        mine: 是否由求职者（当前登录用户）发送。
        has_image: 该消息块内是否包含图片内容。
    """
    text: str = ''
    kind: str = 'text'
    mine: bool = False
    has_image: bool = False


@dataclass
class ChatSnapshot:
    """聊天会话界面状态快照。
    
    用于观测某一时间点聊天窗口的整体状态。
    
    Attributes:
        messages: 当前已展示的消息列表。
        input_text: 当前输入框中尚未发送的草稿内容。
        daily_limit: 当前界面是否正显示每日上限相关阻断提示。
    """
    messages: List[Message] = field(default_factory=list)
    input_text: str = ''
    daily_limit: bool = False


@dataclass
class JobContext:
    """单次岗位投递任务的上下文环境。
    
    封装单个岗位的数据、打招呼语文本、简历附件路径及执行序号，
    并提供标准化的字段属性转换（兼容中英文键名）。
    
    Attributes:
        job: 原始岗位数据字典（可能包含 'link', '公司', '职位' 等字段）。
        greeting: 本次投递要发送的打招呼语。
        image_path: 可选的简历图片本地文件路径。
        index: 当前岗位在投递批次中的序号（从 1 开始）。
    """
    job: Dict[str, Any]
    greeting: str
    image_path: Optional[str] = None
    index: int = 0

    @property
    def link(self) -> str:
        """获取标准化的岗位详情页链接。优先取 link，回退取 url。"""
        return str(self.job.get('link') or self.job.get('url') or '')

    @property
    def company(self) -> str:
        """获取标准化的公司名称。兼容中英文键名，缺省为 '未知公司'。"""
        return str(self.job.get('公司') or self.job.get('company') or '未知公司')

    @property
    def position(self) -> str:
        """获取标准化的职位名称。兼容 '职位', 'position', 'title', '岗位' 等键名。"""
        return str(self.job.get('职位') or self.job.get('position') or self.job.get('title') or self.job.get('岗位') or '未知职位')


@dataclass
class JobResult:
    """单次岗位投递的最终执行结果。
    
    记录该岗位的执行状态、中断阶段、耗时及是否发送成功等审计信息。
    
    Attributes:
        index: 岗位批次序号。
        company: 公司名称。
        position: 职位名称。
        status: 投递状态（如 'applied', 'failed', 'skipped', 'daily_limit' 等）。
        stage: 结果终态发生时所在的流水线阶段（如 'precheck', 'history_guard', 'send_greeting', 'audit' 等）。
        error: 异常或错误信息（如有）。
        greeting_sent: 打招呼语是否已确认送达。
        image_sent: 简历图片是否已确认送达。
        retries: 重试次数。
        timings: 各环节性能指标字典（单位：毫秒）。
    """
    index: int
    company: str
    position: str
    status: str
    stage: str
    error: Optional[str] = None
    greeting_sent: bool = False
    image_sent: bool = False
    retries: int = 0
    timings: Dict[str, float] = field(default_factory=dict)

