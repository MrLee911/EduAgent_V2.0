# Query Rewriter：LLM 改写学生口语化查询 → 精炼检索语句
# 对应文档：S2 Pattern 3, 06 §4.1.1

from langchain_core.messages import SystemMessage, HumanMessage

QUERY_REWRITE_PROMPT = """
将以下学生提出的口语化问题，改写为用于知识库检索的精炼查询语句。

要求：
1. 去除口语化表达（"那个""就是""怎么说呢"等）
2. 提取核心概念和关键词
3. 长度控制在 30 字以内
4. 如果问题本身已经很精炼，直接返回原问题
5. 只返回改写后的查询文本，不要加任何解释

学生问题：{question}
"""


async def rewrite_query(question: str, llm) -> str:
    """
    用 LLM 改写查询（使用轻量模型降低成本）。

    此函数在 LangGraph 的 rewrite_query 节点中调用。
    推荐轻量模型：gpt-4o-mini / deepseek-chat / qwen-turbo。

    Args:
        question: 学生的原始问题
        llm: LLM 实例（轻量模型）

    Returns:
        改写后的查询语句
    """
    messages = [
        SystemMessage(content="你是一个查询改写助手。只返回改写后的查询文本。"),
        HumanMessage(content=QUERY_REWRITE_PROMPT.format(question=question)),
    ]

    try:
        response = await llm.ainvoke(messages)
        rewritten = response.content.strip()

        # 安全检查：改写结果不能为空或过短
        if not rewritten or len(rewritten) < 2:
            return question  # fallback 到原问题

        return rewritten
    except Exception:
        # LLM 改写失败 → fallback 到原问题
        return question
