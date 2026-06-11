# 01_project-overview.md

## 1. 规则文件用途

本文件是 EduAgent 项目的 CodeBuddy 项目级规则文件。

文件位置：

```text
.codebuddy/rules/01_project-overview.md
```

本文件用于让 CodeBuddy 快速理解 EduAgent 项目的整体定位、技术边界、核心模块、目录结构、文档读取顺序和全局开发约束。

本文件不是完整需求文档，也不是完整技术架构文档。详细内容应阅读 `codebuddy-docs/` 下的相关文档。

本规则文件应在所有任务中生效，尤其适用于：

1. 第一次接手 EduAgent 项目。
2. 需要理解项目总体架构。
3. 需要判断某个修改是否符合项目定位。
4. 需要决定应该先阅读哪些文档。
5. 需要判断某个功能应该放到哪个模块。
6. 需要避免把 EduAgent 错误开发成普通 CRUD 系统或简单 RAG 聊天机器人。

------

## 2. 项目名称与核心定位

项目名称：

```text
EduAgent
```

项目全称：

```text
EduAgent 课程资源与教学任务智能体
```

项目核心定位：

```text
面向教学场景的课程智能体平台
```

EduAgent 不是简单的 RAG 聊天机器人，也不是普通的课程资源管理系统。

EduAgent 应被理解为：

```text
EduAgent
= 课程业务系统
+ RAG 知识库
+ MCP 工具生态
+ Skills 技能系统
+ Agent Orchestrator
+ Planner
+ Tool Router
+ Skill Router
+ LangGraph 工作流
+ 多智能体协作
+ 教学业务落库
+ 执行审计
```

CodeBuddy 在开发本项目时，必须始终把 EduAgent 当作“课程智能体平台”进行开发，而不是只开发成：

```text
课程资料上传系统
课程问答系统
普通 ChatBot
单一 RAG Demo
普通 CRUD 管理后台
```

------

## 3. 项目建设目标

EduAgent 的建设目标是构建一个可用于教学演示、课程项目实践和智能体开发训练的完整系统。

系统应支持教师、学生、管理员围绕课程资料完成以下工作：

1. 课程创建与管理。
2. 学生加入课程。
3. 课程资料上传。
4. 课程资料解析、切片、向量化。
5. 课程知识库构建。
6. 基于课程资料的智能问答。
7. 教学任务生成。
8. 教学报告生成。
9. 课程资源分析。
10. 代码辅导。
11. 教学设计。
12. 学习路径推荐。
13. MCP 工具调用。
14. Runtime Skills 复用。
15. Agent 执行过程审计。
16. 平台级能力管理和运维审计。

项目最终不是只完成“能问答”，而是要形成：

```text
课程数据
→ 课程知识库
→ 教学智能体
→ 教学任务
→ 教学报告
→ 学习路径
→ 执行审计
```

的完整教学智能体闭环。

------

## 4. 用户角色

EduAgent 至少包含以下角色：

| 角色   | 说明                   | 核心能力                                              |
| ------ | ---------------------- | ----------------------------------------------------- |
| 学生   | 课程学习者             | 加入课程、查看资源、课程问答、查看任务、获得学习建议  |
| 教师   | 课程建设者和教学管理者 | 创建课程、上传资料、生成任务、生成报告、分析课程资源  |
| 管理员 | 平台管理者             | 用户管理、系统设置、MCP 管理、Skills 管理、Agent 审计 |

开发时必须注意：

1. 学生不能管理课程核心配置。
2. 学生不能访问其他课程数据。
3. 教师只能管理自己有权限的课程。
4. 管理员拥有平台管理权限，但仍需遵守数据安全和审计要求。
5. 权限判断必须在后端完成，不能只依赖前端页面控制。
6. 大模型不能作为权限判断主体。

------

## 5. 核心业务闭环

EduAgent 的基础业务闭环是：

```text
教师创建课程
→ 学生加入课程
→ 教师上传课程资料
→ 系统解析课程资料
→ 系统构建课程知识库
→ 学生基于课程资料提问
→ AI 返回答案和引用来源
→ 教师生成教学任务
→ 教师发布任务
→ 学生查看任务
→ 教师生成教学报告
```

新版智能体平台闭环进一步扩展为：

