# 08 CodeBuddy 开发任务书

> 项目名称：EduAgent 课程资源与教学任务智能体
> 文档类型：CodeBuddy 开发任务书 / 智能体平台建设任务书 / 修复与扩展任务书
> 适用对象：CodeBuddy / AI 编程助手 / 后端开发 / 前端开发 / Agent 开发 / MCP 开发 / Skills 开发 / 测试人员
> 对应代码：`backend/`、`frontend/`、`docker-compose.yml`、`nginx.conf`、`codebuddy-docs/`
> 文档版本：v2.0
> 优化日期：2026-06-10

------

## 1. 文档目的

本文档是 CodeBuddy 继续开发、修复和扩展 EduAgent 项目的执行任务书。

新版 EduAgent 不再定位为简单的：

```text
课程管理系统 + RAG 问答机器人
```

而应升级为：

```text
课程智能体平台
= 课程业务系统
+ RAG 知识库
+ MCP 工具生态
+ Skills 技能系统
+ Agent Orchestrator
+ Planner
+ Tool Router
+ Skill Router
+ 多智能体协作
+ 教学任务生成
+ 教学报告分析
+ 代码辅导
+ 教学设计
+ 学习路径推荐
```

当前项目已经具备一定基础：

1. FastAPI 后端基础框架。
2. Vue 3 前端基础框架。
3. PostgreSQL 数据模型。
4. Alembic 初始迁移。
5. Redis、Celery、ChromaDB、MinIO、Nginx、Docker Compose 编排。
6. 用户认证、课程管理、资源管理、问答、任务、报告、管理员接口。
7. RAG 文档处理链路。
8. Agent / LangGraph 原型结构。
9. 前端主要页面和 API 封装。
10. `codebuddy-docs/` 开发文档体系。

但当前项目仍然缺少真正体现“智能体平台”的关键能力：

```text
backend/app/mcp/
backend/app/skills/
Agent Orchestrator
Intent Router
Planner
Skill Router
Tool Router
MCP Client
MCP Registry
Skill Registry
Skill Executor
Agent 执行记录
MCP 工具调用记录
Skill 执行记录
资源分析智能体
代码辅导智能体
教学设计智能体
学习路径智能体
```

因此，CodeBuddy 后续开发的重点不是从零重建项目，而是在现有代码基础上完成：

```text
现有主链路修复
→ RAG 稳定化
→ Skills 框架建设
→ MCP 框架建设
→ Agent Orchestrator 建设
→ 多智能体能力扩展
→ 前端页面扩展
→ 测试与部署验收
```

------

## 2. CodeBuddy 开发总原则

### 2.1 不得从零重建项目

当前项目不是空项目，CodeBuddy 不得删除已有项目重新生成。

正确做法：

```text
读取现有代码
→ 分析现有实现
→ 定位问题
→ 小步修复
→ 增量扩展
→ 补充测试
→ 更新文档
```

错误做法：

```text
删除 backend/
删除 frontend/
重新生成全套项目
忽略现有数据库模型
忽略现有 API
忽略现有前端页面
```

------

### 2.2 先稳定，后扩展

项目已有 RAG、QA、Task、Report 主链路。新增 MCP 和 Skills 之前，必须先保证现有链路稳定。

推荐顺序：

```text
修复 P0 问题
→ 稳定认证、课程、资源、问答、任务、报告
→ 再新增 Skills
→ 再新增 MCP
→ 再新增 Agent Orchestrator
→ 再扩展多智能体能力
```

不要一开始就大规模重构 Agent，否则容易破坏已有功能。

------

### 2.3 Service 层不可被绕过

Agent、Skill、MCP Tool 都不能绕过 Service 层权限和业务事务。

Service 层负责：

1. 登录认证。
2. 角色权限。
3. 课程权限。
4. 业务校验。
5. 数据库事务。
6. 结果落库。
7. API 响应兼容。

Agent 层负责：

1. 意图识别。
2. 任务规划。
3. Skill 选择。
4. Tool 选择。
5. RAG 检索。
6. MCP 工具调用。
7. LLM 生成。
8. 输出解析。
9. 护栏检查。

错误做法：

```text
Agent 直接访问任意数据库表
Agent 自己判断用户是否有权限
MCP Tool 执行原始 SQL
Skill 绕过课程成员校验
```

正确做法：

```text
API
→ Dependencies 权限校验
→ Service
→ Agent / Skill / MCP
→ Service 落库
→ API Response
```

------

### 2.4 权限必须由代码判断

LLM 可以参与意图识别、规划和内容生成，但不能负责最终权限判断。

禁止：

```text
把所有工具交给 LLM，让 LLM 自己判断能不能调用。
```

必须：

```text
代码层过滤当前用户可用的 Skills 和 Tools。
代码层校验 MCP Tool 调用权限。
代码层校验 course_id。
代码层拒绝跨课程访问。
```

------

### 2.5 不得引入未经确认的新技术栈

当前技术栈已经确定。

后端：

```text
FastAPI
SQLAlchemy Async
PostgreSQL
Redis
Celery
ChromaDB
LangChain
LangGraph
Pydantic v2
httpx
```

前端：

```text
Vue 3
TypeScript
Vite
Vue Router
Pinia
Axios
Tailwind CSS
marked
DOMPurify
lucide-vue-next
```

AI / Agent：

```text
DeepSeek / OpenAI-Compatible API
RAG
LangGraph
MCP
Skills
Guardrails
Memory
```

部署：

```text
Docker
Docker Compose
Nginx
```

不得擅自替换为 React、Next.js、Django、Flask、MongoDB、Qdrant、Milvus、Naive UI、shadcn-vue 等。

------

### 2.6 不得泄露敏感信息

CodeBuddy 不得在代码、文档、测试、日志、Dockerfile 或 README 中写入：

```text
真实 API Key
真实 JWT Secret
真实数据库密码
真实对象存储密钥
真实服务器地址
个人账号密码
.env 中的真实配置
api-key.txt 中的真实密钥
```

正式交付时必须删除：

```text
.env
api-key.txt
backend/venv/
frontend/node_modules/
backend/storage/
data/
__pycache__/
.pytest_cache/
*.pyc
```

------

## 3. 必读文档清单

CodeBuddy 开发前必须阅读：

```text
codebuddy-docs/README.md
codebuddy-docs/overview.md
codebuddy-docs/00_环境配置说明.md
codebuddy-docs/specs/01_项目需求规格文档.md
codebuddy-docs/specs/02_技术架构文档.md
codebuddy-docs/specs/03_数据模型与数据库设计.md
codebuddy-docs/specs/04_API接口文档.md
codebuddy-docs/specs/05_AI智能体行为定义.md
codebuddy-docs/specs/06_提示词模板.md
codebuddy-docs/specs/07_页面流程图.md
codebuddy-docs/specs/08_CodeBuddy开发任务书.md
```

涉及后端 API 时阅读：

```text
codebuddy-docs/skills/fastapi-async-patterns/SKILL.md
codebuddy-docs/skills/postgres-sqlalchemy-patterns/SKILL.md
```

涉及 RAG 时阅读：

```text
codebuddy-docs/skills/rag-implementation-patterns/SKILL.md
```

涉及 Agent / LangGraph 时阅读：

```text
codebuddy-docs/skills/langgraph-workflow-patterns/SKILL.md
```

涉及前端页面时阅读：

```text
codebuddy-docs/skills/vue3-tailwind-component-patterns/SKILL.md
```

涉及 Docker 部署时阅读：

```text
codebuddy-docs/skills/docker-compose-dev-patterns/SKILL.md
```

------

## 4. 当前项目真实模块清单

### 4.1 当前已有后端模块

```text
backend/app/
├── api/
├── agent/
├── core/
├── models/
├── rag/
├── schemas/
├── scripts/
├── services/
├── tasks/
├── config.py
├── database.py
├── dependencies.py
├── exceptions.py
└── main.py
```

当前已有 API 模块：

| 模块 | 文件               | 路由前缀                                |
| ---- | ------------------ | --------------------------------------- |
| 认证 | `api/auth.py`      | `/api/v1/auth`                          |
| 课程 | `api/courses.py`   | `/api/v1/courses`                       |
| 资源 | `api/resources.py` | `/api/v1/courses/{course_id}/resources` |
| 问答 | `api/qa.py`        | `/api/v1/courses/{course_id}/qa`        |
| 任务 | `api/tasks.py`     | `/api/v1/courses/{course_id}/tasks`     |
| 报告 | `api/reports.py`   | `/api/v1/courses/{course_id}/reports`   |
| 管理 | `api/admin.py`     | `/api/v1/admin`                         |

------

### 4.2 当前已有前端模块

```text
frontend/src/
├── api/
├── assets/
├── components/
├── composables/
├── router/
├── stores/
├── types/
└── views/
```

当前已有页面：

```text
LoginView.vue
RegisterView.vue
HomeView.vue
CoursesView.vue
CourseDetailView.vue
CourseResourcesView.vue
CourseQAView.vue
CourseTasksView.vue
TaskDetailView.vue
CourseReportsView.vue
ReportDetailView.vue
CourseSettingsView.vue
ProfileView.vue
NotFoundView.vue
admin/AdminUsersView.vue
admin/AdminSettingsView.vue
```

------

### 4.3 需要新增的智能体平台模块

新版架构需要新增：

