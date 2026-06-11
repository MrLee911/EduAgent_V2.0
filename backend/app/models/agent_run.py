# backend/app/models/agent_run.py — Agent 执行审计模型
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, UUIDMixin


class AgentRun(Base, UUIDMixin):
    """Agent 执行记录模型"""
    __tablename__ = "agent_runs"

    agent_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="Agent 类型")
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True,
    )
    intent: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="识别的意图")
    selected_skill: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="选中的 Skill")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="running")
    step_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="执行耗时(ms)")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- 关系 ---
    steps: Mapped[list["AgentStep"]] = relationship(
        "AgentStep", back_populates="agent_run", cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<AgentRun(id={self.id}, agent_type='{self.agent_type}', status='{self.status}')>"


class AgentStep(Base, UUIDMixin):
    """Agent 执行步骤模型"""
    __tablename__ = "agent_steps"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False,
    )
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    step_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="步骤名")
    skill_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tool_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    input_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="输入摘要")
    output_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True, comment="输出摘要")
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="running")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- 关系 ---
    agent_run: Mapped["AgentRun"] = relationship(back_populates="steps")

    def __repr__(self) -> str:
        return f"<AgentStep(id={self.id}, step_name='{self.step_name}')>"