```text
课程资料上传
→ ResourceAnalysisAgent 分析资源
→ Skills 提取知识点和资料缺口
→ CourseQAAgent 支持课程问答
→ TaskGenerationAgent 生成任务
→ LessonDesignAgent 生成教学设计
→ ReportGenerationAgent 生成教学报告
→ StudyPathAgent 推荐学习路径
→ MCP Tool 记录工具调用
→ Agent Runs 记录智能体执行过程
```

CodeBuddy 开发功能时，应优先判断当前修改属于哪个闭环节点。

不要孤立开发单个页面、单个接口或单个 Prompt，应保证它能接入完整业务链路。

------

## 6. 当前已具备的基础能力

当前 EduAgent 已具备以下基础能力。

### 6.1 用户认证

已具备：

1. 用户注册。
2. 用户登录。
3. JWT access token。
4. 当前用户信息获取。
5. 用户资料修改。
6. 学生、教师、管理员角色区分。

需要注意：

1. 登录接口与前端 Token 管理必须保持一致。
2. Refresh Token 相关链路需要与前端保持一致。
3. 服务端退出登录和 Token 黑名单能力需要进一步完善。

### 6.2 课程管理

已具备：

1. 教师创建课程。
2. 课程列表。
3. 课程详情。
4. 课程更新。
5. 课程删除。
6. 学生通过课程码加入课程。
7. 课程成员管理。
8. 学生退出课程。
9. 教师移除课程成员。

核心约束：

```text
所有课程内数据必须通过 course_id 隔离。
```

### 6.3 课程资源管理

已具备：

1. 单文件上传。
2. 批量文件上传。
3. 资源列表。
4. 资源详情。
5. 资源状态轮询。
6. 资源重新处理。
7. 资源删除。
8. 资源处理状态流转。

资源状态包括：

```text
uploading
parsing
chunking
embedding
ready
failed
```

需要注意：

1. 前后端批量上传接口路径必须一致。
2. 文件类型配置和实际解析器能力必须一致。
3. 本地文件存储、MinIO、Nginx 静态文件访问路径必须统一。

### 6.4 RAG 知识库

已具备或已有基础实现：

1. PDF 解析。
2. DOCX 解析。
3. PPTX 解析。
4. Markdown 解析。
5. TXT 解析。
6. 文本切片。
7. BGE-M3 Embedding。
8. ChromaDB 向量存储。
9. 检索器。
10. Reranker。
11. Query Rewriter。
12. Post Processor。
13. 降级策略。

需要注意：

1. RAG 必须限定 `course_id`。
2. RAG 不是只服务问答，也应服务任务生成、报告生成、资源分析、教学设计和学习路径。
3. RAG 输出应尽量提供 sources。
4. 资料不足时不得编造引用来源。

### 6.5 教学任务与报告

已具备或已有基础实现：

1. 教学任务生成。
2. 教学任务列表。
3. 教学任务详情。
4. 教学任务更新。
5. 教学任务重新生成。
6. 教学任务发布。
7. 教学任务归档。
8. 教学任务删除。
9. 教学报告生成。
10. 教学报告列表。
11. 教学报告详情。
12. 教学报告导出。

需要注意：

1. 任务生成字段名必须前后端一致。
2. 报告生成不能使用硬编码日期。
3. 前端删除 UI 必须与后端 API 能力一致。

### 6.6 Agent 原型能力

当前项目已有 `backend/app/agent/` 原型目录，包含：

1. executor。
2. state。
3. guardrails。
4. memory。
5. workflows。
6. tools。
7. prompts。

需要注意：

1. 当前 Agent workflow 中如果存在 mock LLM 节点，不得作为生产主链路。
2. Agent 不得绕过 Service 层。
3. Agent 执行必须记录过程。
4. Tool 调用必须有权限检查和审计。
5. 异步工具调用必须正确 `await`。

------

## 7. 后续需要建设的智能体平台能力

EduAgent 后续应补齐以下平台级能力。

### 7.1 Agent Orchestrator

Agent Orchestrator 负责智能体总调度，包括：

1. 接收用户任务。
2. 识别用户意图。
3. 调用 Planner 生成执行计划。
4. 调用 Skill Router 选择技能。
5. 调用 Tool Router 选择工具。
6. 编排 LangGraph Workflow。
7. 记录 Agent Run 和 Agent Step。
8. 处理执行失败和降级响应。

### 7.2 Runtime Skills

Runtime Skills 用于封装可复用的教学业务能力，例如：