```text
backend/app/mcp/
backend/app/skills/
backend/app/agent/orchestrator.py
backend/app/agent/planner.py
backend/app/agent/router.py
backend/app/agent/prompts/intent.py
backend/app/agent/prompts/planner.py
backend/app/agent/prompts/skill_router.py
backend/app/agent/prompts/tool_router.py
backend/app/agent/prompts/mcp.py
backend/app/agent/prompts/builders.py
```

------

## 5. 开发阶段总览

新版任务书将开发分为 13 个阶段。

| 阶段    | 名称                                       | 目标                                            |
| ------- | ------------------------------------------ | ----------------------------------------------- |
| 阶段 0  | 代码审查与运行基线确认                     | 确认项目当前能否安装、启动、测试                |
| 阶段 1  | P0 一致性问题修复                          | 修复会导致核心流程失败的问题                    |
| 阶段 2  | 认证与权限链路完善                         | 修复 Token、角色、课程权限和管理员权限          |
| 阶段 3  | 数据库模型与迁移修复                       | 修复模型、迁移、Schema 不一致                   |
| 阶段 4  | RAG 主链路稳定化                           | 稳定上传、解析、切片、向量、检索、引用          |
| 阶段 5  | 后端 API 与 Service 完善                   | 保证现有接口真实可用                            |
| 阶段 6  | 前端页面与 API 联调                        | 修复字段、路径、状态和页面交互                  |
| 阶段 7  | Skills 基础框架实现                        | 新增 Skill Registry、Executor 和内置 Skills     |
| 阶段 8  | MCP 基础框架实现                           | 新增 MCP Client、Registry、权限和内部工具       |
| 阶段 9  | Agent Orchestrator / Planner / Router 实现 | 实现智能体编排、意图识别、规划和路由            |
| 阶段 10 | 多智能体工作流接入                         | QA、任务、报告、资源分析、代码辅导等 Agent 接入 |
| 阶段 11 | 前端智能体能力页面扩展                     | 增加资源分析、技能中心、MCP 管理、执行记录页面  |
| 阶段 12 | 测试与验收补充                             | 补充 API、RAG、Agent、MCP、Skills、前端测试     |
| 阶段 13 | 部署、安全与文档交付                       | 完成 Docker、安全清理和文档同步                 |

------

# 阶段 0：代码审查与运行基线确认

## 0.1 阶段目标

在修改代码前，确认当前项目真实状态，形成基线报告。

CodeBuddy 必须完成：

1. 读取项目目录。
2. 确认后端依赖。
3. 确认前端依赖。
4. 确认 Docker Compose 服务。
5. 确认数据库迁移。
6. 确认当前 API 路由。
7. 确认当前 Agent 原型状态。
8. 确认当前是否存在 MCP 和 Skills 运行时代码。
9. 输出代码基线审查报告。

------

## 0.2 输入文件

```text
README.md
.env.example
docker-compose.yml
docker-compose.prod.yml
nginx.conf
backend/requirements.txt
backend/app/config.py
backend/app/main.py
backend/app/api/
backend/app/agent/
backend/app/rag/
backend/app/services/
backend/alembic/versions/
frontend/package.json
frontend/src/router/index.ts
frontend/src/api/
frontend/src/views/
codebuddy-docs/specs/
```

------

## 0.3 任务清单

| 编号  | 任务                | 目标文件 / 命令                             | 验收标准                                    |
| ----- | ------------------- | ------------------------------------------- | ------------------------------------------- |
| T0.1  | 检查目录结构        | 项目根目录                                  | 确认 backend、frontend、codebuddy-docs 存在 |
| T0.2  | 检查后端依赖        | `backend/requirements.txt`                  | 依赖与代码使用一致                          |
| T0.3  | 检查前端依赖        | `frontend/package.json`                     | 依赖与页面代码一致                          |
| T0.4  | 检查环境变量        | `.env.example`、`config.py`                 | 配置项能被正确读取                          |
| T0.5  | 检查 Docker Compose | `docker-compose.yml`                        | 服务名、端口、卷挂载无明显冲突              |
| T0.6  | 检查数据库迁移      | `alembic/versions/`                         | 初始迁移能创建核心表                        |
| T0.7  | 检查 API 路由       | `backend/app/api/`                          | 路由与文档匹配                              |
| T0.8  | 检查前端路由        | `frontend/src/router/index.ts`              | 页面与路由匹配                              |
| T0.9  | 检查 Agent 原型     | `backend/app/agent/`                        | 标记 Mock、异步问题和未接入部分             |
| T0.10 | 检查 MCP 目录       | `backend/app/mcp/`                          | 当前不存在则记录为待新增                    |
| T0.11 | 检查 Skills 目录    | `backend/app/skills/`                       | 当前不存在则记录为待新增                    |
| T0.12 | 输出基线报告        | `codebuddy-docs/review/代码基线审查报告.md` | 记录当前问题、风险和修复顺序                |

------

## 0.4 验收标准

阶段 0 完成后应得到：

```text
codebuddy-docs/review/代码基线审查报告.md
```

报告至少包含：

1. 当前项目能否启动。
2. 当前后端依赖是否完整。
3. 当前前端依赖是否完整。
4. 当前数据库迁移是否可执行。
5. 当前 API 路由数量。
6. 当前前端页面数量。
7. 当前 RAG 主链路状态。
8. 当前 Agent 原型状态。
9. 当前 MCP 缺失项。
10. 当前 Skills 缺失项。
11. 当前 P0 问题清单。
12. 当前 P1 问题清单。
13. 建议修复顺序。

------

# 阶段 1：P0 一致性问题修复

## 1.1 阶段目标

优先修复会导致核心业务流程直接失败的问题。

------

## 1.2 当前 P0 问题

| 编号  | 问题                                          | 影响                     |
| ----- | --------------------------------------------- | ------------------------ |
| P0-01 | 登录接口未返回 `refresh_token`                | 前端自动刷新不可用       |
| P0-02 | 资源批量上传路径前后端不一致                  | 批量上传失败             |
| P0-03 | 教学任务生成字段前后端不一致                  | 额外要求无法传到后端     |
| P0-04 | 资源搜索路由可能被详情路由覆盖                | 搜索接口不可用           |
| P0-05 | `Resource.uploaded_by` 模型与迁移可空性不一致 | ORM 与数据库语义冲突     |
| P0-06 | `gen_random_uuid()` 依赖扩展未显式创建        | 新库迁移可能失败         |
| P0-07 | Agent Tool 异步检索缺少 `await`               | Agent 检索不可用         |
| P0-08 | Workflow LLM 节点存在 Mock                    | Agent 主链路不可直接使用 |
| P0-09 | 生产镜像使用 gunicorn 但依赖可能缺失          | 生产启动失败             |

------

## 1.3 任务清单

| 编号 | 问题                                | 修改文件                                                     | 修复要求                                             |
| ---- | ----------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------- |
| T1.1 | 登录接口未返回 `refresh_token`      | `schemas/user.py`、`api/auth.py`、`stores/auth.ts`、`api/client.ts` | 登录响应必须返回并保存 refresh_token                 |
| T1.2 | 批量上传路径不一致                  | `frontend/src/api/resources.ts`                              | 统一为 `/upload-batch`                               |
| T1.3 | 任务额外要求字段不一致              | `frontend/src/api/tasks.ts`、`CourseTasksView.vue`、`types/index.ts` | 统一为 `additional_instructions`                     |
| T1.4 | 资源搜索路由顺序问题                | `backend/app/api/resources.py`                               | `/resources/search` 必须定义在 `/{resource_id}` 之前 |
| T1.5 | `Resource.uploaded_by` 可空性不一致 | `models/resource.py`、迁移                                   | 与 `ON DELETE SET NULL` 保持一致                     |
| T1.6 | `gen_random_uuid()` 扩展缺失        | Alembic 迁移                                                 | 增加 `CREATE EXTENSION IF NOT EXISTS pgcrypto`       |
| T1.7 | `search_knowledge` 缺少 `await`     | `agent/tools/search_knowledge.py`                            | 异步检索必须正确 await                               |
| T1.8 | Workflow LLM Mock                   | `agent/workflows/`                                           | 标记为非生产；接入前不得替换 Service 主链路          |
| T1.9 | 生产镜像缺少 gunicorn               | `requirements.txt` 或 `Dockerfile`                           | 补充 `gunicorn` 或修改启动命令                       |

------

## 1.4 验收标准

| 编号     | 验收项       | 通过标准                                              |
| -------- | ------------ | ----------------------------------------------------- |
| P0-AC-01 | 登录响应     | `/auth/login` 返回 `access_token` 和 `refresh_token`  |
| P0-AC-02 | Token 刷新   | access token 失效后前端能用 refresh token 刷新        |
| P0-AC-03 | 批量上传     | 前端调用 `/resources/upload-batch` 成功               |
| P0-AC-04 | 任务生成     | 前端传入 `additional_instructions` 后后端能接收       |
| P0-AC-05 | 资源搜索     | `/resources/search?q=xxx` 不会被识别为 resource_id    |
| P0-AC-06 | 数据库迁移   | 新库执行 Alembic 迁移成功                             |
| P0-AC-07 | Agent Tool   | `search_knowledge` 返回真实检索结果，不返回 coroutine |
| P0-AC-08 | Agent 主链路 | Mock Workflow 不进入生产 API                          |
| P0-AC-09 | 生产依赖     | 生产镜像启动命令依赖完整                              |

------

# 阶段 2：认证与权限链路完善

## 2.1 阶段目标

