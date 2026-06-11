# CODEBUDDY.md

## 1. 项目身份

本项目是 **EduAgent**。

EduAgent 是一个**课程智能体平台**，不是简单的 RAG 问答机器人，也不是普通的课程资料管理系统。

系统核心能力包括：

- 课程资源管理
- 课程知识库构建
- RAG 检索增强问答
- 教学任务生成
- 教学报告生成
- Agent Orchestrator 智能体编排
- MCP 工具调用
- Runtime Skills 运行时技能
- LangGraph 工作流
- 智能体执行审计
- 教师、学生、管理员多角色协作流程

开发本项目时，必须始终把它理解为：

```text
课程业务系统 + RAG 知识库 + 智能体编排 + MCP 工具生态 + Runtime Skills 技能系统
```

不要把本项目降级为普通 CRUD 系统，也不要只实现成简单的课程问答机器人。

------

## 2. 编码前必须阅读的文档

在修改代码之前，应根据任务类型阅读 `codebuddy-docs/` 下的相关文档。

### 2.1 项目整体理解

优先阅读：

- @codebuddy-docs/README.md
- @codebuddy-docs/overview.md
- @codebuddy-docs/00_环境配置说明.md

### 2.2 需求、架构和接口设计

需要开发新功能、修改业务逻辑或调整架构时，阅读：

- @codebuddy-docs/specs/01_项目需求规格文档.md
- @codebuddy-docs/specs/02_技术架构文档.md
- @codebuddy-docs/specs/03_数据模型与数据库设计.md
- @codebuddy-docs/specs/04_API接口文档.md
- @codebuddy-docs/specs/05_AI智能体行为定义.md
- @codebuddy-docs/specs/06_提示词模板.md
- @codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
- @codebuddy-docs/specs/08_CodeBuddy开发任务书.md

### 2.3 问题修复和审查

修复问题前，阅读：

- @codebuddy-docs/review/07_页面流程图审查报告.md

如果任务涉及某个具体模块，应同时阅读对应的 `.codebuddy/rules/` 规则文件和 `.codebuddy/skills/` 技能文档。

------

## 3. 技术栈约束

### 3.1 后端技术栈

后端使用：

- Python
- FastAPI
- SQLAlchemy Async
- Alembic
- PostgreSQL
- Redis
- Celery
- ChromaDB
- LangChain
- LangGraph
- httpx
- Pydantic

不得随意替换后端技术栈。

### 3.2 前端技术栈

前端使用：

- Vue 3
- TypeScript
- Vue Router
- Pinia
- Tailwind CSS
- Axios
- marked
- DOMPurify
- lucide

不得把前端改成 React、Next.js、Angular 或其他框架。

### 3.3 AI 与智能体技术栈

AI 与智能体相关能力包括：

- DeepSeek 兼容模式的大模型调用配置
- RAG 知识库
- BGE-M3 Embedding 模型
- Reranker
- Agent Orchestrator
- Intent Router
- Planner
- Skill Router
- Tool Router
- MCP Tools
- Runtime Skills
- LangGraph Workflows
- Guardrails
- 执行审计日志

本项目课程内容和代码示例优先使用 DeepSeek 作为大模型供应商，不使用 OpenAI 作为默认供应商。

### 3.4 基础设施

项目基础设施包括：

- Docker
- Docker Compose
- Nginx
- PostgreSQL
- Redis
- ChromaDB
- MinIO 或本地文件存储

------

## 4. 总体架构规则

普通业务请求应遵循：

```text
Frontend
  ↓
FastAPI Router
  ↓
Service Layer
  ↓
Domain Logic / Repository / ORM
  ↓
Database / Vector Store / File Storage
```

AI 与智能体请求应遵循：

```text
Frontend
  ↓
FastAPI Router
  ↓
Service Layer
  ↓
Agent Orchestrator
  ↓
Intent Router
  ↓
Planner
  ↓
Skill Router / Tool Router
  ↓
Runtime Skills / MCP Tools / LangGraph Workflows
  ↓
Service Layer Persistence
  ↓
Database / Vector Store / Audit Logs
```

必须遵守以下架构边界：

1. 不得绕过 Service Layer。
2. 不得让 Router 直接写复杂业务逻辑。
3. 不得让 LangGraph Workflow 直接替代业务 Service。
4. 不得让 MCP Tool 绕过权限校验。
5. 不得让 Runtime Skill 直接越权访问数据库。
6. 不得让大模型判断用户是否有权限。
7. 权限必须由后端代码判断。
8. 智能体执行过程必须可审计、可追踪。

