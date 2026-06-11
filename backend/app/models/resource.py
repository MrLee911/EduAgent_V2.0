# backend/app/models/resource.py — 资源模型 + 文本切片模型（对应 03 §4.4/4.5）
import uuid
from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum
from .base import Base, UUIDMixin, TimestampMixin
from .enums import ResourceFileType, ResourceStatus


class Resource(Base, UUIDMixin):
    """资源模型。

    对应 03 §4.4 resources 表。
    """
    __tablename__ = "resources"

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="原始文件名",
    )
    file_type: Mapped[ResourceFileType] = mapped_column(
        SAEnum(ResourceFileType, name="resource_file_type"),
        nullable=False,
        comment="文件格式",
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="文件大小（字节）",
    )
    file_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="MinIO 存储路径",
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default="",
        comment="AI 生成的资源摘要",
    )
    status: Mapped[ResourceStatus] = mapped_column(
        SAEnum(ResourceStatus, name="resource_status"),
        nullable=False,
        server_default="uploading",
        comment="处理状态",
    )
    chunk_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="切片数量",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="处理失败时的错误信息",
    )
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="上传者",
    )
    created_at: Mapped[str] = mapped_column(
        server_default="now()",
        nullable=False,
        comment="上传时间",
    )

    # --- 关系 ---
    course: Mapped["Course"] = relationship(back_populates="resources")
    uploader: Mapped["User"] = relationship(
        "User",
        back_populates="uploaded_resources",
        foreign_keys=[uploaded_by],
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        "Chunk",
        back_populates="resource",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Resource(id={self.id}, file_name='{self.file_name}', status='{self.status}')>"


class Chunk(Base, UUIDMixin):
    """文本切片模型（关系数据库与 ChromaDB 的桥梁）。

    对应 03 §4.5 chunks 表。
    """
    __tablename__ = "chunks"

    resource_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("resources.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属课程（冗余，加速按课程检索）",
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="在源文件中的切片序号",
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="切片文本内容",
    )
    token_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="0",
        comment="Token 数量（用于计费和截断控制）",
    )
    chroma_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="ChromaDB 中对应的向量记录 ID",
    )
    created_at: Mapped[str] = mapped_column(
        server_default="now()",
        nullable=False,
        comment="创建时间",
    )

    # --- 关系 ---
    resource: Mapped["Resource"] = relationship(back_populates="chunks")
    course: Mapped["Course"] = relationship(back_populates="chunks")

    def __repr__(self) -> str:
        return f"<Chunk(id={self.id}, resource_id={self.resource_id}, chunk_index={self.chunk_index})>"
