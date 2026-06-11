# backend/app/models/report.py — 教学报告模型（对应 03 §4.8 reports 表）
import uuid
from datetime import date
from sqlalchemy import String, Text, Date, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, UUIDMixin
from .enums import ReportType


class Report(Base, UUIDMixin):
    """教学报告模型。

    对应 03 §4.8 reports 表。
    """
    __tablename__ = "reports"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    report_type: Mapped[ReportType] = mapped_column(
        SAEnum(ReportType, name="report_type"),
        nullable=False,
        comment="weekly / monthly / semester",
    )
    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="统计起始日期",
    )
    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="统计截止日期",
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="报告标题（自动生成）",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="",
        comment="报告正文（Markdown）",
    )
    statistics: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'{}'",
        comment="量化统计数据 JSONB",
    )
    generated_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="生成者",
    )
    created_at: Mapped[str] = mapped_column(
        server_default="now()",
        nullable=False,
        comment="生成时间",
    )

    # --- 关系 ---
    course: Mapped["Course"] = relationship(back_populates="reports")
    generator: Mapped["User | None"] = relationship(
        "User",
        back_populates="generated_reports",
        foreign_keys=[generated_by],
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, title='{self.title}', report_type='{self.report_type}')>"
