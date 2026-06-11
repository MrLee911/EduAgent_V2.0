---
name: fastapi-async-patterns
description: >
  FastAPI 异步端点与项目结构实施模式——当 CodeBuddy 开始编写 FastAPI 路由、
  SSE 流式响应、Celery 后台任务、Pydantic Schema 或 Dependency 注入时触发。
  覆盖：async def 使用决策树、SSE StreamingResponse 标准模板、Celery 任务定义与调用、
  Depends 链式注入模式、统一响应包装、异常处理层次、本项目 38 个端点的异步/同步分类表、
  APIRouter 模块拆分规范。
agent_created: true
---

# FastAPI Async Implementation Patterns

## Purpose

本 Skill 提供教学智能体项目中 FastAPI 后端的专家级实施模式。
当 CodeBuddy 需要编写 FastAPI 应用入口、路由端点、SSE 流式响应、Celery 后台任务
或 Pydantic 请求/响应模型时，应使用本 Skill 中的模式和参数。

## When to Use

在以下场景中触发本 Skill：
- CodeBuddy 开始搭建 FastAPI 应用入口（`main.py`）
- CodeBuddy 开始编写 APIRouter 路由文件（`api/*.py`）
- CodeBuddy 需要实现 SSE 流式响应（`StreamingResponse`）
- CodeBuddy 需要定义 Celery 后台任务
- CodeBuddy 需要编写 Depends 依赖注入函数
- CodeBuddy 需要定义 Pydantic Schema（请求体/响应体）
- CodeBuddy 需要处理异常和统一错误响应

---

## Pattern 1: 应用入口与路由注册

### 主应用入口 `backend/app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import api_router
from app.config import settings
from app.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建数据库表（开发环境，生产用 Alembic）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时：释放连接池
    await engine.dispose()


