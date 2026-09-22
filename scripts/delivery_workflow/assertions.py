"""投递断言与状态验证模块。

本模块提供确定性的状态断言，用于验证投递各阶段的前置条件与后置效果：
- 遮罩清除断言（assert_overlay_clear）
- 招呼语发送与内容比对断言（assert_greeting_sent）
- 简历图片发送确认断言（assert_image_sent）
不依赖截图或模糊像素比对，直接对 DOM 提取的消息列表和输入框状态进行严格断言。
"""
import re
from typing import Any, Iterable
from .exceptions import GreetingSendFailedError, ImageUploadFailedError, OverlayBlockedError
from .observers import mine_text_messages, normalize_messages


def _norm(text: str) -> str:
    """去除文本中的所有连续空白字符，便于进行严格且抗格式干扰的字符比对。"""
    return re.sub(r'\s+', '', text or '')


def assert_overlay_clear(removed: bool, remaining_blocked: bool = False) -> None:
    """断言聊天工作台区域的遮罩/引导浮层已被清除。
    
    Args:
        removed: 是否成功移除了浮层元素。
        remaining_blocked: 检查后界面是否仍然存在阻挡层。
        
    Raises:
        OverlayBlockedError: 当 remaining_blocked 为 True 时抛出。
    """
    if remaining_blocked:
        raise OverlayBlockedError('聊天区域仍被浮层遮挡')


def greeting_sent(before: Iterable[Any], after: Iterable[Any], input_value: str, expected: str) -> bool:
    """检查打招呼语是否满足“成功送达”的三重确定性条件。
    
    判断依据：
    1. 输入框已被清空（not _norm(input_value)），说明点击发送或回车已被消费；
    2. 我方纯文本消息数量在操作后至少增加 1 条（increased）；
    3. 新增的消息气泡中包含预期打招呼语的前 14 个特征字符（content_ok）。
    
    Args:
        before: 发送前的消息列表。
        after: 发送后的消息列表。
        input_value: 发送操作后当前输入框内的残留文本。
        expected: 预期的打招呼语文本。
        
    Returns:
        bool: 当且仅当上述三项条件同时满足时返回 True。
    """
    before_text = mine_text_messages(before)
    after_text = mine_text_messages(after)
    # 取前 14 个无空白字符作为探针文本
    probe = _norm(expected)[:14]
    increased = len(after_text) >= len(before_text) + 1
    # 仅在新增的消息段内查找是否存在匹配探针
    content_ok = any(probe and probe in _norm(m.text) for m in after_text[len(before_text):])
    return not _norm(input_value) and increased and content_ok


def assert_greeting_sent(before: Iterable[Any], after: Iterable[Any], input_value: str, expected: str) -> None:
    """断言打招呼语已确认送达。
    
    若未满足 greeting_sent 判定条件，则抛出详细的 GreetingSendFailedError 异常，
    其中包含输入框残留文字快照及前后消息量统计，便于追查失败现场。
    
    Args:
        before: 发送前的消息列表。
        after: 发送后的消息列表。
        input_value: 发送操作后当前输入框内的残留文本。
        expected: 预期的打招呼语文本。
        
    Raises:
        GreetingSendFailedError: 打招呼语发送失败或无法证明送达。
    """
    if not greeting_sent(before, after, input_value, expected):
        raise GreetingSendFailedError(
            '输入框未清空或文字气泡未确认送达: input=%r before=%d after=%d after_text=%r' % (
                input_value[:80],
                len(mine_text_messages(before)),
                len(mine_text_messages(after)),
                [m.text[:80] for m in mine_text_messages(after)]
            )
        )


def assert_image_sent(before: Iterable[Any], after: Iterable[Any]) -> None:
    """断言简历图片消息已成功发出并出现在聊天记录中。
    
    通过比对发送前后包含图片的我方消息数量，若 after 阶段的我方图片消息数量大于 before 阶段，
    则判定图片上传成功。
    
    Args:
        before: 上传前的消息列表。
        after: 上传后的消息列表。
        
    Raises:
        ImageUploadFailedError: 未检测到新的我方图片气泡时抛出。
    """
    before_images = sum(m.has_image and m.mine for m in normalize_messages(before))
    after_messages = normalize_messages(after)
    if sum(m.has_image and m.mine for m in after_messages) <= before_images:
        raise ImageUploadFailedError('最新消息未确认包含我方图片')

