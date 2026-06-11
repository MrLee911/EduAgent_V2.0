# backend/app/models/task.py — 教学任务模型（对应 03 §4.7 tasks 表）
import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, UUIDMixin, TimestampMixin
from .enums import TaskType, TaskDifficulty, TaskStatus


class Task(Base, UUIDMixin, TimestampMixin):
    """教学任务模型。

    对应 03 §4.7 tasks 表。
    """
    __tablename__ = "tasks"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="任务标题",
    )
    task_type: Mapped[TaskType] = mapped_column(
        SAEnum(TaskType, name="task_type"),
        nullable=False,
        comment="class_exercise / homework / lab_guide",
    )
    topic: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        server_default="",
        comment="任务对应章节/主题",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="",
        comment="任务详细内容（Markdown）",
    )
    difficulty: Mapped[TaskDifficulty] = mapped_column(
        SAEnum(TaskDifficulty, name="task_difficulty"),
        nullable=False,
        server_default="medium",
        comment="难度",
    )
    estimated_time: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="",
        comment="预计完成时间",
    )
    reference_resources: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'[]'",
        comment="引用的知识库资源",
    )
    status: Mapped[TaskStatus] = mapped_column(
        SAEnum(TaskStatus, name="task_status"),
        nullable=False,
        server_default="draft",
        comment="draft / published / archived",
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="创建教师",
    )

    # --- 关系 ---
    course: Mapped["Course"] = relationship(back_populates="tasks")
    creator: Mapped["User | None"] = relationship(
        "User",
        back_populates="created_tasks",
        foreign_keys=[created_by],
    )

    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"
