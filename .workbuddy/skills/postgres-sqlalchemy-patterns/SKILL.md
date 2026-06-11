---
name: postgres-sqlalchemy-patterns
description: >
  PostgreSQL + SQLAlchemy 2.0 实施模式——当 CodeBuddy 开始编写 ORM 模型定义、
  数据库会话管理、Alembic 迁移或复杂查询时触发。覆盖：Base + Mixin 标准、
  枚举类型映射、JSONB 字段查询、关系定义与级联策略、async_sessionmaker 配置、
  Alembic 迁移脚本模板、分页查询模式、事务管理、本项目 8 张表完整模型参考。
agent_created: true
---

# PostgreSQL + SQLAlchemy 2.0 Implementation Patterns

## Purpose

本 Skill 提供教学智能体项目中数据库层的专家级实施模式。涵盖 SQLAlchemy 2.0 声明式映射、
异步会话管理、Alembic 数据库迁移、复杂查询优化及本项目 8 张核心表的完整 ORM 模型定义。

## When to Use

在以下场景中触发本 Skill：
- CodeBuddy 开始编写 `backend/app/models/` 下的任何模型文件
- CodeBuddy 需要定义 `database.py`（`async_sessionmaker` + `get_db` 依赖）
- CodeBuddy 开始运行 `alembic revision --autogenerate` 或手动编写迁移脚本
- CodeBuddy 需要实现 JSONB 字段的查询（`sources` / `statistics` / `reference_resources`）
- CodeBuddy 需要实现带分页的列表查询
- CodeBuddy 需要处理事务（批量插入 `chunks` 等场景）

---

## Core Patterns

### Pattern 1: Base + Mixin 标准模板

**所有模型** 必须继承自 `Base` 和两个 Mixin：

```python
# backend/app/models/base.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""
    pass

class UUIDMixin:
    """UUID 主键 Mixin。

    规则：
    - 所有表主键用 UUID v4（gen_random_uuid()）
    - 不在应用层生成 UUID，由数据库生成（保证分布式一致性）
    """
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",  # ← 数据库侧生成，非 Python 侧
    )

class TimestampMixin:
    """创建/更新时间戳 Mixin。

    规则：
    - `created_at` 在 INSERT 时自动填充（server_default=now()）
    - `updated_at` 在 UPDATE 时自动更新（onupdate=now()）
    - 使用 TIMESTAMPTZ（带时区），存储 UTC
    """
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",  # ← PostgreSQL 函数，非 Python lambda
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default="now()",
        onupdate="now()",  # ← 每次 UPDATE 自动刷新
        nullable=False,
    )
```

**⚠️ 关键决策：`server_default` vs `default`**

| 方式 | 适用场景 | 本项目使用 |
|------|---------|:--:|
| `server_default="gen_random_uuid()"` | 数据库生成 UUID（无需 Python roundtrip） | ✅ 主键 id |
| `server_default="now()"` | 数据库生成时间戳（不需要 Python 对象） | ✅ created_at / updated_at |
| `default=uuid.uuid4` | Python 侧生成（需要读取 id 做后续操作） | ❌ 本项目不用 |
| `default=lambda: datetime.now(timezone.utc)` | Python 侧生成时间戳（灵活但多一次函数调用） | ❌ 本项目不用 |

---

### Pattern 2: PostgreSQL 枚举类型映射

**规则：Python `enum.Enum` → `SAEnum(enum_cls)`**

```python
# backend/app/models/enums.py —— 集中定义所有枚举
import enum

class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"

class CourseStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"

class CourseMemberRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"

class ResourceFileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    MD = "md"
    TXT = "txt"
    XLSX = "xlsx"

class ResourceStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"

class QAFeedback(str, enum.Enum):
    NONE = "none"
    LIKE = "like"
    DISLIKE = "dislike"

class TaskType(str, enum.Enum):
    CLASS_EXERCISE = "class_exercise"
    HOMEWORK = "homework"
    LAB_GUIDE = "lab_guide"

class TaskDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class TaskStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class ReportType(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEMESTER = "semester"
```

**在模型中使用**：

```python
from sqlalchemy import Enum as SAEnum
from .enums import UserRole

class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole),         # ← 映射到 PostgreSQL CREATE TYPE
        nullable=False,
        server_default="student",  # ← 与 Python enum 值对应
    )
```

