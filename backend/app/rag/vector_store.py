# ChromaDB 连接管理：课程级 Collection 隔离 + HttpClient 连接池
# 对应文档：S2 Pattern 1.3, 03 §5.1

import chromadb
from chromadb.config import Settings
from app.config import settings

# 每个课程一个 Collection，实现课程级知识隔离
COLLECTION_PREFIX = "course_"

# 全局 HttpClient 单例（复用连接）
_client: chromadb.HttpClient = None


def get_chroma_client() -> chromadb.HttpClient:
    """获取 ChromaDB HttpClient 单例"""
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,  # "chromadb"
            port=settings.CHROMA_PORT,  # 8000
            settings=Settings(anonymized_telemetry=False),
        )
    return _client


def get_collection_name(course_id: str) -> str:
    """课程 ID → Collection 名称映射（UUID 中的 - 替换为 _）"""
    return f"{COLLECTION_PREFIX}{course_id.replace('-', '_')}"


async def get_or_create_collection(course_id: str):
    """
    获取或创建课程的 ChromaDB Collection。

    每个课程独立的 Collection：
    - 命名：course_{course_id}
    - 距离度量：cosine（BGE-M3 已归一化，cosine = 点积）
    - embedding_function=None：手动传入 embedding（更灵活）
    """
    client = get_chroma_client()
    collection_name = get_collection_name(course_id)

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=None,  # 手动传 embedding
        )
    except Exception:
        collection = client.create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",  # BGE-M3 已归一化，必须用余弦距离
                "course_id": course_id,
            },
        )
    return collection


async def delete_collection(course_id: str):
    """删除课程对应的 ChromaDB Collection（课程删除时调用）"""
    client = get_chroma_client()
    collection_name = get_collection_name(course_id)
    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass  # Collection 不存在，忽略


async def delete_chunks_by_ids(course_id: str, chroma_ids: list[str]):
    """按 chroma_id 列表删除向量（资源删除时调用）"""
    if not chroma_ids:
        return
    collection = await get_or_create_collection(course_id)
    collection.delete(ids=chroma_ids)