1. course_qa。
2. resource_analysis。
3. task_generation。
4. report_generation。
5. code_explanation。
6. lesson_design。
7. quiz_generation。
8. study_path。

每个 Runtime Skill 必须具备：

1. 输入 Schema。
2. 输出 Schema。
3. 权限校验。
4. 执行日志。
5. 错误处理。
6. 可测试样例。

### 7.3 MCP 工具生态

MCP 工具用于向 Agent 暴露可调用工具能力，例如：

1. 课程知识库检索工具。
2. 课程资源查询工具。
3. 课程任务草稿生成工具。
4. 教学报告草稿生成工具。
5. 代码沙箱工具。
6. 资源分析工具。
7. Agent 执行状态查询工具。

所有 MCP Tool 必须满足：

1. 有工具名称。
2. 有工具描述。
3. 有输入 Schema。
4. 有输出 Schema。
5. 有权限要求。
6. 有风险等级。
7. 有超时控制。
8. 有调用审计日志。

### 7.4 LangGraph 工作流

LangGraph 用于编排复杂智能体流程，例如：

1. 课程问答流程。
2. 任务生成流程。
3. 报告生成流程。
4. 资源分析流程。
5. 教学设计流程。
6. 学习路径推荐流程。

LangGraph Workflow 不得绕过：

1. Service 层。
2. 权限检查。
3. 数据库事务。
4. 审计记录。
5. Prompt 安全边界。

------

## 8. 技术栈总览

### 8.1 后端技术栈

后端使用：

1. Python。
2. FastAPI。
3. SQLAlchemy Async。
4. Alembic。
5. PostgreSQL。
6. Redis。
7. Celery。
8. ChromaDB。
9. LangChain。
10. LangGraph。
11. httpx。
12. Pydantic。

不得随意替换后端框架、ORM、数据库或异步架构。

### 8.2 前端技术栈

前端使用：

1. Vue 3。
2. TypeScript。
3. Vue Router。
4. Pinia。
5. Tailwind CSS。
6. Axios。
7. marked。
8. DOMPurify。
9. lucide。

不得把前端重写为 React、Next.js、Angular 或其他框架。

### 8.3 AI 与智能体技术栈

AI 与智能体相关能力包括：

1. DeepSeek 兼容模式的大模型调用配置。
2. RAG 知识库。
3. BGE-M3 Embedding。
4. Reranker。
5. Agent Orchestrator。
6. Intent Router。
7. Planner。
8. Skill Router。
9. Tool Router。
10. MCP Tools。
11. Runtime Skills。
12. LangGraph Workflows。
13. Guardrails。
14. Agent / Skill / MCP 执行审计。

本项目课程和代码示例默认使用 DeepSeek 相关写法，不使用 OpenAI 作为默认供应商。

### 8.4 基础设施

项目基础设施包括：

1. Docker。
2. Docker Compose。
3. Nginx。
4. PostgreSQL。
5. Redis。
6. ChromaDB。
7. MinIO 或本地文件存储。

------

## 9. 推荐项目目录结构

EduAgent 推荐项目根目录结构如下：

```text
EduAgent/
├── CODEBUDDY.md
├── README.md
├── .env.example
├── .mcp.json
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx.conf
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── agent/
│   │   ├── core/
│   │   ├── models/
│   │   ├── rag/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tasks/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── dependencies.py
│   │   └── main.py
│   ├── alembic/
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── router/
│   │   ├── stores/
│   │   ├── types/
│   │   └── views/
│   └── package.json
│
├── codebuddy-docs/
│   ├── README.md
│   ├── overview.md
│   ├── 00_环境配置说明.md
│   ├── specs/
│   └── review/
│
└── .codebuddy/
    ├── settings.json
    ├── rules/
    └── skills/
```

如果 CodeBuddy 发现当前项目缺少 `.codebuddy/` 目录，不要删除重建项目，而应按需增量新增。

------

## 10. 推荐后续新增运行时代码目录

为了让 EduAgent 成为真正的课程智能体平台，后续建议新增以下后端运行时代码目录。

### 10.1 MCP 工具生态目录

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

用途：

1. 注册 MCP Server。
2. 管理 MCP Tool。
3. 调用内部或外部 MCP 工具。
4. 校验工具权限。
5. 记录 MCP Tool 调用。
6. 为 Agent 和 Skills 提供工具能力。

### 10.2 Skills 技能系统目录

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

用途：