------

## 5. 通用开发规则

开发时必须遵守：

1. 不得删除项目后重新创建。
2. 不得随意更换技术栈。
3. 不得大规模重写已有系统。
4. 不得硬编码真实 API Key、JWT Secret、数据库密码或模型密钥。
5. 不得提交 `.env`、`api-key.txt`、本地凭据、运行日志、缓存文件、虚拟环境目录。
6. 示例配置必须写入 `.env.example`。
7. 后端、前端、数据库、API 和文档必须保持一致。
8. 修改数据库模型时必须同步 Alembic migration。
9. 修改后端 API 时必须同步前端 API 封装和 TypeScript 类型。
10. 修改前端页面或路由时必须同步页面流程文档。
11. 修改 AI 行为时必须同步提示词模板和智能体行为定义文档。
12. 修改 Skills、MCP Tools 或 Agent Workflows 时必须同步相关规则和审计逻辑。
13. 优先进行小范围、可审查、可测试的修改。
14. 完成任务后必须说明修改了哪些文件、为什么修改、如何验证。

------

## 6. 后端开发规则

后端代码必须遵循当前 FastAPI 项目结构。

应使用：

- FastAPI Router 编写 HTTP 接口
- Pydantic Schema 定义请求和响应结构
- Service Layer 编写业务逻辑
- SQLAlchemy Async 访问数据库
- Alembic 管理数据库迁移
- FastAPI Depends 注入认证、数据库会话和权限依赖

禁止：

1. 在 Router 中编写大量业务逻辑。
2. 绕过 Service Layer 直接操作数据库。
3. 在后端代码中硬编码密钥。
4. 用前端权限判断替代后端权限校验。
5. 让大模型直接决定权限。
6. 在工具调用中绕过课程权限和用户权限。

课程级别的数据操作必须校验：

- 当前用户身份
- 当前用户是否属于该课程
- 当前用户在该课程中的角色
- 当前请求是否限定在正确的 `course_id` 范围内

后端相关修改应优先参考：

- `.codebuddy/skills/fastapi-async-patterns/SKILL.md`
- `.codebuddy/skills/postgres-sqlalchemy-patterns/SKILL.md`
- `.codebuddy/skills/rag-implementation-patterns/SKILL.md`
- `.codebuddy/skills/langgraph-workflow-patterns/SKILL.md`
- `.codebuddy/skills/mcp-tool-development-patterns/SKILL.md`
- `.codebuddy/skills/runtime-skills-development-patterns/SKILL.md`

------

## 7. 前端开发规则

前端代码必须遵循当前 Vue 3 + TypeScript 项目结构。

应使用：

- Vue 3 Composition API
- TypeScript 类型定义
- Vue Router 管理路由
- Pinia 管理状态
- Axios 封装 API 请求
- Tailwind CSS 编写样式
- 可复用组件
- DOMPurify 安全渲染 Markdown

前端页面必须处理：

- loading 状态
- empty 空状态
- error 错误状态
- success 成功状态
- 权限不足状态
- 接口请求失败状态
- AI 生成中状态
- AI 生成失败状态

禁止：

1. 把前端权限当成唯一安全边界。
2. 在页面中写死后端接口返回结构。
3. 页面调用不存在的后端接口。
4. 前端字段名和后端 Schema 不一致。
5. 不处理接口失败和空数据状态。
6. 直接渲染未经清洗的 Markdown 或 HTML。

前端相关修改应优先参考：

- `.codebuddy/skills/vue3-tailwind-component-patterns/SKILL.md`
- `codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md`

------

## 8. 数据库开发规则

数据库相关开发必须遵循：

- PostgreSQL
- SQLAlchemy Async Models
- Alembic Migrations
- 明确的外键关系
- 一致的时间字段
- 必要的查询索引
- 智能体、Skill、MCP 执行审计表

修改数据库模型时必须同步：

1. SQLAlchemy Model。
2. Alembic Migration。
3. Pydantic Schema。
4. 相关 Service。
5. 相关 API 文档。
6. `codebuddy-docs/specs/03_数据模型与数据库设计.md`。

课程相关数据应尽量包含 `course_id`，确保课程级数据隔离。

智能体、Skill、MCP 执行记录必须可追踪。

建议审计表包括：

- `agent_runs`
- `agent_steps`
- `skill_definitions`
- `skill_runs`
- `mcp_servers`
- `mcp_tool_calls`

审计日志不得保存敏感密钥。

