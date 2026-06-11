# backend/app/models/user.py — 用户模型（对应 03 §4.1 users 表）
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, UUIDMixin, TimestampMixin
from .enums import UserRole


class User(Base, UUIDMixin, TimestampMixin):
    """用户模型。

    对应 03 §4.1 users 表。
    """
    __tablename__ = "users"

    # --- 基础字段 ---
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="登录用户名",
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="邮箱（用于找回密码）",
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="bcrypt 哈希",
    )
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, name="user_role"),
        nullable=False,
        server_default="student",
        comment="teacher / student / admin",
    )
    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="显示名称（可选）",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default="true",
        comment="账户是否启用（软删除替代）",
    )

    # --- 关系 ---
    # 教师创建的课程
    courses_teaching: Mapped[list["Course"]] = relationship(
        "Course",
        back_populates="teacher",
        foreign_keys="Course.teacher_id",
    )

    # 课程成员关系（学生/教师）
    course_memberships: Mapped[list["CourseMember"]] = relationship(
        "CourseMember",
        back_populates="user",
    )

    # 上传的资源
    uploaded_resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="uploader",
        foreign_keys="Resource.uploaded_by",
    )

    # 问答记录
    qa_records: Mapped[list["QARecord"]] = relationship(
        "QARecord",
        back_populates="user",
    )

    # 创建的任务
    created_tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="creator",
        foreign_keys="Task.created_by",
    )

    # 生成的报告
    generated_reports: Mapped[list["Report"]] = relationship(
        "Report",
        back_populates="generator",
        foreign_keys="Report.generated_by",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
