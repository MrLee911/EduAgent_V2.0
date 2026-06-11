# 02_backend-rules.md

## 1. 规则文件用途

本文件是 EduAgent 项目的后端开发规则文件。

文件位置：

```text
.codebuddy/rules/02_backend-rules.md
```

本文件用于约束 CodeBuddy 在 EduAgent 项目中进行后端开发、后端修复、后端重构、API 调整、Service 层改造、数据库访问、RAG 后端能力、Agent 后端能力、MCP 工具后端能力、Runtime Skills 后端能力时的行为。

本文件不是完整后端架构文档。完整架构、数据库、API 设计应同时阅读：

```text
codebuddy-docs/specs/02_技术架构文档.md
codebuddy-docs/specs/03_数据模型与数据库设计.md
codebuddy-docs/specs/04_API接口文档.md
codebuddy-docs/specs/05_AI智能体行为定义.md
codebuddy-docs/specs/06_提示词模板.md
.codebuddy/skills/fastapi-async-patterns/SKILL.md
.codebuddy/skills/postgres-sqlalchemy-patterns/SKILL.md
.codebuddy/skills/rag-implementation-patterns/SKILL.md
.codebuddy/skills/langgraph-workflow-patterns/SKILL.md
.codebuddy/skills/mcp-tool-development-patterns/SKILL.md
.codebuddy/skills/runtime-skills-development-patterns/SKILL.md
```

------

## 2. 后端项目定位

EduAgent 后端不是普通 CRUD API 后端。

EduAgent 后端应同时承担：

1. 用户认证。
2. 角色权限控制。
3. 课程业务管理。
4. 课程资源管理。
5. 文件上传与解析。
6. RAG 知识库构建。
7. 课程问答。
8. 教学任务生成。
9. 教学报告生成。
10. Agent 编排。
11. Runtime Skills 执行。
12. MCP Tool 管理和调用。
13. LangGraph Workflow 调度。
14. 异步任务处理。
15. 数据库持久化。
16. 执行审计。
17. 安全边界控制。

CodeBuddy 在修改后端代码时，必须始终保持这个定位：

```text
后端 = 业务系统后端 + AI 能力服务层 + 智能体执行控制层 + 权限与审计边界
```

不要把后端只开发成简单的接口转发层，也不要让大模型、前端、MCP 工具或 LangGraph Workflow 绕过后端业务规则。

------

## 3. 后端技术栈约束

EduAgent 后端必须继续使用当前技术栈。

### 3.1 必须使用的技术

```text
Python
FastAPI
SQLAlchemy Async
Alembic
PostgreSQL
Redis
Celery
ChromaDB
LangChain
LangGraph
Pydantic
httpx
```

### 3.2 不得替换的内容

不得随意替换：

1. FastAPI。
2. SQLAlchemy Async。
3. PostgreSQL。
4. Alembic。
5. Vue 前端对应的 API 契约。
6. 当前 RAG 基础结构。
7. 当前 Agent 目录结构。
8. 当前 Docker / Docker Compose 基础部署方式。

### 3.3 禁止行为

禁止：

1. 把 FastAPI 改成 Flask、Django、Tornado 或其他后端框架。
2. 把 SQLAlchemy Async 改成同步 ORM 调用。
3. 绕过 Alembic 直接修改数据库结构。
4. 用临时 JSON 文件替代数据库。
5. 把关键业务逻辑写在 Prompt 中。
6. 把权限判断交给大模型。
7. 在后端代码中硬编码真实密钥。

------

## 4. 后端推荐目录结构

后端代码应保持或逐步整理为以下结构：

