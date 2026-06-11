# backend/app/api/tasks.py — M05 教学任务接口（8 端点）
from fastapi import APIRouter, Depends, Query
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
from app.models.task import Task
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.task import (
    TaskGenerateRequest, TaskUpdateRequest, TaskDeleteConfirm,
    TaskResponse, TaskListResponse, TaskStatusResponse,
)
from app.services import task_service
from app.exceptions import NotFoundException, ForbiddenException

router = APIRouter()


def ensure_course_manager(course: Course, user: User) -> None:
    if user.role.value != "admin" and course.teacher_id != user.id:
        raise ForbiddenException(message="只有课程教师或管理员可以管理教学任务")


# ── 6.1 生成教学任务 ──
@router.post("/{course_id}/tasks/generate", response_model=ApiResponse[TaskResponse], status_code=201)
async def generate_task(
    data: TaskGenerateRequest,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """生成教学任务：检索知识→LLM生成→写入数据库"""
    ensure_course_manager(course, current_user)
    result = await task_service.generate_task(db, course, current_user, data)
    return ApiResponse(code=201, message="任务生成成功", data=result)


# ── 6.2 获取任务列表 ──
@router.get("/{course_id}/tasks", response_model=ApiResponse[list[TaskListResponse]])
async def list_tasks(
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    task_type: str | None = Query(None, description="class_exercise/homework/lab_guide"),
    difficulty: str | None = Query(None, description="easy/medium/hard"),
    status: str | None = Query(None, description="draft/published/archived"),
    keyword: str | None = Query(None, description="按标题/主题模糊搜索"),
):
    """获取任务列表（教师看全部，学生只看已发布）"""
    items, total = await task_service.list_tasks(
        db, str(course.id), current_user,
        page=page, page_size=page_size,
        task_type=task_type, difficulty=difficulty,
        status=status, keyword=keyword,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 6.3 获取任务详情 ──
@router.get("/{course_id}/tasks/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task_detail(
    task_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取任务详情"""
    from sqlalchemy import select
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.course_id == course.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(resource="任务", id=task_id)
    detail = await task_service.get_task_detail(db, task, current_user)
    return ApiResponse(data=detail)


# ── 6.4 更新任务内容 ──
@router.patch("/{course_id}/tasks/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task(
    task_id: str,
    data: TaskUpdateRequest,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """更新任务内容（仅限 draft 状态）"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.course_id == course.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(resource="任务", id=task_id)
    detail = await task_service.update_task(db, task, data)
    return ApiResponse(data=detail)


# ── 6.5 重新生成任务 ──
@router.post("/{course_id}/tasks/{task_id}/regenerate", response_model=ApiResponse[TaskResponse])
async def regenerate_task(
    task_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """重新生成任务内容（保留原参数，重新调用LLM）"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.course_id == course.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(resource="任务", id=task_id)
    detail = await task_service.regenerate_task(db, task, course, current_user)
    return ApiResponse(data=detail)


# ── 6.6 发布任务 ──
@router.post("/{course_id}/tasks/{task_id}/publish", response_model=ApiResponse[TaskStatusResponse])
async def publish_task(
    task_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """发布任务（仅限 draft 状态）"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.course_id == course.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(resource="任务", id=task_id)
    detail = await task_service.publish_task(db, task)
    return ApiResponse(message="任务已发布", data=detail)


# ── 6.7 归档任务 ──
@router.post("/{course_id}/tasks/{task_id}/archive", response_model=ApiResponse[TaskStatusResponse])
async def archive_task(
    task_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """归档任务"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.course_id == course.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(resource="任务", id=task_id)
    detail = await task_service.archive_task(db, task)
    return ApiResponse(message="任务已归档", data=detail)


# ── 6.8 删除任务 ──
@router.delete("/{course_id}/tasks/{task_id}", response_model=ApiResponse)
async def delete_task(
    task_id: str,
    data: TaskDeleteConfirm,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """删除任务（需二次确认）"""
    ensure_course_manager(course, current_user)
    from sqlalchemy import select
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.course_id == course.id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise NotFoundException(resource="任务", id=task_id)
    await task_service.delete_task(db, task, data.confirm)
    return ApiResponse(message="任务已删除", data=None)
