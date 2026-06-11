# backend/app/api/auth.py — M01 认证模块：注册/登录/刷新/个人信息/更新/退出（6 端点）
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.common import ApiResponse
from app.schemas.user import (
    UserCreate,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RefreshRequest,
    TokenRefreshResponse,
    UserUpdate,
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from app.exceptions import (
    ConflictException,
    UnauthorizedException,
    ValidationException,
)

router = APIRouter()


# ============================================================
# 2.1 用户注册
# ============================================================
@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
async def register(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    """用户注册。校验用户名/邮箱唯一性，bcrypt 哈希密码。"""
    # 检查用户名或邮箱是否已存在
    result = await db.execute(
        select(User).where(
            or_(User.username == body.username, User.email == body.email)
        )
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.username == body.username:
            raise ConflictException(message="用户名已存在")
        else:
            raise ConflictException(message="邮箱已被注册")

    # 验证角色合法性
    if body.role not in ("teacher", "student"):
        raise ValidationException(message="角色必须为 teacher 或 student")

    # 创建用户
    user = User(
        username=body.username,
        email=body.email,
        password_hash=hash_password(body.password),
        role=UserRole(body.role),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return ApiResponse(
        code=201,
        message="注册成功",
        data=UserResponse.model_validate(user),
    )


# ============================================================
# 2.2 用户登录
# ============================================================
@router.post("/login", response_model=ApiResponse[TokenResponse])
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """用户登录。支持用户名或邮箱+密码登录。"""
    # 查询用户（用户名或邮箱）
    result = await db.execute(
        select(User).where(
            or_(User.username == body.username, User.email == body.username)
        )
    )
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException(message="用户名或密码错误")

    # 验证密码
    if not verify_password(body.password, user.password_hash):
        raise UnauthorizedException(message="用户名或密码错误")

    # 检查账户状态
    if not user.is_active:
        raise UnauthorizedException(message="账户已被禁用，请联系管理员")

    # 生成 Token
    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    return ApiResponse(
        code=200,
        message="success",
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=7200,
            user=UserResponse.model_validate(user),
        ),
    )


# ============================================================
# 2.3 Token 刷新
# ============================================================
@router.post("/refresh", response_model=ApiResponse[TokenRefreshResponse])
async def refresh_token(
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    """使用 refresh_token 获取新的 access_token。"""
    try:
        payload = verify_token(body.refresh_token)
    except Exception:
        raise UnauthorizedException(
            message="refresh_token 无效或已过期",
            error_type="TOKEN_INVALID",
        )

    if payload.get("type") != "refresh":
        raise UnauthorizedException(
            message="无效的 Token 类型",
            error_type="TOKEN_INVALID",
        )

    # 验证用户仍存在且活跃
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedException(message="用户不存在或已被禁用")

    # 生成新 Token
    new_access_token = create_access_token(user.id, user.role.value)
    new_refresh_token = create_refresh_token(user.id)

    return ApiResponse(
        code=200,
        message="success",
        data=TokenRefreshResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=7200,
            refresh_token=new_refresh_token,
        ),
    )


# ============================================================
# 2.4 获取当前用户信息
# ============================================================
@router.get("/me", response_model=ApiResponse[UserResponse])
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """获取当前登录用户的完整信息。"""
    return ApiResponse(
        code=200,
        message="success",
        data=UserResponse.model_validate(current_user),
    )


# ============================================================
# 2.5 更新当前用户信息
# ============================================================
@router.patch("/me", response_model=ApiResponse[UserResponse])
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新当前用户的显示名称、邮箱或密码（全部可选）。"""
    if body.display_name is not None:
        current_user.display_name = body.display_name

    if body.email is not None:
        # 检查邮箱唯一性
        result = await db.execute(
            select(User).where(
                User.email == body.email,
                User.id != current_user.id,
            )
        )
        if result.scalar_one_or_none():
            raise ConflictException(message="邮箱已被其他用户使用")
        current_user.email = body.email

    if body.password is not None:
        # 验证新密码强度
        if len(body.password) < 8:
            raise ValidationException(message="密码至少 8 个字符")
        current_user.password_hash = hash_password(body.password)

    await db.commit()
    await db.refresh(current_user)

    return ApiResponse(
        code=200,
        message="更新成功",
        data=UserResponse.model_validate(current_user),
    )


# ============================================================
# 2.6 退出登录
# ============================================================
@router.post("/logout", response_model=ApiResponse)
async def logout(
    current_user: User = Depends(get_current_user),
):
    """退出登录。Token 黑名单在阶段四接入 Redis 后补充。"""
    # TODO: 阶段四接入 Redis 后将 Token 加入黑名单
    return ApiResponse(
        code=200,
        message="已退出登录",
        data=None,
    )