```text
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py
│   │       ├── courses.py
│   │       ├── resources.py
│   │       ├── qa.py
│   │       ├── tasks.py
│   │       ├── reports.py
│   │       ├── admin.py
│   │       ├── skills.py
│   │       ├── mcp.py
│   │       └── agent_runs.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── course.py
│   │   ├── resource.py
│   │   ├── qa.py
│   │   ├── task.py
│   │   ├── report.py
│   │   ├── agent.py
│   │   ├── skill.py
│   │   └── mcp.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── course.py
│   │   ├── resource.py
│   │   ├── qa.py
│   │   ├── task.py
│   │   ├── report.py
│   │   ├── agent.py
│   │   ├── skill.py
│   │   └── mcp.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── course_service.py
│   │   ├── resource_service.py
│   │   ├── qa_service.py
│   │   ├── task_service.py
│   │   ├── report_service.py
│   │   ├── agent_service.py
│   │   ├── skill_service.py
│   │   └── mcp_service.py
│   │
│   ├── rag/
│   │   ├── parsers/
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   ├── retriever.py
│   │   ├── reranker.py
│   │   ├── query_rewriter.py
│   │   ├── post_processor.py
│   │   └── degradation.py
│   │
│   ├── agent/
│   │   ├── orchestrator.py
│   │   ├── intent_router.py
│   │   ├── planner.py
│   │   ├── skill_router.py
│   │   ├── tool_router.py
│   │   ├── executor.py
│   │   ├── state.py
│   │   ├── memory.py
│   │   ├── guardrails.py
│   │   ├── workflows/
│   │   ├── tools/
│   │   └── prompts/
│   │
│   ├── mcp/
│   │   ├── client.py
│   │   ├── registry.py
│   │   ├── schemas.py
│   │   ├── permissions.py
│   │   └── adapters/
│   │
│   ├── skills/
│   │   ├── base.py
│   │   ├── schemas.py
│   │   ├── registry.py
│   │   ├── executor.py
│   │   └── builtin/
│   │
│   ├── tasks/
│   │   ├── resource_processing.py
│   │   ├── embedding_tasks.py
│   │   ├── report_tasks.py
│   │   └── agent_tasks.py
│   │
│   ├── dependencies.py
│   ├── database.py
│   └── main.py
│
├── alembic/
├── tests/
└── requirements.txt
```

如果当前项目目录尚未完全达到该结构，CodeBuddy 应采用**增量整理**方式，不得删除现有代码后重建。

------

## 5. 后端分层规则

后端必须遵守以下分层：

```text
FastAPI Router
  ↓
Dependency / Permission Check
  ↓
Service Layer
  ↓
Domain Logic / Repository / ORM
  ↓
Database / Vector Store / File Storage
```

AI 与智能体能力必须遵守以下分层：

```text
FastAPI Router
  ↓
Service Layer
  ↓
Agent Orchestrator / Skill Executor / MCP Client
  ↓
Runtime Skills / MCP Tools / LangGraph Workflow
  ↓
Service Layer Persistence
  ↓
Database / Vector Store / Audit Logs
```

### 5.1 Router 层职责

Router 层只负责：

1. 接收 HTTP 请求。
2. 解析路径参数、查询参数和请求体。
3. 注入当前用户。
4. 注入数据库会话。
5. 调用 Service。
6. 返回 Pydantic Response。
7. 抛出标准 HTTP 异常。

Router 层不得：

1. 写复杂业务逻辑。
2. 直接拼接 SQL。
3. 直接操作向量数据库。
4. 直接调用大模型完成核心业务。
5. 直接调用 MCP 工具绕过 Service。
6. 直接写 Agent 执行流程。
7. 直接处理复杂文件解析逻辑。

错误示例：

```python
@router.post("/courses/{course_id}/qa")
async def ask(course_id: UUID, request: QARequest, db: AsyncSession = Depends(get_db)):
    # 错误：Router 中直接检索知识库、拼 prompt、调模型、写数据库
    chunks = await vector_store.search(request.question)
    answer = await llm.invoke(...)
    db.add(...)
    await db.commit()
    return answer
```

推荐示例：

