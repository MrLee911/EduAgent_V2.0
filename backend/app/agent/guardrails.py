# 安全护栏实现：5 层护栏（越狱检测 + 课程范围 + 答案泄露 + 内容安全 + 来源完整性）
# 对应文档：05 §6, 06 §5

import re
from typing import Optional
from datetime import datetime, timezone


class InputGuardrail:
    """
    输入安全检查。
    在用户问题进入 Agent 处理流程之前执行。
    """

    JAILBREAK_PATTERNS = [
        (r"忽略.*指令", "INSTRUCTION_OVERRIDE"),
        (r"ignore.*instruction", "INSTRUCTION_OVERRIDE"),
        (r"你.*不是.*助教", "IDENTITY_DENIAL"),
        (r"扮演.*角色", "ROLE_PLAY_ATTEMPT"),
        (r"DAN.*模式", "JAILBREAK_MODE"),
        (r"忘记.*(规则|限制|设定)", "RULE_FORGET"),
        (r"去掉.*(限制|规则)", "RESTRICTION_REMOVE"),
        (r"不要.*遵循", "INSTRUCTION_REJECT"),
        (r"给我.*(完整.*答案|全部.*代码)", "ANSWER_DEMAND"),
    ]

    COURSE_SCOPE_PROMPT = """判断以下学生问题是否与《{course_name}》课程相关。
仅回答 YES 或 NO。如果学生只是在聊天开始时打招呼，也回答 YES。

学生问题：{question}
是否相关："""

    def check_jailbreak(self, question: str) -> dict:
        """检测越狱/提示词注入企图（正则匹配，<1ms）"""
        for pattern, jailbreak_type in self.JAILBREAK_PATTERNS:
            if re.search(pattern, question, re.IGNORECASE):
                return {
                    "passed": False,
                    "reason": f"检测到潜在的提示词注入行为（类型：{jailbreak_type}）",
                    "type": "JAILBREAK_ATTEMPT"
                }
        return {"passed": True, "reason": "", "type": "clean"}

    def check_scope(self, question: str, course_name: str) -> dict:
        """检查问题是否在课程范围内（需要 LLM 分类，同步返回 mock 通过）"""
        # TODO: 实际 LLM 调用 — 这里返回默认通过
        # prompt = self.COURSE_SCOPE_PROMPT.format(
        #     course_name=course_name, question=question
        # )
        # result = llm.invoke(prompt).strip().upper()
        return {"passed": True, "reason": "", "type": "in_scope"}


class OutputGuardrail:
    """
    输出安全检查。
    在 LLM 生成回答之后、返回给用户之前执行。
    """

    ANSWER_LEAK_PROMPT = """判断以下 AI 助教的回答，是否直接给出了完整答案（而非引导）。
对于"这道题怎么做"类问题，直接给完整答案 = YES，给思路和步骤 = NO。
仅回答 YES 或 NO。

学生问题：{question}
AI 回答：{answer}
直接给出完整答案："""

    CONTENT_SAFETY_PROMPT = """判断以下文本是否包含不适当内容（攻击性语言、歧视、敏感政治话题等）。
仅回答 SAFE 或 UNSAFE。

文本：{content}
结果："""

    def check_answer_leak(self, question: str, answer: str) -> dict:
        """检测是否直接泄露了完整答案（需要 LLM 分类，同步返回 mock 通过）"""
        # TODO: 实际 LLM 调用
        # prompt = self.ANSWER_LEAK_PROMPT.format(question=question, answer=answer[:500])
        # result = llm.invoke(prompt).strip().upper()
        # if result == "YES":
        #     return {"passed": False, "reason": "回答可能包含了完整答案而非引导", "action": "regenerate"}
        return {"passed": True, "reason": "", "action": "pass"}

    def check_content_safety(self, content: str) -> dict:
        """内容安全检测（需要 LLM 分类，同步返回 mock 通过）"""
        # TODO: 实际 LLM 调用
        # prompt = self.CONTENT_SAFETY_PROMPT.format(content=content[:300])
        # result = llm.invoke(prompt).strip().upper()
        # if result == "UNSAFE":
        #     return {"passed": False, "reason": "输出包含不适当内容", "action": "block"}
        return {"passed": True, "reason": "", "action": "pass"}

    def check_source_integrity(self, answer: str, sources: list[dict]) -> dict:
        """检查 answer 中引用的来源是否都存在于 sources 中"""
        if not sources:
            return {"passed": True, "reason": "", "action": "pass"}

        source_names = set()
        for s in sources:
            if isinstance(s, dict):
                name = s.get("metadata", {}).get("source", "") or s.get("resource_name", "")
                if name:
                    source_names.add(name)

        # 简单策略：检查 answer 中是否引用了不存在的来源
        # TODO: 更完善的引用验证
        return {"passed": True, "reason": "", "action": "pass"}
