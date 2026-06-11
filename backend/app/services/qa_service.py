# backend/app/services/qa_service.py — M04 智能问答业务逻辑
import uuid
import json
import re
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.models.user import User
from app.models.course import Course
from app.models.resource import Resource, Chunk
from app.models.qa_record import QARecord
from app.models.enums import QAFeedback, ResourceStatus
from app.schemas.qa import (
    QAAskRequest, QAResponse, QAHistoryItemResponse,
    QASourceItem, QAFeedbackRequest, QAStreamSource, QAStreamDoneData,
)
from app.exceptions import NotFoundException, KnowledgeBaseEmptyException, AIServiceException
from app.config import settings
import httpx

LLM_TIMEOUT = httpx.Timeout(12.0, connect=5.0)
QA_SOURCE_LIMIT = 10
QA_MEMORY_LIMIT = 8


async def _check_knowledge_base(db: AsyncSession, course_id: str) -> int:
    """检查课程知识库是否有数据"""
    result = await db.execute(
        select(func.count(Chunk.id)).where(
            Chunk.course_id == course_id
        )
    )
    count = result.scalar() or 0
    return count


def _query_terms(question: str) -> set[str]:
    words = {term.lower() for term in re.findall(r"[A-Za-z0-9_]+", question)}
    chars = {char for char in question if "\u4e00" <= char <= "\u9fff"}
    return words | chars


def _source_resource_id(source: dict) -> str:
    metadata = source.get("metadata") or {}
    return str(source.get("resource_id") or metadata.get("resource_id") or "")


def _normalize_source(source: dict, default_index: int = 0) -> dict:
    metadata = source.get("metadata") or {}
    resource_id = str(source.get("resource_id") or metadata.get("resource_id") or "")
    resource_name = source.get("resource_name") or metadata.get("file_name") or metadata.get("resource_name") or ""
    chunk_index = source.get("chunk_index", metadata.get("chunk_index", default_index))
    metadata = {
        **metadata,
        "resource_id": resource_id,
        "file_name": resource_name,
        "chunk_index": chunk_index,
    }
    return {
        **source,
        "resource_id": resource_id,
        "resource_name": resource_name,
        "chunk_index": chunk_index,
        "metadata": metadata,
    }


def _diversify_sources(sources: list[dict], limit: int = QA_SOURCE_LIMIT) -> list[dict]:
    normalized = [_normalize_source(source, i) for i, source in enumerate(sources)]
    selected: list[dict] = []
    seen_resources: set[str] = set()
    seen_chunks: set[str] = set()

    for source in normalized:
        chunk_id = str(source.get("chunk_id", ""))
        resource_id = _source_resource_id(source)
        if chunk_id in seen_chunks or resource_id in seen_resources:
            continue
        selected.append(source)
        seen_chunks.add(chunk_id)
        if resource_id:
            seen_resources.add(resource_id)
        if len(selected) >= limit:
            return selected

    for source in normalized:
        chunk_id = str(source.get("chunk_id", ""))
        if chunk_id in seen_chunks:
            continue
        selected.append(source)
        seen_chunks.add(chunk_id)
        if len(selected) >= limit:
            break

    return selected


async def _fallback_chunk_sources(db: AsyncSession, course_id: str, question: str, limit: int = QA_SOURCE_LIMIT) -> list[dict]:
    """Fallback retrieval from PostgreSQL chunks when vector retrieval returns no hits."""
    result = await db.execute(
        select(Chunk, Resource)
        .join(Resource, Resource.id == Chunk.resource_id)
        .where(
            Chunk.course_id == course_id,
            Resource.status == ResourceStatus.READY,
        )
        .order_by(Chunk.created_at.desc())
        .limit(80)
    )
    rows = result.all()
    if not rows:
        return []

    query_terms = _query_terms(question)
    scored = []
    for chunk, resource in rows:
        content = chunk.content or ""
        lower_content = content.lower()
        score = sum(1 for term in query_terms if term in lower_content)
        scored.append((score, chunk, resource))

    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    sources = []
    for score, chunk, resource in scored:
        sources.append({
            "content": chunk.content,
            "resource_id": str(resource.id),
            "resource_name": resource.file_name,
            "chunk_index": chunk.chunk_index,
            "metadata": {
                "resource_id": str(resource.id),
                "file_name": resource.file_name,
                "chunk_index": chunk.chunk_index,
            },
            "score": 1.0 if score > 0 else 0.5,
            "chunk_id": str(chunk.id),
        })
    return _diversify_sources(sources, limit=limit)


