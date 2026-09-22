"""纯观察者函数模块。

负责将来自浏览器 DOM 提取的原始数据解析并转换为标准化模型，
提供不产生任何副作用的只读状态判断与文本特征匹配工具函数。
"""
from typing import Any, Iterable, List
from .models import Message


def normalize_messages(raw: Iterable[Any]) -> List[Message]:
    """将多种异构格式的消息数据转换为标准的 Message 对象列表。
    
    支持传入已有的 Message 实例、字典对象（如 CDP JS 返回的 JSON 字典）或具有相应属性的 Python 对象。
    
    Args:
        raw: 原始消息数据集合，可以为列表或迭代器。
        
    Returns:
        List[Message]: 标准化后的 Message 对象列表。
    """
    out = []
    for item in raw or []:
        if isinstance(item, Message):
            out.append(item)
            continue
        if isinstance(item, dict):
            # 处理 JS 注入提取的字典结构
            out.append(Message(
                text=str(item.get('text') or ''),
                kind=str(item.get('kind') or 'text'),
                mine=bool(item.get('mine')),
                has_image=bool(item.get('has_image') or item.get('image'))
            ))
        else:
            # 处理具有相应属性的普通对象
            out.append(Message(
                text=str(getattr(item, 'text', '') or ''),
                mine=bool(getattr(item, 'mine', False)),
                has_image=bool(getattr(item, 'has_image', False))
            ))
    return out


def classify_chat_button(text: str) -> str:
    """分类 BOSS 职位详情页的沟通按钮状态。
    
    根据按钮文本关键字判断当前岗位的可沟通状态：
    - 'already_communicated': 包含“继续沟通”、“已沟通”、“已投递”，代表该岗位历史已发起过会话；
    - 'start': 包含“立即沟通”或“沟通”，代表新岗位，可以发起初次投递；
    - 'offline': 按钮文本为空或为其他异常状态（如岗位已下线、招聘已停止）。
    
    Args:
        text: 从详情页按钮提取的文本字符串。
        
    Returns:
        str: 按钮分类标识 ('offline' | 'already_communicated' | 'start')。
    """
    value = (text or '').strip()
    if not value:
        return 'offline'
    if any(x in value for x in ('继续沟通', '已沟通', '已投递')):
        return 'already_communicated'
    if '立即沟通' in value or '沟通' in value:
        return 'start'
    return 'offline'


def mine_text_messages(messages: Iterable[Any]) -> List[Message]:
    """提取消息列表中所有由我方（求职者）发送且不包含图片的纯文本消息。
    
    用于后续与打招呼语进行送达与内容比对。
    
    Args:
        messages: 原始消息列表或 Message 列表。
        
    Returns:
        List[Message]: 我方发送的非空纯文本消息列表。
    """
    return [m for m in normalize_messages(messages) if m.mine and not m.has_image and m.text.strip()]


def has_matching_greeting(messages: Iterable[Any], expected: str) -> bool:
    """检查历史消息中是否已经存在匹配的打招呼语。
    
    通过提取预期打招呼语的前 14 个非空白字符作为特征探针（probe），
    与所有我方纯文本消息做模糊包含匹配，防止重复发送招呼语。
    
    Args:
        messages: 原始消息列表或 Message 列表。
        expected: 预期的打招呼语正文。
        
    Returns:
        bool: 若历史消息中已包含匹配文本则返回 True，否则返回 False。
    """
    probe = ''.join((expected or '').split())[:14]
    return bool(probe) and any(probe in ''.join(m.text.split()) for m in mine_text_messages(messages))


def has_resume_image(messages: Iterable[Any]) -> bool:
    """检查当前会话消息记录中是否已包含我方发送的简历图片。
    
    Args:
        messages: 原始消息列表或 Message 列表。
        
    Returns:
        bool: 当且仅当我方已发出包含真实图片的消息时返回 True。
    """
    return any(m.has_image and m.mine for m in normalize_messages(messages))

