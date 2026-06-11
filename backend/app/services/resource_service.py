# backend/app/services/resource_service.py — M03 资源管理业务逻辑
import uuid
import os
import re
import shutil
from pathlib import Path
from urllib.parse import quote, unquote
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.course import Course
from app.models.resource import Resource, Chunk
from app.models.enums import ResourceFileType, ResourceStatus
from app.schemas.resource import (
    ResourceUploadResponseInner, ResourceUploadResponse,
    ResourceListResponse, ResourceDetailResponse, ResourceSearchResponse,
    ResourceStatusResponse, ResourceProgressInfo, ResourceReprocessResponse,
)
from app.exceptions import NotFoundException, ForbiddenException, ValidationException
from app.config import settings

ALLOWED_EXTENSIONS = {"pdf", "docx", "pptx", "md", "txt", "xlsx"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
LOCAL_RESOURCE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage" / "resources"
LOCAL_STORAGE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage"


def _safe_filename(file_name: str) -> str:
    name = os.path.basename(file_name or "resource.md").strip()
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    return name or "resource.md"


def _save_uploaded_file(
    *,
    user_id: str,
    course_id: str,
    resource_id: str,
    file_name: str,
    file_content: bytes,
) -> str:
    safe_name = _safe_filename(file_name)
    target_dir = LOCAL_RESOURCE_ROOT / user_id / course_id / resource_id
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / safe_name).write_bytes(file_content)

    return "/files/resources/" + "/".join(
        quote(part)
        for part in [user_id, course_id, resource_id, safe_name]
    )


def _read_saved_file(file_url: str) -> bytes:
    """Read a previously uploaded local file from its public /files URL."""
    if not file_url or not file_url.startswith("/files/"):
        raise ValidationException(message="找不到原始文件，无法重新处理")

    relative_path = unquote(file_url.removeprefix("/files/")).replace("/", os.sep)
    target_path = (LOCAL_STORAGE_ROOT / relative_path).resolve()
    storage_root = LOCAL_STORAGE_ROOT.resolve()

    if storage_root not in target_path.parents and target_path != storage_root:
        raise ValidationException(message="原始文件路径无效，无法重新处理")
    if not target_path.is_file():
        raise ValidationException(message="原始文件不存在，无法重新处理")

    return target_path.read_bytes()


def _format_resource_list_item(resource: Resource) -> dict:
    """将 Resource 模型转换为列表响应 dict"""
    return {
        "id": str(resource.id),
        "file_name": resource.file_name,
        "file_type": resource.file_type.value if hasattr(resource.file_type, 'value') else str(resource.file_type),
        "file_size": resource.file_size,
        "file_url": resource.file_url or "",
        "status": resource.status.value if hasattr(resource.status, 'value') else str(resource.status),
        "chunk_count": resource.chunk_count,
        "summary": resource.summary or "",
        "uploaded_by": {
            "id": str(resource.uploader.id),
            "display_name": resource.uploader.display_name,
        } if resource.uploader else None,
        "created_at": str(resource.created_at) if resource.created_at else None,
    }


def _format_resource_detail(resource: Resource) -> dict:
    """将 Resource 模型转换为详情响应 dict"""
    return {
        "id": str(resource.id),
        "file_name": resource.file_name,
        "file_type": resource.file_type.value if hasattr(resource.file_type, 'value') else str(resource.file_type),
        "file_size": resource.file_size,
        "file_url": resource.file_url or "",
        "status": resource.status.value if hasattr(resource.status, 'value') else str(resource.status),
        "chunk_count": resource.chunk_count,
        "summary": resource.summary or "",
        "error_message": resource.error_message,
        "uploaded_by": {
            "id": str(resource.uploader.id),
            "display_name": resource.uploader.display_name,
        } if resource.uploader else None,
        "created_at": str(resource.created_at) if resource.created_at else None,
    }