async def _representative_resource_sources(db: AsyncSession, course_id: str, limit: int = QA_SOURCE_LIMIT) -> list[dict]:
    """Pick one representative chunk from each ready resource to improve chapter coverage."""
    result = await db.execute(
        select(Chunk, Resource)
        .join(Resource, Resource.id == Chunk.resource_id)
        .where(
            Chunk.course_id == course_id,
            Resource.status == ResourceStatus.READY,
        )
        .order_by(Resource.file_name.asc(), Chunk.chunk_index.asc())
    )
    rows = result.all()

    sources = []
    seen_resources: set[str] = set()
    for chunk, resource in rows:
        resource_id = str(resource.id)
        if resource_id in seen_resources:
            continue
        sources.append({
            "content": chunk.content,
            "resource_id": resource_id,
            "resource_name": resource.file_name,
            "chunk_index": chunk.chunk_index,
            "metadata": {
                "resource_id": resource_id,
                "file_name": resource.file_name,
                "chunk_index": chunk.chunk_index,
            },
            "score": 0.45,
            "chunk_id": str(chunk.id),
        })
        seen_resources.add(resource_id)
        if len(sources) >= limit:
            break
    return sources


async def _collect_sources(db: AsyncSession, course_id: str, question: str, limit: int = QA_SOURCE_LIMIT) -> list[dict]:
    from app.rag.retriever import Retriever

    retriever = Retriever(course_id)
    try:
        sources = await retriever.search(question, top_k=limit * 2, similarity_threshold=0.0)
    except Exception:
        sources = []

    fallback_sources = await _fallback_chunk_sources(db, course_id, question, limit=limit)
    representative_sources = await _representative_resource_sources(db, course_id, limit=limit)
    sources = _diversify_sources([*sources, *fallback_sources, *representative_sources], limit=limit)
    return sources


def _build_fallback_answer(question: str, sources: list[dict], memory: str = "") -> str:
    """Build a deterministic answer when the configured LLM is unavailable."""
    snippets = []
    for i, source in enumerate(sources[:QA_SOURCE_LIMIT], 1):
        content = (source.get("content") or "").strip()
        if len(content) > 500:
            content = content[:500] + "..."
        snippets.append(f"{i}. {content}")
    joined = "\n".join(snippets) if snippets else "当前知识库中没有可用片段。"
    memory_block = ""
    if memory and memory != "（暂无历史问答记忆）":
        memory_block = f"\n\n**历史问答记忆：**\n{memory}\n"
    return (
        "我暂时无法连接外部 AI 模型，先根据课程资料给出可用参考：\n\n"
        f"**问题：** {question}\n\n"
        f"{memory_block}"
        f"**相关资料：**\n{joined}\n\n"
        "你可以根据以上片段继续追问更具体的问题。"
    )


async def _build_memory_context(
    db: AsyncSession,
    course_id: str,
    user_id: str | None,
    limit: int = QA_MEMORY_LIMIT,
) -> str:
    """Build a compact long-term memory block from previous QA records."""
    if not user_id:
        return "（暂无历史问答记忆）"

    result = await db.execute(
        select(QARecord)
        .where(
            QARecord.course_id == course_id,
            QARecord.user_id == user_id,
        )
        .order_by(QARecord.created_at.desc())
        .limit(limit)
    )
    records = list(reversed(result.scalars().all()))
    if not records:
        return "（暂无历史问答记忆）"

    blocks = []
    for i, record in enumerate(records, 1):
        answer = (record.answer or "").strip()
        if len(answer) > 260:
            answer = answer[:260] + "..."
        blocks.append(f"{i}. 学生曾问：{record.question}\n   助教曾答：{answer}")
    return "\n".join(blocks)