在可以满足审计要求的情况下，优先保存输入摘要和输出摘要，不要无节制保存完整 Prompt 和完整模型响应。

------

## 9. RAG 开发规则

RAG 是平台级能力，不只是课程问答功能。

RAG 应支持：

- 课程问答
- 资源分析
- 任务生成
- 报告生成
- 教案设计
- 学习路径生成
- Agent 工具调用
- Runtime Skills
- MCP 知识库检索工具

RAG 检索必须遵守课程边界。

每次检索必须限定：

- `course_id`
- 当前用户权限
- 当前课程资源范围

RAG 输出必须遵守：

1. 有依据时给出引用来源。
2. 资料不足时明确说明不足。
3. 不得编造不存在的资料来源。
4. 不得跨课程检索资料。
5. 不得泄露用户无权访问的资源。
6. 检索失败时必须有降级策略。

RAG 相关修改应优先参考：

- `.codebuddy/skills/rag-implementation-patterns/SKILL.md`

------

## 10. Agent、MCP 与 Runtime Skills 规则

EduAgent 应采用分层智能体架构：

```text
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
Runtime Skills / MCP Tools / LangGraph Workflows
```

### 10.1 Agent 规则

Agent 执行必须满足：

1. 可审计。
2. 可追踪。
3. 可失败恢复。
4. 不绕过权限。
5. 不暴露系统 Prompt。
6. 不泄露密钥。
7. 不直接替代业务 Service。
8. 不直接向用户返回未经处理的工具错误。

Agent 执行过程应记录：

- `agent_run_id`
- 用户 ID
- 课程 ID
- 意图识别结果
- 计划步骤
- 工具调用
- Skill 调用
- 执行状态
- 错误信息
- 执行耗时

### 10.2 Runtime Skills 规则

Runtime Skills 是项目运行时能力，例如：

- 课程问答
- 资源分析
- 任务生成
- 报告生成
- 教案设计
- 测验生成
- 学习路径生成
- 代码解释

每个 Runtime Skill 必须具备：

- 输入 Schema
- 输出 Schema
- 权限校验
- 执行日志
- 错误处理
- 稳定输出格式
- 可测试样例

Runtime Skills 相关修改应优先参考：

- `.codebuddy/skills/runtime-skills-development-patterns/SKILL.md`

### 10.3 MCP 规则

MCP Tools 是暴露给 Agent 层调用的工具能力。

每个 MCP Tool 必须具备：

- 工具名称
- 工具描述
- 输入 Schema
- 输出 Schema
- 权限要求
- 风险等级
- 超时时间
- 调用审计日志

MCP Tool 禁止：

1. 执行不受限制的原始 SQL。
2. 读取任意本地文件。
3. 读取 `.env`。
4. 读取密钥文件。
5. 绕过课程权限。
6. 返回真实服务器敏感路径。
7. 执行危险系统命令。

MCP 相关修改应优先参考：

- `.codebuddy/skills/mcp-tool-development-patterns/SKILL.md`

------

## 11. Prompt 与 AI 输出规则

Prompt 模板属于项目资产，不能随意散落在代码中。

修改 AI 行为时必须同步：

- `codebuddy-docs/specs/05_AI智能体行为定义.md`
- `codebuddy-docs/specs/06_提示词模板.md`

Prompt 编写必须遵守：

1. 明确角色。
2. 明确任务。
3. 明确上下文。
4. 明确输出格式。
5. 明确失败处理方式。
6. 明确安全边界。
7. 资料不足时不得编造。
8. 不得要求模型判断权限。
9. 不得在 Prompt 中写入真实密钥。
10. 必须防范 Prompt Injection。

结构化输出必须定义清楚字段、类型和枚举值。

------

## 12. 安全规则

安全规则必须严格执行。

禁止提交：

- `.env`
- `.env.*`
- `api-key.txt`
- 数据库密码
- JWT Secret
- 模型 API Key
- 私有 Token
- 本地凭据
- 生产日志
- 用户上传文件
- 向量数据库运行数据
- 本地虚拟环境目录
- `__pycache__`
- `.pytest_cache`
- `node_modules`

后端必须强制校验：

- 用户认证
- 用户授权
- 系统角色
- 课程成员身份
- 课程角色
- 数据归属
- 文件访问权限
- 工具调用权限

AI 安全必须包含：

- Prompt Injection 防护
- System Prompt 保护
- 密钥保护
- 权限感知工具调用
- 安全降级回答
- 执行审计日志

------

## 13. 当前已知重要风险

开发时必须注意以下风险。

### 13.1 P0 风险

