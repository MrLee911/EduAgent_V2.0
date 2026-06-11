# backend/app/dependencies.py — FastAPI Dependency 链式注入（6 个 Depends）
from typing import AsyncGenerator
from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.course import Course, CourseMember
from app.models.enums import UserRole
from app.core.security import verify_token
from app.exceptions import UnauthorizedException, ForbiddenException, NotFoundException, CourseAccessException
from app.config import settings

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """解析 JWT Token → 获取当前用户。

    所有需认证接口的基依赖。
    Token 黑名单检查在阶段四接入 Redis 后补充。
    """
    token = credentials.credentials

    # 解码 Token
    try:
        payload = verify_token(token)
    except Exception:
        raise UnauthorizedException(
            message="Token 无效或已过期",
            error_type="TOKEN_INVALID",
        )

    # 验证 Token 类型（只用 access_token）
    if payload.get("type") != "access":
        raise UnauthorizedException(
            message="无效的 Token 类型",
            error_type="TOKEN_INVALID",
        )

    # 查询用户
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedException(message="用户不存在")

    if not user.is_active:
        raise ForbiddenException(message="账户已被禁用")

    return user


def require_role(*roles: str):
    """工厂函数：创建角色权限检查依赖。

    用法：
        current_user: User = Depends(require_role("teacher"))
        current_user: User = Depends(require_role("teacher", "admin"))
    """

    async def _check_role(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role.value not in roles:
            raise ForbiddenException(message=f"需要以下角色之一: {', '.join(roles)}")
        return current_user

    return _check_role


async def verify_course_exists(
    course_id: str,
    db: AsyncSession = Depends(get_db),
) -> Course:
    """验证课程存在。所有 /courses/{course_id}/ 端点的前置依赖。"""
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundException(resource="课程", id=course_id)
    return course


async def verify_course_member(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseMember:
    """验证当前用户是课程成员。

    管理员拥有所有课程访问权限。
    """
    # 管理员可访问所有课程
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(Course).where(Course.id == course_id))
        course = result.scalar_one_or_none()
        if not course:
            raise NotFoundException(resource="课程", id=course_id)
        # 返回虚拟 CourseMember 让下游代码可用
        return CourseMember(
            course_id=course_id,
            user_id=current_user.id,
            role="teacher",
        )

    result = await db.execute(
        select(CourseMember).where(
            CourseMember.course_id == course_id,
            CourseMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise CourseAccessException()
    return member


async def get_optional_user(
    authorization: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> AsyncGenerator[User | None, None]:
    """可选认证：如果携带 Token 则解析用户，否则为 None。

    用于公开接口（如公共课程列表）可选的个性化展示。
    """
    if not authorization or not authorization.startswith("Bearer "):
        yield None
        return

    try:
        token = authorization[len("Bearer "):]
        payload = verify_token(token)
        if payload.get("type") != "access":
            yield None
            return
        result = await db.execute(select(User).where(User.id == payload["sub"]))
        user = result.scalar_one_or_none()
        yield user if (user and user.is_active) else None
    except Exception:
        yield None