async def _run_qa_pipeline(
    db: AsyncSession,
    course_id: str,
    user_id: str | None,
    question: str,
    conversation_id: str | None = None,
) -> dict:
    """执行完整 RAG 问答链路：检索 → 生成 → 写入 qa_records
    
    Returns dict matching QAResponse schema.
    """
    from app.rag.query_rewriter import rewrite_query
    from app.rag.reranker import rerank_with_bge
    from app.rag.post_processor import format_knowledge_for_prompt, format_sources_for_db

    # 1. 查询改写
    conv_id = conversation_id or str(uuid.uuid4())
    try:
        rewritten_q = await rewrite_query(question)
        if not rewritten_q:
            rewritten_q = question
    except Exception:
        rewritten_q = question

    # 2. 检索并尽量覆盖多份资料
    sources = await _collect_sources(db, course_id, rewritten_q, limit=QA_SOURCE_LIMIT)
    if not sources:
        raise KnowledgeBaseEmptyException()

    # 3. Rerank（候选数 ≥ 8 时启用）
    if len(sources) >= 8:
        try:
            sources = await rerank_with_bge(rewritten_q, sources)
        except Exception:
            pass  # reranker 失败时降级到 MMR 顺序

    # 4. 取 Top 10，并尽量按资料来源多样化
    sources = _diversify_sources(sources, limit=QA_SOURCE_LIMIT)

    # 5. 拼接上下文 + 调用 LLM 生成回答
    knowledge_text = format_knowledge_for_prompt(sources)
    memory_text = await _build_memory_context(db, course_id, user_id)
    system_prompt = _build_qa_system_prompt()
    user_prompt = _build_qa_user_prompt(rewritten_q, knowledge_text, memory_text)

    try:
        answer = await _call_llm(system_prompt, user_prompt)
    except Exception as e:
        answer = _build_fallback_answer(question, sources, memory_text)

    # 6. 后处理：构建 sources
    db_sources = format_sources_for_db(sources)

    # 7. 写入 qa_records
    qa_record = QARecord(
        id=uuid.uuid4(),
        course_id=uuid.UUID(course_id),
        user_id=uuid.UUID(user_id) if user_id else None,
        conversation_id=conv_id,
        question=question,
        answer=answer,
        sources=db_sources,
        feedback=QAFeedback.NONE,
    )
    db.add(qa_record)
    await db.commit()
    await db.refresh(qa_record)

    # 8. 构建 source 响应项
    source_items = []
    for i, src in enumerate(sources):
        source_items.append({
            "resource_id": src.get("resource_id", ""),
            "resource_name": src.get("resource_name", ""),
            "chunk_id": str(src.get("chunk_id", "")),
            "chunk_index": src.get("chunk_index", i),
            "score": float(src.get("score", 0.0)),
            "text_preview": src.get("text_preview", src.get("content", "")[:200]),
        })

    return {
        "id": str(qa_record.id),
        "conversation_id": conv_id,
        "question": question,
        "answer": answer,
        "sources": source_items,
        "feedback": "none",
        "created_at": str(qa_record.created_at) if qa_record.created_at else None,
    }


def _build_qa_system_prompt() -> str:
    """构建 QA 系统提示词"""
    return (
        "你是一个专业的课程教学助手。请优先根据提供的课程资料回答学生的问题。\n\n"
        "要求：\n"
        "1. 优先使用课程资料中的内容，并在相关处说明依据\n"
        "2. 如果课程资料不足以完整回答，可以补充通用知识，但必须明确标注为“补充说明”\n"
        "3. 不要把课程资料中没有出现的内容伪装成资料原文\n"
        "4. 使用 Markdown 格式，便于阅读\n"
        "5. 对于编程问题，给出代码示例和解释\n"
        "6. 不要直接给出作业答案，而是引导学生思考\n"
        "7. 结合历史问答记忆理解学生的上下文、薄弱点和连续追问，不要机械重复上一轮答案\n"
        "8. 回答要像助教在辅导：先直接回应问题，再用例子、步骤、对比或小结帮助理解\n"
        "9. 如果学生连续追问同一知识点，要承接前文，用更具体或不同角度解释\n"
    )


def _build_qa_user_prompt(question: str, knowledge: str, memory: str) -> str:
    """构建 QA 用户提示词"""
    return (
        f"# 课程资料\n{knowledge}\n\n"
        f"# 历史问答记忆\n{memory}\n\n"
        f"# 学生问题\n{question}\n\n"
        "请先结合历史问答记忆判断学生当前问题的上下文，再基于课程资料回答；如果资料不足，请在“补充说明”中结合通用知识解释。"
    )