**⚠️ 关键约束**：
- 枚举在 Alembic 首次迁移中创建（`op.create_table` 之前 `op.execute("CREATE TYPE ...")`）
- 降级迁移中需要 `op.execute("DROP TYPE ...")`
- 不能在 Python 中新增枚举值而不迁移数据库

---

### Pattern 3: 关系定义与级联策略

**本项目外键删除策略速查表**：

| 子表 | 外键 → 父表 | 策略 | 理由 |
|------|-----------|:--:|------|
| courses | teacher_id → users.id | `CASCADE` | 用户删，课删 |
| course_members | course_id → courses.id | `CASCADE` | 课删，成员关系清 |
| course_members | user_id → users.id | `CASCADE` | 用户删，成员关系清 |
| resources | course_id → courses.id | `CASCADE` | 课删，资源删 |
| resources | uploaded_by → users.id | **`SET NULL`** | 用户删，资源留（归课程）|
| chunks | resource_id → resources.id | `CASCADE` | 资源删，切片清 |
| chunks | course_id → courses.id | `CASCADE` | 课删，切片清 |
| qa_records | course_id → courses.id | `CASCADE` | 课删，问答清 |
| qa_records | user_id → users.id | **`SET NULL`** | 用户删，匿名留 |
| tasks | course_id → courses.id | `CASCADE` | 课删，任务清 |
| tasks | created_by → users.id | **`SET NULL`** | 用户删，任务留 |
| reports | course_id → courses.id | `CASCADE` | 课删，报告清 |
| reports | generated_by → users.id | **`SET NULL`** | 用户删，报告留 |

**SQLAlchemy 实现示例**：

```python
# --- CASCADE 示例（课程删除 → 成员关系全清）---
class CourseMember(Base, UUIDMixin):
    __tablename__ = "course_members"
    __table_args__ = (UniqueConstraint("course_id", "user_id"),)

    course_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),  # ← DDL 级别 CASCADE
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 关系定义（ORM 级别）
    course: Mapped["Course"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="course_memberships")

# --- SET NULL 示例（用户删除 → 问答记录留为匿名）---
class QARecord(Base, UUIDMixin):
    __tablename__ = "qa_records"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),  # ← DDL 级别 SET NULL
        nullable=True,  # ← 必须 nullable=True
    )

    user: Mapped["User | None"] = relationship(back_populates="qa_records")
```

**⚠️ CASCADE + relationship(cascade="all, delete-orphan") 组合规则**：

```python
# 只在 "一" 侧使用 cascade="all, delete-orphan"
class Course(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "courses"

    # ↓ ORM 级联：删除 Course 实例时，Child 对象同步删除
    members: Mapped[list["CourseMember"]] = relationship(
        "CourseMember",
        back_populates="course",
        cascade="all, delete-orphan",  # ← ORM 级联
    )
    resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="course",
        cascade="all, delete-orphan",
    )
    tasks: Mapped[list["Task"]] = relationship(
        "Task",
        back_populates="course",
        cascade="all, delete-orphan",
    )
```

---

### Pattern 4: 异步数据库会话配置

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# 1. 异步引擎（连接池配置）
engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://user:pass@host:5432/db
    echo=settings.APP_DEBUG,  # 开发环境打印 SQL
    pool_size=20,             # 连接池大小
    max_overflow=10,          # 溢出连接数
    pool_pre_ping=True,       # 连接前检查有效性（避免 stale connection）
)

# 2. 会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # ← 关键！commit 后不使对象过期
)

