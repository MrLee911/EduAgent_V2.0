# backend/app/models/course.py — 课程模型 + 课程成员模型（对应 03 §4.2/4.3）
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, UUIDMixin, TimestampMixin
from .enums import CourseStatus, CourseMemberRole


class Course(Base, UUIDMixin, TimestampMixin):
    """课程模型。

    对应 03 §4.2 courses 表。
    """
    __tablename__ = "courses"

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="课程名称，如 'Python 程序设计'",
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        comment="课程码（6位字母数字，系统生成）",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="",
        comment="课程描述",
    )
    semester: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default="",
        comment="学期，如 '2026年春季'",
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="授课教师",
    )
    cover_image: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="封面图 URL",
    )
    status: Mapped[CourseStatus] = mapped_column(
        SAEnum(CourseStatus, name="course_status"),
        nullable=False,
        server_default="active",
        comment="active / archived",
    )

    # --- 关系 ---
    teacher: Mapped["User"] = relationship(
        "User",
        back_populates="courses_teaching",
        foreign_keys=[teacher_id],
    )
    members: Mapped[list["CourseMember"]] = relationship(
        "CourseMember",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    qa_records: Mapped[list["QARecord"]] = relationship(
        "QARecord",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="course",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, name='{self.name}', code='{self.code}')>"


class CourseMember(Base, UUIDMixin):
    """课程成员模型（多对多关系表）。

    对应 03 §4.3 course_members 表。
    """
    __tablename__ = "course_members"
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[CourseMemberRole] = mapped_column(
        SAEnum(CourseMemberRole, name="course_member_role"),
        nullable=False,
        server_default="student",
    )
    joined_at: Mapped[datetime] = mapped_column(
        server_default="now()",
        nullable=False,
        comment="加入时间",
    )

    # --- 关系 ---
    course: Mapped["Course"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="course_memberships")

    def __repr__(self) -> str:
        return f"<CourseMember(course_id={self.course_id}, user_id={self.user_id}, role='{self.role}')>"