保证用户登录、Token 刷新、角色权限、课程权限、管理员权限稳定，并为后续 MCP / Skills / Agent 权限体系打基础。

------

## 2.2 任务清单

| 编号  | 任务                         | 修改文件                                      | 验收标准                                           |
| ----- | ---------------------------- | --------------------------------------------- | -------------------------------------------------- |
| T2.1  | 完善登录响应                 | `auth.py`、`schemas/user.py`                  | 返回 access_token、refresh_token、expires_in、user |
| T2.2  | 完善刷新 Token               | `auth.py`、`core/security.py`                 | refresh_token 类型校验正确                         |
| T2.3  | 完善前端 Token 保存          | `stores/auth.ts`                              | 登录后保存 access_token、refresh_token、user       |
| T2.4  | 完善前端自动刷新             | `api/client.ts`                               | 401 时自动刷新，失败后退出登录                     |
| T2.5  | 完善退出登录                 | `auth.py`、`stores/auth.ts`                   | 前端清理 token；后端预留黑名单机制                 |
| T2.6  | 校验课程成员权限             | `dependencies.py`                             | 非课程成员访问课程内接口返回 403                   |
| T2.7  | 校验课程教师权限             | `dependencies.py`、各 API                     | 学生不能上传资源、生成任务、生成报告               |
| T2.8  | 校验管理员权限               | `admin.py`                                    | 非 admin 访问管理员接口返回 403                    |
| T2.9  | 管理员创建用户               | `admin.py`                                    | 管理员可创建 student、teacher、admin               |
| T2.10 | 管理员更新用户改为 JSON Body | `admin.py`、`schemas/user.py`、`api/admin.ts` | 前后端参数一致                                     |
| T2.11 | 抽象 Agent 权限上下文        | 新增 `agent/context.py` 或复用 schemas        | Agent 调用时携带 user_role、course_role            |
| T2.12 | 抽象 Tool 权限上下文         | 新增 `mcp/permissions.py`                     | MCP 调用前可校验权限                               |
| T2.13 | 抽象 Skill 权限上下文        | 新增 `skills/schemas.py`                      | Skill 执行前可校验权限                             |

------

## 2.3 权限上下文标准

后续 Agent / Skill / MCP 调用必须使用统一上下文：

```json
{
  "request_id": "uuid",
  "user_id": "uuid",
  "user_role": "teacher",
  "course_id": "uuid",
  "course_role": "teacher",
  "conversation_id": "uuid"
}
```

------

## 2.4 验收标准

1. 学生可以注册、登录、刷新 Token。
2. 教师可以注册、登录、刷新 Token。
3. 管理员可以通过后台创建用户。
4. 学生访问教师接口返回 403。
5. 未登录访问受保护接口返回 401。
6. 被禁用用户不能继续访问系统。
7. 前端刷新 Token 失败后自动退出登录。
8. 管理员更新用户时前后端参数格式一致。
9. Agent / Skill / MCP 调用均可获得统一权限上下文。
10. LLM 不负责最终权限判断。

------

# 阶段 3：数据库模型与迁移修复

## 3.1 阶段目标

修复数据库模型、迁移文件、Schema 和 Service 之间的不一致问题，并为 Agent / MCP / Skills 执行审计新增数据结构。

------

## 3.2 现有数据库修复任务

| 编号 | 任务                              | 修改文件                                  | 验收标准                                    |
| ---- | --------------------------------- | ----------------------------------------- | ------------------------------------------- |
| T3.1 | 补充 pgcrypto 扩展                | Alembic 迁移                              | 新数据库可执行 `gen_random_uuid()`          |
| T3.2 | 修正 `Resource.uploaded_by`       | `models/resource.py`                      | ORM 与迁移可空性一致                        |
| T3.3 | 明确 JSONB 字段语义               | `models/qa_record.py`、`models/task.py`   | `sources`、`reference_resources` 语义为数组 |
| T3.4 | 增加 `qa_records.conversation_id` | 新 Alembic 迁移、`models/qa_record.py`    | 问答历史可按 conversation 查询              |
| T3.5 | 增加问答历史索引                  | 新 Alembic 迁移                           | `course_id + user_id + created_at` 查询高效 |
| T3.6 | 修正 `file_url` 注释              | `models/resource.py`                      | 不再限定为 MinIO                            |
| T3.7 | 明确 xlsx 支持策略                | `config.py`、`.env.example`、前端上传校验 | 支持则补解析器；不支持则移除                |
| T3.8 | 检查级联删除                      | `models/`、Service                        | 删除课程/资源时数据一致                     |

------

## 3.3 新增 Agent / MCP / Skills 表

建议新增以下表：

```text
skill_definitions
skill_runs
mcp_servers
mcp_tool_calls
agent_runs
agent_steps
```

------

### 3.3.1 skill_definitions

用途：

保存技能定义和元数据。

字段建议：

```text
id
name
display_name
description
version
enabled
allowed_roles JSONB
input_schema JSONB
output_schema JSONB
created_at
updated_at
```

------

### 3.3.2 skill_runs

用途：

保存技能执行记录。

字段建议：

```text
id
skill_name
user_id
course_id
input_summary JSONB
output_summary JSONB
status
latency_ms
error_message
created_at
```

------

### 3.3.3 mcp_servers

用途：

保存 MCP Server 配置。

字段建议：

```text
id
name
description
transport
endpoint
enabled
allowed_roles JSONB
created_at
updated_at
```

------

### 3.3.4 mcp_tool_calls

用途：

保存 MCP 工具调用记录。

字段建议：

```text
id
server_name
tool_name
user_id
course_id
arguments_summary JSONB
result_summary JSONB
status
latency_ms
error_message
created_at
```

------

### 3.3.5 agent_runs

用途：

保存 Agent 执行记录。

字段建议：

```text
id
agent_type
user_id
course_id
intent
selected_skill
status
step_count
latency_ms
error_message
created_at
```

------

### 3.3.6 agent_steps

用途：

保存 Agent 执行步骤。

字段建议：

```text
id
agent_run_id
step_index
step_name
skill_name
tool_name
input_summary JSONB
output_summary JSONB
status
latency_ms
error_message
created_at
```

------

## 3.4 数据库验收标准

| 编号     | 验收项         | 通过标准                                        |
| -------- | -------------- | ----------------------------------------------- |
| DB-AC-01 | 新库迁移       | `alembic upgrade head` 成功                     |
| DB-AC-02 | 问答记录       | `qa_records` 包含 `conversation_id`             |
| DB-AC-03 | 资源上传者字段 | 用户删除后资源可保留，`uploaded_by` 可为空      |
| DB-AC-04 | JSONB 字段     | sources、reference_resources 保存数组结构       |
| DB-AC-05 | 课程删除       | 课程关联数据清理正确                            |
| DB-AC-06 | 资源删除       | chunk 和 ChromaDB 向量清理正确                  |
| DB-AC-07 | Skill 执行记录 | `skill_runs` 可记录执行历史                     |
| DB-AC-08 | MCP 调用记录   | `mcp_tool_calls` 可记录工具调用                 |
| DB-AC-09 | Agent 执行记录 | `agent_runs` 和 `agent_steps` 可记录执行轨迹    |
| DB-AC-10 | 数据隔离       | 新增表均包含 user_id / course_id 或可追溯上下文 |

------

# 阶段 4：RAG 主链路稳定化

## 4.1 阶段目标

保证课程资源从上传到问答引用来源的完整链路稳定，并为 Skills 和 MCP 提供可复用的课程知识检索能力。

------

## 4.2 完整 RAG 链路

```text
上传文件
→ 保存资源记录
→ Celery 异步处理
→ 文档解析
→ 文本切片
→ Embedding
→ 写入 ChromaDB
→ 写入 chunks 表
→ RAG 检索
→ Reranker 精排
→ 返回引用来源
→ LLM 回答 / Skill 使用 / MCP Tool 使用
```

------

## 4.3 任务清单

| 编号  | 任务                 | 修改文件                                           | 验收标准                               |
| ----- | -------------------- | -------------------------------------------------- | -------------------------------------- |
| T4.1  | 检查文档解析器       | `rag/parsers.py`                                   | pdf、docx、pptx、md、txt 可解析        |
| T4.2  | 统一文件类型支持     | `config.py`、前端上传组件、文档                    | xlsx 支持策略明确                      |
| T4.3  | 检查文本切片         | `rag/chunker.py`                                   | chunk_size、overlap、中文分隔符正常    |
| T4.4  | 检查 Embedding 加载  | `rag/embeddings.py`                                | BGE-M3 可加载；失败时开发兜底          |
| T4.5  | 检查向量写入         | `rag/indexer.py`、`rag/vector_store.py`            | ChromaDB 和 chunks 双写成功            |
| T4.6  | 检查 Retriever       | `rag/retriever.py`                                 | 限定 course_id 检索                    |
| T4.7  | 修复查询改写         | `rag/query_rewriter.py`、`qa_service.py`           | 函数签名和调用一致                     |
| T4.8  | 检查 Reranker        | `rag/reranker.py`                                  | 失败时可降级                           |
| T4.9  | 统一 sources 格式    | `rag/post_processor.py`、`qa_service.py`、前端类型 | 引用来源字段一致                       |
| T4.10 | 完善降级策略         | `rag/degradation.py`、`qa_service.py`              | ChromaDB / Reranker / LLM 失败时有兜底 |
| T4.11 | 封装 RAG Tool        | `agent/tools/`                                     | 可供 Agent / Skill 调用                |
| T4.12 | 封装 RAG MCP Adapter | `mcp/adapters/internal_rag.py`                     | 可作为 MCP Tool 调用                   |
| T4.13 | 增加 RAG 测试        | `backend/tests/test_rag.py`                        | 覆盖解析、切片、检索、引用来源         |