# 3. FastAPI 依赖注入
async def get_db() -> AsyncSession:
    """每个请求一个会话，请求结束后自动关闭。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
```

**⚠️ `expire_on_commit=False` 是必须的**：设为 `True`（默认）时，commit 后所有属性标记为 expired，下次访问会触发 lazy load——在异步上下文中会报 `MissingGreenlet` 错误。

**⚠️ `pool_pre_ping=True` 防止 stale 连接**：如果 PostgreSQL 重启或空闲超时断开连接，下次请求会先 `SELECT 1` 检查连接有效性，无效则自动重连。

```python
# backend/app/config.py —— DATABASE_URL 构建
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "edu_agent"
    POSTGRES_USER: str = "edu_agent"
    POSTGRES_PASSWORD: str = "change-me"

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ⚠️ Alembic 用同步 URL
    @property
    def DATABASE_URL_SYNC(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
```

---

### Pattern 5: 模型定义完整模板

**以 User 模型为例——所有模型的规范参考**：

```python
# backend/app/models/user.py
import uuid
from sqlalchemy import String, Boolean
from sqlalchemy.dialects.postgresql import UUID
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
        SAEnum(UserRole),
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
        foreign_keys="Course.teacher_id",  # ← 指定外键，避免歧义
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
```

**⚠️ `foreign_keys=` 参数何时需要**：

| 场景 | 是否需要 `foreign_keys=` |
|------|:--:|
| 表 A 只有一个外键指向表 B | ❌ 不需要 |
| 表 A 有**多个**外键指向表 B（如 User→Course 有两条路径） | ✅ **必须**指定 |
| User 中：`courses_teaching` 通过 `Course.teacher_id`，`course_memberships` 通过 `CourseMember.user_id`——两条不同路径 | ✅ User 需要指定 |

---

### Pattern 6: JSONB 字段查询模式

本项目有 3 个 JSONB 字段：

| 表 | JSONB 字段 | 结构 |
|----|-----------|------|
| qa_records | `sources` | `[{"resource_id": "uuid", "resource_name": "xx.pdf", "chunk_id": "uuid", "chunk_index": 5, "score": 0.92, "text_preview": "..."}]` |
| tasks | `reference_resources` | `[{"resource_id": "uuid", "resource_name": "xx.pdf"}]` |
| reports | `statistics` | `{"total_tasks": 12, "total_qa": 45, "top_questions": [...], "suggestions": [...]}` |

**SQLAlchemy 定义**：

```python
from sqlalchemy.dialects.postgresql import JSONB

class QARecord(Base, UUIDMixin):
    __tablename__ = "qa_records"

    sources: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default="'[]'",  # ← 注意：PostgreSQL JSONB 字符串用单引号包裹
    )
```

**查询 JSONB 字段**：

```python
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import JSONB

# 查询某个 resource_id 被引用过的所有问答（sources 数组包含特定 resource_id）
stmt = (
    select(QARecord)
    .where(
        QARecord.sources.cast(String).contains("550e8400-e29b-41d4-a716-446655440000")
    )
)

# 查询 statistics 中包含特定 key 的报告
stmt = select(Report).where(Report.statistics["total_tasks"].as_float() > 10)

# 查询 suggestions 数组不为空的报告
stmt = select(Report).where(
    Report.statistics["suggestions"].as_string() != "[]"
)
```

**⚠️ JSONB 查询性能提示**：
- 对 JSONB 字段内的高频查询路径建 GIN 索引（本项目暂不需要）
- 避免 `WHERE jsonb_field LIKE '%xxx%'`，用 `@>` 操作符（`contains`）代替

---

### Pattern 7: 分页查询标准模板

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Generic, TypeVar

T = TypeVar("T")

async def paginated_query(
    session: AsyncSession,
    model: type[T],
    page: int = 1,
    per_page: int = 20,
    **filters,
) -> tuple[list[T], int]:
    """通用分页查询。

    Args:
        session: 数据库会话
        model: ORM 模型类
        page: 页码（从 1 开始）
        per_page: 每页条数（默认 20，最大 100）
        **filters: 过滤条件（如 course_id="uuid"）

    Returns:
        (items, total): 当前页数据 + 总条数
    """
    per_page = min(per_page, 100)  # 限制最大 100 条

    # 构建基础查询
    base = select(model)
    for attr, value in filters.items():
        if value is not None:
            base = base.where(getattr(model, attr) == value)

    # 总数查询
    count_stmt = select(func.count()).select_from(base.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    # 分页查询
    offset = (page - 1) * per_page
    items_stmt = base.offset(offset).limit(per_page).order_by(model.created_at.desc())
    items = (await session.execute(items_stmt)).scalars().all()

    return list(items), total
```

**在路由中使用**：

```python
# 对应 API 文档 04 §3 课程资源列表接口
async def list_resources(
    course_id: uuid.UUID,
    page: int = 1,
    per_page: int = 20,
    file_type: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    items, total = await paginated_query(
        session=session,
        model=Resource,
        page=page,
        per_page=per_page,
        course_id=course_id,
        # file_type 需要特殊处理（枚举类型）
    )
    return ApiResponse(
        data=items,
        meta={
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        }
    )
```

---

### Pattern 8: Alembic 迁移脚本模板

**首次迁移（创建所有枚举 + 表）**：

```python
# backend/alembic/versions/001_initial_schema.py
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
    # ⚠️ 枚举必须在建表之前创建
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

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", postgresql.ENUM("teacher", "student", "admin", name="user_role"), nullable=False, server_default="student"),
        sa.Column("display_name", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_role", "users", ["role"])

    # --- courses ---
    op.create_table(
        "courses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(20), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("semester", sa.String(20), nullable=False, server_default=""),
        sa.Column("teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("cover_image", sa.String(500)),
        sa.Column("status", postgresql.ENUM("active", "archived", name="course_status"), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_courses_teacher", "courses", ["teacher_id"])
    op.create_index("idx_courses_status", "courses", ["status"])

    # --- course_members ---
    op.create_table(
        "course_members",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", postgresql.ENUM("teacher", "student", name="course_member_role"), nullable=False, server_default="student"),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("course_id", "user_id"),
    )
    op.create_index("idx_cm_user", "course_members", ["user_id"])

    # --- resources ---
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_type", postgresql.ENUM("pdf", "docx", "pptx", "md", "txt", "xlsx", name="resource_file_type"), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_url", sa.String(1000), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("status", postgresql.ENUM("uploading", "parsing", "chunking", "embedding", "ready", "failed", name="resource_status"), nullable=False, server_default="uploading"),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text()),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_resources_course", "resources", ["course_id"])
    op.create_index("idx_resources_status", "resources", ["status"])
    op.create_index("idx_resources_type", "resources", ["file_type"])

    # --- chunks ---
    op.create_table(
        "chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("chroma_id", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_chunks_resource", "chunks", ["resource_id"])
    op.create_index("idx_chunks_course", "chunks", ["course_id"])

    # --- qa_records ---
    op.create_table(
        "qa_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("feedback", postgresql.ENUM("none", "like", "dislike", name="qa_feedback"), nullable=False, server_default="none"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_qa_course", "qa_records", ["course_id"])
    op.create_index("idx_qa_user", "qa_records", ["user_id"])
    op.create_index("idx_qa_created", "qa_records", ["created_at"])

    # --- tasks ---
    op.create_table(
        "tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("task_type", postgresql.ENUM("class_exercise", "homework", "lab_guide", name="task_type"), nullable=False),
        sa.Column("topic", sa.String(200), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("difficulty", postgresql.ENUM("easy", "medium", "hard", name="task_difficulty"), nullable=False, server_default="medium"),
        sa.Column("estimated_time", sa.String(20), nullable=False, server_default=""),
        sa.Column("reference_resources", postgresql.JSONB(), nullable=False, server_default="'[]'"),
        sa.Column("status", postgresql.ENUM("draft", "published", "archived", name="task_status"), nullable=False, server_default="draft"),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_tasks_course", "tasks", ["course_id"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_type", "tasks", ["task_type"])

    # --- reports ---
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("course_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_type", postgresql.ENUM("weekly", "monthly", "semester", name="report_type"), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("statistics", postgresql.JSONB(), nullable=False, server_default="'{}'"),
        sa.Column("generated_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_reports_course", "reports", ["course_id"])
    op.create_index("idx_reports_dates", "reports", ["course_id", "start_date", "end_date"])


def downgrade() -> None:
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
```

---

### Pattern 9: 批量事务处理（chunks 插入 + ChromaDB 写入）

```python
# backend/app/services/chunk_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chunk import Chunk
from app.models.resource import Resource
import uuid

async def batch_insert_chunks(
    session: AsyncSession,
    resource_id: uuid.UUID,
    course_id: uuid.UUID,
    chunks_data: list[dict],  # [{"content": "...", "chroma_id": "...", "token_count": 384, "chunk_index": 0}, ...]
) -> None:
    """批量插入 chunks 并更新 resource 状态。

    事务要求：
    1. 所有 chunks 和 resource 状态更新在同一事务中
    2. 如果 ChromaDB 写入失败（在 Celery 任务中），这里的 PostgreSQL 数据保留但 resource.status 回退到 'failed'
    """
    async with session.begin():  # ← 自动 commit/rollback
        # 批量插入 chunks
        chunks = [
            Chunk(
                resource_id=resource_id,
                course_id=course_id,
                chunk_index=cd["chunk_index"],
                content=cd["content"],
                token_count=cd["token_count"],
                chroma_id=cd["chroma_id"],
            )
            for cd in chunks_data
        ]
        session.add_all(chunks)

        # 更新 resource 状态和 chunk 计数
        resource = await session.get(Resource, resource_id)
        resource.status = "embedding"  # chunks 已写，等待 ChromaDB
        resource.chunk_count = len(chunks_data)

    # 事务已提交，现在可以在 Celery 任务中异步写入 ChromaDB
    # ...
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern 1: 在应用层生成 UUID

```python
# 错误：Python 侧生成 UUID
class User(Base, UUIDMixin):
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,  # ❌ Python 生成
    )
```

**问题**：多实例部署时可能产生冲突；Python 需要生成 UUID 对象（内存分配）。

**✅ 正确**：用 `server_default="gen_random_uuid()"`——由 PostgreSQL 原生生成。

---

### ❌ Anti-Pattern 2: 忘记 `onupdate="now()"` on `updated_at`

```python
# 错误：updated_at 只在 INSERT 时设置
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default="now()",  # ← 只有 default，没有 onupdate
)
```

**问题**：UPDATE 时 `updated_at` 不变，无法追踪修改时间。

**✅ 正确**：加 `onupdate="now()"`。

---

### ❌ Anti-Pattern 3: 同步代码在 async 会话中

```python
# 错误：在 async def 中调用同步 session
async def get_users(session: AsyncSession):
    users = session.execute(select(User)).all()  # ❌ 同步 .all()
    return users
```

**问题**：`AsyncSession.execute()` 返回 `Result`，不能直接 `.all()`。

**✅ 正确**：
```python
async def get_users(session: AsyncSession):
    result = await session.execute(select(User))  # ← await
    return result.scalars().all()                  # ← .scalars().all()
```

---

### ❌ Anti-Pattern 4: 忘记 `expire_on_commit=False`

```python
# 错误
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession)
# 默认 expire_on_commit=True
```

**问题**：commit 后访问对象属性会触发 `MissingGreenlet` 错误（异步上下文无法 lazy load）。

**✅ 正确**：显式设置 `expire_on_commit=False`。

---

### ❌ Anti-Pattern 5: JSONB 字段用 Python dict 初始化为 `{}`

```python
# 错误
sources: Mapped[dict] = mapped_column(JSONB, default={})
```

**问题**：`{}` 是可变默认值，多实例共享同一 dict 引用。

**✅ 正确**：用 `server_default="'[]'"` 或 `default_factory=list`。

---

### ❌ Anti-Pattern 6: 多个外键指向同一父表时不指定 `foreign_keys=`

```python
# 错误
class User(Base, UUIDMixin, TimestampMixin):
    courses_teaching: Mapped[list["Course"]] = relationship("Course", back_populates="teacher")
    course_memberships: Mapped[list["CourseMember"]] = relationship("CourseMember", back_populates="user")
    # ❌ SQLAlchemy 不知道 courses_teaching 走哪条路径
```

**问题**：SQLAlchemy 无法确定 `relationship` 和 `ForeignKey` 的对应关系，报 `AmbiguousForeignKeysError`。

**✅ 正确**：加 `foreign_keys=` 参数。

---

### ❌ Anti-Pattern 7: 在 `.env` 中硬编码同步 URL，异步 URL 手动拼接

```python
# 错误
DATABASE_URL=postgresql://user:pass@host/db  # ← 同步 URL
DATABASE_URL_ASYNC=postgresql+asyncpg://user:pass@host/db  # ← 手动拼接
```

**问题**：两个环境变量不同步（改密码/主机时容易漏一个）。

**✅ 正确**：用一个 Pydantic Settings `@property` 自动生成异步 URL。

---

## Project-Specific Constraints

### 约束 1: 模型文件 → 表映射（强制一致）

| ORM 模型文件 | 表名 | 对应 03 文档章节 |
|-------------|------|:--:|
| `models/base.py` | (Mixin，无表) | §6.1 |
| `models/enums.py` | (枚举，无表) | §3 |
| `models/user.py` | `users` | §4.1 |
| `models/course.py` | `courses` | §4.2 |
| `models/course_member.py` | `course_members` | §4.3 |
| `models/resource.py` | `resources` | §4.4 |
| `models/chunk.py` | `chunks` | §4.5 |
| `models/qa_record.py` | `qa_records` | §4.6 |
| `models/task.py` | `tasks` | §4.7 |
| `models/report.py` | `reports` | §4.8 |

### 约束 2: `models/__init__.py` 导入所有模型（Alembic 需要）

```python
# backend/app/models/__init__.py
from .base import Base, UUIDMixin, TimestampMixin
from .user import User
from .course import Course
from .course_member import CourseMember
from .resource import Resource
from .chunk import Chunk
from .qa_record import QARecord
from .task import Task
from .report import Report

__all__ = [
    "Base", "UUIDMixin", "TimestampMixin",
    "User", "Course", "CourseMember",
    "Resource", "Chunk", "QARecord",
    "Task", "Report",
]
```

**⚠️ 注意**：`Base.metadata` 需要所有模型被 import 后才能发现表；缺少 `__init__.py` 导入会导致 `alembic revision --autogenerate` 生成空迁移。

### 约束 3: ChromaDB ↔ PostgreSQL 双库一致性

`chunks.chroma_id` 是两库之间的唯一连接键：

```python
# 删除资源时的双库清理流程（在 Celery 任务中执行）
async def delete_resource_with_chunks(
    session: AsyncSession,
    chroma_client,  # ChromaDB 客户端
    resource_id: uuid.UUID,
) -> None:
    # 1. 查 PostgreSQL 中所有关联的 chroma_id
    stmt = select(Chunk.chroma_id).where(Chunk.resource_id == resource_id)
    result = await session.execute(stmt)
    chroma_ids = result.scalars().all()

    # 2. 删除 ChromaDB 中的向量
    collection = chroma_client.get_collection(f"course_{course_id}")
    if chroma_ids:
        collection.delete(ids=list(chroma_ids))  # ChromaDB 删除

    # 3. 删除 PostgreSQL 中的 chunks（CASCADE 会自动处理）
    resource = await session.get(Resource, resource_id)
    await session.delete(resource)
    await session.commit()
```

### 约束 4: `alembic.ini` 配置模板

```ini
# backend/alembic.ini
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://edu_agent:change-me@postgres:5432/edu_agent
# ⚠️ 注意：这里用同步 URL（asyncpg 不支持 DDL）

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

# ...
```

### 约束 5: 数据库初始化脚本

```python
# backend/app/init_db.py —— 开发环境首次启动时调用
from app.database import engine, AsyncSessionLocal
from app.models import Base
from app.models.enums import *  # 确保导入所有模型

async def init_db():
    """创建所有表（仅开发环境使用，生产用 Alembic）。"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ All tables created successfully.")

