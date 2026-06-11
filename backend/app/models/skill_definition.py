# backend/app/models/skill_definition.py — Skill 定义与执行审计模型
import uuid
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, UUIDMixin


class SkillDefinition(Base, UUIDMixin):
    """Skill 定义模型"""
    __tablename__ = "skill_definitions"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="Skill 标识")
    display_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="显示名称")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str] = mapped_column(String(20), nullable=False, server_default="1.0.0")
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    allowed_roles: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'[]'", comment="允许的角色列表")
    input_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="输入 Schema")
    output_schema: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="输出 Schema")

    def __repr__(self) -> str:
        return f"<SkillDefinition(name='{self.name}', enabled={self.enabled})>"


class SkillRun(Base, UUIDMixin):
    """Skill 执行记录模型"""
    __tablename__ = "skill_runs"

    skill_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True,
    )
    input_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    output_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="running")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<SkillRun(skill_name='{self.skill_name}', status='{self.status}')>"
