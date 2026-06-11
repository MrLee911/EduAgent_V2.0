# backend/app/schemas/user.py — 用户相关 Pydantic Schema（请求/响应模型）
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from uuid import UUID as UUIDType
from datetime import datetime
import re


class UserCreate(BaseModel):
    """注册请求体（对应 04 §2.1）"""
    username: str = Field(..., min_length=3, max_length=50,
                          description="登录用户名，3~50 字符，字母数字下划线")
    email: str = Field(..., max_length=255, description="邮箱")
    password: str = Field(..., min_length=8, max_length=128,
                          description="密码，8~128 字符，含大小写字母+数字")
    role: str = Field(default="student", description="teacher 或 student")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("邮箱格式不正确")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r"[a-z]", v) or not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写和小写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v


class LoginRequest(BaseModel):
    """登录请求体（对应 04 §2.2）"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="原始密码")


class UserResponse(BaseModel):
    """用户信息响应（对应 04 §2.4 data 结构）"""
    id: str
    username: str
    email: str
    role: str
    display_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid(cls, v: object) -> str:
        if isinstance(v, UUIDType):
            return str(v)
        return v

    @field_validator("created_at", "updated_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class TokenResponse(BaseModel):
    """登录/刷新 Token 响应（对应 04 §2.2 data 结构）"""
    access_token: str
    refresh_token: str = ""
    token_type: str = "bearer"
    expires_in: int = 7200  # 2 小时
    user: Optional[UserResponse] = None


class RefreshRequest(BaseModel):
    """Token 刷新请求体（对应 04 §2.3）"""
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    """Token 刷新响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 7200
    refresh_token: str


class UserUpdate(BaseModel):
    """更新用户信息请求体（对应 04 §2.5，全部可选）"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
            raise ValueError("邮箱格式不正确")
        return v


class AdminUserUpdate(BaseModel):
    """管理员更新用户请求体（对应 04 §8.3，全部可选，使用 JSON Body）"""
    is_active: Optional[bool] = Field(None, description="是否启用")
    role: Optional[str] = Field(None, description="teacher / student / admin")
    display_name: Optional[str] = Field(None, min_length=1, max_length=100, description="显示名称")
