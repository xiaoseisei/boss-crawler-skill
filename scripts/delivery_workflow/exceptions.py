"""投递工作流异常体系定义。

提供细粒度的业务与环境异常类型，便于调用者对不同失败原因进行针对性处理
（例如：环境重试、每日上限熔断、单个岗位跳过等）。
"""


class DeliveryWorkflowError(Exception):
    """投递工作流基础异常类。所有工作流自定义异常均继承自该类。"""
    pass


class EnvironmentNotReadyError(DeliveryWorkflowError):
    """运行环境未就绪异常。
    
    通常在 CDP 调试端口不可用、Chrome 无法连接或登录失效时抛出。
    """
    pass


class JobDetailInvalidError(DeliveryWorkflowError):
    """岗位详情数据或链接无效异常。
    
    例如缺少必要链接、链接格式错误或岗位已被下线时抛出。
    """
    pass


class DailyLimitReachedError(DeliveryWorkflowError):
    """触达平台每日沟通上限异常。
    
    检测到平台弹窗或文案提示今日沟通次数已用完时抛出，用于触发工作流熔断退出。
    """
    pass


class OverlayBlockedError(DeliveryWorkflowError):
    """界面被弹窗或遮罩层阻挡异常。
    
    例如提示“下载APP”或全局遮罩无法自动移除导致操作被阻断时抛出。
    """
    pass


class GreetingSendFailedError(DeliveryWorkflowError):
    """打招呼语发送失败异常。
    
    在尝试发送招呼语后，输入框未清空或聊天气泡列表中未找到新发送的匹配消息时抛出。
    """
    pass


class ImageUploadFailedError(DeliveryWorkflowError):
    """简历图片上传/发送失败异常。
    
    触发图片文件上传后，在限定重试次数内聊天记录中未能确认出现新的图片消息时抛出。
    """
    pass


class TargetSessionNotFoundError(DeliveryWorkflowError):
    """目标聊天会话未找到或身份校验失败异常。
    
    点击沟通或在聊天列表中搜索后，无法证明当前选中的聊天窗口属于目标公司/岗位时抛出，
    防止将打招呼语或简历误发给错误的招聘者。
    """
    pass