1. 前端批量上传路径可能与后端接口不一致。
2. 任务生成字段可能存在 `extra_instructions` 与 `additional_instructions` 不一致。
3. 登录和刷新 Token 响应可能不一致。
4. 资源搜索路由可能被动态路由遮挡。
5. Agent 工具中的异步 retriever 调用必须正确 `await`。
6. LangGraph Workflow 中的 mock LLM 节点不能作为生产主链路。
7. 使用 `gen_random_uuid()` 的 Alembic migration 需要 PostgreSQL `pgcrypto` 扩展。
8. `Resource.uploaded_by` 模型与迁移中的 nullable 设置必须一致。

### 13.2 P1 风险

1. `qa_records` 需要一致的 conversation 支持。
2. Report workflow 不应使用硬编码日期。
3. 本地文件存储和 MinIO 策略需要统一。
4. Nginx `/files/` 代理路径必须与后端文件存储路径一致。
5. Excel 上传配置和解析能力必须一致。
6. 前端报告删除 UI 必须与后端 API 支持一致。
7. Admin 用户更新接口的请求体和后端参数处理必须一致。

新增功能前，不得扩大这些风险。

------

## 14. 常用命令

### 14.1 后端命令

```bash
cd backend
python -m venv venv
pip install -r requirements.txt
alembic upgrade head
pytest
uvicorn app.main:app --reload
```

### 14.2 前端命令

```bash
cd frontend
npm install
npm run dev
npm run build
```

### 14.3 Docker 命令

```bash
docker compose up -d
docker compose logs -f
docker compose down
```

### 14.4 数据库迁移命令

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

禁止在未确认的情况下执行破坏性命令。

例如：

```bash
rm -rf
docker compose down -v
drop database
truncate table
```

------

## 15. 测试与验证要求

### 15.1 修改后端后

需要验证：

- 后端测试是否通过
- 相关 API 是否可调用
- 参数校验是否正确
- 权限校验是否正确
- 错误响应是否符合规范
- 数据库读写是否正常

### 15.2 修改前端后

需要验证：

- 前端是否能构建
- 页面路由是否正确
- API 封装是否匹配后端
- TypeScript 类型是否正确
- loading / empty / error 状态是否完整
- 权限相关 UI 是否正确

### 15.3 修改数据库后

需要验证：

- Alembic migration 是否能执行
- Model 和 Migration 是否一致
- Schema 是否同步
- Service 是否同步
- API 文档是否同步
- 索引和外键是否合理

### 15.4 修改 AI / Agent 后

需要验证：

- Prompt 输出格式是否稳定
- RAG 是否返回正确 sources
- Agent 是否记录执行日志
- Skill 是否记录执行日志
- MCP Tool 是否记录调用日志
- 权限边界是否有效
- 失败时是否有降级响应

如果无法运行测试，必须说明原因，并给出手动验证步骤。

------

## 16. 文档同步规则

修改 API 时，同步：

- `codebuddy-docs/specs/04_API接口文档.md`
- 前端 API 封装
- 前端 TypeScript 类型

修改数据库模型时，同步：

- `codebuddy-docs/specs/03_数据模型与数据库设计.md`
- Alembic migration

修改前端页面或路由时，同步：

- `codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md`

修改 AI 行为时，同步：

- `codebuddy-docs/specs/05_AI智能体行为定义.md`
- `codebuddy-docs/specs/06_提示词模板.md`

修改开发任务时，同步：

- `codebuddy-docs/specs/08_CodeBuddy开发任务书.md`

修复审查报告中的问题时，同步：

- `codebuddy-docs/review/07_页面流程图审查报告.md`
- 相关规格文档或任务文档

------

## 17. CodeBuddy 输出要求

完成任务后，必须说明：

1. 修改了什么。
2. 修改了哪些文件。
3. 为什么这样修改。
4. 如何验证。
5. 哪些测试已运行。
6. 哪些测试无法运行。
7. 是否同步了文档。
8. 是否还有剩余风险。
9. 后续建议是什么。

不得声称未运行的测试已经通过。

不得隐藏失败、报错或不确定结果。

------

## 18. 最终开发原则

EduAgent 必须作为一个稳定、可维护、可审计的课程智能体平台进行开发。

开发优先级如下：

1. 正确性
2. 安全性
3. 权限控制
4. API 一致性
5. 数据库一致性
6. 前后端契约一致性
7. AI 输出安全
8. 执行过程可追踪
9. 文档一致性
10. 可测试性

所有开发都必须围绕这个目标进行。