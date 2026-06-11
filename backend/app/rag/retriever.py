# 课程知识库检索器：MMR(lambda=0.7) + similarity_threshold=0.6
# 对应文档：S2 Pattern 2.1, 05 §3.2

import json
import numpy as np
from typing import Optional

from .embeddings import get_embedding_model, embed_query
from .vector_store import get_or_create_collection


class Retriever:
    """
    课程知识库检索器 —— 被 search_knowledge 工具调用。

    检索管道：
    Query → Embedding → ChromaDB query → MMR 重排序 → 阈值过滤 → 返回
    """

    def __init__(self, course_id: str):
        self.course_id = course_id
        self._collection = None
        self._embedding_model = None

    async def _ensure_initialized(self):
        """延迟初始化 Collection 和 Embedding Model"""
        if self._collection is None:
            self._collection = await get_or_create_collection(self.course_id)
        if self._embedding_model is None:
            self._embedding_model = get_embedding_model()

    async def search(
        self,
        query: str,
        top_k: int = 5,
        resource_type: Optional[str] = None,
        similarity_threshold: float = 0.6,
    ) -> list[dict]:
        """
        语义检索课程知识库。

        Args:
            query: 检索查询语句
            top_k: 最终返回结果数量
            resource_type: 按资源类型过滤（pdf/docx/pptx/md/txt）
            similarity_threshold: 相似度阈值（低于此值丢弃）

        Returns:
            [{content, metadata: {file_name, page, chapter, resource_id}, score, chunk_id}, ...]
        """
        await self._ensure_initialized()

        # 1. Embedding 向量化
        query_embedding = await embed_query(query)

        # 2. 构建 metadata filter（可选）
        where_filter = None
        if resource_type:
            where_filter = {"resource_type": resource_type}

        # 3. ChromaDB 检索（先多取 4 倍候选，给 MMR 足够空间）
        fetch_k = top_k * 4
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=fetch_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        # 4. MMR 重排序
        ranked = self._mmr_rerank(
            query_embedding=query_embedding,
            candidates=results,
            lambda_mult=0.7,  # 70% 相关性 + 30% 多样性
            top_k=top_k,
        )

        # 5. 相似度阈值过滤
        filtered = [r for r in ranked if r["score"] >= similarity_threshold]

        return filtered

    def _mmr_rerank(
        self,
        query_embedding: list[float],
        candidates: dict,
        lambda_mult: float = 0.7,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Maximal Marginal Relevance 重排序。
        MMR 公式：λ * sim(d, Q) - (1-λ) * max_{已选} sim(d, d')

        目的：在保证相关性的同时，选择内容多样的文档。
        """
        docs = candidates.get("documents", [[]])[0] or []
        metas = candidates.get("metadatas", [[]])[0] or []
        ids_list = candidates.get("ids", [[]])[0] or []
        distances = candidates.get("distances", [[]])[0] or []

        if not docs:
            return []

        n_docs = len(docs)

        # 距离转相似度（cosine distance → similarity = 1 - distance）
        similarities = [1 - d for d in distances]

        # 获取候选 embeddings（用于计算文档间相似度）
        # ChromaDB query 不一定返回 embeddings，需要额外获取
        candidate_embeddings = None
        try:
            emb_results = self._collection.get(
                ids=ids_list,
                include=["embeddings"],
            )
            candidate_embeddings = emb_results.get("embeddings") or []
        except Exception:
            candidate_embeddings = []

        # Simple MMR
        selected_indices = []
        remaining = list(range(n_docs))

        for _ in range(min(top_k, n_docs)):
            mmr_scores = []
            for i in remaining:
                relevance = similarities[i]
                redundancy = 0
                if selected_indices:
                    # 与已选文档的最大相似度
                    max_sim = 0
                    for j in selected_indices:
                        if candidate_embeddings and i < len(candidate_embeddings) and j < len(candidate_embeddings):
                            sim = self._cosine_sim(
                                candidate_embeddings[i],
                                candidate_embeddings[j],
                            )
                            max_sim = max(max_sim, sim)
                    redundancy = max_sim
                mmr = lambda_mult * relevance - (1 - lambda_mult) * redundancy
                mmr_scores.append((i, mmr))

            # 选最高 MMR
            best_idx, _ = max(mmr_scores, key=lambda x: x[1])
            selected_indices.append(best_idx)
            remaining.remove(best_idx)

        # 组装结果
        results = []
        for idx in selected_indices:
            results.append({
                "content": docs[idx],
                "metadata": metas[idx],
                "score": round(similarities[idx], 4),
                "chunk_id": ids_list[idx],
            })

        return results

    @staticmethod
    def _cosine_sim(emb1: list[float], emb2: list[float]) -> float:
        """余弦相似度（BGE-M3 已归一化 = 点积）"""
        if emb1 is None or emb2 is None:
            return 0.0
        return float(np.dot(emb1, emb2))

    def format_results(self, results: list[dict]) -> str:
        """
        格式化检索结果为 JSON 字符串（供 Agent Tool 返回）。
        格式对齐 03 文档 §4.6 sources JSONB schema。
        """
        formatted = []
        for r in results:
            meta = r.get("metadata", {})
            formatted.append({
                "resource_id": meta.get("resource_id", ""),
                "resource_name": meta.get("file_name", "未知文件"),
                "chunk_id": r.get("chunk_id", ""),
                "chunk_index": meta.get("chunk_index", 0),
                "score": r.get("score", 0),
                "text_preview": r.get("content", "")[:100],
            })
        return json.dumps(formatted, ensure_ascii=False)

    def format_for_prompt(self, results: list[dict], max_docs: int = 5) -> str:
        """
        格式化检索结果为 LLM 提示词用的纯文本。
        格式对齐 06 §2.4。
        """
        if not results:
            return "（课程知识库中暂无相关内容）"

        lines = ["## 课程知识库检索结果\n"]
        for i, doc in enumerate(results[:max_docs], 1):
            meta = doc.get("metadata", {})
            source = meta.get("file_name", "未知来源")
            page = meta.get("page", "")
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