async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """调用 LLM 生成回答"""
    async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
        resp = await client.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": settings.LLM_MAX_TOKENS,
                "temperature": settings.LLM_TEMPERATURE,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def ask_question(
    db: AsyncSession,
    course_id: str,
    user: User,
    data: QAAskRequest,
) -> dict:
    """非流式问答"""
    # 检查知识库
    chunk_count = await _check_knowledge_base(db, course_id)
    if chunk_count == 0:
        raise KnowledgeBaseEmptyException()

    return await _run_qa_pipeline(
        db=db,
        course_id=course_id,
        user_id=str(user.id),
        question=data.question,
        conversation_id=data.conversation_id,
    )


async def ask_question_stream(
    db: AsyncSession,
    course_id: str,
    user: User,
    data: QAAskRequest,
) -> AsyncGenerator[str, None]:
    """SSE 流式问答"""
    import asyncio
    try:
        async for event in _ask_question_stream_impl(db, course_id, user, data):
            yield event
    except Exception as exc:
        yield f"event: error\ndata: {json.dumps({'type': 'INTERNAL_ERROR', 'message': f'问答服务异常: {exc}'}, ensure_ascii=False)}\n\n"


async def _ask_question_stream_impl(
    db: AsyncSession,
    course_id: str,
    user: User,
    data: QAAskRequest,
) -> AsyncGenerator[str, None]:
    """SSE 流式问答实现。外层 ask_question_stream 负责兜底异常转 SSE error。"""
    import asyncio

    # 检查知识库
    chunk_count = await _check_knowledge_base(db, course_id)
    if chunk_count == 0:
        yield f"event: error\ndata: {json.dumps({'type': 'KNOWLEDGE_BASE_EMPTY', 'message': '该课程暂无资源，请先上传教学资料'}, ensure_ascii=False)}\n\n"
        return

    from app.rag.query_rewriter import rewrite_query
    from app.rag.reranker import rerank_with_bge
    from app.rag.post_processor import format_knowledge_for_prompt, format_sources_for_db

    conv_id = data.conversation_id or str(uuid.uuid4())

    # 1. Thinking 事件
    yield f"event: thinking\ndata: {json.dumps({'message': '正在检索相关知识...'}, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0)  # flush

    # 2. 查询改写
    try:
        rewritten_q = await rewrite_query(data.question)
        if not rewritten_q:
            rewritten_q = data.question
    except Exception:
        rewritten_q = data.question

    # 3. 检索并尽量覆盖多份资料
    sources = await _collect_sources(db, course_id, rewritten_q, limit=QA_SOURCE_LIMIT)
    if not sources:
        yield f"event: error\ndata: {json.dumps({'type': 'KNOWLEDGE_BASE_EMPTY', 'message': '该课程暂无资源'}, ensure_ascii=False)}\n\n"
        return

    # 4. Rerank
    if len(sources) >= 8:
        try:
            sources = await rerank_with_bge(rewritten_q, sources)
        except Exception:
            pass

    sources = _diversify_sources(sources, limit=QA_SOURCE_LIMIT)

    # 5. Sources 事件
    stream_sources = []
    for i, src in enumerate(sources):
        stream_sources.append({
            "resource_id": src.get("resource_id", ""),
            "resource_name": src.get("resource_name", ""),
            "chunk_id": str(src.get("chunk_id", "")),
            "chunk_index": src.get("chunk_index", i),
            "score": float(src.get("score", 0.0)),
        })
    yield f"event: sources\ndata: {json.dumps(stream_sources, ensure_ascii=False)}\n\n"
    await asyncio.sleep(0)

    # 6. LLM 流式生成
    knowledge_text = format_knowledge_for_prompt(sources)
    memory_text = await _build_memory_context(db, str(course_id), str(user.id))
    system_prompt = _build_qa_system_prompt()
    user_prompt = _build_qa_user_prompt(rewritten_q, knowledge_text, memory_text)

    full_answer = ""
    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT) as client:
            async with client.stream(
                "POST",
                f"{settings.LLM_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.LLM_MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "max_tokens": settings.LLM_MAX_TOKENS,
                    "temperature": settings.LLM_TEMPERATURE,
                    "stream": True,
                },
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        chunk_data = line[6:]
                        if chunk_data == "[DONE]":
                            break
                        try:
                            chunk = json.loads(chunk_data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_answer += content
                                yield f"event: token\ndata: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        full_answer = _build_fallback_answer(data.question, sources, memory_text)
        for i in range(0, len(full_answer), 24):
            content = full_answer[i:i + 24]
            yield f"event: token\ndata: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0)

    # 7. 写入数据库
    db_sources = format_sources_for_db(sources)
    qa_record = QARecord(
        id=uuid.uuid4(),
        course_id=uuid.UUID(course_id),
        user_id=uuid.UUID(str(user.id)),
        conversation_id=conv_id,
        question=data.question,
        answer=full_answer,
        sources=db_sources,
        feedback=QAFeedback.NONE,
    )
    db.add(qa_record)
    await db.commit()
    await db.refresh(qa_record)

    # 8. Done 事件
    done_data = {
        "id": str(qa_record.id),
        "message_id": str(qa_record.id),
        "conversation_id": conv_id,
        "sources": stream_sources,
        "created_at": str(qa_record.created_at) if qa_record.created_at else None,
    }
    yield f"event: done\ndata: {json.dumps(done_data, ensure_ascii=False)}\n\n"


async def get_qa_history(
    db: AsyncSession,
    course_id: str,
    user: User,
    page: int = 1,
    page_size: int = 20,
    conversation_id: str | None = None,
) -> tuple[list[dict], int]:
    """获取问答历史列表"""
    conditions = [
        QARecord.course_id == course_id,
        QARecord.user_id == user.id,
    ]
    if conversation_id:
        conditions.append(QARecord.conversation_id == conversation_id)

    total_q = select(func.count(QARecord.id)).where(and_(*conditions))
    total = (await db.execute(total_q)).scalar() or 0

    q = (
        select(QARecord)
        .where(and_(*conditions))
        .order_by(QARecord.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    records = (await db.execute(q)).scalars().all()

    result = []
    for r in records:
        excerpt = r.answer[:150] + "..." if len(r.answer) > 150 else r.answer
        result.append({
            "id": str(r.id),
            "conversation_id": str(r.conversation_id) if r.conversation_id else "",
            "question": r.question,
            "answer_excerpt": excerpt,
            "feedback": r.feedback.value if hasattr(r.feedback, 'value') else str(r.feedback),
            "created_at": str(r.created_at) if r.created_at else None,
        })

    return result, total


async def get_qa_detail(
    db: AsyncSession,
    course_id: str,
    qa_id: str,
) -> dict:
    """获取问答详情"""
    result = await db.execute(
        select(QARecord).where(
            QARecord.id == qa_id,
            QARecord.course_id == course_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException(resource="问答记录", id=qa_id)

    # 构建 sources
    sources_list = record.sources if isinstance(record.sources, list) else []
    source_items = []
    for i, src in enumerate(sources_list):
        source_items.append({
            "resource_id": src.get("resource_id", ""),
            "resource_name": src.get("resource_name", ""),
            "chunk_id": str(src.get("chunk_id", "")),
            "chunk_index": src.get("chunk_index", i),
            "score": float(src.get("score", 0.0)),
            "text_preview": src.get("text_preview", ""),
        })

    return {
        "id": str(record.id),
        "conversation_id": str(record.conversation_id) if record.conversation_id else "",
        "question": record.question,
        "answer": record.answer,
        "sources": source_items,
        "feedback": record.feedback.value if hasattr(record.feedback, 'value') else str(record.feedback),
        "created_at": str(record.created_at) if record.created_at else None,
    }


async def submit_feedback(
    db: AsyncSession,
    course_id: str,
    qa_id: str,
    data: QAFeedbackRequest,
) -> None:
    """提交问答反馈"""
    if data.feedback not in ("like", "dislike", "none"):
        raise ValueError("feedback 必须是 like / dislike / none")

    result = await db.execute(
        select(QARecord).where(
            QARecord.id == qa_id,
            QARecord.course_id == course_id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise NotFoundException(resource="问答记录", id=qa_id)

    record.feedback = QAFeedback(data.feedback)
    await db.commit()


async def clear_conversation(
    conversation_id: str,
) -> None:
    """清空对话上下文（Redis 缓存清理）"""
    # 清除 Redis 中的对话上下文
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL)
        await r.delete(f"conv:{conversation_id}")
        await r.close()
    except Exception:
        pass  # Redis 不可用时不阻断
