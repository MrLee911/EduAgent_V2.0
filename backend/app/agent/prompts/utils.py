# 提示词变量注入工具：PromptContext + inject_variables + 知识库上下文格式化
# 对应文档：06 §2.2-2.4

import re
from typing import Dict, Any, Optional
from datetime import datetime


class PromptContext:
    """
    提示词上下文管理。
    负责收集和格式化所有 prompt 变量，按需从 DB/Redis/RAG 拉取。
    """

    def __init__(self, course_id: str, user_id: str = ""):
        self.course_id = course_id
        self.user_id = user_id
        self._cache: Dict[str, Any] = {}

    async def build(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        构建完整的变量字典。
        按需从 DB/Redis/RAG 拉取，已拉取的变量缓存到 _cache。
        """
        ctx = {
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "course_id": self.course_id,
            "user_role": await self._resolve_role(),
            "user_name": await self._resolve_display_name(),
            "course_name": await self._resolve_course_name(),
        }
        if extra:
            ctx.update(extra)
        return ctx

    async def with_rag(self, query: str, top_k: int = 5) -> Dict[str, str]:
        """追加 RAG 检索结果到上下文（供 QA/Task Agent 使用）"""
        ctx = await self.build()
        ctx["knowledge_context"] = await self._rag_search(query, top_k)
        return ctx

    async def with_history(self, session_id: str) -> Dict[str, str]:
        """追加对话历史到上下文"""
        ctx = await self.build()
        ctx["conversation_history"] = await self._load_history(session_id)
        return ctx

    # --- 内部方法 ---

    async def _resolve_course_name(self) -> str:
        if "course_name" not in self._cache:
            # SELECT name FROM courses WHERE id = ?
            self._cache["course_name"] = "示例课程"  # TODO: DB 查询
        return self._cache["course_name"]

    async def _resolve_role(self) -> str:
        if "user_role" not in self._cache:
            # SELECT role FROM users WHERE id = ?
            self._cache["user_role"] = "student"
        return self._cache["user_role"]

    async def _resolve_display_name(self) -> str:
        if "user_name" not in self._cache:
            self._cache["user_name"] = "同学"
        return self._cache["user_name"]

    async def _rag_search(self, query: str, top_k: int) -> str:
        from ...rag.retriever import Retriever
        retriever = Retriever(self.course_id)
        results = retriever.search(query=query, top_k=top_k, similarity_threshold=0.6)
        return retriever.format_for_prompt(results)

    async def _load_history(self, session_id: str) -> str:
        from ..memory import ConversationMemory
        memory = ConversationMemory(session_id)
        messages = await memory.get_recent(limit=10)
        return self._format_history(messages)

    @staticmethod
    def _format_history(messages: list) -> str:
        """将对话历史格式化为提示词上下文"""
        if not messages:
            return "（暂无对话历史）"
        lines = []
        for i, msg in enumerate(messages):
            role = "学生" if msg["role"] == "user" else "助教"
            content = msg["content"][:200]  # 截断过长内容
            lines.append(f"[第{i+1}轮] {role}：{content}")
        return "\n".join(lines)


def inject_variables(template: str, ctx: Dict[str, str]) -> str:
    """
    安全注入变量。如果模板中有未提供的占位符，抛出 KeyError。

    用法：
        prompt = inject_variables(QA_SYSTEM_PROMPT, ctx)
    """
    placeholders = set(re.findall(r'\{(\w+)\}', template))
    missing = placeholders - set(ctx.keys())
    if missing:
        raise KeyError(f"模板中存在未注入的变量: {missing}")
    return template.format(**{k: ctx.get(k, "") for k in placeholders})


def format_knowledge_for_prompt(documents: list[dict], max_docs: int = 8) -> str:
    """
    将 RAG 检索结果格式化为 LLM 提示词中的知识上下文。

    Args:
        documents: [{"content": "...", "metadata": {"source": "...", "page": "..."}, "score": 0.85}, ...]
        max_docs: 最多取前 N 条文档
    Returns:
        格式化的知识上下文字符串
    """
    if not documents:
        return "（课程知识库中暂无相关内容）"

    lines = ["## 课程知识库检索结果\n"]
    for i, doc in enumerate(documents[:max_docs], 1):
        source = doc.get("metadata", {}).get("source", "未知来源")
        page = doc.get("metadata", {}).get("page", "")
        score = doc.get("score", 0)
        content = doc.get("content", "")

        source_info = f"来源：{source}"
        if page:
            source_info += f" 第{page}页"
        source_info += f"（相关度：{score:.2f}）"

        lines.append(f"### 参考资料 {i}")
        lines.append(f"{source_info}")
        lines.append(content)
        lines.append("")

    return "\n".join(lines)