```python
@router.post("/courses/{course_id}/qa", response_model=QAResponse)
async def ask_question(
    course_id: UUID,
    request: QARequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await qa_service.ask_question(
        db=db,
        course_id=course_id,
        user=current_user,
        request=request,
    )
```

### 5.2 Service 层职责

Service 层负责：

1. 核心业务流程。
2. 权限校验。
3. 数据库读写。
4. 调用 RAG。
5. 调用 Agent Orchestrator。
6. 调用 Skill Executor。
7. 调用 MCP Client。
8. 事务控制。
9. 异常封装。
10. 审计记录。

Service 层必须是后端业务的主入口。

Agent、MCP、Skill、LangGraph 都不得绕过 Service 层直接修改业务数据。

------

## 6. API 设计规则

### 6.1 API 路径规则

API 应统一使用：

```text
/api/v1
```

课程内资源应尽量采用嵌套路径：

```text
/api/v1/courses/{course_id}/resources
/api/v1/courses/{course_id}/qa
/api/v1/courses/{course_id}/tasks
/api/v1/courses/{course_id}/reports
/api/v1/courses/{course_id}/agent-runs
/api/v1/courses/{course_id}/skills
```

平台管理接口应采用：

```text
/api/v1/admin/users
/api/v1/admin/settings
/api/v1/admin/mcp/servers
/api/v1/admin/mcp/tools
/api/v1/admin/mcp/tool-calls
/api/v1/admin/agent-runs
/api/v1/admin/skills
/api/v1/admin/skills/runs
```

### 6.2 路由顺序规则

静态路由必须写在动态路由之前。

例如：

```python
@router.get("/search")
async def search_resources(...):
    ...

@router.get("/{resource_id}")
async def get_resource(...):
    ...
```

禁止把动态路由放在前面导致静态路由被遮挡：

```python
# 错误
@router.get("/{resource_id}")
async def get_resource(...):
    ...

@router.get("/search")
async def search_resources(...):
    ...
```

当前项目需要特别注意：

```text
resources/search
```

不得被：

```text
resources/{resource_id}
```

遮挡。

### 6.3 请求体规则

请求体必须使用 Pydantic Schema。

禁止直接使用裸 `dict` 承载复杂业务请求，除非是明确的动态 JSON 场景。

错误示例：

```python
async def update_user(data: dict):
    ...
```

推荐示例：

```python
class UserUpdateRequest(BaseModel):
    username: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
```

### 6.4 响应规则

响应应使用明确的 Pydantic Response Schema。

常见响应类型包括：

1. 单对象响应。
2. 列表响应。
3. 分页响应。
4. 操作结果响应。
5. AI 生成响应。
6. 流式响应。
7. 文件下载响应。

前端依赖的字段必须稳定，不得随意改名。

------

## 7. Pydantic Schema 规则

### 7.1 Schema 命名规则

推荐命名：

```text
XxxCreate
XxxUpdate
XxxResponse
XxxListResponse
XxxDetailResponse
XxxGenerateRequest
XxxGenerateResponse
```

示例：

```python
class TaskGenerateRequest(BaseModel):
    task_type: str
    difficulty: str
    additional_instructions: str | None = None
```

### 7.2 字段命名规则

后端、前端、文档必须保持字段一致。

当前项目需要特别注意：

```text
additional_instructions
```

不要在前端使用：

```text
extra_instructions
```

除非后端 Schema 同步兼容。

### 7.3 枚举规则

涉及状态、角色、资源类型、任务类型、报告类型时，优先使用 Enum。

示例：

```python
class ResourceStatus(str, Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"
```

不得在多个文件中散落硬编码字符串。

------

## 8. SQLAlchemy Async 规则

### 8.1 数据库会话规则

数据库访问必须使用 `AsyncSession`。

推荐：

```python
async def get_course_by_id(db: AsyncSession, course_id: UUID):
    result = await db.execute(select(Course).where(Course.id == course_id))
    return result.scalar_one_or_none()
```

