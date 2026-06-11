# backend/app/models/base.py — ORM 基础类（Base + UUIDMixin + TimestampMixin）
import uuid
from datetime import datetime
from sqlalchemy import DateTime, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""
    pass


class UUIDMixin:
    """UUID 主键 Mixin。
    使用 server_default="gen_random_uuid()" 由 PostgreSQL 原生生成，
    保证多实例/应用层无冲突。
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),  # 数据库侧生成
    )


class TimestampMixin:
    """创建/更新时间戳 Mixin。
    - created_at: INSERT 时自动填充
    - updated_at: INSERT + UPDATE 时自动填充
    使用 server_default + onupdate 确保数据库侧时间一致。
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("now()"),
        onupdate=func.now(),
        nullable=False,
    )