------

## 4.4 引用来源统一格式

所有 QA 回答、任务参考资源和报告引用必须优先使用以下结构：

```json
{
  "resource_id": "uuid",
  "resource_name": "Python基础.pdf",
  "chunk_id": "uuid",
  "chunk_index": 3,
  "score": 0.91,
  "text_preview": "引用片段..."
}
```

------

## 4.5 验收标准

1. 上传 PDF 后资源状态最终变为 `ready`。
2. 上传 DOCX 后资源状态最终变为 `ready`。
3. 上传 PPTX 后资源状态最终变为 `ready`。
4. 上传 MD / TXT 后资源状态最终变为 `ready`。
5. 资源处理失败时状态为 `failed`，并记录 `error_message`。
6. `chunks` 表有对应切片。
7. ChromaDB 中有对应向量。
8. 问答能检索到当前课程资料。
9. A 课程问题不能检索 B 课程资料。
10. 问答返回结构化 sources。
11. Reranker 失败时问答不整体失败。
12. ChromaDB 失败时有 PostgreSQL chunk 兜底。
13. RAG 能被 Skill 调用。
14. RAG 能被内部 MCP Tool 调用。

------

# 阶段 5：后端 API 与 Service 完善

## 5.1 阶段目标

保证现有业务接口与 API 文档一致，并为后续 Agent / Skill / MCP 接入保留稳定 Service 边界。

------

## 5.2 现有 API 模块验收

| 模块     | 必须稳定的能力                                     |
| -------- | -------------------------------------------------- |
| 认证模块 | 注册、登录、刷新 Token、当前用户、退出             |
| 课程模块 | 创建、列表、详情、更新、删除、加入、成员管理       |
| 资源模块 | 上传、批量上传、列表、搜索、状态、重新处理、删除   |
| 问答模块 | 非流式问答、流式问答、历史、详情、反馈、清空上下文 |
| 任务模块 | 生成、列表、详情、编辑、重新生成、发布、归档、删除 |
| 报告模块 | 生成、列表、详情、导出                             |
| 管理模块 | 用户列表、创建用户、更新用户、系统设置             |

------

## 5.3 Service 与 Agent 接入要求

在阶段 5 不要求立即重构为 Agent，但必须为后续接入留出清晰边界。

推荐方式：

```python
class QAService:
    async def ask_question(...):
        # 1. 权限和业务校验
        # 2. 调用 RAG / Agent
        # 3. 保存 qa_records
        # 4. 返回兼容 API 响应
```

后续改造时：

```text
QAService
→ AgentOrchestrator.run(intent="course_qa")
→ course_qa Skill
→ RAG MCP Tool
→ LLM
→ QAService 保存结果
```

------

## 5.4 验收标准

1. `/docs` 中接口路径、方法、Schema 正确。
2. 所有课程内接口均校验课程权限。
3. 所有教师接口均校验教师或管理员权限。
4. 所有管理员接口均校验 admin 权限。
5. 所有列表接口分页正常。
6. 所有删除接口有确认机制。
7. 所有错误响应格式统一。
8. 后端接口与 `04_API接口文档.md` 一致。
9. Service 层保留后续接入 Agent 的扩展点。
10. 不允许 Agent 直接替代 Service 事务边界。

------

# 阶段 6：前端页面与 API 联调

## 6.1 阶段目标

保证前端页面、API 封装、TypeScript 类型、后端 Schema 完全一致，并为后续 Skills / MCP / Agent 页面扩展做准备。

------

## 6.2 当前必须修复任务

| 编号  | 任务                   | 修改文件                                                     | 验收标准                            |
| ----- | ---------------------- | ------------------------------------------------------------ | ----------------------------------- |
| T6.1  | 修复批量上传 API       | `api/resources.ts`                                           | 路径为 `/upload-batch`              |
| T6.2  | 修复任务字段           | `api/tasks.ts`、`CourseTasksView.vue`、`types/index.ts`      | 字段为 `additional_instructions`    |
| T6.3  | 修复管理员更新用户     | `api/admin.ts`、`AdminUsersView.vue`、后端 `admin.py`        | 前后端均使用 JSON Body              |
| T6.4  | 修复资源搜索参数       | `api/resources.ts`、`CourseResourcesView.vue`、后端 `resources.py` | 参数名称一致                        |
| T6.5  | 处理报告删除按钮       | `CourseReportsView.vue` 或后端 reports API                   | 无后端接口则移除按钮                |
| T6.6  | 增加课程详情默认重定向 | `router/index.ts`                                            | `/courses/:courseId` 自动进入资源页 |
| T6.7  | 完善 Token 刷新保存    | `stores/auth.ts`、`api/client.ts`                            | refresh_token 正常保存和清理        |
| T6.8  | 统一 Markdown 渲染     | `MarkdownRenderer.vue`                                       | marked + DOMPurify                  |
| T6.9  | 替换新增页面 Emoji     | 各 views                                                     | 新增或修改页面使用 Lucide 图标      |
| T6.10 | 检查移动端布局         | Layout、Sidebar、页面                                        | 课程底部 TabBar 不遮挡内容          |

------

## 6.3 为智能体平台预留前端入口

后续建议新增页面：

```text
课程内：
/courses/:courseId/analysis
/courses/:courseId/lesson-design
/courses/:courseId/study-path
/courses/:courseId/skills

管理员：
/admin/skills
/admin/mcp
/admin/agent-runs
```

------

## 6.4 前端验收标准

1. 未登录访问受保护页面跳转 `/login`。
2. 已登录访问 `/login` 跳转 `/home`。
3. 学生看不到报告、课程设置、管理员页面。
4. 学生看不到资源上传和任务生成按钮。
5. 教师能管理自己的课程。
6. 管理员能进入后台。
7. 所有页面具备 loading、empty、error、normal 状态。
8. 所有 Markdown 内容安全渲染。
9. 所有删除操作有确认弹窗。
10. 所有 API 字段与后端一致。
11. 后续新增智能体页面必须继续使用当前前端技术栈。

------

# 阶段 7：Skills 基础框架实现

## 7.1 阶段目标

新增 EduAgent 运行时 Skills 系统，将复杂教学能力封装为可注册、可调用、可测试的技能。

注意：

```text
codebuddy-docs/skills/ 是 CodeBuddy 开发规范 Skill。
backend/app/skills/ 是 EduAgent 运行时 Skill。
二者不是同一个概念。
```

------

## 7.2 新增目录结构

```text
backend/app/skills/
├── __init__.py
├── base.py
├── schemas.py
├── registry.py
├── loader.py
├── executor.py
├── builtin/
│   ├── course_qa/
│   ├── resource_analysis/
│   ├── task_generation/
│   ├── report_generation/
│   ├── code_explanation/
│   ├── lesson_design/
│   ├── quiz_generation/
│   └── study_path/
└── custom/
```

------

## 7.3 基础框架任务

| 编号 | 任务               | 文件                      | 验收标准                                      |
| ---- | ------------------ | ------------------------- | --------------------------------------------- |
| T7.1 | 定义 BaseSkill     | `skills/base.py`          | 所有 Skill 继承统一接口                       |
| T7.2 | 定义 Skill Schema  | `skills/schemas.py`       | 包含 SkillContext、SkillResult、SkillMetadata |
| T7.3 | 实现 SkillRegistry | `skills/registry.py`      | 可注册、获取、列出 Skill                      |
| T7.4 | 实现 SkillExecutor | `skills/executor.py`      | 可校验权限、执行 Skill、返回结果              |
| T7.5 | 实现 Skill Loader  | `skills/loader.py`        | 可加载 builtin Skills                         |
| T7.6 | 增加执行日志       | `skill_runs` 或结构化日志 | 记录 skill_name、user_id、course_id、status   |
| T7.7 | 增加测试           | `tests/test_skills.py`    | Registry 和 Executor 可测                     |

------

## 7.4 内置 Skills 实现任务

| Skill               | 文件目录                            | 目标                     |
| ------------------- | ----------------------------------- | ------------------------ |
| `course_qa`         | `skills/builtin/course_qa/`         | 基于课程资料回答问题     |
| `resource_analysis` | `skills/builtin/resource_analysis/` | 分析课程资源摘要和知识点 |
| `task_generation`   | `skills/builtin/task_generation/`   | 生成教学任务             |
| `report_generation` | `skills/builtin/report_generation/` | 生成教学报告             |
| `code_explanation`  | `skills/builtin/code_explanation/`  | 解释和分析代码           |
| `lesson_design`     | `skills/builtin/lesson_design/`     | 生成教学设计             |
| `quiz_generation`   | `skills/builtin/quiz_generation/`   | 生成测验题               |
| `study_path`        | `skills/builtin/study_path/`        | 生成学习路径建议         |

------

## 7.5 每个 Skill 必须包含

```text
SKILL.md
skill.py
prompts.py
```

### SKILL.md 必须包含

1. 技能定位。
2. 适用场景。
3. 输入参数。
4. 输出结果。
5. 可调用工具。
6. 执行步骤。
7. 安全限制。
8. 示例。

------

## 7.6 Skills 验收标准

