# backend/app/services/task_service.py — M05 教学任务业务逻辑
import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.course import Course
from app.models.resource import Chunk, Resource
from app.models.task import Task
from app.models.enums import TaskType, TaskDifficulty, TaskStatus, UserRole, ResourceStatus
from app.schemas.task import (
    TaskGenerateRequest, TaskUpdateRequest,
    TaskResponse, TaskListResponse, TaskStatusResponse,
)
from app.exceptions import (
    NotFoundException, ForbiddenException, ValidationException,
    AIServiceException, TaskStatusException,
)
from app.config import settings
import httpx


def _format_task_list_item(task: Task) -> dict:
    """格式化任务列表项"""
    return {
        "id": str(task.id),
        "title": task.title,
        "task_type": task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
        "topic": task.topic,
        "difficulty": task.difficulty.value if hasattr(task.difficulty, 'value') else str(task.difficulty),
        "estimated_time": task.estimated_time,
        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
        "created_by": {
            "id": str(task.creator.id),
            "display_name": task.creator.display_name,
        } if task.creator else None,
        "created_at": str(task.created_at) if task.created_at else None,
    }


def _format_task_detail(task: Task) -> dict:
    """格式化任务详情"""
    ref_resources = task.reference_resources if isinstance(task.reference_resources, list) else []
    return {
        "id": str(task.id),
        "course_id": str(task.course_id) if task.course_id else None,
        "title": task.title,
        "task_type": task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
        "topic": task.topic,
        "content": task.content,
        "difficulty": task.difficulty.value if hasattr(task.difficulty, 'value') else str(task.difficulty),
        "estimated_time": task.estimated_time,
        "reference_resources": [
            {
                "resource_id": r.get("resource_id", ""),
                "resource_name": r.get("resource_name", ""),
                "chunk_id": r.get("chunk_id", ""),
            }
            for r in ref_resources
        ],
        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
        "created_by": {
            "id": str(task.creator.id),
            "display_name": task.creator.display_name,
        } if task.creator else None,
        "created_at": str(task.created_at) if task.created_at else None,
        "updated_at": str(task.updated_at) if task.updated_at else None,
    }


async def _call_task_llm(
    topic: str,
    task_type: str,
    difficulty: str,
    additional_instructions: str | None,
    knowledge_text: str,
) -> str:
    """调用 LLM 生成教学任务内容"""
    type_names = {"class_exercise": "随堂练习", "homework": "课后作业", "lab_guide": "实验指导"}
    type_name = type_names.get(task_type, task_type)
    diff_names = {"easy": "简单", "medium": "中等", "hard": "困难"}
    diff_name = diff_names.get(difficulty, difficulty)

    system_prompt = (
        "你是一个专业的课程教学设计专家。请根据提供的课程资料，生成一份高质量的教学任务。\n\n"
        f"任务类型：{type_name}\n"
        f"难度等级：{diff_name}\n\n"
        "要求：\n"
        "1. 使用 Markdown 格式输出\n"
        "2. 包含清晰的任务说明和具体要求\n"
        "3. 题目由易到难排列\n"
        "4. 给出评分标准（如适用）\n"
        "5. 基于课程资料的内容范围出题，不要超纲\n"
    )

    user_prompt = (
        f"# 主题\n{topic}\n\n"
        f"# 课程相关资料\n{knowledge_text}\n\n"
        f"# 额外要求\n{additional_instructions or '无'}\n\n"
        "请生成完整的教学任务内容。"
    )

    async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=8.0)) as client:
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
                "max_tokens": settings.LLM_MAX_TASKS_TOKENS,
                "temperature": 0.8,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


async def _generate_task_title(topic: str, task_type: str) -> str:
    """生成任务标题"""
    type_prefix = {"class_exercise": "随堂练习", "homework": "课后作业", "lab_guide": "实验指导"}
    prefix = type_prefix.get(task_type, "任务")
    return f"{prefix}：{topic}"


async def _estimate_time(content: str, difficulty: str) -> str:
    """估算任务完成时间"""
    word_count = len(content)
    base_time = {"easy": 30, "medium": 60, "hard": 90}
    minutes = base_time.get(difficulty, 60) + word_count // 500 * 10
    return f"{minutes}分钟"


async def _load_task_with_creator(db: AsyncSession, task_id: uuid.UUID | str) -> Task:
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.creator))
        .where(Task.id == task_id)
    )
    return result.scalar_one()