禁止在 async 函数中使用同步 Session。

### 8.2 查询规则

必须 `await db.execute(...)`。

禁止忘记 `await`。

错误示例：

```python
result = db.execute(select(User))
```

正确示例：

```python
result = await db.execute(select(User))
```

### 8.3 事务规则

写操作应明确处理：

1. `db.add(...)`
2. `await db.flush()`
3. `await db.commit()`
4. `await db.refresh(model)`

如果发生异常，应回滚：

```python
try:
    db.add(obj)
    await db.commit()
    await db.refresh(obj)
except Exception:
    await db.rollback()
    raise
```

对于复杂业务，建议 Service 层统一控制事务。

### 8.4 N+1 查询防护

涉及关系加载时，应使用：

```python
selectinload
joinedload
```

避免在循环中逐条查询数据库。

### 8.5 数据删除规则

删除策略必须清晰。

可选策略：

1. 软删除。
2. 硬删除。
3. 级联删除。
4. 禁止删除，只允许归档。

课程、资源、任务、报告、Agent 执行记录等数据删除前必须确认业务影响。

不得无条件级联删除重要审计数据。

------

## 9. Alembic 迁移规则

修改数据库结构时必须同步 Alembic migration。

需要生成 migration 的情况：

1. 新增表。
2. 删除表。
3. 新增字段。
4. 删除字段。
5. 修改字段类型。
6. 修改 nullable。
7. 新增索引。
8. 删除索引。
9. 新增枚举。
10. 修改外键关系。

推荐命令：

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

生成 migration 后必须人工检查。

重点检查：

1. UUID 默认值。
2. PostgreSQL extension。
3. Enum 变更。
4. nullable 变更。
5. 数据迁移逻辑。
6. 索引命名。
7. 外键约束。
8. downgrade 是否合理。

当前项目注意：

如果 migration 使用：

```sql
gen_random_uuid()
```

必须确保启用：

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

------

## 10. 权限与课程隔离规则

这是 EduAgent 后端最重要的规则之一。

所有课程级数据访问必须校验：

1. 用户是否已登录。
2. 用户是否存在。
3. 用户是否 active。
4. 用户是否为课程成员。
5. 用户在课程中的角色。
6. 操作是否允许该角色执行。
7. 当前数据是否属于当前 `course_id`。

### 10.1 课程级权限

课程相关接口必须基于 `course_id` 做权限检查。

常见权限：

| 操作        | 学生         | 教师           | 管理员       |
| ----------- | ------------ | -------------- | ------------ |
| 查看课程    | 已加入可查看 | 自己课程可查看 | 可查看       |
| 上传资源    | 通常不可     | 可             | 可           |
| 删除资源    | 不可         | 可             | 可           |
| 课程问答    | 已加入可使用 | 可使用         | 可使用       |
| 生成任务    | 通常不可     | 可             | 可           |
| 发布任务    | 不可         | 可             | 可           |
| 查看任务    | 已加入可查看 | 可查看         | 可查看       |
| 生成报告    | 通常不可     | 可             | 可           |
| MCP 管理    | 不可         | 不可           | 可           |
| Skills 管理 | 不可         | 不可           | 可           |
| Agent 审计  | 有限制       | 课程内可查看   | 平台级可查看 |

### 10.2 禁止越权

禁止：

1. 用户访问未加入课程的数据。
2. 学生删除课程资源。
3. 学生生成教师报告。
4. 教师访问其他教师课程数据。
5. MCP Tool 绕过课程权限。
6. Skill Executor 绕过用户权限。
7. Agent Orchestrator 直接访问无权限数据。
8. RAG 检索跨课程资源。

### 10.3 权限不能交给大模型

错误做法：

```text
把用户角色和课程信息发给大模型，让模型判断是否可以执行。
```

正确做法：