async def upload_resource(
    db: AsyncSession,
    course: Course,
    user: User,
    file,
    minio_path: str = "",
) -> Resource:
    """上传单个资源：验证文件 → 创建 Resource 记录 → 触发 Celery 异步处理
    
    minio_path: MinIO 中存储路径（如果已上传到 MinIO 则传入，否则留空）
    """
    file_name = file.filename
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    # 验证文件类型
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationException(message=f"不支持的文件格式: {ext}，支持: {', '.join(sorted(ALLOWED_EXTENSIONS))}")

    # 验证文件大小
    file.file.seek(0, 2)  # seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # seek back to start
    if file_size > MAX_FILE_SIZE:
        raise ValidationException(message=f"文件超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制")

    # 映射文件类型
    file_type = ResourceFileType(ext)

    # 读取文件内容（用于后续 Celery 处理时使用）
    file_content = await file.read()

    # 保存原始文件到本地静态目录，每个资源单独一个目录，避免同名覆盖。
    resource_id = uuid.uuid4()
    file_url = _save_uploaded_file(
        user_id=str(user.id),
        course_id=str(course.id),
        resource_id=str(resource_id),
        file_name=file_name,
        file_content=file_content,
    )

    # 创建 Resource 记录
    resource = Resource(
        id=resource_id,
        course_id=course.id,
        file_name=file_name,
        file_type=file_type,
        file_size=file_size,
        file_url=minio_path or file_url,
        status=ResourceStatus.UPLOADING,
        uploaded_by=user.id,
    )
    db.add(resource)
    await db.commit()
    await db.refresh(resource)

    # 触发 Celery 异步处理
    try:
        from app.tasks.rag_tasks import process_document
        process_document.delay(
            resource_id=str(resource.id),
            course_id=str(course.id),
            file_content=file_content,
            file_type=ext,
            file_name=file_name,
        )
    except Exception as exc:
        resource.status = ResourceStatus.FAILED
        resource.error_message = f"文档处理任务入队失败: {exc}"
        await db.commit()
        await db.refresh(resource)

    return resource


async def batch_upload_resources(
    db: AsyncSession,
    course: Course,
    user: User,
    files: list,
) -> list[dict]:
    """批量上传资源"""
    if len(files) > 10:
        raise ValidationException(message="单次最多上传 10 个文件")

    results = []
    for file in files:
        try:
            resource = await upload_resource(db, course, user, file)
            results.append({
                "id": str(resource.id),
                "file_name": resource.file_name,
                "file_type": resource.file_type.value if hasattr(resource.file_type, 'value') else str(resource.file_type),
                "file_size": resource.file_size,
                "file_url": resource.file_url or "",
                "status": resource.status.value if hasattr(resource.status, 'value') else str(resource.status),
                "created_at": str(resource.created_at) if resource.created_at else None,
            })
        except Exception as e:
            results.append({
                "file_name": file.filename,
                "error": str(e),
            })

    return results


