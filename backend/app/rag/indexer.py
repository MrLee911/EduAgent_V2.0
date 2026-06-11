# 文档索引器：Embedding + ChromaDB + PostgreSQL chunks 双写全流程
# 对应文档：S2 Pattern 1.4

import uuid
from typing import List

from .embeddings import get_embedding_model
from .vector_store import get_or_create_collection
from app.database import async_session
from app.models.resource import Chunk, Resource
from sqlalchemy import select, update


async def index_chunks(
    course_id: str,
    resource_id: str,
    chunks: List[dict],
) -> int:
    """
    将 chunks 向量化并写入 ChromaDB + PostgreSQL 双库。

    流程：
    1. Embedding 向量化（BGE-M3）
    2. ChromaDB collection.add()
    3. PostgreSQL chunks 表同步写入
    4. resources 表更新 status='ready', chunk_count=N

    Returns:
        实际写入的 chunk 数量
    """
    if not chunks:
        return 0

    # === Step 1: Embedding 向量化 ===
    embedding_model = get_embedding_model()
    texts = [chunk["content"] for chunk in chunks]
    embeddings = await embedding_model.aembed_documents(texts)

    # === Step 2: ChromaDB 写入 ===
    collection = await get_or_create_collection(course_id)

    chroma_ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "resource_id": resource_id,
            "course_id": course_id,
            "file_name": chunk["file_name"],
            "page": chunk.get("page", 0) or 0,
            "chapter": chunk.get("chapter", ""),
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]

    collection.add(
        ids=chroma_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    # === Step 3: PostgreSQL chunks 表同步写入 ===
    async with async_session() as session:
        for i, chunk in enumerate(chunks):
            db_chunk = Chunk(
                resource_id=resource_id,
                course_id=course_id,
                chunk_index=chunk["chunk_index"],
                content=chunk["content"],
                token_count=chunk["token_count"],
                chroma_id=chroma_ids[i],
            )
            session.add(db_chunk)

        # === Step 4: 更新 resources 表状态 ===
        stmt = (
            update(Resource)
            .where(Resource.id == resource_id)
            .values(status="ready", chunk_count=len(chunks))
        )
        await session.execute(stmt)
        await session.commit()

    return len(chunks)
