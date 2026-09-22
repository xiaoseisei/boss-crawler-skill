import json
import uuid
from pathlib import Path

from scripts.delivery_workflow.assertions import greeting_sent, assert_image_sent
from scripts.delivery_workflow.exceptions import ImageUploadFailedError
from scripts.delivery_workflow.models import Message
from scripts.delivery_workflow.observers import has_resume_image
from scripts.delivery_workflow.runner import run_jobs


class FakeOps:
    def __init__(self, mode='ok'):
        self.mode = mode; self.calls = []; self.messages = []
    def open_job_detail(self, url): self.calls.append(('open', url))
    def read_job_chat_button(self): return '立即沟通'
    def click_start_chat(self): self.calls.append(('click_chat',))
    def read_daily_limit_dialog(self): return self.mode == 'limit'
    def open_chat_workspace(self): self.calls.append(('workspace',))
    def remove_overlay(self): self.calls.append(('overlay',)); return True
    def select_chat_session(self, company='', position=''): self.calls.append(('select', company, position)); self.identity = company + ' ' + position
    def read_active_chat_identity(self): return getattr(self, 'identity', '甲 后端')
    def read_messages(self): return list(self.messages)
    def read_input_value(self): return '' if self.messages else 'draft'
    def focus_input(self): self.calls.append(('focus',))
    def fill_input(self, text): self.calls.append(('fill', text))
    def press_enter(self):
        self.calls.append(('enter',))
        if self.mode != 'greeting_fail': self.messages.append(Message(text='你好，看到岗位和我的经历比较匹配', mine=True))
    def click_send_button(self):
        self.calls.append(('send',))
        if self.mode == 'greeting_retry': self.messages.append(Message(text='你好，看到岗位和我的经历比较匹配', mine=True))
    def upload_file(self, path):
        self.calls.append(('upload', path))
        if self.mode != 'image_fail': self.messages.append(Message(has_image=True, mine=True))


def job(suffix='a'): return {'link': 'https://example.test/job-' + suffix, 'company': '甲-' + suffix, 'position': '后端-' + suffix, 'greeting': '你好，看到岗位和我的经历比较匹配'}


def test_greeting_requires_clear_input_and_new_message():
    assert greeting_sent([], [Message(text='你好，看到岗位和我的经历比较匹配', mine=True)], '', '你好，看到岗位和我的经历比较匹配')
    assert not greeting_sent([], [], 'draft', '你好')


def test_greeting_failure_does_not_upload(tmp_path):
    ops = FakeOps('greeting_fail')
    result = run_jobs(ops, [job('fail')], str(tmp_path), image_path='resume.png')
    assert result[0].status == 'failed'
    assert not any(c[0] == 'upload' for c in ops.calls)


def test_success_uploads_only_after_greeting(tmp_path):
    ops = FakeOps()
    result = run_jobs(ops, [job('success-' + uuid.uuid4().hex)], str(tmp_path), image_path='resume.png')
    assert result[0].status == 'applied'
    names = [c[0] for c in ops.calls]
    assert names.index('enter') < names.index('upload')
    assert (tmp_path / 'delivery_workflow.jsonl').exists()


def test_daily_limit_stops_batch(tmp_path):
    ops = FakeOps('limit')
    result = run_jobs(ops, [job('limit1'), job('limit2')], str(tmp_path))
    assert len(result) == 1 and result[0].status == 'daily_limit'


def test_system_card_or_boss_image_does_not_trigger_false_positive():
    system_card_msgs = [
        Message(text="系统卡片：双方意向匹配度较高", mine=False, has_image=True),
        Message(text="BOSS消息：请发简历", mine=False, has_image=False),
    ]
    # 验证系统卡片或BOSS消息中的图片不会被视作已发送简历图片
    assert not has_resume_image(system_card_msgs)

    # 验证 assert_image_sent 不会因出现系统卡片图片而误判为成功
    try:
        assert_image_sent([], system_card_msgs)
        assert False, "Should have raised ImageUploadFailedError"
    except ImageUploadFailedError:
        pass

    # 验证我方发送真实图片后能正常识别与断言
    my_image_msgs = list(system_card_msgs) + [Message(text="", mine=True, has_image=True)]
    assert has_resume_image(my_image_msgs)
    assert_image_sent(system_card_msgs, my_image_msgs)