```text
后端代码先判断权限；
权限通过后，才允许调用模型、RAG、Skill、MCP 或 Agent。
```

------

## 11. 认证与 Token 规则

### 11.1 登录规则

登录接口必须返回前端需要的 Token 字段。

如果前端依赖：

```text
access_token
refresh_token
token_type
expires_in
user
```

后端响应必须一致。

### 11.2 Refresh Token 规则

如果前端实现了 refresh token 逻辑，后端必须：

1. 提供 refresh 接口。
2. 返回新的 access token。
3. 正确校验 refresh token。
4. 处理 refresh token 过期。
5. 处理 refresh token 无效。
6. 保持响应结构稳定。

### 11.3 Logout 规则

如果实现退出登录，应明确：

1. 是否只是前端清除 token。
2. 是否后端维护 token blacklist。
3. blacklist 存储位置。
4. blacklist 过期策略。
5. 多端登录处理方式。

不得在文档中声称已实现 blacklist，但代码实际未实现。

------

## 12. 文件上传与资源处理规则

### 12.1 上传接口规则

课程资源上传接口必须保证前后端路径一致。

当前项目需特别注意：

```text
后端 upload-batch
前端 batch-upload
```

这类路径不一致必须修复为同一标准。

推荐统一为：

```text
POST /api/v1/courses/{course_id}/resources/upload-batch
```

### 12.2 文件类型规则

允许上传的文件类型必须与实际解析能力一致。

如果配置允许：

```text
pdf
docx
pptx
md
txt
xlsx
```

则后端必须有对应解析器。

如果没有 xlsx 解析器，则不得在配置或前端中声明支持 xlsx。

### 12.3 文件存储规则

需要统一以下内容：

1. 本地文件存储目录。
2. MinIO 对象存储策略。
3. 数据库中的文件路径字段。
4. Nginx `/files/` 访问路径。
5. 文件删除时的物理文件清理策略。
6. 文件重新处理时的覆盖策略。

### 12.4 资源处理状态

资源处理流程应清晰：

```text
uploading
→ parsing
→ chunking
→ embedding
→ ready
```

失败时：

```text
failed
```

失败信息应记录到数据库，方便前端展示和重新处理。

------

## 13. RAG 后端规则

RAG 相关能力必须作为后端可复用能力实现。

不要把 RAG 逻辑只写在 Q&A 接口中。

RAG 应可服务：

1. 课程问答。
2. 资源分析。
3. 任务生成。
4. 报告生成。
5. 教学设计。
6. 学习路径。
7. Runtime Skills。
8. MCP Tools。
9. Agent Workflows。

### 13.1 RAG 检索规则

每次检索必须限定：

```text
course_id
user_id
resource scope
permission scope
```

禁止跨课程检索。

禁止用户检索无权访问的资料。

### 13.2 RAG 引用规则

如果回答使用了课程资料，应返回 sources。

sources 应包含：

1. resource_id。
2. resource_name。
3. chunk_id。
4. score。
5. page 或 section。
6. excerpt。

不得编造 sources。

### 13.3 RAG 降级规则

如果出现以下情况：

1. 没有可用资源。
2. 检索不到相关内容。
3. 向量库不可用。
4. Reranker 失败。
5. LLM 调用失败。

后端必须返回稳定的降级响应，不得抛出未处理异常给前端。

------

## 14. Agent 后端规则

Agent 后端必须通过统一入口执行。

推荐入口：

```text
Agent Orchestrator
```

不得让多个 API 分散直接调用不同 workflow。

### 14.1 Agent 执行链路

推荐链路：

```text
Service Layer
  ↓
Agent Orchestrator
  ↓
Intent Router
  ↓
Planner
  ↓
Skill Router
  ↓
Tool Router
  ↓
LangGraph Workflow
  ↓
Skill Executor / MCP Client
  ↓
Service Layer Persistence
```

### 14.2 Agent 审计规则