1. 注册 Skill。
2. 执行 Skill。
3. 校验 Skill 输入输出。
4. 管理 Skill 权限。
5. 记录 Skill 执行日志。
6. 封装可复用教学能力。

### 10.3 Agent 编排扩展目录

当前已有：

```text
backend/app/agent/
```

后续需要增强为：

```text
backend/app/agent/
├── orchestrator.py
├── planner.py
├── intent_router.py
├── skill_router.py
├── tool_router.py
├── executor.py
├── state.py
├── memory.py
├── guardrails.py
├── workflows/
├── tools/
└── prompts/
```

用途：

1. 统一智能体入口。
2. 识别用户意图。
3. 生成执行计划。
4. 选择 Skill。
5. 选择 Tool。
6. 调用 LangGraph Workflow。
7. 记录执行过程。
8. 返回结构化结果。

------

## 11. 文档读取顺序

CodeBuddy 在执行任务前，应根据任务类型阅读对应文档。

### 11.1 第一次理解项目

阅读：

```text
CODEBUDDY.md
codebuddy-docs/README.md
codebuddy-docs/overview.md
codebuddy-docs/00_环境配置说明.md
```

### 11.2 需求和功能开发

阅读：

```text
codebuddy-docs/specs/01_项目需求规格文档.md
codebuddy-docs/specs/02_技术架构文档.md
```

### 11.3 数据库开发

阅读：

```text
codebuddy-docs/specs/03_数据模型与数据库设计.md
.codebuddy/skills/postgres-sqlalchemy-patterns/SKILL.md
```

### 11.4 API 开发

阅读：

```text
codebuddy-docs/specs/04_API接口文档.md
.codebuddy/skills/fastapi-async-patterns/SKILL.md
```

### 11.5 前端开发

阅读：

```text
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
.codebuddy/skills/vue3-tailwind-component-patterns/SKILL.md
```

### 11.6 AI / Agent 开发

阅读：

```text
codebuddy-docs/specs/05_AI智能体行为定义.md
codebuddy-docs/specs/06_提示词模板.md
.codebuddy/skills/rag-implementation-patterns/SKILL.md
.codebuddy/skills/langgraph-workflow-patterns/SKILL.md
.codebuddy/skills/mcp-tool-development-patterns/SKILL.md
.codebuddy/skills/runtime-skills-development-patterns/SKILL.md
```

### 11.7 问题修复

阅读：

```text
codebuddy-docs/review/07_页面流程图审查报告.md
codebuddy-docs/specs/08_CodeBuddy开发任务书.md
```

------

## 12. 全局开发禁止事项

CodeBuddy 不得执行以下行为：

1. 不得删除项目后重新创建。
2. 不得把现有项目当作空项目处理。
3. 不得随意替换技术栈。
4. 不得将前端从 Vue 改为 React。
5. 不得将后端从 FastAPI 改为其他框架。
6. 不得绕过 SQLAlchemy Async 改成同步数据库访问。
7. 不得绕过 Alembic 直接修改数据库结构。
8. 不得将真实密钥写入代码或文档。
9. 不得提交 `.env`、`api-key.txt`、本地日志、缓存、虚拟环境、用户上传文件。
10. 不得让大模型判断权限。
11. 不得让 Agent、MCP、Skill 绕过 Service 层。
12. 不得无依据编造 RAG 引用来源。
13. 不得开发一个无法测试、无法审计、无法维护的功能。
14. 不得只改后端不改前端契约。
15. 不得只改前端不确认后端 API。
16. 不得只改模型不生成数据库迁移。
17. 不得只改 Prompt 不同步提示词文档。

------

## 13. 全局开发优先级

EduAgent 的开发优先级如下：

1. 安全性。
2. 权限正确性。
3. 数据隔离。
4. API 一致性。
5. 数据库一致性。
6. 前后端契约一致性。
7. RAG 结果可追溯。
8. Agent 执行可审计。
9. Skills 输入输出稳定。
10. MCP 工具调用安全。
11. 页面交互完整。
12. 文档同步。
13. 测试可验证。
14. 用户体验优化。

当开发效率和安全性冲突时，优先安全性。

当模型生成便利性和权限边界冲突时，优先权限边界。

当功能扩展和当前系统稳定性冲突时，优先系统稳定性。

------

## 14. 已知高优先级风险

开发时必须注意以下已知风险。

### 14.1 P0 风险

