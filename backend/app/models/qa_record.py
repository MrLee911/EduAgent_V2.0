# backend/app/models/qa_record.py — 问答记录模型（对应 03 §4.6 qa_records 表）
import uuid
from sqlalchemy import Text, ForeignKey, String, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, UUIDMixin
from .enums import QAFeedback


class QARecord(Base, UUIDMixin):
    """问答记录模型。

    对应 03 §4.6 qa_records 表。
    """
    __tablename__ = "qa_records"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="提问者（删除后 Anonymous）",
    )
    conversation_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default="",
        comment="对话 ID，用于关联多轮对话",
    )
    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="用户问题",
    )
    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="智能体回答（Markdown）",
    )
    sources: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'[]'",
        comment="引用来源 JSONB",
    )
    feedback: Mapped[QAFeedback] = mapped_column(
        SAEnum(QAFeedback, name="qa_feedback"),
        nullable=False,
        server_default="none",
        comment="用户反馈",
    )
    created_at: Mapped[str] = mapped_column(
        server_default="now()",
        nullable=False,
        comment="提问时间",
    )

    __table_args__ = (
        Index("ix_qa_records_course_user_created", "course_id", "user_id", "created_at"),
        Index("ix_qa_records_conversation", "conversation_id"),
    )

    # --- 关系 ---
    course: Mapped["Course"] = relationship(back_populates="qa_records")
    user: Mapped["User | None"] = relationship(back_populates="qa_records")

    def __repr__(self) -> str:
        return f"<QARecord(id={self.id}, question='{self.question[:50]}...')"
