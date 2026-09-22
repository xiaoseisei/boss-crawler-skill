import os
import json

candidates = [
    {
        'idx': 1,
        'company': '京东集团',
        'position': '多模态大模型算法工程师',
        'link': 'https://www.zhipin.com/job_detail/f2a78cfeb79282500nN_2NW4EVdS.html',
        'image': 'assets/2026-09-18_00-21-59/deliver/#26-京东集团-多模态大模型算法工程师/夏子聪-多模态大模型算法工程师.png',
        'run_dir': 'assets/2026-09-18_00-21-59',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的多模态大模型算法工程师实习岗位。"
            "我具备大模型微调与多模态质检落地实践：曾完成 Qwen3 模型 LoRA 微调及多模态 VLM 内容校验；"
            "同时主导开发 GraphRAG 智能问答系统，将长文本上下文引用准确率做到 97.5%，具备数模国奖扎实算法底子与 Python 工程能力。"
            "附件已上传针对岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        )
    },
    {
        'idx': 2,
        'company': '阿里巴巴集团',
        'position': 'AI应用研发工程师',
        'link': 'https://www.zhipin.com/job_detail/daa4df2b05edd1460nZ53Nq9ElpQ.html',
        'image': 'assets/2026-09-18_10-17-37_batch2/deliver/#24-阿里巴巴集团-AI应用研发工程师/夏子聪-AI应用研发工程师.png',
        'run_dir': 'assets/2026-09-18_10-17-37_batch2',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司在武汉的 AI 应用研发工程师岗位。"
            "我专注于大模型应用研发与智能体系统构建：主导开发的 EduGraph-RAG 系统，通过知识图谱与混合召回将复杂对话检索准确率提升至 97.5%、首字响应低至 0.82 秒；"
            "并基于 FastAPI 与 LangGraph 实现了多 Agent 协作工作流。熟练掌握 Python 全栈，代码严谨规范。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        )
    },
    {
        'idx': 3,
        'company': '百度',
        'position': '大模型应用研发实习生',
        'link': 'https://www.zhipin.com/job_detail/52538183186259050nB42t6-EVRY.html',
        'image': 'assets/2026-09-18_10-17-37_batch2/deliver/#3-百度-大模型应用研发实习生/夏子聪-大模型应用研发实习生.png',
        'run_dir': 'assets/2026-09-18_10-17-37_batch2',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的大模型应用研发实习生岗位。"
            "我深耕大模型 Agent 与工程化落地：熟练运用 LangGraph 搭建多智能体协同流水线与任务反思质检机制；"
            "在 GraphRAG 项目中攻克了长对话上下文精准引用的难题，实现 97.5% 引用精度与低延迟响应。具备扎实的 Python 与大模型调用封装能力。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        )
    },
    {
        'idx': 4,
        'company': 'VAST',
        'position': 'AI Agent 开发实习生（Intern）',
        'link': 'https://www.zhipin.com/job_detail/13769c99986b16860nF93t61GFdX.html',
        'image': 'assets/2026-09-18_10-17-37_batch2/deliver/#4-VAST-AI Agent 开发实习生（Intern）/夏子聪-AI Agent 开发实习生（Intern）.png',
        'run_dir': 'assets/2026-09-18_10-17-37_batch2',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是自动化专业本科生夏子聪，求职贵司的 AI Agent 开发实习生（Intern）岗位。"
            "我专注智能体架构设计与工程化交付：基于 FastAPI 与 LangGraph 实现了包含确定性校验、安全沙箱和多阶段流水线的场景生成 Agent 平台；"
            "同时具备 GraphRAG 知识图谱检索研发经验。熟练使用 Python，对生成式 AI 与 Agent 前沿探索充满热情。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的审阅与评估。非常期待能有机会与您进一步沟通！"
        )
    },
    {
        'idx': 5,
        'company': '多益网络',
        'position': 'AI应用开发工程师【27届校招】',
        'link': 'https://www.zhipin.com/job_detail/c1ad802927e57c6b0nB42921EVNW.html',
        'image': 'assets/2026-09-18_10-17-37_batch2/deliver/#16-多益网络-AI应用开发工程师【27届校招】/夏子聪-AI应用开发工程师【27届校招】.png',
        'run_dir': 'assets/2026-09-18_10-17-37_batch2',
        'greeting': (
            "【随时到岗/可实习6个月/每周5天】您好！我是2027届自动化专业本科生夏子聪，求职贵司的 AI 应用开发工程师【27届校招】岗位。"
            "我具备扎实的 AI 系统开发功底：独立主导过 GraphRAG 智能问答系统，将复杂长对话引用精度做到 97.5%；"
            "并设计过多智能体协同流水线与安全沙箱执行环境。熟练掌握 Python 与主流框架，逻辑严谨，非常契合校招直通与转正发展预期。"
            "附件已上传针对贵司岗位定制的简历长图，诚盼您的查阅与评估。非常期待能有机会与您进一步沟通！"
        )
    }
]

print("Verifying target candidates:")
all_ok = True
for c in candidates:
    abs_img = os.path.abspath(c['image'])
    exists = os.path.exists(abs_img)
    size = os.path.getsize(abs_img) if exists else 0
    c['image'] = abs_img
    print(f"[{c['company']}] {c['position']} -> Exists: {exists} ({size} B)")
    if not exists:
        all_ok = False

with open('assets/today_top5_batch.json', 'w', encoding='utf-8') as f:
    json.dump(candidates, f, ensure_ascii=False, indent=2)

print(f"\nAll assets OK: {all_ok}")
