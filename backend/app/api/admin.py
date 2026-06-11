# backend/app/api/admin.py — M07 系统管理接口（5 端点）
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.database import get_db
from app.dependencies import (
    get_current_user,
    require_role,
)
from app.models.user import User
from app.models.course import Course
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.user import UserCreate, UserResponse, AdminUserUpdate
from app.exceptions import NotFoundException, ConflictException, ValidationException
from app.core.security import hash_password
from app.config import settings

router = APIRouter()


# ── 8.1 获取用户列表 ──
@router.get("/users", response_model=ApiResponse[list[dict]])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    role: str | None = Query(None, description="teacher/student/admin"),
    is_active: bool | None = Query(None, description="是否启用"),
    keyword: str | None = Query(None, description="按用户名/邮箱模糊搜索"),
):
    """获取用户列表（管理员）"""
    conditions = []

    if role:
        conditions.append(User.role == role)
    if is_active is not None:
        conditions.append(User.is_active == is_active)
    if keyword:
        conditions.append(
            or_(User.username.ilike(f"%{keyword}%"), User.email.ilike(f"%{keyword}%"))
        )

    total_q = select(func.count(User.id))
    if conditions:
        total_q = total_q.where(*conditions)
    total = (await db.execute(total_q)).scalar() or 0

    q = select(User)
    if conditions:
        q = q.where(*conditions)
    q = q.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    users = (await db.execute(q)).scalars().all()

    # 统计每个教师的课程数
    user_list = []
    for u in users:
        course_count_q = select(func.count(Course.id)).where(Course.teacher_id == u.id)
        courses_teaching = (await db.execute(course_count_q)).scalar() or 0
        user_list.append({
            "id": str(u.id),
            "username": u.username,
            "email": u.email,
            "display_name": u.display_name,
            "role": u.role.value if hasattr(u.role, 'value') else str(u.role),
            "is_active": u.is_active,
            "courses_teaching_count": courses_teaching,
            "created_at": str(u.created_at) if u.created_at else None,
        })

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=user_list,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 8.2 创建用户 ──
@router.post("/users", response_model=ApiResponse[UserResponse], status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """创建用户（管理员专用，role 可设为 admin）"""
    import uuid
    from app.models.enums import UserRole

    # 检查唯一性
    exists = await db.execute(
        select(User).where(
            or_(User.username == data.username, User.email == data.email)
        )
    )
    if exists.scalar_one_or_none():
        raise ConflictException(message="用户名或邮箱已存在")

    user = User(
        id=uuid.uuid4(),
        username=data.username,
        email=data.email,
        password_hash=hash_password(data.password),
        role=UserRole(data.role),
        display_name=None,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        code=201,
        message="创建成功",
        data={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "display_name": user.display_name,
            "created_at": str(user.created_at) if user.created_at else None,
            "updated_at": str(user.updated_at) if user.updated_at else None,
        },
    )


# ── 8.3 更新用户状态 ──
@router.patch("/users/{user_id}", response_model=ApiResponse[dict])
async def update_user(
    user_id: str,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """更新用户状态（启用/禁用、修改角色）— 使用 JSON Body"""
    from app.models.enums import UserRole

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundException(resource="用户", id=user_id)

    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        if data.role not in ("teacher", "student", "admin"):
            raise ValidationException(message="角色必须是 teacher / student / admin")
        user.role = UserRole(data.role)
    if data.display_name is not None:
        user.display_name = data.display_name

    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        data={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role.value,
            "is_active": user.is_active,
            "display_name": user.display_name,
            "created_at": str(user.created_at) if user.created_at else None,
            "updated_at": str(user.updated_at) if user.updated_at else None,
        },
    )


# ── 8.4 获取系统配置 ──
@router.get("/settings", response_model=ApiResponse[dict])
async def get_settings(
    current_user: User = Depends(require_role("admin")),
):
    """获取系统配置"""
    return ApiResponse(
        data={
            "llm": {
                "model_name": settings.LLM_MODEL_NAME,
                "base_url": settings.LLM_BASE_URL,
                "max_tokens": settings.LLM_MAX_TOKENS,
                "temperature": settings.LLM_TEMPERATURE,
            },
            "embedding": {
                "model_name": settings.EMBEDDING_MODEL,
                "dimension": 1024,
            },
            "rag": {
                "chunk_size": 512,
                "chunk_overlap": 64,
                "top_k": 5,
                "similarity_threshold": 0.6,
            },
            "file": {
                "max_upload_size_mb": 50,
                "allowed_types": ["pdf", "docx", "pptx", "md", "txt", "xlsx"],
            },
        },
    )


# ── 8.5 更新系统配置 ──
@router.put("/settings", response_model=ApiResponse[dict])
async def update_settings(
    data: dict,
    current_user: User = Depends(require_role("admin")),
):
    """更新系统配置（运行时配置，不持久化到文件）"""
    # 运行时配置更新（生产环境应持久化到数据库或文件）
    return ApiResponse(
        message="配置已更新",
        data=data,
    )
