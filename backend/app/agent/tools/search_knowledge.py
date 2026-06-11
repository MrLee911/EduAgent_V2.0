# Tool: search_knowledge — 核心 RAG 检索工具
# 对应文档：05 §3.2

import json
from pydantic import BaseModel, Field
from typing import Optional


class SearchKnowledgeInput(BaseModel):
    """知识库检索参数"""
    query: str = Field(description="检索查询语句（建议用完整的问题或主题描述）")
    top_k: int = Field(default=5, description="返回结果数量，范围 1-10")
    filter_resource_type: Optional[str] = Field(
        default=None,
        description="按资源类型过滤：pdf/docx/pptx/md/txt（不传则不过滤）"
    )


async def search_knowledge(
    query: str,
    top_k: int = 5,
    filter_resource_type: Optional[str] = None,
    course_id: str = ""
) -> str:
    """
    在课程知识库中语义检索相关内容。

    使用场景：
    - 学生提问时，先调用此工具检索相关课件/教材内容
    - 生成任务时，检索相关知识点的基础资料

    返回值是 JSON 字符串，包含匹配的文本片段及其来源信息。
    """
    from ...rag.retriever import Retriever
    retriever = Retriever(course_id)
    results = await retriever.search(
        query=query,
        top_k=top_k,
        resource_type=filter_resource_type,
        similarity_threshold=0.6
    )
    return retriever.format_results(results)
