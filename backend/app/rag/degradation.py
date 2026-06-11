# 三级降级管理器：FULL → RAG_ONLY → UNAVAILABLE
# 对应文档：S2 Pattern 6, 05 §9.1

from enum import Enum
from typing import Optional

from .retriever import Retriever
from .post_processor import format_knowledge_for_prompt, format_sources_for_db


class DegradationLevel(Enum):
    """降级层级"""
    FULL = "full"              # RAG + LLM 完整功能
    RAG_ONLY = "rag_only"      # 仅 RAG（LLM 不可用时返回原文片段）
    UNAVAILABLE = "unavailable"  # 服务完全不可用


async def execute_with_degradation(
    query: str,
    course_id: str,
    llm,  # LLM 实例
    top_k: int = 5,
    similarity_threshold: float = 0.6,
) -> dict:
    """
    带降级的 RAG 执行。

    降级逻辑（三层）：
    Layer 1: RAG 检索 + LLM 生成完整回答
    Layer 2: LLM 不可用 → 仅返回 RAG 检索原文片段
    Layer 3: ChromaDB 不可用 → 返回固定提示

    Returns:
        {
            "answer": str,
            "sources": list[dict],
            "level": DegradationLevel,
            "warning": Optional[str],
        }
    """
    retriever = Retriever(course_id)

    # === Layer 1: 完整 RAG + LLM ===
    try:
        results = await retriever.search(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )

        if not results:
            context = "（知识库中未找到直接相关内容）"
            warning = "以下回答基于模型知识，未在课程资料中找到直接对应内容。"
        else:
            context = format_knowledge_for_prompt(results)
            warning = None

        try:
            answer = await llm.ainvoke_with_context(query, context)
            return {
                "answer": answer,
                "sources": format_sources_for_db(results) if results else [],
                "level": DegradationLevel.FULL,
                "warning": warning,
            }
        except (TimeoutError, ConnectionError, Exception):
            # LLM 不可用 → 降级到 Layer 2
            pass

    except Exception as e:
        # ChromaDB 或 Embedding 不可用 → 直接跳到 Layer 3
        if _is_vector_db_error(e):
            return _layer3_response()
        raise

    # === Layer 2: 仅 RAG（LLM 不可用） ===
    try:
        results = await retriever.search(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
        )
        if results:
            return {
                "answer": _format_rag_only_response(results),
                "sources": format_sources_for_db(results),
                "level": DegradationLevel.RAG_ONLY,
                "warning": "AI 服务暂时降级，以下为知识库直接检索结果。",
            }
    except Exception:
        pass

    # === Layer 3: 服务不可用 ===
    return _layer3_response()


def _format_rag_only_response(results: list[dict]) -> str:
    """Layer 2 降级：仅返回检索到的原文片段"""
    blocks = ["⚠️ AI 服务暂时不可用，以下是知识库中相关度最高的内容：\n"]
    for i, r in enumerate(results[:3], 1):
        meta = r.get("metadata", {})
        file_name = meta.get("file_name", "未知文件")
        content = r.get("content", "")[:500]
        blocks.append(f"**{i}.** [{file_name}] {content}")
    return "\n\n".join(blocks)


def _layer3_response() -> dict:
    """Layer 3：服务完全不可用"""
    return {
        "answer": "智能体服务暂时不可用，请稍后重试。",
        "sources": [],
        "level": DegradationLevel.UNAVAILABLE,
        "warning": "知识库和 AI 服务均不可用。",
    }


def _is_vector_db_error(e: Exception) -> bool:
    """判断是否为 ChromaDB / Embedding 相关错误"""
    error_str = str(e).lower()
    keywords = [
        "chromadb", "chroma", "connection refused",
        "could not connect", "timeout",
        "embedding", "vector store",
    ]
    return any(kw in error_str for kw in keywords)