| 编号        | 验收项            | 通过标准                                 |
| ----------- | ----------------- | ---------------------------------------- |
| SKILL-AC-01 | Skill Registry    | 可以注册和列出内置 Skill                 |
| SKILL-AC-02 | Skill Metadata    | 每个 Skill 有名称、描述、输入输出 Schema |
| SKILL-AC-03 | Skill Executor    | 可以执行指定 Skill                       |
| SKILL-AC-04 | course_qa         | 可以基于课程资料回答问题                 |
| SKILL-AC-05 | resource_analysis | 可以分析课程资源摘要和知识点             |
| SKILL-AC-06 | task_generation   | 可以生成任务草稿                         |
| SKILL-AC-07 | report_generation | 可以生成教学报告                         |
| SKILL-AC-08 | code_explanation  | 可以解释代码                             |
| SKILL-AC-09 | 权限控制          | 学生不能执行教师专属 Skill               |
| SKILL-AC-10 | 执行记录          | Skill 执行有日志或记录                   |
| SKILL-AC-11 | 失败降级          | Skill 失败时返回可理解错误               |

------

# 阶段 8：MCP 基础框架实现

## 8.1 阶段目标

新增 EduAgent MCP 工具生态，将 RAG、课程数据库、文件资源、报告分析、代码沙箱等能力封装为可注册、可调用、可权限控制的工具。

第一阶段建议实现 **内部 MCP 风格工具**，不必一开始接入外部 MCP Server。

------

## 8.2 新增目录结构

```text
backend/app/mcp/
├── __init__.py
├── client.py
├── registry.py
├── schemas.py
├── permissions.py
└── adapters/
    ├── internal_rag.py
    ├── course_db.py
    ├── file_resource.py
    ├── report_analysis.py
    └── code_sandbox.py
```

------

## 8.3 基础框架任务

| 编号 | 任务              | 文件                          | 验收标准                                          |
| ---- | ----------------- | ----------------------------- | ------------------------------------------------- |
| T8.1 | 定义 MCP Schema   | `mcp/schemas.py`              | 包含 MCPToolDefinition、MCPToolResult、MCPContext |
| T8.2 | 实现 MCP Registry | `mcp/registry.py`             | 可注册和列出 MCP Server / Tool                    |
| T8.3 | 实现 MCP Client   | `mcp/client.py`               | 可调用内部 MCP Tool                               |
| T8.4 | 实现权限检查      | `mcp/permissions.py`          | 调用前校验 user_role、course_role、course_id      |
| T8.5 | 实现调用日志      | `mcp_tool_calls` 或结构化日志 | 记录 server、tool、status、latency                |
| T8.6 | 增加测试          | `tests/test_mcp.py`           | Registry、权限、工具调用可测                      |

------

## 8.4 内部 MCP Adapter 实现任务

| Adapter              | 工具示例                                           | 目标                           |
| -------------------- | -------------------------------------------------- | ------------------------------ |
| `internal_rag.py`    | `search_course_knowledge`、`get_chunk_detail`      | 课程知识库检索                 |
| `course_db.py`       | `get_course_stats`、`query_qa_records`             | 安全查询课程数据               |
| `file_resource.py`   | `list_course_files`、`summarize_file`              | 课程资源分析                   |
| `report_analysis.py` | `analyze_qa_hotspots`、`analyze_task_distribution` | 报告统计分析                   |
| `code_sandbox.py`    | `run_python_code`、`analyze_code_error`            | 代码解释和沙箱执行，初期可关闭 |

------

## 8.5 MCP 安全要求

MCP Tool 调用前必须检查：

1. 用户是否登录。
2. 用户是否属于当前课程。
3. 用户是否有调用该 Server 的角色权限。
4. 用户是否有调用该 Tool 的角色权限。
5. Tool 参数是否包含其他课程 ID。
6. Tool 是否为高风险工具。
7. 是否超过调用次数限制。
8. 是否超过执行超时限制。

禁止：

```text
MCP Tool 执行原始 SQL
MCP Tool 返回服务器真实路径
MCP Tool 跨课程访问数据
MCP Tool 输出真实 API Key
MCP Tool 暴露内部异常堆栈给用户
```

------

## 8.6 MCP 验收标准

| 编号      | 验收项         | 通过标准                     |
| --------- | -------------- | ---------------------------- |
| MCP-AC-01 | MCP Registry   | 可以注册和列出 MCP Server    |
| MCP-AC-02 | Tool Schema    | 每个工具有输入输出 Schema    |
| MCP-AC-03 | MCP 权限       | 学生不能调用教师或管理员工具 |
| MCP-AC-04 | RAG MCP Tool   | 可以通过工具检索课程知识库   |
| MCP-AC-05 | Course DB Tool | 可以安全查询课程统计         |
| MCP-AC-06 | File Tool      | 只能访问当前课程资源         |
| MCP-AC-07 | 调用日志       | 工具调用有日志记录           |
| MCP-AC-08 | 异常处理       | 工具失败不会导致系统崩溃     |

------

# 阶段 9：Agent Orchestrator / Planner / Router 实现

## 9.1 阶段目标

新增智能体编排层，让系统能够根据用户请求识别意图、规划任务、选择技能、选择工具并执行。

------

## 9.2 新增文件

```text
backend/app/agent/orchestrator.py
backend/app/agent/planner.py
backend/app/agent/router.py
backend/app/agent/context.py
backend/app/agent/prompts/intent.py
backend/app/agent/prompts/planner.py
backend/app/agent/prompts/skill_router.py
backend/app/agent/prompts/tool_router.py
backend/app/agent/prompts/mcp.py
backend/app/agent/prompts/builders.py
```

------

## 9.3 任务清单

| 编号  | 任务                | 文件                                         | 验收标准                                       |
| ----- | ------------------- | -------------------------------------------- | ---------------------------------------------- |
| T9.1  | 定义 AgentContext   | `agent/context.py`                           | 包含 request_id、user_id、course_id、roles     |
| T9.2  | 增强 AgentState     | `agent/state.py`                             | 支持 intent、plan、skill_calls、mcp_tool_calls |
| T9.3  | 实现 Intent Router  | `agent/router.py`、`prompts/intent.py`       | 可识别主要教学意图                             |
| T9.4  | 实现 Planner        | `agent/planner.py`、`prompts/planner.py`     | 可拆解复杂任务                                 |
| T9.5  | 实现 Skill Router   | `agent/router.py`、`prompts/skill_router.py` | 可选择合适 Skill                               |
| T9.6  | 实现 Tool Router    | `agent/router.py`、`prompts/tool_router.py`  | 可选择 MCP / RAG / Local Tool                  |
| T9.7  | 实现 Orchestrator   | `agent/orchestrator.py`                      | 可完成完整调度                                 |
| T9.8  | 实现 Prompt Builder | `prompts/builders.py`                        | 统一构造 Prompt                                |
| T9.9  | 记录 Agent Run      | `agent_runs` 或日志                          | 可追踪 intent、skill、steps                    |
| T9.10 | 增加测试            | `tests/test_agent_orchestrator.py`           | 意图、规划、路由可测                           |

------

## 9.4 支持的意图类型

```text
course_qa
resource_summary
resource_analysis
task_generation
quiz_generation
lab_guide_generation
report_generation
code_explanation
code_debugging
lesson_design
study_path
admin_analysis
general_help
unknown
```

------

## 9.5 AgentState v2 必须支持

```text
request_id
course_id
user_id
user_role
course_role
course_name
conversation_id
raw_input
normalized_input
intent
plan
current_step
step_results
selected_skill
skill_input
skill_output
skill_calls
mcp_tool_calls
retrieved_docs
final_sources
prompt_messages
llm_output
parsed_output
final_answer
final_payload
guardrail_checks
permissions
error
step_count
```

------

## 9.6 验收标准

| 编号        | 验收项        | 通过标准                               |
| ----------- | ------------- | -------------------------------------- |
| AGENT-AC-01 | Intent Router | 能识别问答、任务、报告、资源分析等意图 |
| AGENT-AC-02 | Planner       | 复杂请求能拆解步骤                     |
| AGENT-AC-03 | Skill Router  | 能根据意图选择正确 Skill               |
| AGENT-AC-04 | Tool Router   | 能根据 Skill 选择正确 Tool             |
| AGENT-AC-05 | Orchestrator  | 能串联意图、规划、技能和工具           |
| AGENT-AC-06 | AgentState    | 记录 plan、skill_calls、mcp_tool_calls |
| AGENT-AC-07 | 权限安全      | 不越权调用 Skill 或 MCP Tool           |
| AGENT-AC-08 | 执行记录      | Agent 执行可追踪                       |
| AGENT-AC-09 | Mock 隔离     | Mock Workflow 不进入生产主链路         |

------

# 阶段 10：多智能体工作流接入

## 10.1 阶段目标

在 Skills、MCP 和 Orchestrator 基础上，逐步接入多智能体工作流。

------

## 10.2 推荐接入顺序

```text
CourseQAAgent
→ TaskGenerationAgent
→ ReportGenerationAgent
→ ResourceAnalysisAgent
→ CodeTutorAgent
→ LessonDesignAgent
→ StudyPathAgent
```

------

## 10.3 CourseQAAgent 接入

目标：

```text
QA Service
→ Agent Orchestrator
→ course_qa Skill
→ RAG MCP Tool
→ LLM
→ Service 保存 qa_records
```

验收标准：

