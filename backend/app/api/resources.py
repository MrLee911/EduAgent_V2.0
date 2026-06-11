# backend/app/api/resources.py — M03 资源管理接口（8 端点）
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import (
    get_current_user,
    require_role,
    verify_course_exists,
    verify_course_member,
)
from app.models.user import User
from app.models.course import Course
from app.models.resource import Resource
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.resource import (
    ResourceDeleteConfirm, ResourceUploadResponse, ResourceUploadResponseInner,
    ResourceListResponse, ResourceDetailResponse, ResourceStatusResponse,
    ResourceReprocessResponse,
)
from app.services import resource_service
from app.exceptions import NotFoundException
from app.exceptions import ForbiddenException

router = APIRouter()


def ensure_course_manager(course: Course, user: User) -> None:
    """Only the course owner teacher or an admin can mutate course resources."""
    if user.role.value != "admin" and course.teacher_id != user.id:
        raise ForbiddenException(message="只有课程教师或管理员可以管理课程资源")


# ── 4.1 上传资源 ──
@router.post("/{course_id}/resources/upload", response_model=ApiResponse[ResourceUploadResponse], status_code=202)
async def upload_resource(
    file: UploadFile = File(...),
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """上传文件资源 → 异步处理链路（解析→切片→向量化）"""
    ensure_course_manager(course, current_user)
    resource = await resource_service.upload_resource(db, course, current_user, file)
    return ApiResponse(
        code=202,
        message="文件已接收，正在处理中",
        data={
            "resources": [{
                "id": str(resource.id),
                "file_name": resource.file_name,
                "file_type": resource.file_type.value if hasattr(resource.file_type, 'value') else str(resource.file_type),
                "file_size": resource.file_size,
                "file_url": resource.file_url or "",
                "status": resource.status.value if hasattr(resource.status, 'value') else str(resource.status),
                "created_at": str(resource.created_at) if resource.created_at else None,
            }]
        },
    )


# ── 4.2 批量上传资源 ──
@router.post("/{course_id}/resources/upload-batch", response_model=ApiResponse[ResourceUploadResponse], status_code=202)
async def batch_upload_resources(
    files: list[UploadFile] = File(...),
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """批量上传文件资源（单次最多 10 个）"""
    ensure_course_manager(course, current_user)
    results = await resource_service.batch_upload_resources(db, course, current_user, files)
    return ApiResponse(
        code=202,
        message="文件已接收，正在处理中",
        data={"resources": results},
    )


# ── 4.3 获取资源列表 ──
@router.get("/{course_id}/resources", response_model=ApiResponse[list[ResourceListResponse]])
async def list_resources(
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    file_type: str | None = Query(None, description="pdf/docx/pptx/md/txt/xlsx"),
    status: str | None = Query(None, description="ready/failed/processing"),
    keyword: str | None = Query(None, description="按文件名模糊搜索"),
    sort_by: str = Query("created_at", description="created_at/file_name/file_size"),
    order: str = Query("desc", description="asc/desc"),
):
    """获取资源列表（分页、筛选、排序）"""
    items, total = await resource_service.list_resources(
        db, str(course.id),
        page=page, page_size=page_size,
        file_type=file_type, status=status,
        keyword=keyword, sort_by=sort_by, order=order,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 4.4 搜索资源 ──（必须在 /{resource_id} 之前定义，否则 "search" 会被当作 resource_id）
@router.get("/{course_id}/resources/search", response_model=ApiResponse[list[ResourceListResponse]])
async def search_resources(
    q: str = Query(..., min_length=1, description="搜索关键词"),
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """搜索资源（文件名模糊匹配）"""
    items, total = await resource_service.search_resources(
        db, str(course.id), q,
        page=page, page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 4.5 获取资源详情 ──
@router.get("/{course_id}/resources/{resource_id}", response_model=ApiResponse[ResourceDetailResponse])
async def get_resource_detail(
    resource_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资源详情"""
    from sqlalchemy import select
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.course_id == course.id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise NotFoundException(resource="资源", id=resource_id)
    detail = await resource_service.get_resource_detail(db, resource)
    return ApiResponse(data=detail)


# ── 4.6 获取资源处理状态 ──
@router.get("/{course_id}/resources/{resource_id}/status", response_model=ApiResponse[ResourceStatusResponse])
async def get_resource_status(
    resource_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取资源处理状态（轮询接口）"""
    from sqlalchemy import select
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.course_id == course.id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise NotFoundException(resource="资源", id=resource_id)
    status_data = await resource_service.get_resource_status(db, resource)
    return ApiResponse(data=status_data)


# ── 4.7 重新处理资源 ──
@router.post("/{course_id}/resources/{resource_id}/reprocess", response_model=ApiResponse[ResourceReprocessResponse], status_code=202)
async def reprocess_resource(
    resource_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """重新处理资源（用于处理失败的资源）"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.course_id == course.id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise NotFoundException(resource="资源", id=resource_id)
    data = await resource_service.reprocess_resource(db, resource)
    return ApiResponse(code=202, message="已开始重新处理", data=data)


# ── 4.8 删除资源 ──
@router.delete("/{course_id}/resources/{resource_id}", response_model=ApiResponse)
async def delete_resource(
    resource_id: str,
    data: ResourceDeleteConfirm,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """删除资源及关联数据（需二次确认）"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Resource).where(Resource.id == resource_id, Resource.course_id == course.id)
    )
    resource = result.scalar_one_or_none()
    if not resource:
        raise NotFoundException(resource="资源", id=resource_id)
    await resource_service.delete_resource(db, resource, data.confirm)
    return ApiResponse(message="资源已删除", data=None)
