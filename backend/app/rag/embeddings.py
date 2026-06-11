# Embedding 模型加载：BGE-M3 本地模型 + L2 归一化
# 对应文档：S2 Pattern 1.3

import hashlib
import math
from typing import Optional
from app.config import settings

_embedding_model: Optional[object] = None


class HashEmbeddingFallback:
    """Deterministic local embedding fallback used when the configured model is unavailable."""

    def __init__(self, dimension: int):
        self.dimension = dimension

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        tokens = text.split() or [text]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8", errors="ignore")).digest()
            for offset in range(0, len(digest), 4):
                idx = int.from_bytes(digest[offset:offset + 2], "little") % self.dimension
                sign = 1.0 if digest[offset + 2] % 2 == 0 else -1.0
                vector[idx] += sign
        norm = math.sqrt(sum(value * value for value in vector))
        if norm == 0:
            return vector
        return [value / norm for value in vector]

    async def aembed_query(self, query: str) -> list[float]:
        return self._embed(query)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]


def get_embedding_model() -> object:
    """
    获取/创建 BGE-M3 Embedding 模型实例（单例）。
    使用 langchain_huggingface.HuggingFaceEmbeddings 包装。
    """
    global _embedding_model
    if _embedding_model is not None:
        return _embedding_model

    from langchain_huggingface import HuggingFaceEmbeddings

    try:
        _embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,  # "BAAI/bge-m3"
            model_kwargs={
                "device": settings.EMBEDDING_DEVICE,  # "cpu" / "cuda"
                "local_files_only": settings.EMBEDDING_LOCAL_ONLY,
            },
            encode_kwargs={
                "normalize_embeddings": True,  # BGE-M3 必须 L2 归一化
            },
        )
    except Exception as exc:
        if settings.EMBEDDING_LOCAL_ONLY:
            _embedding_model = HashEmbeddingFallback(settings.EMBEDDING_DIMENSION)
            return _embedding_model
        raise
    return _embedding_model


async def embed_query(query: str) -> list[float]:
    """对单个查询文本进行向量化"""
    model = get_embedding_model()
    return await model.aembed_query(query)


async def embed_documents(texts: list[str]) -> list[list[float]]:
    """对批量文本进行向量化"""
    model = get_embedding_model()
    return await model.aembed_documents(texts)


def get_embedding_dimension() -> int:
    """获取 Embedding 向量维度"""
    return settings.EMBEDDING_DIMENSION  # 1024