每次 Agent 执行应记录：

1. agent_run_id。
2. user_id。
3. course_id。
4. input_summary。
5. intent。
6. plan。
7. status。
8. started_at。
9. finished_at。
10. latency_ms。
11. error_message。

每个 Agent Step 应记录：

1. agent_run_id。
2. step_index。
3. step_type。
4. step_name。
5. input_summary。
6. output_summary。
7. status。
8. error_message。
9. latency_ms。

### 14.3 mock LLM 禁止作为生产逻辑

当前项目中如果存在 mock LLM 节点，只能用于开发演示或测试。

禁止将 mock LLM 作为生产主链路。

------

## 15. MCP 后端规则

MCP 后端能力必须安全可控。

MCP Tool 不能绕过后端权限。

### 15.1 MCP Tool 必须具备

每个 MCP Tool 必须定义：

1. tool name。
2. description。
3. input schema。
4. output schema。
5. permission requirement。
6. risk level。
7. timeout。
8. audit log。
9. error handling。

### 15.2 MCP Tool 禁止行为

MCP Tool 禁止：

1. 执行任意 SQL。
2. 读取任意本地文件。
3. 读取 `.env`。
4. 读取 `api-key.txt`。
5. 返回真实密钥。
6. 删除课程数据。
7. 绕过 `course_id`。
8. 绕过用户权限。
9. 执行危险系统命令。

### 15.3 MCP Tool 审计

每次 MCP Tool 调用必须记录：

1. user_id。
2. course_id。
3. server_name。
4. tool_name。
5. input_summary。
6. output_summary。
7. status。
8. latency_ms。
9. error_message。
10. created_at。

------

## 16. Runtime Skills 后端规则

Runtime Skills 是 EduAgent 后端运行时能力，不是 CodeBuddy 本地 `.codebuddy/skills/` 文档技能。

不要混淆：

```text
.codebuddy/skills/
= 给 CodeBuddy 看的开发技能文档

backend/app/skills/
= EduAgent 项目运行时技能系统
```

### 16.1 Runtime Skill 必须具备

每个 Runtime Skill 必须有：

1. skill_name。
2. description。
3. input_schema。
4. output_schema。
5. permission_check。
6. execute 方法。
7. error handling。
8. skill_run audit log。

### 16.2 推荐内置 Skill

推荐内置：

1. course_qa。
2. resource_analysis。
3. task_generation。
4. report_generation。
5. code_explanation。
6. lesson_design。
7. quiz_generation。
8. study_path。

### 16.3 Skill 执行记录

每次 Runtime Skill 执行应记录：

1. skill_name。
2. user_id。
3. course_id。
4. input_summary。
5. output_summary。
6. status。
7. latency_ms。
8. error_message。
9. created_at。

------

## 17. Celery 与异步任务规则

耗时任务应使用 Celery 或异步后台任务处理。

适合异步处理的任务：

1. 文件解析。
2. 文档切片。
3. Embedding 生成。
4. 向量库写入。
5. 大报告生成。
6. 大批量资源分析。
7. 长时间 Agent 执行。
8. 批量 MCP Tool 调用。
9. 批量 Skill 执行。

### 17.1 异步任务状态

异步任务必须有可查询状态。

状态包括：

```text
pending
running
success
failed
```

或业务特定状态，例如：

```text
uploading
parsing
chunking
embedding
ready
failed
```

### 17.2 异步任务错误

异步任务失败时必须记录：

1. 错误类型。
2. 错误信息。
3. 失败时间。
4. 可重试标记。
5. 用户可见错误说明。

不得只在日志中记录失败而不更新数据库状态。

------

## 18. 配置管理规则

配置必须集中管理。

推荐位置：

```text
backend/app/core/config.py
```

或当前项目已有配置文件。

### 18.1 配置来源

配置应来自：

1. `.env`
2. 环境变量
3. `.env.example`
4. Docker Compose 环境变量
5. 生产环境 Secret 管理

