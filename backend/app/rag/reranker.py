# 重排序器：BGE-Reranker-v2-m3 精排
# 对应文档：S2 Pattern 4

from typing import List, Optional
from app.config import settings

# 仅当候选结果 ≥ 8 条时启用 Reranker（避免不必要的开销）
RERANK_THRESHOLD = 8

_reranker = None


def _get_reranker():
    """获取/创建 BGE-Reranker 模型实例（单例）"""
    global _reranker
    if _reranker is None:
        from FlagEmbedding import FlagReranker
        _reranker = FlagReranker(
            settings.RERANKER_MODEL,  # "BAAI/bge-reranker-v2-m3"
            use_fp16=True,            # 省显存
        )
    return _reranker


async def rerank_with_bge(
    query: str,
    documents: List[dict],
    top_n: int = 3,
) -> List[dict]:
    """
    用 BGE-Reranker-v2-m3 对检索结果精排。

    仅当候选数 ≥ RERANK_THRESHOLD(8) 时调用，否则直接返回 top_n。

    Args:
        query: 原始查询语句
        documents: 待重排的文档列表 [{content, metadata, score, chunk_id}, ...]
        top_n: 最终返回的文档数

    Returns:
        重排后的 top_n 文档列表
    """
    if len(documents) < RERANK_THRESHOLD:
        # 候选少，MMR 已足够好，跳过 Reranker
        return documents[:top_n]

    try:
        reranker = _get_reranker()
        pairs = [[query, doc["content"]] for doc in documents]
        scores = reranker.compute_score(pairs, normalize=True)

        # 按分数降序排列
        scored = list(zip(documents, scores))
        scored.sort(key=lambda x: x[1], reverse=True)

        return [doc for doc, _ in scored[:top_n]]
    except Exception:
        # Reranker 不可用 → 降级到 MMR 排序结果
        return documents[:top_n]
