# backend/app/api/courses.py — M02 课程管理接口（8 端点）
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
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseDeleteConfirm, CourseJoinRequest,
    CourseListResponse, CourseDetailResponse, CourseCreateResponse,
    CourseJoinResponse, CourseMemberResponse, CourseMemberAddRequest,
)
from app.services import course_service

router = APIRouter()


# ── 3.1 创建课程 ──
@router.post("", response_model=ApiResponse[CourseCreateResponse], status_code=201)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """创建课程：生成课程码 → 写入 courses → 写入 course_members → 创建 ChromaDB Collection"""
    result = await course_service.create_course(db, current_user, data)
    return ApiResponse(code=201, message="课程创建成功", data=result)


# ── 3.2 获取课程列表 ──
@router.get("", response_model=ApiResponse[list[CourseListResponse]])
async def list_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role_filter: str | None = Query(None, description="teaching / joined"),
    status: str | None = Query(None, description="active / archived"),
    keyword: str | None = Query(None, description="按课程名称模糊搜索"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程列表（支持分页、角色筛选、状态筛选、关键词搜索）"""
    items, total = await course_service.list_courses(
        db, current_user,
        page=page, page_size=page_size,
        role_filter=role_filter, status=status, keyword=keyword,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 3.3 获取课程详情 ──
@router.get("/{course_id}", response_model=ApiResponse[CourseDetailResponse])
async def get_course_detail(
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程详情（含统计信息和当前用户角色）"""
    result = await course_service.get_course_detail(db, course, current_user)
    return ApiResponse(data=result)


# ── 3.4 更新课程信息 ──
@router.patch("/{course_id}", response_model=ApiResponse[CourseDetailResponse])
async def update_course(
    data: CourseUpdate,
    course: Course = Depends(verify_course_exists),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新课程信息（仅教师和管理员可操作）"""
    if current_user.role.value != "admin" and course.teacher_id != current_user.id:
        from app.exceptions import ForbiddenException
        raise ForbiddenException(message="只有课程教师可以修改课程信息")
    result = await course_service.update_course(db, course, data)
    return ApiResponse(data=result)


# ── 3.5 删除课程 ──
@router.delete("/{course_id}", response_model=ApiResponse)
async def delete_course(
    data: CourseDeleteConfirm,
    course: Course = Depends(verify_course_exists),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """删除课程及所有关联数据（级联清理，需二次确认）"""
    if current_user.role.value != "admin" and course.teacher_id != current_user.id:
        from app.exceptions import ForbiddenException
        raise ForbiddenException(message="只有课程教师或管理员可以删除课程")
    await course_service.delete_course(db, course, data.confirm, data.confirm_text)
    return ApiResponse(message="课程已删除", data=None)


# ── 3.6 通过课程码加入课程 ──
@router.post("/join", response_model=ApiResponse[CourseJoinResponse], status_code=201)
async def join_course(
    data: CourseJoinRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """通过课程码加入课程（学生专用）"""
    result = await course_service.join_course(db, current_user, data)
    return ApiResponse(code=201, message="成功加入课程", data=result)


# ── 3.7 获取课程成员列表 ──
@router.get("/{course_id}/members", response_model=ApiResponse[list[CourseMemberResponse]])
async def get_course_members(
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
):
    """获取课程成员列表"""
    result = await course_service.get_course_members(db, course)
    return ApiResponse(data=result)


# ── 3.8 添加课程学生 ──
@router.post("/{course_id}/members", response_model=ApiResponse[CourseMemberResponse], status_code=201)
async def add_course_student(
    data: CourseMemberAddRequest,
    course: Course = Depends(verify_course_exists),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教师或管理员按用户名/邮箱添加学生到课程。"""
    if current_user.role.value != "admin" and course.teacher_id != current_user.id:
        from app.exceptions import ForbiddenException
        raise ForbiddenException(message="只有课程教师或管理员可以添加学生")
    result = await course_service.add_course_student(db, course, data)
    return ApiResponse(code=201, message="学生已加入课程", data=result)


# ── 3.9 退出课程 ──
@router.delete("/{course_id}/members/me", response_model=ApiResponse)
async def leave_course(
    course: Course = Depends(verify_course_exists),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """退出课程（学生退出；教师不可退出自己创建的课程）"""
    await course_service.leave_course(db, course, current_user)
    return ApiResponse(message="已退出课程", data=None)


# ── 3.10 移出课程学生 ──
@router.delete("/{course_id}/members/{member_id}", response_model=ApiResponse)
async def remove_course_member(
    member_id: str,
    course: Course = Depends(verify_course_exists),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """教师或管理员从课程中移出学生。"""
    if current_user.role.value != "admin" and course.teacher_id != current_user.id:
        from app.exceptions import ForbiddenException
        raise ForbiddenException(message="只有课程教师或管理员可以移出学生")
    await course_service.remove_course_member(db, course, member_id)
    return ApiResponse(message="学生已移出课程", data=None)
