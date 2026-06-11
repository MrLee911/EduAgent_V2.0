# backend/app/models/__init__.py — 全量模型导入（Alembic 可发现全部模型）
from .base import Base, UUIDMixin, TimestampMixin
from .enums import (
    UserRole,
    CourseStatus,
    CourseMemberRole,
    ResourceFileType,
    ResourceStatus,
    QAFeedback,
    TaskType,
    TaskDifficulty,
    TaskStatus,
    ReportType,
)
from .user import User
from .course import Course, CourseMember
from .resource import Resource, Chunk
from .qa_record import QARecord
from .task import Task
from .report import Report
from .agent_run import AgentRun, AgentStep
from .skill_definition import SkillDefinition, SkillRun
from .mcp_server import MCPServer, MCPToolCall

__all__ = [
    # Base + Mixins
    "Base",
    "UUIDMixin",
    "TimestampMixin",
    # Enums
    "UserRole",
    "CourseStatus",
    "CourseMemberRole",
    "ResourceFileType",
    "ResourceStatus",
    "QAFeedback",
    "TaskType",
    "TaskDifficulty",
    "TaskStatus",
    "ReportType",
    # Models
    "User",
    "Course",
    "CourseMember",
    "Resource",
    "Chunk",
    "QARecord",
    "Task",
    "Report",
    # Agent / Skill / MCP 审计模型
    "AgentRun",
    "AgentStep",
    "SkillDefinition",
    "SkillRun",
    "MCPServer",
    "MCPToolCall",
]