不得在代码中硬编码：

1. 数据库密码。
2. Redis 密码。
3. JWT Secret。
4. LLM API Key。
5. Embedding API Key。
6. MinIO 密钥。
7. 外部服务 Token。

### 18.2 `.env.example`

新增配置项时必须同步：

```text
.env.example
codebuddy-docs/00_环境配置说明.md
```

### 18.3 DeepSeek 默认规则

本项目课程内容和代码示例默认使用 DeepSeek 相关写法。

如果使用 OpenAI-compatible SDK，也应通过配置指向 DeepSeek-compatible endpoint。

不得把 OpenAI 作为默认供应商写死。

------

## 19. 错误处理规则

后端必须提供稳定错误响应。

### 19.1 常见错误类型

应处理：

1. 400 参数错误。
2. 401 未登录。
3. 403 无权限。
4. 404 数据不存在。
5. 409 冲突。
6. 422 校验错误。
7. 500 服务器错误。
8. 503 外部服务不可用。

### 19.2 错误响应

错误响应应包含：

1. error code。
2. message。
3. detail。
4. request_id，若已有。
5. 可选 field errors。

不要把 Python traceback 直接返回给前端。

不要把数据库连接串、密钥、文件真实路径返回给前端。

------

## 20. 日志与审计规则

后端日志应记录：

1. 重要业务操作。
2. 登录失败。
3. 权限拒绝。
4. 文件处理失败。
5. RAG 检索失败。
6. LLM 调用失败。
7. Agent 执行失败。
8. MCP Tool 调用失败。
9. Runtime Skill 执行失败。
10. 数据库迁移问题。

日志不得记录：

1. 明文密码。
2. JWT Secret。
3. 完整 Token。
4. API Key。
5. 数据库密码。
6. 用户敏感数据。
7. 大量完整 Prompt，除非已脱敏且确有必要。

Agent / Skill / MCP 执行应优先落库审计，而不仅是普通日志。

------

## 21. 后端测试规则

后端修改后应尽量运行：

```bash
cd backend
pytest
```

如果涉及数据库迁移，运行：

```bash
cd backend
alembic upgrade head
```

如果涉及 API，至少应验证：

1. 请求路径。
2. 请求参数。
3. 响应字段。
4. 状态码。
5. 权限。
6. 错误处理。

如果无法运行测试，必须说明：

1. 为什么无法运行。
2. 哪些风险未验证。
3. 如何手动验证。

不得声称未运行的测试已经通过。

------

## 22. 后端文档同步规则

修改后端时必须同步相关文档。

### 22.1 修改 API 时

同步：

```text
codebuddy-docs/specs/04_API接口文档.md
frontend/src/api/
frontend/src/types/
```

### 22.2 修改数据库时

同步：

```text
codebuddy-docs/specs/03_数据模型与数据库设计.md
backend/alembic/
```

### 22.3 修改 AI 行为时

同步：

```text
codebuddy-docs/specs/05_AI智能体行为定义.md
codebuddy-docs/specs/06_提示词模板.md
```

### 22.4 修改任务流程时

同步：

```text
codebuddy-docs/specs/08_CodeBuddy开发任务书.md
```

### 22.5 修改页面相关接口时

同步：

```text
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
frontend/src/api/
frontend/src/types/
```

------

## 23. 已知后端高风险问题

开发后端时必须注意这些问题。

### 23.1 P0 问题

1. 批量上传接口前后端路径可能不一致。
2. 任务生成字段 `extra_instructions` 和 `additional_instructions` 可能不一致。
3. 登录响应可能缺少前端需要的 `refresh_token`。
4. Resource search 路由可能被 `/{resource_id}` 遮挡。
5. Agent Tool 中异步 retriever 调用必须 `await`。
6. LangGraph workflow 中 mock LLM 节点不得作为生产链路。
7. Alembic 使用 `gen_random_uuid()` 时必须启用 `pgcrypto`。
8. `Resource.uploaded_by` 模型 nullable 与 migration 必须一致。