async def list_resources(
    db: AsyncSession,
    course_id: str,
    page: int = 1,
    page_size: int = 20,
    file_type: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
    sort_by: str = "created_at",
    order: str = "desc",
) -> tuple[list[dict], int]:
    """获取资源列表（分页、筛选、排序）"""
    conditions = [Resource.course_id == course_id]

    if file_type:
        conditions.append(Resource.file_type == file_type)
    if status:
        if status == "processing":
            # processing = uploading | parsing | chunking | embedding
            conditions.append(
                Resource.status.in_([
                    ResourceStatus.UPLOADING,
                    ResourceStatus.PARSING,
                    ResourceStatus.CHUNKING,
                    ResourceStatus.EMBEDDING,
                ])
            )
        else:
            conditions.append(Resource.status == status)
    if keyword:
        conditions.append(Resource.file_name.ilike(f"%{keyword}%"))

    # 总数
    total_q = select(func.count(Resource.id)).where(and_(*conditions))
    total = (await db.execute(total_q)).scalar() or 0

    # 排序
    sort_col = getattr(Resource, sort_by, Resource.created_at)
    if order == "asc":
        sort_col = sort_col.asc()
    else:
        sort_col = sort_col.desc()

    q = (
        select(Resource)
        .options(selectinload(Resource.uploader))
        .where(and_(*conditions))
        .order_by(sort_col)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    resources = (await db.execute(q)).scalars().all()

    result = [_format_resource_list_item(r) for r in resources]
    return result, total


async def get_resource_detail(
    db: AsyncSession,
    resource: Resource,
) -> dict:
    """获取资源详情"""
    resource = (await db.execute(
        select(Resource)
        .options(selectinload(Resource.uploader))
        .where(Resource.id == resource.id)
    )).scalar_one()
    return _format_resource_detail(resource)


async def search_resources(
    db: AsyncSession,
    course_id: str,
    q: str,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[dict], int]:
    """搜索资源：文件名模糊匹配"""
    conditions = [
        Resource.course_id == course_id,
        Resource.file_name.ilike(f"%{q}%"),
    ]

    total_q = select(func.count(Resource.id)).where(and_(*conditions))
    total = (await db.execute(total_q)).scalar() or 0

    q_result = (
        select(Resource)
        .options(selectinload(Resource.uploader))
        .where(and_(*conditions))
        .order_by(Resource.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    resources = (await db.execute(q_result)).scalars().all()

    result = [_format_resource_list_item(r) for r in resources]
    return result, total


async def get_resource_status(
    db: AsyncSession,
    resource: Resource,
) -> dict:
    """获取资源处理状态（轮询接口）"""
    status_val = resource.status.value if hasattr(resource.status, 'value') else str(resource.status)

    # 构建进度信息
    stage_map = {
        "uploading": ("文件上传中", 1),
        "parsing": ("文本解析中", 2),
        "chunking": ("文本切片中", 3),
        "embedding": ("向量化中", 4),
        "ready": ("处理完成", 5),
        "failed": ("处理失败", 0),
    }
    stage_name, stage_index = stage_map.get(status_val, ("未知", 0))

    progress = {
        "stage": stage_name,
        "stage_index": stage_index,
        "total_stages": 5,
        "chunk_count_done": resource.chunk_count if status_val == "ready" else 0,
        "chunk_count_total": resource.chunk_count if status_val == "ready" else 0,
    }

    return {
        "id": str(resource.id),
        "status": status_val,
        "progress": progress,
    }


async def reprocess_resource(
    db: AsyncSession,
    resource: Resource,
) -> dict:
    """重新处理资源：清除旧数据 → 重新触发处理"""
    if resource.status == ResourceStatus.READY or resource.status == ResourceStatus.FAILED:
        # 清除旧 chunks 数据
        from app.rag.vector_store import delete_chunks_by_ids

        # 获取该资源所有 chunk 的 chroma_id
        chunks_result = await db.execute(
            select(Chunk.chroma_id).where(Chunk.resource_id == resource.id)
        )
        chroma_ids = [row[0] for row in chunks_result.all()]

        # 删除 ChromaDB 向量
        if chroma_ids:
            try:
                await delete_chunks_by_ids(str(resource.course_id), chroma_ids)
            except Exception:
                pass

        # 删除 chunks 表记录
        chunks = (await db.execute(
            select(Chunk).where(Chunk.resource_id == resource.id)
        )).scalars().all()
        for chunk in chunks:
            await db.delete(chunk)

        # 更新资源状态
        resource.status = ResourceStatus.PARSING
        resource.chunk_count = 0
        resource.error_message = None
        await db.commit()

        # 触发 Celery 异步重新处理
        try:
            from app.tasks.rag_tasks import process_document
            file_content = _read_saved_file(resource.file_url or "")
            process_document.delay(
                resource_id=str(resource.id),
                course_id=str(resource.course_id),
                file_content=file_content,
                file_type=resource.file_type.value if hasattr(resource.file_type, 'value') else str(resource.file_type),
                file_name=resource.file_name,
            )
        except Exception as exc:
            resource.status = ResourceStatus.FAILED
            resource.error_message = f"文档处理任务入队失败: {exc}"
            await db.commit()
    else:
        resource.status = ResourceStatus.PARSING
        resource.error_message = None
        await db.commit()

    return {
        "id": str(resource.id),
        "status": resource.status.value if hasattr(resource.status, 'value') else str(resource.status),
    }


async def delete_resource(
    db: AsyncSession,
    resource: Resource,
    confirm: bool,
) -> None:
    """删除资源及关联数据"""
    if not confirm:
        raise ValidationException(message="请确认删除")

    course_id = str(resource.course_id)

    # 1. 删除 ChromaDB 向量
    try:
        from app.rag.vector_store import delete_chunks_by_ids
        chunks_result = await db.execute(
            select(Chunk.chroma_id).where(Chunk.resource_id == resource.id)
        )
        chroma_ids = [row[0] for row in chunks_result.all()]
        if chroma_ids:
            delete_chunks_by_ids(course_id, chroma_ids)
    except Exception:
        pass

    # 2. 删除本地保存的原文件目录
    local_resource_dir = LOCAL_RESOURCE_ROOT / str(resource.uploaded_by) / str(resource.course_id) / str(resource.id)
    if local_resource_dir.exists():
        shutil.rmtree(local_resource_dir, ignore_errors=True)

    # 3-5. 删除 chunks 表和 resources 记录（ORM cascade 处理）
    await db.delete(resource)
    await db.commit()

    # MinIO 文件删除由后台处理