async def _fallback_task_sources(db: AsyncSession, course_id: str, topic: str, limit: int = 5) -> list[dict]:
    """从 PostgreSQL chunks 中兜底检索，避免向量库异常时任务生成不可用。"""
    result = await db.execute(
        select(Chunk, Resource)
        .join(Resource, Resource.id == Chunk.resource_id)
        .where(
            Chunk.course_id == course_id,
            Resource.status == ResourceStatus.READY,
        )
        .order_by(Chunk.created_at.desc())
        .limit(50)
    )
    rows = result.all()
    if not rows:
        return []

    terms = {term.lower() for term in topic.split() if term.strip()}
    terms |= {char for char in topic if "\u4e00" <= char <= "\u9fff"}
    scored = []
    for chunk, resource in rows:
        content = chunk.content or ""
        lower_content = content.lower()
        score = sum(1 for term in terms if term in lower_content)
        scored.append((score, chunk, resource))

    scored.sort(key=lambda item: (item[0], item[1].created_at), reverse=True)
    selected = []
    seen_resources = set()
    for score, chunk, resource in scored:
        resource_id = str(resource.id)
        if resource_id in seen_resources and len(seen_resources) < limit:
            continue
        selected.append({
            "content": chunk.content,
            "metadata": {
                "resource_id": resource_id,
                "file_name": resource.file_name,
                "chunk_index": chunk.chunk_index,
            },
            "resource_id": resource_id,
            "resource_name": resource.file_name,
            "chunk_id": str(chunk.id),
            "chunk_index": chunk.chunk_index,
            "score": 1.0 if score > 0 else 0.5,
        })
        seen_resources.add(resource_id)
        if len(selected) >= limit:
            break
    return selected


async def _retrieve_knowledge(db: AsyncSession, course_id: str, topic: str, top_k: int = 5) -> tuple[str, list[dict]]:
    """检索课程相关知识，返回 prompt 文本和引用来源。"""
    try:
        from app.rag.retriever import Retriever
        from app.rag.post_processor import format_knowledge_for_prompt

        retriever = Retriever(course_id)
        sources = await retriever.search(topic, top_k=top_k, similarity_threshold=0.0)
        if not sources:
            sources = await _fallback_task_sources(db, course_id, topic, limit=top_k)
        if sources:
            return format_knowledge_for_prompt(sources), sources[:top_k]
    except Exception:
        pass

    sources = await _fallback_task_sources(db, course_id, topic, limit=top_k)
    if sources:
        from app.rag.post_processor import format_knowledge_for_prompt
        return format_knowledge_for_prompt(sources), sources
    return "（课程资料不可用）", []


async def generate_task(
    db: AsyncSession,
    course: Course,
    user: User,
    data: TaskGenerateRequest,
) -> dict:
    """生成教学任务：检索知识 → LLM生成 → 写入数据库"""
    # 检索知识
    knowledge, sources = await _retrieve_knowledge(db, str(course.id), data.topic)

    if knowledge == "（课程资料不可用）":
        raise ValidationException(message="知识库相关资源不足", details=[{"field": "topic", "message": "该课程暂无相关资料"}])

    # LLM 生成
    try:
        content = await _call_task_llm(
            topic=data.topic,
            task_type=data.task_type,
            difficulty=data.difficulty,
            additional_instructions=data.additional_instructions,
            knowledge_text=knowledge,
        )
    except Exception as e:
        raise AIServiceException(message=f"任务生成失败: {str(e)}")

    # 生成标题和预估时间
    title = await _generate_task_title(data.topic, data.task_type)
    estimated_time = await _estimate_time(content, data.difficulty)

    # 写入数据库
    task = Task(
        id=uuid.uuid4(),
        course_id=course.id,
        title=title,
        task_type=TaskType(data.task_type),
        topic=data.topic,
        content=content,
        difficulty=TaskDifficulty(data.difficulty),
        estimated_time=estimated_time,
        reference_resources=[
            {
                "resource_id": s.get("resource_id") or s.get("metadata", {}).get("resource_id", ""),
                "resource_name": s.get("resource_name") or s.get("metadata", {}).get("file_name", ""),
                "chunk_id": s.get("chunk_id", ""),
            }
            for s in sources
        ],
        status=TaskStatus.DRAFT,
        created_by=user.id,
    )
    db.add(task)
    await db.commit()
    task = await _load_task_with_creator(db, task.id)

    return _format_task_detail(task)


