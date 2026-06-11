# Celery 异步任务：文档处理 + 知识库重建
# 对应文档：S2 Pattern 1 全流程

import os
import tempfile
from typing import Optional

from app.celery_app import celery_app
from app.database import async_session
from app.models.enums import ResourceStatus
from app.models.resource import Resource
from sqlalchemy import select, update


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def process_document(self, resource_id: str, course_id: str, file_content: bytes, file_type: str, file_name: str = ""):
    """
    异步处理上传的文档：解析 → 分块 → 向量化 → ChromaDB + PostgreSQL 双写。

    流程（S2 Pattern 1）：
    1. 更新 resources.status = 'parsing'
    2. 调用 parsers.parse_file() 解析文件
    3. 调用 chunker.chunk_documents() 分块
    4. 调用 indexer.index_chunks() 向量化 + 双库写入
    5. 更新 resources.status = 'ready', chunk_count = N
    6. 如果出错 → resources.status = 'failed'
    """
    import asyncio
    import tempfile

    async def _update_resource(**values):
        async with async_session() as session:
            stmt = update(Resource).where(Resource.id == resource_id).values(**values)
            await session.execute(stmt)
            await session.commit()

    async def _process():
        from app.rag.parsers import parse_file
        from app.rag.chunker import chunk_documents
        from app.rag.indexer import index_chunks

        await _update_resource(status=ResourceStatus.PARSING, error_message=None)

        # Step 1: 将 bytes 写入临时文件
        suffix = f".{file_type}" if file_type else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_content)
            tmp_path = tmp.name

        try:
            documents = await parse_file(tmp_path, file_type)
            for doc in documents:
                doc.metadata["file_name"] = file_name or doc.metadata.get("file_name", "")

            await _update_resource(status=ResourceStatus.CHUNKING)
            chunks = await chunk_documents(documents)

            await _update_resource(status=ResourceStatus.EMBEDDING)
            chunk_count = await index_chunks(course_id, resource_id, chunks)

            await _update_resource(status=ResourceStatus.READY, chunk_count=chunk_count)
        finally:
            os.unlink(tmp_path)

        return chunk_count

    try:
        chunk_count = asyncio.get_event_loop().run_until_complete(_process())
        return {
            "resource_id": resource_id,
            "status": "ready",
            "chunk_count": chunk_count,
        }
    except Exception as exc:
        asyncio.get_event_loop().run_until_complete(
            _update_resource(
                status=ResourceStatus.FAILED,
                error_message=str(exc)[:2000],
            )
        )

        return {
            "resource_id": resource_id,
            "status": "failed",
            "error": str(exc),
        }


@celery_app.task(bind=True, max_retries=2, default_retry_delay=120)
def rebuild_index(self, course_id: str):
    """
    重建课程知识库索引。

    用途：
    - 更换 Embedding 模型后重建所有向量
    - ChromaDB 数据损坏后从 PostgreSQL chunks 恢复

    流程：
    1. 从 PostgreSQL chunks 表读取所有文本
    2. 删除 ChromaDB 中原有 Collection
    3. 重新创建 Collection
    4. 逐批向量化 + 写入 ChromaDB + 更新 chroma_id
    """
    import asyncio

    async def _rebuild():
        from app.rag.vector_store import delete_collection, get_or_create_collection
        from app.rag.embeddings import get_embedding_model
        from app.models.resource import Chunk
        from sqlalchemy import select

        # 1. 读取所有 chunks
        async with async_session() as session:
            stmt = select(Chunk).where(Chunk.course_id == course_id).order_by(Chunk.chunk_index)
            result = await session.execute(stmt)
            chunks = result.scalars().all()

            if not chunks:
                return 0

            texts = [c.content for c in chunks]

        # 2. 删除旧 Collection，创建新 Collection
        await delete_collection(course_id)
        collection = await get_or_create_collection(course_id)

        # 3. 向量化
        embedding_model = get_embedding_model()
        embeddings = await embedding_model.aembed_documents(texts)

        # 4. 写入 ChromaDB
        import uuid
        new_chroma_ids = [str(uuid.uuid4()) for _ in chunks]
        metadatas = [
            {
                "resource_id": c.resource_id,
                "course_id": c.course_id,
            }
            for c in chunks
        ]

        collection.add(
            ids=new_chroma_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas,
        )

        # 5. 更新 PostgreSQL chroma_id
        async with async_session() as session:
            for i, chunk in enumerate(chunks):
                stmt = (
                    update(Chunk)
                    .where(Chunk.id == chunk.id)
                    .values(chroma_id=new_chroma_ids[i])
                )
                await session.execute(stmt)
            await session.commit()

        return len(chunks)

    try:
        count = asyncio.get_event_loop().run_until_complete(_rebuild())
        return {
            "course_id": course_id,
            "status": "rebuilt",
            "chunk_count": count,
        }
    except Exception as exc:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc)
        return {
            "course_id": course_id,
            "status": "error",
            "error": str(exc),
        }


@celery_app.task(bind=True)
def delete_resource_vectors(self, resource_id: str, course_id: str, chroma_ids: list[str]):
    """
    删除资源时清理 ChromaDB 中的向量数据。

    流程（约束 3）：
    1. 从 ChromaDB 删除指定 chroma_ids 的向量
    2. 更新 resources.status = 'deleted'
    """
    import asyncio

    async def _delete():
        from app.rag.vector_store import delete_chunks_by_ids
        await delete_chunks_by_ids(course_id, chroma_ids)

        async with async_session() as session:
            stmt = (
                update(Resource)
                .where(Resource.id == resource_id)
                .values(status="deleted")
            )
            await session.execute(stmt)
            await session.commit()

    try:
        asyncio.get_event_loop().run_until_complete(_delete())
        return {"resource_id": resource_id, "status": "vectors_deleted"}
    except Exception as exc:
        return {"resource_id": resource_id, "status": "error", "error": str(exc)}