1. 前端批量上传路径可能与后端接口不一致。
2. 任务生成字段名可能存在 `extra_instructions` 与 `additional_instructions` 不一致。
3. 登录和刷新 Token 响应可能不一致。
4. 资源搜索路由可能被动态路由遮挡。
5. Agent 工具中的异步 retriever 调用必须正确 `await`。
6. LangGraph Workflow 中的 mock LLM 节点不能作为生产主链路。
7. Alembic migration 使用 `gen_random_uuid()` 时需要 PostgreSQL `pgcrypto` 扩展。
8. `Resource.uploaded_by` 模型与 migration 的 nullable 设置必须一致。

### 14.2 P1 风险

1. `qa_records` 需要一致的 conversation 支持。
2. Report workflow 不应使用硬编码日期。
3. 本地文件存储和 MinIO 策略需要统一。
4. Nginx `/files/` 代理路径必须与后端文件存储路径一致。
5. Excel 上传配置和解析能力必须一致。
6. 前端报告删除 UI 必须与后端 API 支持一致。
7. Admin 用户更新接口的请求体和后端参数处理必须一致。

新增功能时，不得扩大这些风险。

修复功能时，应优先处理 P0 风险。

------

## 15. CodeBuddy 执行任务时的判断流程

CodeBuddy 接到任务后，应先判断任务类型。

### 15.1 如果是后端任务

检查：

1. 是否涉及 API。
2. 是否涉及 Service。
3. 是否涉及数据库。
4. 是否涉及权限。
5. 是否涉及 RAG、Agent、MCP 或 Skill。
6. 是否需要同步前端类型。
7. 是否需要同步 API 文档。

### 15.2 如果是前端任务

检查：

1. 是否已有对应后端 API。
2. API 字段是否一致。
3. 页面路由是否存在。
4. 权限显示是否正确。
5. 是否处理 loading / empty / error 状态。
6. 是否需要同步页面流程文档。

### 15.3 如果是数据库任务

检查：

1. SQLAlchemy Model 是否修改。
2. Alembic migration 是否生成。
3. Pydantic Schema 是否同步。
4. Service 是否同步。
5. API 文档是否同步。
6. 是否影响已有数据。

### 15.4 如果是 AI / Agent 任务

检查：

1. 是否涉及 Prompt。
2. 是否涉及 RAG。
3. 是否涉及 Agent Orchestrator。
4. 是否涉及 LangGraph Workflow。
5. 是否涉及 MCP Tool。
6. 是否涉及 Runtime Skill。
7. 是否有权限校验。
8. 是否有执行审计。
9. 是否有失败降级策略。

------

## 16. 输出要求

CodeBuddy 完成任何任务后，必须输出：

1. 修改了什么。
2. 修改了哪些文件。
3. 为什么这样修改。
4. 如何验证。
5. 哪些测试已运行。
6. 哪些测试无法运行。
7. 是否同步了相关文档。
8. 是否存在剩余风险。
9. 后续建议是什么。

不得声称未运行的测试已经通过。

不得隐藏失败、报错或不确定结果。

不得只输出“已完成”，必须说明具体修改内容和验证方式。

------

## 17. 与其他规则文件的关系

本文件只负责项目总览和全局规则。

其他规则文件负责更具体的开发约束：

```text
.codebuddy/rules/02_backend-rules.md
.codebuddy/rules/03_frontend-rules.md
.codebuddy/rules/04_database-rules.md
.codebuddy/rules/05_ai-agent-rules.md
.codebuddy/rules/06_mcp-rules.md
.codebuddy/rules/07_runtime-skills-rules.md
.codebuddy/rules/08_testing-rules.md
.codebuddy/rules/09_security-rules.md
```

如果某个任务已经有更具体的规则文件，应同时遵守本文件和具体规则文件。

发生冲突时，优先级如下：

```text
安全规则
> 权限规则
> 数据一致性规则
> API 契约规则
> 当前任务要求
> 通用风格建议
```

------

## 18. 最终原则

EduAgent 必须作为一个稳定、可维护、可审计、可扩展的课程智能体平台进行开发。

CodeBuddy 开发时必须坚持：

```text
不破坏现有系统
不绕过权限边界
不降低项目定位
不编造 AI 结果
不忽略文档同步
不跳过测试验证
```

所有新增能力都必须服务于 EduAgent 的核心目标：

```text
帮助教师和学生围绕课程资料完成可追踪、可复用、可审计的智能教学任务。
```