async def list_tasks(
    db: AsyncSession,
    course_id: str,
    user: User,
    page: int = 1,
    page_size: int = 20,
    task_type: str | None = None,
    difficulty: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    """获取任务列表"""
    conditions = [Task.course_id == course_id]

    # 学生只能看已发布的任务
    if user.role == UserRole.STUDENT:
        conditions.append(Task.status == TaskStatus.PUBLISHED)
    elif status:
        conditions.append(Task.status == status)

    if task_type:
        conditions.append(Task.task_type == task_type)
    if difficulty:
        conditions.append(Task.difficulty == difficulty)
    if keyword:
        conditions.append(
            or_(Task.title.ilike(f"%{keyword}%"), Task.topic.ilike(f"%{keyword}%"))
        )

    total_q = select(func.count(Task.id)).where(and_(*conditions))
    total = (await db.execute(total_q)).scalar() or 0

    q = (
        select(Task)
        .options(selectinload(Task.creator))
        .where(and_(*conditions))
        .order_by(Task.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    tasks = (await db.execute(q)).scalars().all()

    result = [_format_task_list_item(t) for t in tasks]
    return result, total


async def get_task_detail(
    db: AsyncSession,
    task: Task,
    user: User,
) -> dict:
    """获取任务详情"""
    # 学生只能查看已发布的任务
    if user.role == UserRole.STUDENT and task.status != TaskStatus.PUBLISHED:
        raise ForbiddenException(message="该任务尚未发布")

    task = await _load_task_with_creator(db, task.id)
    return _format_task_detail(task)


async def update_task(
    db: AsyncSession,
    task: Task,
    data: TaskUpdateRequest,
) -> dict:
    """更新任务内容（仅限 draft 状态）"""
    if task.status != TaskStatus.DRAFT:
        raise TaskStatusException(message="只能修改草稿状态的任务")

    if data.title is not None:
        task.title = data.title
    if data.content is not None:
        task.content = data.content
    if data.difficulty is not None:
        task.difficulty = TaskDifficulty(data.difficulty)
    if data.estimated_time is not None:
        task.estimated_time = data.estimated_time

    await db.commit()
    task = await _load_task_with_creator(db, task.id)

    return _format_task_detail(task)


async def regenerate_task(
    db: AsyncSession,
    task: Task,
    course: Course,
    user: User,
) -> dict:
    """重新生成任务内容"""
    knowledge, sources = await _retrieve_knowledge(db, str(course.id), task.topic)
    if knowledge == "（课程资料不可用）":
        raise ValidationException(message="知识库相关资源不足", details=[{"field": "topic", "message": "该课程暂无相关资料"}])

    try:
        content = await _call_task_llm(
            topic=task.topic,
            task_type=task.task_type.value if hasattr(task.task_type, 'value') else str(task.task_type),
            difficulty=task.difficulty.value if hasattr(task.difficulty, 'value') else str(task.difficulty),
            additional_instructions=None,
            knowledge_text=knowledge,
        )
    except Exception as e:
        raise AIServiceException(message=f"任务重新生成失败: {str(e)}")

    task.content = content
    task.estimated_time = await _estimate_time(content, task.difficulty.value if hasattr(task.difficulty, 'value') else str(task.difficulty))
    task.reference_resources = [
        {
            "resource_id": s.get("resource_id") or s.get("metadata", {}).get("resource_id", ""),
            "resource_name": s.get("resource_name") or s.get("metadata", {}).get("file_name", ""),
            "chunk_id": s.get("chunk_id", ""),
        }
        for s in sources
    ]
    task.status = TaskStatus.DRAFT

    await db.commit()
    task = await _load_task_with_creator(db, task.id)

    return _format_task_detail(task)


async def publish_task(
    db: AsyncSession,
    task: Task,
) -> dict:
    """发布任务"""
    if task.status != TaskStatus.DRAFT:
        raise TaskStatusException(message="只能发布草稿状态的任务")

    task.status = TaskStatus.PUBLISHED
    await db.commit()
    await db.refresh(task)

    return {
        "id": str(task.id),
        "status": task.status.value,
        "updated_at": str(task.updated_at) if task.updated_at else None,
    }


async def archive_task(
    db: AsyncSession,
    task: Task,
) -> dict:
    """归档任务"""
    task.status = TaskStatus.ARCHIVED
    await db.commit()
    await db.refresh(task)

    return {
        "id": str(task.id),
        "status": task.status.value,
    }


async def delete_task(
    db: AsyncSession,
    task: Task,
    confirm: bool,
) -> None:
    """删除任务"""
    if not confirm:
        raise ValidationException(message="请确认删除")

    await db.delete(task)
    await db.commit()
