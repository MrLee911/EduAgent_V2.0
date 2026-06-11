"""Initial schema: enums + 8 tables

Revision ID: 001
Revises:
Create Date: 2026-06-09
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """创建所有枚举 + 8 张表 + 21 个索引。"""
    # ============================================================
    # PostgreSQL 扩展（gen_random_uuid 在 PG14+ 内置，PG13 及以下需要 pgcrypto）
    # ============================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # ============================================================
    # 枚举类型（建表之前创建）
    # ============================================================
    op.execute("CREATE TYPE user_role AS ENUM ('teacher', 'student', 'admin')")
    op.execute("CREATE TYPE course_status AS ENUM ('active', 'archived')")
    op.execute("CREATE TYPE course_member_role AS ENUM ('teacher', 'student')")
    op.execute("CREATE TYPE resource_file_type AS ENUM ('pdf', 'docx', 'pptx', 'md', 'txt', 'xlsx')")
    op.execute("CREATE TYPE resource_status AS ENUM ('uploading', 'parsing', 'chunking', 'embedding', 'ready', 'failed')")
    op.execute("CREATE TYPE qa_feedback AS ENUM ('none', 'like', 'dislike')")
    op.execute("CREATE TYPE task_type AS ENUM ('class_exercise', 'homework', 'lab_guide')")
    op.execute("CREATE TYPE task_difficulty AS ENUM ('easy', 'medium', 'hard')")
    op.execute("CREATE TYPE task_status AS ENUM ('draft', 'published', 'archived')")
    op.execute("CREATE TYPE report_type AS ENUM ('weekly', 'monthly', 'semester')")

    # ============================================================
    # 1. users
    # ============================================================
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("teacher", "student", "admin", name="user_role", create_type=False),
                  nullable=False, server_default="student"),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # ============================================================
    # 2. courses
    # ============================================================
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("semester", sa.String(20), nullable=False, server_default=""),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cover_image", sa.String(500)),
        sa.Column("status", postgresql.ENUM("active", "archived", name="course_status", create_type=False),
                  nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_courses_teacher", "courses", ["teacher_id"])
    op.create_index("idx_courses_status", "courses", ["status"])

    # ============================================================
    # 3. course_members
    # ============================================================
    op.create_table(
        "course_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", postgresql.ENUM("teacher", "student", name="course_member_role", create_type=False),
                  nullable=False, server_default="student"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.UniqueConstraint("course_id", "user_id"),
    )
    op.create_index("idx_cm_user", "course_members", ["user_id"])

    # ============================================================
    # 4. resources
    # ============================================================
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_type", postgresql.ENUM(
            "pdf", "docx", "pptx", "md", "txt", "xlsx", name="resource_file_type", create_type=False),
            nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_url", sa.String(1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", postgresql.ENUM(
            "uploading", "parsing", "chunking", "embedding", "ready", "failed",
            name="resource_status", create_type=False), nullable=False, server_default="uploading"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_resources_course", "resources", ["course_id"])
    op.create_index("idx_resources_status", "resources", ["status"])
    op.create_index("idx_resources_type", "resources", ["file_type"])

    # ============================================================
    # 5. chunks
    # ============================================================
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chroma_id", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_chunks_resource", "chunks", ["resource_id"])
    op.create_index("idx_chunks_course", "chunks", ["course_id"])

    # ============================================================
    # 6. qa_records
    # ============================================================
    op.create_table(
        "qa_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("feedback", postgresql.ENUM("none", "like", "dislike", name="qa_feedback", create_type=False),
                  nullable=False, server_default="none"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_qa_course", "qa_records", ["course_id"])
    op.create_index("idx_qa_user", "qa_records", ["user_id"])
    op.create_index("idx_qa_created", "qa_records", ["created_at"])

    # ============================================================
    # 7. tasks
    # ============================================================
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("task_type", postgresql.ENUM(
            "class_exercise", "homework", "lab_guide", name="task_type", create_type=False), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty", postgresql.ENUM("easy", "medium", "hard", name="task_difficulty", create_type=False),
                  nullable=False, server_default="medium"),
        sa.Column("estimated_time", sa.String(20), nullable=False, server_default=""),
        sa.Column("reference_resources", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'[]'::jsonb")),
        sa.Column("status", postgresql.ENUM("draft", "published", "archived", name="task_status", create_type=False),
                  nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_tasks_course", "tasks", ["course_id"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_type", "tasks", ["task_type"])

    # ============================================================
    # 8. reports
    # ============================================================
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type", postgresql.ENUM(
            "weekly", "monthly", "semester", name="report_type", create_type=False), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("statistics", postgresql.JSONB(), nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text("now()")),
    )
    op.create_index("idx_reports_course", "reports", ["course_id"])
    op.create_index("idx_reports_dates", "reports", ["course_id", "start_date", "end_date"])


def downgrade() -> None:
    """回滚：删除 8 张表 + 10 个枚举。"""
    # 删除表（按依赖逆序）
    op.drop_table("reports")
    op.drop_table("tasks")
    op.drop_table("qa_records")
    op.drop_table("chunks")
    op.drop_table("resources")
    op.drop_table("course_members")
    op.drop_table("courses")
    op.drop_table("users")

    # 删除枚举类型（按创建时的逆序）
    op.execute("DROP TYPE report_type")
    op.execute("DROP TYPE task_status")
    op.execute("DROP TYPE task_difficulty")
    op.execute("DROP TYPE task_type")
    op.execute("DROP TYPE qa_feedback")
    op.execute("DROP TYPE resource_status")
    op.execute("DROP TYPE resource_file_type")
    op.execute("DROP TYPE course_member_role")
    op.execute("DROP TYPE course_status")
    op.execute("DROP TYPE user_role")
