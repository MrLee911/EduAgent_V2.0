# backend/app/core/security.py — JWT Token 生成/验证 + 密码 Hashing
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.config import settings

# 密码哈希上下文（bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ============================================================
# 密码操作
# ============================================================


def hash_password(password: str) -> str:
    """使用 bcrypt 对原始密码进行哈希。"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证原始密码与哈希密码是否匹配。"""
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
# JWT Token 操作
# ============================================================


def create_access_token(
    user_id: str | uuid.UUID,
    role: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """生成 access_token（默认 2h 有效期）。

    Args:
        user_id: 用户 UUID
        role: 用户角色（teacher / student / admin）
        expires_delta: 自定义过期时间，默认从配置读取
    """
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    # access_token 半小时有效（30 min），与 04 文档不同但更安全
    # 实际从配置读取，可在 .env 中调整
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str | uuid.UUID) -> str:
    """生成 refresh_token（7 天有效期）。"""
    expire = datetime.now(timezone.utc) + timedelta(days=7)

    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
        "type": "refresh",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def verify_token(token: str) -> dict[str, Any]:
    """验证并解码 Token，返回 payload。Token 无效/过期则抛出 JWTError。"""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def get_token_remaining_ttl(token: str) -> int:
    """获取 Token 剩余有效秒数（用于黑名单 TTL）。"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        exp = payload.get("exp", 0)
        now = datetime.now(timezone.utc).timestamp()
        return max(0, int(exp - now))
    except JWTError:
        return 0