1. `/qa/ask` 返回结构不变。
2. `/qa/ask-stream` SSE 格式不变。
3. `sources` 格式不变。
4. 结果保存到 `qa_records`。
5. 学生不能跨课程问答。
6. 资料不足时明确说明。

------

## 10.4 TaskGenerationAgent 接入

目标：

```text
Task Service
→ Agent Orchestrator
→ task_generation / quiz_generation Skill
→ RAG MCP Tool
→ LLM
→ Service 保存 tasks draft
```

验收标准：

1. `/tasks/generate` 返回真实 task ID。
2. 任务默认 `draft`。
3. `additional_instructions` 生效。
4. 学生不能生成任务。
5. 任务引用资源格式统一。

------

## 10.5 ReportGenerationAgent 接入

目标：

```text
Report Service
→ Agent Orchestrator
→ report_generation Skill
→ Course DB / Report Analysis MCP Tools
→ LLM
→ Service 保存 reports
```

验收标准：

1. 报告使用真实日期范围。
2. 报告数字来自真实 statistics。
3. 不编造数据。
4. 返回真实 report ID。
5. 学生不能生成或查看报告。

------

## 10.6 ResourceAnalysisAgent 接入

目标：

```text
Resource Analysis API 或内部任务
→ resource_analysis Skill
→ File Resource MCP Tool
→ RAG / LLM
→ 保存资源摘要或分析结果
```

验收标准：

1. 能生成资源摘要。
2. 能提取知识点。
3. 能发现资料缺失或重复。
4. 不编造文件内容。
5. 只分析当前课程资源。

------

## 10.7 CodeTutorAgent 接入

目标：

```text
代码解释请求
→ code_explanation Skill
→ 可选 Code Sandbox MCP Tool
→ LLM
→ 返回教学式解释
```

验收标准：

1. 能解释代码。
2. 能分析报错。
3. 学生不会得到完整可提交作业答案。
4. 代码执行默认受限或关闭。
5. 不输出危险命令。

------

## 10.8 LessonDesignAgent 接入

目标：

```text
教师请求教学设计
→ lesson_design Skill
→ RAG MCP Tool
→ LLM
→ 返回教学设计 Markdown
```

验收标准：

1. 输出教学目标、重点、难点、流程、活动、练习。
2. 课时分配合理。
3. 基于课程资料。
4. 教师可编辑使用。

------

## 10.9 StudyPathAgent 接入

目标：

```text
学生请求复习建议
→ study_path Skill
→ 当前学生 qa_records + 课程资源
→ LLM
→ 返回学习路径
```

验收标准：

1. 只分析当前学生数据。
2. 不泄露其他学生问答。
3. 推荐当前课程资源。
4. 语气积极，建议具体。

------

# 阶段 11：前端智能体能力页面扩展

## 11.1 阶段目标

在现有页面稳定后，扩展体现智能体平台能力的前端页面。

------

## 11.2 建议新增课程内页面

| 路由                               | 页面           | 功能                         |
| ---------------------------------- | -------------- | ---------------------------- |
| `/courses/:courseId/analysis`      | 课程资源分析页 | 调用 resource_analysis Skill |
| `/courses/:courseId/lesson-design` | 教学设计页     | 调用 lesson_design Skill     |
| `/courses/:courseId/study-path`    | 学习路径页     | 调用 study_path Skill        |
| `/courses/:courseId/skills`        | 课程技能页     | 展示当前课程可用 Skills      |

------

## 11.3 建议新增管理员页面

| 路由                | 页面             | 功能                               |
| ------------------- | ---------------- | ---------------------------------- |
| `/admin/skills`     | Skills 管理页    | 查看内置 Skills、启用状态、权限    |
| `/admin/mcp`        | MCP 管理页       | 查看 MCP Server 和 Tool            |
| `/admin/agent-runs` | Agent 执行记录页 | 查看 Agent / Skill / Tool 执行日志 |

------

## 11.4 前端 API 建议

新增：

```text
frontend/src/api/skills.ts
frontend/src/api/mcp.ts
frontend/src/api/agent.ts
```

------

## 11.5 页面验收标准

1. 教师可以在课程内查看资源分析。
2. 教师可以生成教学设计。
3. 学生可以查看自己的学习路径。
4. 管理员可以查看 Skills 列表。
5. 管理员可以查看 MCP Tools。
6. 管理员可以查看 Agent 执行记录。
7. 学生不能访问教师和管理员页面。
8. 所有页面具备 loading、error、empty、normal 状态。
9. Markdown 内容使用 `MarkdownRenderer`。
10. 删除或高风险操作必须二次确认。

------

# 阶段 12：测试与验收补充

## 12.1 阶段目标

补充后端、RAG、Agent、MCP、Skills、前端和端到端测试，确保核心业务链路可验证。

------

## 12.2 后端测试任务

| 编号   | 测试类型          | 文件                               | 覆盖内容                              |
| ------ | ----------------- | ---------------------------------- | ------------------------------------- |
| T12.1  | Smoke Test        | `backend/tests/test_smoke.py`      | `/health`、应用启动                   |
| T12.2  | Auth API Test     | `backend/tests/test_auth.py`       | 注册、登录、刷新、权限                |
| T12.3  | Course API Test   | `backend/tests/test_courses.py`    | 创建、加入、成员、删除                |
| T12.4  | Resource API Test | `backend/tests/test_resources.py`  | 上传、列表、状态、删除                |
| T12.5  | QA API Test       | `backend/tests/test_qa.py`         | 问答、SSE、历史、反馈                 |
| T12.6  | Task API Test     | `backend/tests/test_tasks.py`      | 生成、发布、学生只读                  |
| T12.7  | Report API Test   | `backend/tests/test_reports.py`    | 生成、详情、导出                      |
| T12.8  | Admin API Test    | `backend/tests/test_admin.py`      | 用户管理、系统设置                    |
| T12.9  | RAG Test          | `backend/tests/test_rag.py`        | 解析、切片、检索、sources             |
| T12.10 | Skills Test       | `backend/tests/test_skills.py`     | Registry、Executor、内置 Skills       |
| T12.11 | MCP Test          | `backend/tests/test_mcp.py`        | Registry、权限、Tool 调用             |
| T12.12 | Agent Test        | `backend/tests/test_agent.py`      | Intent、Planner、Router、Orchestrator |
| T12.13 | Guardrail Test    | `backend/tests/test_guardrails.py` | 越狱、越权、敏感信息检测              |

------

## 12.3 前端测试任务

| 编号   | 测试内容         | 验收标准                                |
| ------ | ---------------- | --------------------------------------- |
| T12.14 | 路由守卫         | 未登录访问受保护页面跳转登录            |
| T12.15 | 角色页面         | 学生不能进入 admin / reports / settings |
| T12.16 | 登录页           | 成功登录后保存 token                    |
| T12.17 | 课程列表         | 创建和加入课程按钮正常                  |
| T12.18 | 资源页           | 上传、状态、失败展示正常                |
| T12.19 | 问答页           | SSE token 正常追加                      |
| T12.20 | 任务页           | 学生只看 published                      |
| T12.21 | 报告页           | MD 导出正常                             |
| T12.22 | Skills 页面      | 根据角色显示可用 Skills                 |
| T12.23 | MCP 管理页       | 管理员可查看 Tools                      |
| T12.24 | Agent 执行记录页 | 管理员可查看执行记录                    |
| T12.25 | MarkdownRenderer | XSS 内容被过滤                          |
| T12.26 | 响应式布局       | 移动端底部导航不遮挡                    |

------

## 12.4 端到端验收链路

基础业务链路：

```text
注册教师
→ 教师登录
→ 教师创建课程
→ 注册学生
→ 学生登录
→ 学生通过课程码加入课程
→ 教师上传课程资料
→ 资源状态变为 ready
→ 学生基于资料提问
→ AI 返回答案和引用来源
→ 教师生成任务草稿
→ 教师发布任务
→ 学生查看任务
→ 教师生成报告
→ 教师导出 Markdown 报告
→ 管理员查看用户列表
```

智能体平台链路：

```text
教师上传课程资料
→ ResourceAnalysisAgent 分析资源
→ LessonDesignAgent 生成教学设计
→ QuizGeneration Skill 生成测验题
→ TaskGenerationAgent 生成任务草稿
→ ReportGenerationAgent 生成报告
→ 管理员查看 Agent / Skill / MCP 执行记录
```

------

# 阶段 13：部署、安全与文档交付

## 13.1 阶段目标

保证项目可以通过 Docker Compose 启动，敏感文件被清理，文档与代码保持一致。

------

## 13.2 部署任务

| 编号   | 任务                      | 修改文件                                 | 验收标准                              |
| ------ | ------------------------- | ---------------------------------------- | ------------------------------------- |
| T13.1  | 检查 `.env.example`       | `.env.example`                           | 包含所有必需配置，无真实密钥          |
| T13.2  | 清理敏感文件              | `.env`、`api-key.txt`                    | 不进入交付包                          |
| T13.3  | 检查 `.gitignore`         | `.gitignore`                             | 排除 `.env`、密钥、venv、node_modules |
| T13.4  | 修复 ChromaDB 端口说明    | `docker-compose.yml`、文档               | 容器内 8000，宿主机映射清晰           |
| T13.5  | 统一文件存储策略          | `nginx.conf`、`main.py`、资源服务        | 本地存储或 MinIO 策略明确             |
| T13.6  | 修复 Nginx `/files/` 代理 | `nginx.conf`                             | 与实际文件存储一致                    |
| T13.7  | 检查 frontend dist 挂载   | `docker-compose.yml`                     | 不覆盖镜像构建产物                    |
| T13.8  | 检查生产启动命令          | `backend/Dockerfile`、`requirements.txt` | gunicorn 依赖或命令正确               |
| T13.9  | 检查 Redis 密码配置       | `docker-compose.prod.yml`、`config.py`   | 如启用密码，URL 支持密码              |
| T13.10 | 增加 Agent 配置           | `config.py`、`.env.example`              | AGENT / MCP / SKILLS 配置完整         |
| T13.11 | 完成部署文档              | README / docs                            | 启动、迁移、访问、排错清楚            |

