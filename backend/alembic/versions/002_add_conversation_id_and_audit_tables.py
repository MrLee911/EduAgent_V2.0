"""Add conversation_id to qa_records, pgcrypto extension, agent audit tables

Revision ID: 002
Revises: 001
Create Date: 2026-06-11
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 确保 pgcrypto 扩展可用（PG13 及以下需要；PG14+ 内置但不影响）
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. qa_records 添加 conversation_id 列
    op.add_column(
        "qa_records",
        sa.Column("conversation_id", sa.String(255), nullable=False, server_default=""),
    )

    # 3. 添加索引
    op.create_index(
        "ix_qa_records_course_user_created",
        "qa_records",
        ["course_id", "user_id", "created_at"],
    )
    op.create_index(
        "ix_qa_records_conversation",
        "qa_records",
        ["conversation_id"],
    )

    # 4. agent_runs 审计表
    op.create_table(
        "agent_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_type", sa.String(100), nullable=False, comment="Agent 类型"),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("intent", sa.String(100), nullable=True, comment="识别的意图"),
        sa.Column("selected_skill", sa.String(100), nullable=True, comment="选中的 Skill"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running",
                   comment="running / completed / failed"),
        sa.Column("step_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer, nullable=True, comment="执行耗时(ms)"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True,
                   server_default=sa.text("now()")),
    )
    op.create_index("ix_agent_runs_user", "agent_runs", ["user_id"])
    op.create_index("ix_agent_runs_course", "agent_runs", ["course_id"])
    op.create_index("ix_agent_runs_status", "agent_runs", ["status"])

    # 5. agent_steps 审计表
    op.create_table(
        "agent_steps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("agent_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("step_index", sa.Integer, nullable=False),
        sa.Column("step_name", sa.String(100), nullable=False, comment="步骤名"),
        sa.Column("skill_name", sa.String(100), nullable=True),
        sa.Column("tool_name", sa.String(100), nullable=True),
        sa.Column("input_summary", postgresql.JSONB, nullable=True, comment="输入摘要"),
        sa.Column("output_summary", postgresql.JSONB, nullable=True, comment="输出摘要"),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_steps_run", "agent_steps", ["agent_run_id"])

    # 6. skill_definitions 表
    op.create_table(
        "skill_definitions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True, comment="Skill 标识"),
        sa.Column("display_name", sa.String(200), nullable=False, comment="显示名称"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("version", sa.String(20), nullable=False, server_default="1.0.0"),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_roles", postgresql.JSONB, nullable=False,
                   server_default=sa.text("'[]'::jsonb"),
                   comment="允许的角色列表"),
        sa.Column("input_schema", postgresql.JSONB, nullable=True, comment="输入 Schema"),
        sa.Column("output_schema", postgresql.JSONB, nullable=True, comment="输出 Schema"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True,
                   server_default=sa.text("now()")),
    )

    # 7. skill_runs 审计表
    op.create_table(
        "skill_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("skill_name", sa.String(100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_summary", postgresql.JSONB, nullable=True),
        sa.Column("output_summary", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )
    op.create_index("ix_skill_runs_user", "skill_runs", ["user_id"])
    op.create_index("ix_skill_runs_course", "skill_runs", ["course_id"])

    # 8. mcp_servers 表
    op.create_table(
        "mcp_servers",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("transport", sa.String(20), nullable=False, server_default="internal"),
        sa.Column("endpoint", sa.String(500), nullable=True),
        sa.Column("enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("allowed_roles", postgresql.JSONB, nullable=False,
                   server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True,
                   server_default=sa.text("now()")),
    )

    # 9. mcp_tool_calls 审计表
    op.create_table(
        "mcp_tool_calls",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                   server_default=sa.text("gen_random_uuid()")),
        sa.Column("server_name", sa.String(100), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("arguments_summary", postgresql.JSONB, nullable=True),
        sa.Column("result_summary", postgresql.JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("latency_ms", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                   server_default=sa.text("now()")),
    )
    op.create_index("ix_mcp_tool_calls_user", "mcp_tool_calls", ["user_id"])
    op.create_index("ix_mcp_tool_calls_course", "mcp_tool_calls", ["course_id"])


def downgrade() -> None:
    op.drop_table("mcp_tool_calls")
    op.drop_table("mcp_servers")
    op.drop_table("skill_runs")
    op.drop_table("skill_definitions")
    op.drop_table("agent_steps")
    op.drop_table("agent_runs")

    op.drop_index("ix_qa_records_conversation", "qa_records")
    op.drop_index("ix_qa_records_course_user_created", "qa_records")
    op.drop_column("qa_records", "conversation_id")