### 23.2 P1 问题

1. `qa_records` conversation 支持需要统一。
2. Report workflow 不得使用硬编码日期。
3. MinIO 和本地存储策略需要统一。
4. Nginx `/files/` 代理路径与后端存储路径需要统一。
5. Excel 配置与 parser 能力需要一致。
6. Reports 删除 UI 与后端 API 需要一致。
7. Admin update user 请求 body 和后端参数需要一致。

------

## 24. 后端开发任务执行流程

CodeBuddy 执行后端任务时，应按以下流程：

```text
1. 判断任务类型
2. 阅读 CODEBUDDY.md
3. 阅读本规则文件
4. 阅读相关 specs 文档
5. 阅读相关 Skill
6. 检查现有代码
7. 制定最小修改方案
8. 修改代码
9. 同步 Schema / Service / API / Migration / 文档
10. 运行测试或说明无法运行原因
11. 输出修改说明和风险
```

### 24.1 判断是否需要数据库迁移

如果修改了：

1. models。
2. 字段。
3. 表关系。
4. 索引。
5. Enum。
6. nullable。
7. default。

必须考虑 Alembic migration。

### 24.2 判断是否需要前端同步

如果修改了：

1. API 路径。
2. 请求字段。
3. 响应字段。
4. 状态枚举。
5. 分页格式。
6. 错误码。

必须同步前端 API wrapper 和 TypeScript types。

### 24.3 判断是否需要审计

如果修改了：

1. Agent。
2. MCP Tool。
3. Runtime Skill。
4. 大模型调用。
5. 课程资源处理。
6. 教学任务生成。
7. 教学报告生成。

必须考虑执行审计和错误日志。

------

## 25. 后端禁止事项清单

CodeBuddy 后端开发时禁止：

1. 删除重建后端项目。
2. 替换 FastAPI。
3. 替换 SQLAlchemy Async。
4. 绕过 Alembic。
5. 绕过 Service 层。
6. 在 Router 中写复杂业务逻辑。
7. 在 Prompt 中写权限逻辑。
8. 让大模型判断权限。
9. MCP Tool 直接访问任意数据库表。
10. MCP Tool 读取 `.env`。
11. Runtime Skill 绕过课程权限。
12. RAG 跨课程检索。
13. 编造 RAG sources。
14. 返回未脱敏 traceback。
15. 返回数据库连接串。
16. 提交 `.env`。
17. 提交 `api-key.txt`。
18. 提交虚拟环境目录。
19. 提交用户上传文件。
20. 声称未运行的测试已通过。

------

## 26. 后端输出要求

完成后端任务后，必须说明：

1. 修改了哪些后端文件。
2. 是否修改了 API 契约。
3. 是否修改了数据库模型。
4. 是否新增或修改了 Alembic migration。
5. 是否修改了 Pydantic Schema。
6. 是否修改了 Service。
7. 是否影响前端 API wrapper。
8. 是否影响权限逻辑。
9. 是否影响 RAG / Agent / MCP / Skills。
10. 是否同步了文档。
11. 运行了哪些测试。
12. 哪些测试未运行及原因。
13. 是否有剩余风险。

不得只回答：

```text
已完成
```

必须给出可审查的修改说明。

------

## 27. 最终原则

EduAgent 后端必须保持：

```text
安全
稳定
可维护
可扩展
可测试
可审计
```

所有后端修改都必须优先保证：

1. 权限正确。
2. 课程数据隔离。
3. API 契约稳定。
4. 数据库结构一致。
5. 异步调用正确。
6. RAG 结果可信。
7. Agent 执行可追踪。
8. MCP 工具调用安全。
9. Runtime Skills 输入输出稳定。
10. 文档同步完整。