------

## 13.3 推荐新增环境变量

```env
AGENT_ENABLED=true
AGENT_TRACE_ENABLED=true
AGENT_MAX_STEPS=10
AGENT_DEFAULT_TIMEOUT_SECONDS=120

SKILLS_ENABLED=true
SKILLS_LOAD_MODE=builtin
SKILLS_CUSTOM_PATH=backend/app/skills/custom
SKILLS_EXECUTION_TIMEOUT_SECONDS=120

MCP_ENABLED=true
MCP_MODE=internal
MCP_TOOL_TIMEOUT_SECONDS=30
MCP_MAX_TOOL_CALLS_PER_RUN=20
MCP_SERVER_CONFIG_PATH=backend/app/mcp/servers.yaml

CODE_SANDBOX_ENABLED=false
CODE_SANDBOX_TIMEOUT_SECONDS=5
CODE_SANDBOX_MEMORY_LIMIT_MB=128
```

------

## 13.4 文档同步任务

CodeBuddy 修改代码后，必须同步更新相关文档。

| 修改内容        | 必须同步更新                                          |
| --------------- | ----------------------------------------------------- |
| 环境变量        | `00_环境配置说明.md`、`.env.example`                  |
| 技术架构        | `02_技术架构文档.md`                                  |
| API 路径 / 字段 | `04_API接口文档.md`                                   |
| 数据库字段      | `03_数据模型与数据库设计.md`                          |
| 前端页面        | `07_页面流程图.md`                                    |
| Agent 工作流    | `05_AI智能体行为定义.md`                              |
| Prompt          | `06_提示词模板.md`                                    |
| MCP / Skills    | `05_AI智能体行为定义.md`、`08_CodeBuddy开发任务书.md` |
| 开发任务        | `08_CodeBuddy开发任务书.md`                           |
| 部署服务        | `02_技术架构文档.md`、`00_环境配置说明.md`            |

------

# 14. 全局代码规范

## 14.1 后端规范

1. API 路由层只做参数接收、权限校验和 Service 调用。
2. 业务逻辑必须放在 `services/`。
3. 数据库模型必须放在 `models/`。
4. 请求和响应模型必须放在 `schemas/`。
5. RAG 逻辑必须放在 `rag/`。
6. Agent 逻辑必须放在 `agent/`。
7. MCP 逻辑必须放在 `mcp/`。
8. Skills 逻辑必须放在 `skills/`。
9. 异步任务必须放在 `tasks/`。
10. 不得在路由函数中直接写复杂 SQL。
11. 不得在代码中硬编码 API Key。
12. 所有课程内查询必须带 `course_id`。
13. 所有写操作必须校验权限。
14. 新增数据库字段必须新增 Alembic 迁移。
15. 新增接口必须补测试。
16. 新增枚举必须同步前端类型。
17. 删除外部资源必须处理数据库、文件和 ChromaDB 一致性。

------

## 14.2 前端规范

1. API 调用统一写在 `frontend/src/api/`。
2. 页面不得硬编码完整后端地址。
3. 类型定义必须与后端 Schema 保持一致。
4. Token 逻辑统一在 `auth.ts` 和 `client.ts`。
5. 页面必须处理 loading、error、empty、normal 状态。
6. 删除操作必须使用 ConfirmDialog。
7. Markdown 必须使用 MarkdownRenderer。
8. 学生页面不得显示教师操作按钮。
9. 管理员页面必须有角色路由守卫。
10. 新增页面必须更新路由和页面流程文档。
11. 新增 API 字段必须更新 `types/index.ts`。
12. 移动端布局必须测试。
13. 新增图标优先使用 Lucide。
14. 不得在前端保存真实模型 API Key。
15. SSE 逻辑必须支持中断。

------

## 14.3 RAG 规范

1. 检索必须限定课程。
2. 向量写入必须保存可追溯元数据。
3. PostgreSQL chunk 与 ChromaDB 向量必须一一对应。
4. 删除资源必须删除对应向量。
5. Reranker 失败不能导致问答整体失败。
6. Embedding 维度变化必须重建索引。
7. 引用来源字段必须统一。
8. 资料不足时必须明确说明。
9. HashEmbeddingFallback 只能用于开发兜底。
10. 不得跨课程检索。

------

## 14.4 Agent 规范

1. Agent 不得绕过权限校验。
2. Agent 必须使用统一 AgentContext。
3. AgentState 必须记录 intent、plan、skill_calls、mcp_tool_calls。
4. Agent Tool 必须限定 `course_id`。
5. 异步 Tool 必须使用 `await`。
6. Workflow 节点不得使用 Mock 文案进入生产链路。
7. Prompt 必须限制课程范围。
8. LLM 输出必须有解析失败兜底。
9. Agent 返回的 ID 必须是真实数据库 ID。
10. 流式输出必须符合 SSE 格式。
11. 修改 Prompt 必须同步文档和测试。

------

## 14.5 MCP 规范

1. MCP Tool 不得执行原始 SQL。
2. MCP Tool 必须有输入输出 Schema。
3. MCP Tool 必须有权限配置。
4. MCP Tool 调用前必须校验用户角色和课程角色。
5. MCP Tool 不得跨课程访问数据。
6. MCP Tool 不得返回服务器真实文件路径。
7. MCP Tool 不得暴露内部异常堆栈。
8. MCP Tool 必须有超时。
9. MCP Tool 调用必须记录日志。
10. 高风险 Tool 默认关闭。

------

## 14.6 Skills 规范

1. 每个 Skill 必须继承 BaseSkill。
2. 每个 Skill 必须有 SKILL.md。
3. 每个 Skill 必须有 input_schema 和 output_schema。
4. 每个 Skill 必须声明 allowed_roles。
5. Skill 执行前必须校验权限。
6. Skill 不得直接读取 `.env`。
7. Skill 不得跨课程访问数据。
8. Skill 输出必须可解析。
9. Skill 失败必须返回可理解错误。
10. 每个内置 Skill 必须有测试。

------

# 15. 当前优先修复清单

## 15.1 P0 必修

| 编号  | 问题                          | 影响                     |
| ----- | ----------------------------- | ------------------------ |
| P0-01 | 登录不返回 refresh_token      | 前端自动刷新不可用       |
| P0-02 | 批量上传路径不一致            | 批量上传失败             |
| P0-03 | 任务字段不一致                | 额外要求无法传给后端     |
| P0-04 | 资源搜索路由顺序              | 搜索接口可能不可用       |
| P0-05 | `Resource.uploaded_by` 不一致 | 模型与迁移冲突           |
| P0-06 | `pgcrypto` 扩展缺失           | 新库 UUID 默认值可能失败 |
| P0-07 | Agent Tool 缺少 await         | Agent 检索不可用         |
| P0-08 | Workflow LLM 节点 Mock        | Agent 主链路不可用       |
| P0-09 | gunicorn 依赖风险             | 生产镜像可能启动失败     |

------

## 15.2 P1 建议修复

| 编号  | 问题                              | 影响                    |
| ----- | --------------------------------- | ----------------------- |
| P1-01 | `qa_records` 缺少 conversation_id | 多轮历史不完整          |
| P1-02 | Report Workflow 日期硬编码        | 报告时间错误            |
| P1-03 | Skills 框架缺失                   | 智能体能力无法复用      |
| P1-04 | MCP 框架缺失                      | 无法体现工具生态        |
| P1-05 | Agent Orchestrator 缺失           | 无法统一编排 Agent      |
| P1-06 | Prompt Builder 缺失               | Prompt 分散维护         |
| P1-07 | Agent 执行记录缺失                | 执行不可审计            |
| P1-08 | MinIO 与本地存储不一致            | 文件访问可能失败        |
| P1-09 | Nginx `/files/` 代理不一致        | 资源文件可能无法下载    |
| P1-10 | xlsx 支持不完整                   | 用户上传 Excel 可能失败 |
| P1-11 | 报告删除 UI 无接口                | 页面功能误导            |
| P1-12 | Admin 更新用户参数格式不一致      | 用户管理可能失败        |

------

# 16. 最终验收标准

## 16.1 基础功能验收

| 编号     | 验收项     | 通过标准                       |
| -------- | ---------- | ------------------------------ |
| FINAL-01 | 注册登录   | student / teacher 可以注册登录 |
| FINAL-02 | Token 刷新 | refresh_token 链路完整         |
| FINAL-03 | 创建课程   | 教师可以创建课程               |
| FINAL-04 | 加入课程   | 学生可以通过课程码加入         |
| FINAL-05 | 上传资源   | 教师可以上传课程资料           |
| FINAL-06 | 资源处理   | 资源最终变为 ready 或 failed   |
| FINAL-07 | 智能问答   | 学生可以基于资料提问           |
| FINAL-08 | 引用来源   | 问答返回 sources               |
| FINAL-09 | 任务生成   | 教师可以生成任务草稿           |
| FINAL-10 | 任务发布   | 学生可以查看已发布任务         |
| FINAL-11 | 报告生成   | 教师可以生成报告               |
| FINAL-12 | 报告导出   | Markdown 导出正常              |
| FINAL-13 | 管理后台   | 管理员可以管理用户             |
| FINAL-14 | 权限控制   | 学生不能访问教师和管理员功能   |
| FINAL-15 | 课程隔离   | A 课程不能访问 B 课程数据      |