async def seed_demo_data():
    """插入演示数据（可选）。"""
    # ...
```

---

## 速查表

| 我要做什么 | 看哪个 Pattern | 产出文件 |
|-----------|:--:|---------|
| 创建所有 ORM 模型 | Pattern 1 + 5 | `models/*.py` × 8 |
| 定义枚举类型 | Pattern 2 | `models/enums.py` |
| 设置外键 + 级联 | Pattern 3 | 各模型文件 |
| 配置 async_sessionmaker | Pattern 4 | `database.py` |
| 写 JSONB 字段 | Pattern 6 | `models/qa_record.py` / `models/task.py` / `models/report.py` |
| 实现分页查询 | Pattern 7 | 各 `services/*.py` |
| 生成首次迁移 | Pattern 8 | `alembic/versions/001_*.py` |
| 批量插入 + 事务 | Pattern 9 | `services/chunk_service.py` |
| 双库一致性清理 | 约束 3 | `services/resource_service.py` |

---

## 与项目文档兼容性

| 文档 | 兼容性说明 |
|------|-----------|
| [03_数据模型与数据库设计.md](../../../docs/03_数据模型与数据库设计.md) | 本 Skill 的所有表结构、枚举、索引、外键策略与 03 完全一致。`server_default` 值（如 `"gen_random_uuid()"`）与 03 DDL 对应。 |
| [02_技术架构文档.md](../../../docs/02_技术架构文档.md) | PostgreSQL 16 + SQLAlchemy 2.0 + Alembic 技术栈一致。目录结构 `backend/app/models/` + `backend/app/database.py` 路径对应。`async_sessionmaker` 与 FastAPI 的 `Depends(get_db)` 衔接（参见 [fastapi-async-patterns](../../fastapi-async-patterns/SKILL.md) Pattern 5）。 |
| [01_项目需求规格文档.md](../../../docs/01_项目需求规格文档.md) | 每张表对应一个功能模块需求（FR-01→users, FR-02→courses/members, FR-03→resources/chunks, FR-04→qa_records, FR-05→tasks, FR-06→reports）。 |
| [04_API接口文档.md](../../../docs/04_API接口文档.md) | API Schema 的字段名和类型与 ORM 模型字段对应。分页查询的 `page/per_page/total` 与 API 响应 `meta` 字段对应。 |