app = FastAPI(
    title="EduAgent API",
    description="课程资源与教学任务智能体后端接口",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置（开发环境全开放）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(api_router, prefix="/api/v1")
```

### 路由汇总 `backend/app/api/router.py`

```python
from fastapi import APIRouter
from app.api import auth, users, courses, resources, qa, tasks, reports, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户"])
api_router.include_router(courses.router, prefix="/courses", tags=["课程"])
api_router.include_router(resources.router, prefix="/courses", tags=["资源"])
api_router.include_router(qa.router, prefix="/courses", tags=["问答"])
api_router.include_router(tasks.router, prefix="/courses", tags=["任务"])
api_router.include_router(reports.router, prefix="/courses", tags=["报告"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理"])
```

**关键规则**：`resources`、`qa`、`tasks`、`reports` 四个模块使用 `/courses/{course_id}/...` 路径，但通过不同 `APIRouter` 文件拆分，CodeBuddy 按模块独立实现。

---

## Pattern 2: async def 使用决策树

**这是 CodeBuddy 最容易出错的点：该用 async 的地方没用，不该用的地方反而加了 async。**

```
┌─────────────────────────────────────────────────────────────┐
│                    这个端点是否需要 async?                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  端点内部是否有 I/O 等待？                                    │
│  (DB 查询 / LLM 调用 / HTTP 请求 / Redis 操作 / 文件读写)     │
│          │                                                  │
│     ┌────┴────┐                                             │
│     │  是      │  否（纯计算 / 无等待）                       │
│     ▼         ▼                                             │
│  async def   def                                            │
│  配合        SQLAlchemy async 版本                          │
│  await       async def get_db()                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 本项目 38 个端点分类

**必须用 `async def`（含 I/O 等待）**：

| 模块 | 端点 | I/O 操作 |
|------|------|---------|
| auth | 注册/登录/Token刷新/退出 | DB 读写 + Redis |
| courses | CRUD + 加入/退出/成员列表 | DB 读写 |
| resources | 上传/列表/详情/搜索/删除 | DB 读写 + MinIO + Celery 投递 |
| qa | 问答/SSE流式/历史/详情 | ChromaDB + LLM 调用 + DB 读写 |
| tasks | 生成/CRUD/发布/归档 | LLM 调用 + DB 读写 |
| reports | 生成/导出 | LLM 调用 + DB 聚合 |
| admin | CRUD | DB 读写 |

**结论：本项目 38 个端点全部使用 `async def`。**

### 标准端点模板

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.response import ApiResponse

router = APIRouter()

@router.get("/courses", response_model=ApiResponse)
async def list_courses(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取课程列表"""
    # 1. 业务逻辑（Service 层）
    result = await course_service.list_courses(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    # 2. 统一响应包装
    return ApiResponse(
        code=200,
        message="success",
        data=result.items,
        meta={
            "page": page,
            "page_size": page_size,
            "total": result.total,
            "total_pages": result.total_pages,
        },
    )
```

---

## Pattern 3: SSE 流式响应标准模板

### FastAPI 端点实现

```python
import asyncio
import json
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator


async def sse_event_generator(
    course_id: str,
    question: str,
    user_id: str,
    conversation_id: str,
) -> AsyncGenerator[str, None]:
    """SSE 事件生成器——核心流式管道"""

    try:
        # === 阶段 1: thinking ===
        yield format_sse("thinking", {"message": "正在检索相关知识..."})

        # === 阶段 2: RAG 检索 ===
        sources = await rag_service.search_and_rerank(
            course_id=course_id,
            query=question,
            top_k=5,
        )

        if not sources:
            yield format_sse("error", {
                "type": "KNOWLEDGE_BASE_EMPTY",
                "message": "该课程暂无资源，请先上传教学资料"
            })
            return

        yield format_sse("sources", {
            "sources": [{"resource_name": s["file_name"], "score": s["score"]} for s in sources]
        })

        # === 阶段 3: LLM 流式生成 ===
        full_answer = ""
        async for chunk in llm_service.stream_generate(
            question=question,
            context=sources,
            conversation_id=conversation_id,
        ):
            full_answer += chunk
            yield format_sse("token", {"content": chunk})

            # 每 30 秒发一次 keepalive（防止浏览器超时断开）
            # （如果 chunk 输出间隔本身就 < 30s，不需要额外处理）

        # === 阶段 4: 存储结果 ===
        qa_record = await qa_service.save_qa_record(
            db=db,
            course_id=course_id,
            user_id=user_id,
            question=question,
            answer=full_answer,
            sources=sources,
            conversation_id=conversation_id,
        )

        yield format_sse("done", {
            "id": str(qa_record.id),
            "conversation_id": conversation_id,
            "sources": qa_record.sources,
            "created_at": qa_record.created_at.isoformat(),
        })

    except Exception as e:
        yield format_sse("error", {
            "type": "INTERNAL_ERROR",
            "message": str(e)
        })


@router.post("/{course_id}/qa/ask-stream")
async def ask_stream(
    course_id: str,
    body: QAAskRequest,
    current_user: User = Depends(get_current_user),
):
    """流式问答端点"""
    # 验证课程权限
    await deps.verify_course_member(course_id, current_user.id)

    return StreamingResponse(
        sse_event_generator(
            course_id=course_id,
            question=body.question,
            user_id=str(current_user.id),
            conversation_id=body.conversation_id or str(uuid4()),
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx 禁用缓冲
        },
    )
```

### SSE 格式化工具函数

```python
def format_sse(event: str, data: dict) -> str:
    """格式化为 SSE 事件字符串"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
```

### 5 种 SSE 事件类型（本项目标准）

| 事件类型 | 触发时机 | 前端行为 |
|---------|---------|---------|
| `thinking` | RAG 检索阶段 | 显示骨架屏 + 状态文案 |
| `sources` | 检索完成 | 渲染来源引用卡片（文件名+相似度） |
| `token` | LLM 逐 token 输出 | 追加到 Markdown 渲染区域 |
| `done` | 回答完成 | 推送完整结果到历史列表、停止 loading |
| `error` | 任何阶段失败 | 显示错误 Toast、恢复输入框 |

### 关键约束

- **不要用 `BackgroundTasks`**：BackgroundTasks 不支持流式，只能用 `StreamingResponse`
- **AsyncGenerator 必须用 `try/except` 包裹**：否则异常不会以 SSE 格式返回，浏览器端收不到错误事件
- **Nginx 配置必须加 `proxy_buffering off`**：否则 SSE 会被缓冲，前端收不到逐 token

---

## Pattern 4: Celery 后台任务

### 为什么用 Celery 而不是 BackgroundTasks

| 方案 | 优点 | 缺点 | 适合场景 |
|------|------|------|---------|
| `BackgroundTasks` | 零配置、代码简单 | 进程内执行、不持久化 | 发送邮件通知（< 5s） |
| **Celery** ✅ | 进程隔离、持久化、重试 | 需 Redis Broker + Worker 进程 | **文件处理（> 10s）** |

**本项目选择 Celery 的原因**：文件上传后需要解析 → 分块 → Embedding → 写 ChromaDB + PostgreSQL，整个 Pipeline 可能需要 30s-2min，BackgroundTasks 随时可能因 Uvicorn worker 重启而丢失任务。

### Celery 配置 `backend/app/celery_app.py`

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "eduagent",
    broker=settings.CELERY_BROKER_URL,     # redis://redis:6379/0
    backend=settings.CELERY_RESULT_BACKEND, # redis://redis:6379/0
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,           # 任务执行完成后才确认（防止崩溃丢失）
    worker_prefetch_multiplier=1,  # 每次只取 1 个任务（公平调度）
    task_soft_time_limit=300,      # 软超时 5 分钟
    task_time_limit=600,           # 硬超时 10 分钟
)
```

### 任务定义 `backend/app/tasks/resource_processing.py`

```python
from app.celery_app import celery_app
from app.services.resource_service import ResourceService
from app.database import async_session_factory


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def process_resource(self, resource_id: str, file_path: str, course_id: str):
    """处理上传的资源文件：解析 → 分块 → Embedding → 存储"""
    try:
        # Celery task 是同步的，需要 new_event_loop 来运行 async 代码
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _process():
            async with async_session_factory() as db:
                service = ResourceService(db)
                await service.process_resource(
                    resource_id=resource_id,
                    file_path=file_path,
                    course_id=course_id,
                )

        loop.run_until_complete(_process())
        loop.close()

    except Exception as exc:
        # 重试机制
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=1)
def delete_resource_chunks(self, chroma_ids: list[str]):
    """删除资源对应的向量数据"""
    try:
        from app.agent.tools.vectordb import get_chroma_client
        client = get_chroma_client()
        collection = client.get_collection("course_materials")
        collection.delete(ids=chroma_ids)
    except Exception as exc:
        raise self.retry(exc=exc)
```

### 在路由中调用 Celery 任务

```python
from app.tasks.resource_processing import process_resource

@router.post("/{course_id}/resources/upload")
async def upload_resource(
    course_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # 1. 保存文件到 MinIO
    file_key = await storage_service.upload_file(file, course_id)

    # 2. 创建 resource 记录（status=processing）
    resource = await resource_service.create_resource(
        db=db,
        course_id=course_id,
        file_name=file.filename,
        file_key=file_key,
        file_size=file.size,
        uploader_id=current_user.id,
    )

    # 3. 投递 Celery 异步任务（不等待）
    process_resource.delay(
        resource_id=str(resource.id),
        file_path=file_key,
        course_id=course_id,
    )

    # 4. 立即返回（状态为 processing）
    return ApiResponse(
        code=201,
        message="文件已上传，正在处理中",
        data={"resource_id": str(resource.id), "status": "processing"},
    )
```

**关键约束**：
- `process_resource.delay()` 是**异步投递**，调用后立即返回，不阻塞请求
- 前端通过 `GET /courses/{course_id}/resources/{resource_id}` 轮询 status 字段
- 不要同步等待 Celery 结果（`.get()`），这会让请求阻塞 30s-2min

---

## Pattern 5: Dependency 链式注入

### 核心依赖函数 `backend/app/dependencies.py`

```python
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.course import Course, CourseMember
from app.core.security import decode_access_token
from app.core.redis import redis_client

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """解析 JWT Token → 获取当前用户（所有需认证接口的基依赖）"""
    token = credentials.credentials

    # 1. 检查 Token 是否在黑名单中（退出登录）
    is_blacklisted = await redis_client.get(f"blacklist:{token}")
    if is_blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "TOKEN_INVALID", "message": "Token 已失效，请重新登录"},
        )

    # 2. 解码 Token
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "TOKEN_INVALID", "message": "Token 无效或已过期"},
        )

    # 3. 查询用户
    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"type": "UNAUTHORIZED", "message": "用户不存在"},
        )

    return user


async def require_role(role: str):
    """工厂函数：创建角色权限检查依赖"""
    async def _check_role(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"type": "FORBIDDEN", "message": f"需要 {role} 权限"},
            )
        return current_user
    return _check_role


async def verify_course_member(
    course_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CourseMember:
    """验证当前用户是课程成员（所有课程级接口的基依赖）"""
    result = await db.execute(
        select(CourseMember).where(
            CourseMember.course_id == course_id,
            CourseMember.user_id == current_user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"type": "FORBIDDEN", "message": "你不是该课程的成员"},
        )
    return member
```

### 依赖链使用示例

```python
# 认证 + 课程成员 → 返回课程详情
@router.get("/{course_id}")
async def get_course(
    course_id: str,
    course: Course = Depends(verify_course_exists),      # 先验证课程存在
    member: CourseMember = Depends(verify_course_member), # 再验证用户是成员
):
    ...

# 认证 + 教师角色 → 创建课程
@router.post("/")
async def create_course(
    body: CourseCreateRequest,
    current_user: User = Depends(require_role("teacher")), # 必须是教师
    db: AsyncSession = Depends(get_db),
):
    ...
```

### 本项目依赖链汇总

| 依赖函数 | 检查内容 | 用于哪些端点 |
|---------|---------|------------|
| `get_current_user` | JWT 解析 + 黑名单 + 用户存在 | 所有需认证的端点 |
| `require_role("teacher")` | 角色 = teacher 或 admin | 课程 CRUD、任务发布、报告生成 |
| `require_role("admin")` | 角色 = admin | 用户管理、系统配置 |
| `verify_course_member` | 用户 ∈ course_members | 所有 `/courses/{course_id}/` 端点 |
| `verify_course_exists` | 课程存在性 | 所有 `/courses/{course_id}/` 端点 |
| `get_db` | 数据库会话（AsyncSession） | 所有需 DB 操作的端点 |

---

## Pattern 6: 统一异常处理

### 自定义异常类 `backend/app/exceptions.py`

```python
class AppException(Exception):
    """应用基础异常"""
    def __init__(self, status_code: int, error_type: str, message: str):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message


class NotFoundException(AppException):
    def __init__(self, resource: str, id: str):
        super().__init__(
            status_code=404,
            error_type="NOT_FOUND",
            message=f"{resource} 不存在: {id}",
        )


class ForbiddenException(AppException):
    def __init__(self, message: str = "权限不足"):
        super().__init__(status_code=403, error_type="FORBIDDEN", message=message)


class AIServiceException(AppException):
    def __init__(self, message: str = "AI 服务暂不可用"):
        super().__init__(status_code=502, error_type="AI_SERVICE_ERROR", message=message)


class KnowledgeBaseEmptyException(AppException):
    def __init__(self):
        super().__init__(
            status_code=400,
            error_type="KNOWLEDGE_BASE_EMPTY",
            message="该课程暂无资源，请先上传教学资料",
        )
```

### 全局异常处理器 `backend/app/main.py` 追加

```python
from fastapi import Request
from fastapi.responses import JSONResponse
from app.exceptions import AppException
from app.schemas.response import ErrorInfo, ErrorDetail

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "data": None,
            "error": {
                "type": exc.error_type,
                "details": [{"message": exc.message}],
            },
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """兜底：未预期的异常统一返回 500"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "error": {
                "type": "INTERNAL_ERROR",
                "details": [{"message": str(exc)}],  # 生产环境去掉 str(exc)
            },
        },
    )
```

### 异常处理层次

```
用户请求
  │
  ├── 正常 → ApiResponse(code=2xx)
  │
  ├── 业务异常 (AppException) → app_exception_handler → 统一错误格式
  │   ├── NotFoundException (404)
  │   ├── ForbiddenException (403)
  │   ├── AIServiceException (502)
  │   └── KnowledgeBaseEmptyException (400)
  │
  ├── FastAPI 内置异常 (HTTPException) → 默认处理 → 统一错误格式
  │
  └── 未预期异常 (Exception) → global_exception_handler → 500 统一格式
```

---

## Pattern 7: 异步数据库操作

### 数据库连接 `backend/app/database.py`

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings
from app.models.base import Base

engine = create_async_engine(
    settings.DATABASE_URL,  # postgresql+asyncpg://user:pass@postgres:5432/eduagent
    echo=settings.DB_ECHO,  # 开发环境 True，生产 False
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,     # 连接前检查有效性
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不使对象过期
)


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

### 异步查询示例

```python
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

async def get_paginated_courses(
    db: AsyncSession,
    user_id: str,
    page: int,
    page_size: int,
) -> tuple[list[Course], int]:
    """分页获取用户参与的课程列表"""
    # 总数查询
    count_query = select(func.count()).select_from(Course).join(CourseMember).where(
        CourseMember.user_id == user_id,
        CourseMember.status == "active",
    )
    total = (await db.execute(count_query)).scalar_one()

    # 数据查询
    data_query = (
        select(Course)
        .join(CourseMember)
        .where(CourseMember.user_id == user_id, CourseMember.status == "active")
        .order_by(Course.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    courses = (await db.execute(data_query)).scalars().all()

    return courses, total
```

---

## Anti-Patterns (What NOT to Do)

### ❌ AP1: BackgroundTasks 做长任务

```python
# ❌ 错误：文件处理可能 30s+，BackgroundTasks 会随 worker 重启丢失
from fastapi import BackgroundTasks

@router.post("/upload")
async def upload(file: UploadFile, background_tasks: BackgroundTasks):
    resource = await save_resource(db, file)
    background_tasks.add_task(process_file, resource.id)  # 危险！
    return {"status": "ok"}
```

```python
# ✅ 正确：用 Celery 投递异步任务
from app.tasks.resource_processing import process_resource

@router.post("/upload")
async def upload(file: UploadFile):
    resource = await save_resource(db, file)
    process_resource.delay(resource_id=str(resource.id), file_path=file_key)  # 安全！
    return ApiResponse(code=201, message="文件已上传，正在处理中", ...)
```

### ❌ AP2: SSE 生成器没有 try/except

```python
# ❌ 错误：异常会以 500 HTML 格式返回，前端 EventSource 无法解析
async def sse_generator():
    sources = await rag_search()  # 如果这里抛异常，浏览器收到乱码
    yield format_sse("sources", sources)
```

```python
# ✅ 正确：用 try/except 兜底，任何异常都以 SSE error 事件返回
async def sse_generator():
    try:
        sources = await rag_search()
        yield format_sse("sources", sources)
    except Exception as e:
        yield format_sse("error", {"type": "INTERNAL_ERROR", "message": str(e)})
```

### ❌ AP3: Celery 任务内同步调用 async 函数

```python
# ❌ 错误：直接在 Celery 任务中 await（Celery task 不是 async）
@celery_app.task
def process_file(file_path: str):
    result = await rag_service.process(file_path)  # SyntaxError！
```

```python
# ✅ 正确：通过 new_event_loop 运行 async 代码
@celery_app.task
def process_file(file_path: str):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(rag_service.process(file_path))
    finally:
        loop.close()
    return result
```

### ❌ AP4: 依赖注入忘记 await

```python
# ❌ 错误：SQLAlchemy async 查询忘记 await
async def get_user(db: AsyncSession, user_id: str):
    result = db.execute(select(User).where(User.id == user_id))  # 返回 coroutine，不是结果！
    return result.scalar_one_or_none()  # AttributeError: 'coroutine' object has no attribute 'scalar_one_or_none'
```

```python
# ✅ 正确：所有 async DB 操作必须 await
async def get_user(db: AsyncSession, user_id: str):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### ❌ AP5: 分页接口忘记返回 meta

```python
# ❌ 错误：前端无法知道还有多少页
return ApiResponse(code=200, message="success", data=courses)
```

```python
# ✅ 正确：分页接口必须附带 meta
return ApiResponse(
    code=200,
    message="success",
    data=courses,
    meta={"page": page, "page_size": page_size, "total": total, "total_pages": total_pages},
)
```

### ❌ AP6: 直接 raise HTTPException，不通过 AppException

```python
# ❌ 错误：不同异常格式不统一，有些用 detail string，有些用 detail dict
raise HTTPException(status_code=404, detail="课程不存在")  # 字符串格式
raise HTTPException(status_code=400, detail={"type": "ERROR", "message": "..."})  # 字典格式
```

```python
# ✅ 正确：统一用 AppException 子类 + 全局异常处理器
raise NotFoundException(resource="课程", id=course_id)
# 自动输出：{"code": 404, "message": "课程 不存在: xxx", "data": null, "error": {"type": "NOT_FOUND", "details": [...]}}
```

### ❌ AP7: 路由文件内写业务逻辑

```python
# ❌ 错误：路由文件塞满 SQL 查询和业务逻辑，难以测试和维护
@router.get("/courses")
async def list_courses(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Course).join(CourseMember)...)  # 200 行 SQL...
    return ...
```

```python
# ✅ 正确：路由只做参数校验 + 调用 Service + 返回，业务逻辑在 Service 层
@router.get("/courses")
async def list_courses(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await course_service.list_courses(db, current_user.id, page, page_size)
    return ApiResponse(code=200, message="success", data=result.items, meta=result.meta)
```

---

## Project-Specific Constraints

### 1. APIRouter 模块拆分规范

| 文件 | prefix | 负责的端点 | 对应文档章节 |
|------|--------|----------|:--:|
| `api/auth.py` | `/auth` | 注册/登录/Token/退出/个人信息 | API 2.1-2.6 |
| `api/users.py` | `/users` | 用户管理（admin） | API 8.1-8.3 |
| `api/courses.py` | `/courses` | 课程 CRUD、加入/退出、成员 | API 3.1-3.7 |
| `api/resources.py` | `/courses/{course_id}/resources` | 资源上传/列表/详情/搜索/删除 | API 4.1-4.8 |
| `api/qa.py` | `/courses/{course_id}/qa` | 问答/SSE/历史/反馈 | API 5.1-5.6 |
| `api/tasks.py` | `/courses/{course_id}/tasks` | 任务生成/CRUD/发布/归档 | API 6.1-6.8 |
| `api/reports.py` | `/courses/{course_id}/reports` | 报告生成/列表/导出 | API 7.1-7.4 |
| `api/admin.py` | `/admin` | 系统管理 | API 8.1-8.5 |

### 2. 统一响应接口

**所有端点必须返回 `ApiResponse` 包装**（定义在 `backend/app/schemas/response.py`），不要直接返回裸 dict 或 Pydantic model：

```python
# ✅ 正确
return ApiResponse(code=200, message="success", data={"id": "..."})

# ❌ 错误
return {"id": "..."}
```

### 3. 文件上传 → Celery 异步处理链路

```
POST /courses/{id}/resources/upload
  │
  ├── ① 保存文件到 MinIO（同步，~1s）
  │   └── 返回 file_key
  │
  ├── ② 创建 resources 记录，status='processing'（同步）
  │   └── 返回 resource_id
  │
  ├── ③ process_resource.delay(resource_id, file_path, course_id)（异步）
  │   └── Celery Worker 执行：
  │       ├── 解析文件内容（PyPDF2/python-docx）
  │       ├── RecursiveCharacterTextSplitter(chunk_size=512, overlap=64)
  │       ├── BGE-M3 Embedding
  │       ├── 写入 ChromaDB（collection=course_{course_id}）
  │       └── 写入 PostgreSQL chunks 表，更新 resources.status='ready'
  │
  └── ④ 立即返回 201 + resource_id + status='processing'
        └── 前端轮询 GET /courses/{id}/resources/{id} 直到 status='ready'
```

### 4. 异步数据库会话管理

- 使用 SQLAlchemy 2.0 async 模式（`asyncpg` 驱动）
- `get_db()` 通过 `async_sessionmaker` 创建会话
- 所有 Service 函数签名：`async def service_method(db: AsyncSession, ...)`
- 不要在 Service 中自己管理会话生命周期（由 FastAPI Depends 的 `get_db` 统一管理）

### 5. 依赖注入顺序（必须严格）

```
端点 → get_db (session) → get_current_user (JWT) → verify_course_member (权限)
                                 ↘ require_role("teacher") (角色)
```

顺序不可颠倒，因为 `verify_course_member` 依赖 `get_current_user` 返回的 user.id。

------

### 6. Skills / MCP / Agent API 边界

新增 Skills、MCP、Agent 相关 API 时，必须继续遵守现有 FastAPI 分层规范：

1. 路由层只负责参数校验、依赖注入、权限入口和调用 Service。
2. 不得在路由函数中直接写 Agent、Skill、MCP 业务逻辑。
3. 不得在路由函数中直接访问数据库或 ChromaDB。
4. 课程内接口必须继续复用现有认证和课程权限依赖。
5. Skills API、MCP API、Agent Runs API 必须统一使用现有响应结构和异常处理。
6. Agent、Skill、MCP 的权限判断必须由后端代码完成，不能交给 LLM 判断。
7. 流式接口仍然必须遵守 SSE 事件格式和异常兜底规范。

推荐调用链路：

```text
API Router
→ Dependency 权限校验
→ Service
→ Agent Orchestrator / Skill Executor / MCP Client
→ 返回统一响应
```

---

## References

与以下文档严格对齐：
- `docs/04_API接口文档.md`：所有 38 个接口的路径、参数、响应格式（以本文档为准）
- `docs/02_技术架构文档.md`：目录结构 `backend/app/api/`、`schemas/`、`services/`、`tasks/`
- `docs/03_数据模型与数据库设计.md`：SQLAlchemy 模型 + AsyncSession 用法
- `docs/05_AI智能体行为定义.md`：AgentExecutor 在 Service 层的调用方式

---

## Quick Reference: 要做某事 → 看哪个 Pattern

| 要做某事 | 看哪个 Pattern | 产出文件 |
|---------|:-----------:|---------|
| 搭建 FastAPI 入口 + CORS + 路由注册 | Pattern 1 | `main.py` + `api/router.py` |
| 判断端点该用 async def 还是 def | Pattern 2 | 所有 `api/*.py` |
| 实现 QA 流式回答 | Pattern 3 | `api/qa.py` + `services/qa_service.py` |
| 文件上传后异步处理 | Pattern 4 | `tasks/resource_processing.py` |
| JWT 认证 + 角色权限检查 | Pattern 5 | `dependencies.py` |
| 统一异常格式 | Pattern 6 | `exceptions.py` + `main.py` |
| 数据库异步查询 + 分页 | Pattern 7 | `database.py` + 所有 `services/*.py` |