------

## 16.2 智能体平台验收

| 编号           | 验收项             | 通过标准                                 |
| -------------- | ------------------ | ---------------------------------------- |
| AGENT-FINAL-01 | Agent Orchestrator | 能统一调度 Intent、Planner、Skill、Tool  |
| AGENT-FINAL-02 | Intent Router      | 能识别主要教学意图                       |
| AGENT-FINAL-03 | Planner            | 能拆解复杂教学任务                       |
| AGENT-FINAL-04 | Skill Router       | 能选择正确 Skill                         |
| AGENT-FINAL-05 | Tool Router        | 能选择正确 MCP / RAG / Local Tool        |
| AGENT-FINAL-06 | AgentState         | 能记录 plan、skill_calls、mcp_tool_calls |
| AGENT-FINAL-07 | Agent Runs         | Agent 执行可审计                         |
| AGENT-FINAL-08 | 多 Agent           | QA、任务、报告、资源分析至少可运行       |
| AGENT-FINAL-09 | Mock 清理          | 生产链路不使用 Mock LLM 节点             |
| AGENT-FINAL-10 | SSE                | QA 流式输出格式不变                      |

------

## 16.3 Skills 验收

| 编号           | 验收项            | 通过标准                      |
| -------------- | ----------------- | ----------------------------- |
| SKILL-FINAL-01 | Skill Registry    | 可注册和列出内置 Skills       |
| SKILL-FINAL-02 | Skill Executor    | 可执行 Skill 并返回结构化结果 |
| SKILL-FINAL-03 | course_qa         | 能基于课程资料问答            |
| SKILL-FINAL-04 | resource_analysis | 能分析资源摘要和知识点        |
| SKILL-FINAL-05 | task_generation   | 能生成教学任务                |
| SKILL-FINAL-06 | report_generation | 能生成教学报告                |
| SKILL-FINAL-07 | code_explanation  | 能解释代码                    |
| SKILL-FINAL-08 | lesson_design     | 能生成教学设计                |
| SKILL-FINAL-09 | study_path        | 能生成学习路径                |
| SKILL-FINAL-10 | Skill 权限        | 学生不能执行教师专属 Skill    |

------

## 16.4 MCP 验收

| 编号         | 验收项         | 通过标准                       |
| ------------ | -------------- | ------------------------------ |
| MCP-FINAL-01 | MCP Registry   | 可注册和列出 MCP Server / Tool |
| MCP-FINAL-02 | MCP Client     | 可调用内部 MCP Tool            |
| MCP-FINAL-03 | RAG Tool       | 可检索课程知识库               |
| MCP-FINAL-04 | Course DB Tool | 可安全查询课程统计             |
| MCP-FINAL-05 | File Tool      | 只能访问当前课程文件           |
| MCP-FINAL-06 | Report Tool    | 可生成报告统计分析             |
| MCP-FINAL-07 | MCP 权限       | 学生不能调用教师或管理员工具   |
| MCP-FINAL-08 | MCP 日志       | 工具调用可审计                 |
| MCP-FINAL-09 | MCP 安全       | 不执行原始 SQL，不返回真实路径 |
| MCP-FINAL-10 | MCP 异常       | 工具失败不会导致系统崩溃       |

------

## 16.5 技术验收

| 编号    | 验收项         | 通过标准                         |
| ------- | -------------- | -------------------------------- |
| TECH-01 | 后端启动       | FastAPI 正常启动                 |
| TECH-02 | 前端启动       | Vue 页面正常访问                 |
| TECH-03 | 数据库迁移     | Alembic 可成功执行               |
| TECH-04 | Celery         | Worker 可处理资源任务            |
| TECH-05 | Redis          | Token / Celery / Memory 连接正常 |
| TECH-06 | ChromaDB       | 向量写入和检索正常               |
| TECH-07 | Docker Compose | 核心服务可启动                   |
| TECH-08 | SSE            | 流式问答通过 Nginx 正常返回      |
| TECH-09 | Markdown       | 前端安全渲染                     |
| TECH-10 | 测试           | 核心测试通过                     |

------

## 16.6 安全验收

| 编号   | 验收项      | 通过标准                         |
| ------ | ----------- | -------------------------------- |
| SEC-01 | 密码安全    | 数据库只保存哈希密码             |
| SEC-02 | JWT 安全    | 未登录访问返回 401               |
| SEC-03 | 角色安全    | 无权限访问返回 403               |
| SEC-04 | 课程隔离    | 非课程成员不能访问课程数据       |
| SEC-05 | 文件上传    | 校验文件类型和大小               |
| SEC-06 | XSS 防护    | Markdown 经 DOMPurify 清理       |
| SEC-07 | 密钥清理    | 交付包不含 `.env`、`api-key.txt` |
| SEC-08 | 日志安全    | 日志不输出 API Key 和密码        |
| SEC-09 | MCP 安全    | Tool 不能越权访问                |
| SEC-10 | Skill 安全  | Skill 不能绕过权限               |
| SEC-11 | Prompt 安全 | 越狱请求被拦截                   |
| SEC-12 | 代码沙箱    | 高风险代码执行默认关闭或沙箱化   |

------

# 17. CodeBuddy 执行提示词

可以将下面内容作为 CodeBuddy 的项目级执行指令：

```text
你正在维护 EduAgent 课程资源与教学任务智能体项目。

这是一个已有代码项目，不是空项目。你必须先读取现有代码，再根据 codebuddy-docs 中的文档进行修复、扩展和验收。

项目目标不是简单 RAG 聊天机器人，而是课程智能体平台：

EduAgent = 课程业务系统 + RAG 知识库 + MCP 工具生态 + Skills 技能系统 + Agent Orchestrator + Planner + Tool Router + Skill Router + 多智能体协作。

开发规则：

1. 不得删除现有 backend、frontend、codebuddy-docs 后重新生成项目。
2. 以当前代码为事实来源，文档与代码冲突时先指出冲突，再修复。
3. 后端使用 FastAPI + SQLAlchemy Async + PostgreSQL + Redis + Celery + ChromaDB。
4. 前端使用 Vue 3 + TypeScript + Pinia + Vue Router + Axios + Tailwind CSS。
5. AI 能力使用 RAG + LLM + LangGraph + MCP + Skills。
6. 不得写入真实 API Key、JWT Secret、数据库密码。
7. 修改 API 时必须同步修改前端 API、TypeScript 类型和 API 文档。
8. 修改数据库模型时必须新增 Alembic 迁移，并同步数据库文档。
9. 修改 Prompt 或 Agent 工作流时必须同步智能体文档和提示词文档。
10. 修改页面时必须同步页面流程图文档。
11. 所有课程内查询必须校验 course_id。
12. 所有教师操作必须校验教师或管理员权限。
13. 修复问题时优先处理 P0 清单。
14. 每次修改后必须给出验证方式。
15. 不允许让 Mock LLM 节点进入生产主链路。
16. 新增 Skills 必须放在 backend/app/skills/。
17. 新增 MCP 能力必须放在 backend/app/mcp/。
18. 新增 Agent 编排能力必须通过 Agent Orchestrator / Planner / Router 实现。
19. Skill 输入输出必须有 Schema。
20. MCP Tool 输入输出必须有 Schema。
21. MCP Tool 不得执行原始 SQL。
22. 权限必须由代码判断，不能交给 LLM 判断。
23. Agent、Skill、MCP 都不能绕过 Service 层权限校验和数据库事务。
24. 所有 Agent / Skill / MCP 调用必须有日志或执行记录。
```

------

# 18. 本文档总结

本任务书的核心不是指导 CodeBuddy 从零开发 EduAgent，而是指导 CodeBuddy 在当前已有项目基础上完成：

```text
代码审查
→ P0 修复
→ 认证权限完善
→ 数据库一致性修复
→ RAG 主链路稳定化
→ 后端 API 完善
→ 前端联调
→ Skills 基础框架
→ MCP 基础框架
→ Agent Orchestrator / Planner / Router
→ 多智能体工作流
→ 前端智能体页面扩展
→ 测试补充
→ 部署和文档交付
```

当前最优先的开发顺序是：

```text
1. 修复现有前后端接口和字段不一致
2. 修复认证 Token 刷新链路
3. 修复数据库模型与迁移不一致
4. 稳定 RAG 查询改写、检索和引用来源
5. 稳定 QA / Task / Report Service 主链路
6. 新增 backend/app/skills 基础框架
7. 新增 backend/app/mcp 基础框架
8. 新增 Agent Orchestrator / Planner / Router
9. 将 QA / Task / Report 改造为 Skill
10. 扩展资源分析、代码辅导、教学设计、学习路径
11. 补充前端智能体页面
12. 补充测试、部署和安全清理
```

只要上述阶段全部完成，并通过最终验收标准，EduAgent 才能从普通课程 RAG 系统升级为真正可展示、可教学、可扩展的课程智能体平台。