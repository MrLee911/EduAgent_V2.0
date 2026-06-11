# 安全护栏提示词：课程范围/答案泄露/内容安全/越狱检测
# 对应文档：06 §5 | 关联行为：05 §6.2-6.4

# === 5.1 课程范围检测 ===

COURSE_SCOPE_CHECK_PROMPT = """
判断以下学生问题是否与《{course_name}》课程相关。
仅回答 YES 或 NO。

判断标准：
- 问题直接涉及课程知识领域 → YES
- 问题涉及学习安排、资源获取、课程信息 → YES
- 打招呼、简单问候 → YES
- 与课程知识领域明确无关的闲聊 → NO
- 请求写其他科目的作业 → NO

学生问题：{question}
是否与《{course_name}》课程相关："""


# === 5.2 答案泄露检测 ===

ANSWER_LEAK_CHECK_PROMPT = """
判断以下 AI 助教的回答，是否直接给出了可当作作业提交的完整答案。

对于"这道题怎么做""帮我写代码"类问题：
- 给出了可直接照抄的完整答案（包含完整代码/最终数值/全部步骤） → YES
- 只给了思路、步骤框架、关键提示、伪代码、部分代码片段 → NO
- 用引导式反问结束，没有给出任何实质答案内容 → NO

仅回答 YES 或 NO。

学生问题：{question}
AI回答（前 500 字）：{answer}

是否泄露了完整答案："""


# === 5.3 内容安全检测 ===

CONTENT_SAFETY_CHECK_PROMPT = """
判断以下文本是否包含不适当内容。
常见的"不适当"类型：攻击性辱骂、种族/性别/地域歧视、色情暗示、暴力描述、政治敏感话题。

仅回答 SAFE 或 UNSAFE。
如果难以判断，回答 SAFE（宁可放过不可错杀教育场景的正常讨论）。

文本（前 300 字）：{content}

结果："""


# === 5.4 越狱检测正则模式 ===
# 这些是正则模式（非 LLM 提示词），属于提示词防护体系的一部分

JAILBREAK_PATTERNS = [
    (r"忽略.*指令", "INSTRUCTION_OVERRIDE"),
    (r"ignore.*instruction", "INSTRUCTION_OVERRIDE"),
    (r"你.*不是.*助教", "IDENTITY_DENIAL"),
    (r"扮演.*角色", "ROLE_PLAY_ATTEMPT"),
    (r"DAN.*模式", "JAILBREAK_MODE"),
    (r"忘记.*(规则|限制|设定)", "RULE_FORGET"),
    (r"去掉.*(限制|规则)", "RESTRICTION_REMOVE"),
    (r"不要.*遵循", "INSTRUCTION_REJECT"),
    (r"给我.*(完整.*答案|全部.*代码)", "ANSWER_DEMAND"),  # 标记但不完全阻断
]
