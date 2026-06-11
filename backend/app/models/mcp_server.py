# backend/app/models/mcp_server.py — MCP Server 与工具调用审计模型
import uuid
from sqlalchemy import String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base, UUIDMixin


class MCPServer(Base, UUIDMixin):
    """MCP Server 配置模型"""
    __tablename__ = "mcp_servers"

    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    transport: Mapped[str] = mapped_column(String(20), nullable=False, server_default="internal")
    endpoint: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")
    allowed_roles: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default="'[]'")

    def __repr__(self) -> str:
        return f"<MCPServer(name='{self.name}', enabled={self.enabled})>"


class MCPToolCall(Base, UUIDMixin):
    """MCP 工具调用审计模型"""
    __tablename__ = "mcp_tool_calls"

    server_name: Mapped[str] = mapped_column(String(100), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    course_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("courses.id", ondelete="SET NULL"), nullable=True,
    )
    arguments_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="running")
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<MCPToolCall(tool_name='{self.tool_name}', status='{self.status}')>"
