# EduAgent 课程智能体平台 — CodeBuddy 开发资料包

> 项目名称：EduAgent 课程资源与教学任务智能体
> 文档类型：CodeBuddy 开发资料包入口说明
> 适用对象：CodeBuddy / AI 编程助手 / 后端开发 / 前端开发 / Agent 开发 / MCP 开发 / Skills 开发 / 测试人员
> 文档版本：v2.0
> 优化日期：2026-06-10

------

## 1. 项目说明

EduAgent 是一个面向教学场景的 **课程智能体平台**。

它不是简单的 RAG 聊天机器人，也不是单纯的课程资料问答系统，而是一个围绕课程教学流程设计的智能体应用系统。

新版 EduAgent 的核心定位是：

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
+ 多智能体协作
+ 教学业务落库
+ 执行审计
```

系统目标是帮助教师和学生围绕课程资料完成：

1. 课程管理。
2. 课程资源上传。
3. 课程知识库构建。
4. 基于课程资料的智能问答。
5. 教学任务生成。
6. 教学报告生成。
7. 课程资源分析。
8. 代码辅导。
9. 教学设计。
10. 学习路径推荐。
11. MCP 工具调用。
12. Skills 技能复用。
13. Agent 执行审计。

------

## 2. CodeBuddy 使用本资料包的目的

本资料包用于指导 CodeBuddy 在已有 EduAgent 代码项目上进行：

```text
代码审查
→ 问题修复
→ 文档对齐
→ RAG 稳定化
→ Skills 框架建设
→ MCP 框架建设
→ Agent 编排建设
→ 多智能体能力扩展
→ 前端页面扩展
→ 测试与部署验收
```

CodeBuddy 必须注意：

```text
这是已有代码项目，不是空项目。
不得删除 backend、frontend、codebuddy-docs 后重新生成项目。
必须基于当前代码进行增量修复和扩展。
```

------

## 3. 当前项目主要目录

项目根目录建议结构如下：

```text
EduAgent/
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
│   ├── review/
│   └── skills/
│
├── docker-compose.yml
├── docker-compose.prod.yml
├── nginx.conf
└── .env.example
```

------

## 4. 后续需要新增的运行时代码目录

为了让 EduAgent 真正成为课程智能体平台，后续需要新增以下后端运行时代码目录。

### 4.1 MCP 工具生态目录

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

------

### 4.2 Skills 技能系统目录

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
5. 封装课程问答、资源分析、任务生成、报告生成、代码解释、教学设计、学习路径等能力。

------

### 4.3 Agent 编排扩展目录

当前已有：

```text
backend/app/agent/
```

后续需要增强：

```text
backend/app/agent/
├── orchestrator.py
├── planner.py
├── router.py
├── context.py
├── state.py
├── executor.py
├── guardrails.py
├── memory.py
├── tools/
├── workflows/
└── prompts/
```

用途：

1. Agent Orchestrator 统一调度。
2. Intent Router 识别意图。
3. Planner 拆解复杂教学任务。
4. Skill Router 选择技能。
5. Tool Router 选择工具。
6. Guardrails 执行安全检查。
7. AgentState 记录执行过程。

------

## 5. 文档目录说明

### 5.1 根目录文档

| 文档                 | 作用                                          |
| -------------------- | --------------------------------------------- |
| `README.md`          | 本文档，CodeBuddy 文档入口                    |
| `overview.md`        | 项目总体概览，说明项目定位和能力边界          |
| `00_环境配置说明.md` | 环境变量、模型配置、Docker 启动、本地启动说明 |

------

### 5.2 specs 规格文档

目录：

```text
codebuddy-docs/specs/
```

| 文档                         | 作用                                                         |
| ---------------------------- | ------------------------------------------------------------ |
| `01_项目需求规格文档.md`     | 定义业务需求、角色权限、MCP、Skills、多智能体需求            |
| `02_技术架构文档.md`         | 定义系统架构、RAG、MCP、Skills、Agent Orchestrator           |
| `03_数据模型与数据库设计.md` | 定义 PostgreSQL、ChromaDB、Agent / Skill / MCP 审计数据模型  |
| `04_API接口文档.md`          | 定义认证、课程、资源、问答、任务、报告、Skills、MCP、Agent API |
| `05_AI智能体行为定义.md`     | 定义多智能体、MCP、Skills、Planner、Router、Guardrails 行为  |
| `06_提示词模板.md`           | 定义 System Prompt、Intent、Planner、Skill、Tool、MCP、Guardrail Prompt |
| `07_页面流程图.md`           | 定义前端页面、路由、权限、智能体平台页面规划                 |
| `08_CodeBuddy开发任务书.md`  | 定义 CodeBuddy 修复和扩展项目的执行任务                      |

------

### 5.3 review 审查文档

目录：

```text
codebuddy-docs/review/
```

用途：

1. 存放代码审查报告。
2. 存放页面流程图审查报告。
3. 存放架构一致性审查报告。
4. 存放接口联调审查报告。
5. 存放后续 CodeBuddy 自动审查结果。

建议新增：

```text
代码基线审查报告.md
MCP与Skills架构审查报告.md
前后端接口一致性审查报告.md
Agent工作流审查报告.md
```

------

### 5.4 skills 开发规范文档

目录：

```text
codebuddy-docs/skills/
```

注意：

```text
codebuddy-docs/skills/ 是给 CodeBuddy 使用的开发规范 Skill。
backend/app/skills/ 是 EduAgent 运行时 Skill。
二者不是同一个概念。
```

当前已有开发规范 Skill：

| Skill 文档                                  | 作用                                   |
| ------------------------------------------- | -------------------------------------- |
| `fastapi-async-patterns/SKILL.md`           | FastAPI 异步接口开发规范               |
| `postgres-sqlalchemy-patterns/SKILL.md`     | PostgreSQL + SQLAlchemy 模型与查询规范 |
| `rag-implementation-patterns/SKILL.md`      | RAG 实现规范                           |
| `langgraph-workflow-patterns/SKILL.md`      | LangGraph 工作流开发规范               |
| `vue3-tailwind-component-patterns/SKILL.md` | Vue 3 + Tailwind 前端组件开发规范      |
| `docker-compose-dev-patterns/SKILL.md`      | Docker Compose 开发部署规范            |

后续建议新增 CodeBuddy 开发规范 Skill：

```text
mcp-tool-development-patterns/SKILL.md
runtime-skills-development-patterns/SKILL.md
agent-orchestrator-patterns/SKILL.md
agent-audit-logging-patterns/SKILL.md
```

------

## 6. 推荐阅读顺序

### 6.1 CodeBuddy 首次接手项目

推荐阅读顺序：

```text
1. README.md
2. overview.md
3. 08_CodeBuddy开发任务书.md
4. 01_项目需求规格文档.md
5. 02_技术架构文档.md
6. 04_API接口文档.md
7. 07_页面流程图.md
8. 03_数据模型与数据库设计.md
9. 05_AI智能体行为定义.md
10. 06_提示词模板.md
11. 00_环境配置说明.md
```

------

### 6.2 修复现有项目问题时

优先阅读：

```text
08_CodeBuddy开发任务书.md
04_API接口文档.md
03_数据模型与数据库设计.md
07_页面流程图.md
00_环境配置说明.md
```

重点处理：

1. 登录 `refresh_token`。
2. 批量上传路径。
3. 任务字段名称。
4. 资源搜索路由。
5. 数据库迁移。
6. 前端 API 封装。
7. Agent Tool 异步调用。

------

### 6.3 开发 RAG 功能时

优先阅读：

```text
02_技术架构文档.md
03_数据模型与数据库设计.md
04_API接口文档.md
05_AI智能体行为定义.md
06_提示词模板.md
skills/rag-implementation-patterns/SKILL.md
```

重点关注：

1. 文档解析。
2. 文本切片。
3. Embedding。
4. ChromaDB。
5. Retriever。
6. Reranker。
7. sources 格式。
8. 课程隔离。

------

### 6.4 开发 MCP 功能时

优先阅读：

```text
01_项目需求规格文档.md
02_技术架构文档.md
03_数据模型与数据库设计.md
04_API接口文档.md
05_AI智能体行为定义.md
06_提示词模板.md
08_CodeBuddy开发任务书.md
```

重点实现：

1. `backend/app/mcp/schemas.py`
2. `backend/app/mcp/registry.py`
3. `backend/app/mcp/client.py`
4. `backend/app/mcp/permissions.py`
5. `backend/app/mcp/adapters/internal_rag.py`
6. `backend/app/mcp/adapters/course_db.py`
7. `backend/app/mcp/adapters/file_resource.py`
8. `backend/app/mcp/adapters/report_analysis.py`
9. `mcp_servers`
10. `mcp_tool_calls`

------

### 6.5 开发 Skills 功能时

优先阅读：

```text
01_项目需求规格文档.md
02_技术架构文档.md
03_数据模型与数据库设计.md
04_API接口文档.md
05_AI智能体行为定义.md
06_提示词模板.md
08_CodeBuddy开发任务书.md
```

重点实现：

1. `backend/app/skills/base.py`
2. `backend/app/skills/schemas.py`
3. `backend/app/skills/registry.py`
4. `backend/app/skills/loader.py`
5. `backend/app/skills/executor.py`
6. `course_qa`
7. `resource_analysis`
8. `task_generation`
9. `report_generation`
10. `code_explanation`
11. `lesson_design`
12. `quiz_generation`
13. `study_path`
14. `skill_definitions`
15. `skill_runs`

------

### 6.6 开发 Agent 编排功能时

优先阅读：

```text
02_技术架构文档.md
05_AI智能体行为定义.md
06_提示词模板.md
08_CodeBuddy开发任务书.md
03_数据模型与数据库设计.md
04_API接口文档.md
```

重点实现：

1. `Agent Orchestrator`
2. `Intent Router`
3. `Planner`
4. `Skill Router`
5. `Tool Router`
6. `AgentState v2`
7. `Guardrails`
8. `AgentRun`
9. `AgentStep`
10. 多智能体工作流。

------

### 6.7 开发前端页面时

优先阅读：

```text
07_页面流程图.md
04_API接口文档.md
01_项目需求规格文档.md
08_CodeBuddy开发任务书.md
skills/vue3-tailwind-component-patterns/SKILL.md
```

重点实现：

1. 修复现有页面问题。
2. 新增智能体平台页面。
3. 新增 API 封装。
4. 新增 TypeScript 类型。
5. 新增路由和权限。
6. 保持 Markdown 安全渲染。
7. 不暴露敏感信息。

------

## 7. 当前项目已具备的主要功能

### 7.1 基础业务能力

当前项目已具备或已有代码基础：

1. 用户注册。
2. 用户登录。
3. 当前用户信息。
4. 课程创建。
5. 课程加入。
6. 课程成员管理。
7. 课程资源上传。
8. 资源异步处理。
9. RAG 知识库构建。
10. 非流式问答。
11. SSE 流式问答。
12. 问答历史。
13. 教学任务生成。
14. 教学任务发布和归档。
15. 教学报告生成。
16. 报告详情。
17. 报告 Markdown 导出。
18. 管理员用户管理。
19. 前端基础页面。
20. Docker Compose 编排。

------

### 7.2 AI 与 RAG 能力

当前已有或规划支持：

1. 文档解析。
2. 文本切片。
3. Embedding。
4. ChromaDB 向量检索。
5. Reranker 精排。
6. 查询改写。
7. 引用来源。
8. 检索失败降级。
9. DeepSeek / OpenAI-Compatible LLM 调用。
10. LangGraph 工作流原型。

------

### 7.3 智能体平台待补能力

当前还需要新增：

1. `backend/app/mcp/`。
2. `backend/app/skills/`。
3. Agent Orchestrator。
4. Intent Router。
5. Planner。
6. Skill Router。
7. Tool Router。
8. Skill Registry。
9. Skill Executor。
10. MCP Client。
11. MCP Registry。
12. MCP 权限检查。
13. MCP 调用审计。
14. Skill 执行审计。
15. Agent 执行审计。
16. 资源分析智能体。
17. 代码辅导智能体。
18. 教学设计智能体。
19. 学习路径智能体。
20. 前端智能体平台页面。

------

## 8. 当前优先修复问题

CodeBuddy 应优先修复以下 P0 问题。

| 编号  | 问题                                | 影响                          | 参考文档                                |
| ----- | ----------------------------------- | ----------------------------- | --------------------------------------- |
| P0-01 | 登录接口未返回 `refresh_token`      | 前端自动刷新不可用            | `04_API接口文档.md`                     |
| P0-02 | 批量上传路径不一致                  | 批量上传失败                  | `04_API接口文档.md`、`07_页面流程图.md` |
| P0-03 | 任务生成字段不一致                  | 额外要求无法传到后端          | `04_API接口文档.md`                     |
| P0-04 | 资源搜索路由顺序风险                | search 可能被当成 resource_id | `04_API接口文档.md`                     |
| P0-05 | `Resource.uploaded_by` 可空性不一致 | ORM 与迁移冲突                | `03_数据模型与数据库设计.md`            |
| P0-06 | `pgcrypto` 扩展缺失                 | 新库 UUID 生成可能失败        | `03_数据模型与数据库设计.md`            |
| P0-07 | Agent Tool 异步调用缺少 `await`     | Agent 检索不可用              | `05_AI智能体行为定义.md`                |
| P0-08 | Workflow LLM 节点仍是 Mock          | Agent 不能进入生产链路        | `05_AI智能体行为定义.md`                |
| P0-09 | 生产镜像 gunicorn 依赖风险          | 生产启动失败                  | `00_环境配置说明.md`                    |

------

## 9. 智能体平台扩展优先级

### 9.1 第一批：必须优先完成

```text
1. 修复现有 P0 问题
2. 稳定认证、课程、资源、问答、任务、报告主链路
3. 新增 Skills 基础框架
4. 新增 MCP 基础框架
5. 新增 Agent Orchestrator / Planner / Router
```

------

### 9.2 第二批：核心智能体能力

```text
1. CourseQAAgent
2. TaskGenerationAgent
3. ReportGenerationAgent
4. ResourceAnalysisAgent
```

------

### 9.3 第三批：扩展智能体能力

```text
1. CodeTutorAgent
2. LessonDesignAgent
3. StudyPathAgent
4. AdminAnalysisAgent
```

------

### 9.4 第四批：前端管理和审计页面

```text
1. CourseAnalysisView
2. CourseLessonDesignView
3. CourseStudyPathView
4. CourseSkillsView
5. CourseCodeTutorView
6. CourseAgentRunsView
7. AdminSkillsView
8. AdminMCPView
9. AdminAgentRunsView
```

------

## 10. 技术栈说明

### 10.1 后端技术栈

| 技术             | 作用                        |
| ---------------- | --------------------------- |
| FastAPI          | API 服务                    |
| SQLAlchemy Async | 异步 ORM                    |
| asyncpg          | PostgreSQL 异步驱动         |
| Alembic          | 数据库迁移                  |
| PostgreSQL       | 业务数据库                  |
| Redis            | 缓存、Celery Broker、Memory |
| Celery           | 异步任务                    |
| ChromaDB         | 向量数据库                  |
| LangChain        | RAG 基础能力                |
| LangGraph        | Agent 工作流                |
| Pydantic v2      | Schema 校验                 |
| httpx            | LLM API 调用                |

------

### 10.2 前端技术栈

| 技术            | 作用          |
| --------------- | ------------- |
| Vue 3           | 前端框架      |
| TypeScript      | 静态类型      |
| Vite            | 构建工具      |
| Vue Router      | 路由          |
| Pinia           | 状态管理      |
| Axios           | API 请求      |
| Tailwind CSS    | 样式          |
| marked          | Markdown 渲染 |
| DOMPurify       | XSS 清理      |
| lucide-vue-next | 图标          |

------

### 10.3 AI / Agent 技术栈

| 技术                             | 作用           |
| -------------------------------- | -------------- |
| DeepSeek / OpenAI-Compatible API | 主 LLM         |
| BGE-M3                           | Embedding      |
| BGE-Reranker-v2-m3               | Reranker       |
| RAG                              | 检索增强生成   |
| LangGraph                        | 工作流编排     |
| MCP                              | 工具生态接入   |
| Skills                           | 业务技能封装   |
| Guardrails                       | 输入输出安全   |
| AgentState                       | 智能体状态管理 |

------

## 11. CodeBuddy 开发规则

CodeBuddy 必须遵守以下规则。

### 11.1 项目规则

1. 不得删除项目重新生成。
2. 不得重建前后端项目结构。
3. 不得替换已确定技术栈。
4. 必须先阅读文档，再修改代码。
5. 必须以当前代码为事实来源。
6. 文档和代码冲突时，先指出冲突，再修复。
7. 修改代码后必须说明验证方式。

------

### 11.2 后端规则

1. API 层只负责请求接收和 Service 调用。
2. Service 层负责业务逻辑和数据库事务。
3. RAG 逻辑放在 `backend/app/rag/`。
4. Agent 逻辑放在 `backend/app/agent/`。
5. MCP 逻辑放在 `backend/app/mcp/`。
6. Skills 逻辑放在 `backend/app/skills/`。
7. 新增数据库字段必须写 Alembic 迁移。
8. 新增接口必须补 Pydantic Schema。
9. 所有课程内接口必须校验 `course_id`。
10. 所有教师接口必须校验教师或管理员权限。

------

### 11.3 前端规则

1. API 调用统一写入 `frontend/src/api/`。
2. 类型统一写入 `frontend/src/types/`。
3. 页面必须配置路由。
4. 路由必须配置权限。
5. 所有 AI Markdown 内容必须使用 `MarkdownRenderer`。
6. 所有删除操作必须二次确认。
7. 页面必须处理 loading、empty、error、normal 状态。
8. 不得在前端保存模型 API Key。
9. 不得在前端展示完整系统 Prompt。

------

### 11.4 Agent / MCP / Skills 规则

1. Agent 不得绕过 Service 层权限。
2. 权限必须由代码判断，不能交给 LLM。
3. MCP Tool 不得执行原始 SQL。
4. MCP Tool 不得跨课程访问。
5. MCP Tool 不得返回服务器真实路径。
6. Skill 必须有输入输出 Schema。
7. Skill 必须有 `SKILL.md`。
8. Skill 执行前必须校验权限。
9. AgentState 必须记录 `skill_calls` 和 `mcp_tool_calls`。
10. 生产链路不得使用 Mock LLM 节点。

------

## 12. 推荐开发路线

### 12.1 第一阶段：代码审查与基线确认

目标：

```text
确认当前项目能否安装、启动、迁移、运行。
```

输出：

```text
codebuddy-docs/review/代码基线审查报告.md
```

------

### 12.2 第二阶段：修复 P0 问题

目标：

```text
修复会导致现有核心功能不可用的问题。
```

重点：

1. 认证 Token。
2. 批量上传。
3. 任务字段。
4. 资源搜索。
5. 数据库迁移。
6. Agent Tool 异步。
7. 生产启动依赖。

------

### 12.3 第三阶段：稳定现有主链路

目标：

```text
用户、课程、资源、问答、任务、报告主流程稳定可用。
```

------

### 12.4 第四阶段：建设 Skills 基础框架

目标：

```text
实现 Skill Registry、Skill Executor 和核心内置 Skills。
```

优先 Skill：

```text
course_qa
task_generation
report_generation
resource_analysis
```

------

### 12.5 第五阶段：建设 MCP 基础框架

目标：

```text
实现 MCP Client、MCP Registry、MCP 权限和内部 MCP Tools。
```

优先 MCP Adapter：

```text
internal_rag
course_db
file_resource
report_analysis
```

------

### 12.6 第六阶段：建设 Agent Orchestrator

目标：

```text
实现 Intent Router、Planner、Skill Router、Tool Router 和 AgentState v2。
```

------

### 12.7 第七阶段：接入多智能体能力

目标：

```text
将 QA、任务、报告、资源分析等能力接入 Agent / Skills / MCP。
```

------

### 12.8 第八阶段：扩展前端页面

目标：

```text
新增课程资源分析、教学设计、学习路径、课程技能、MCP 管理、Agent 执行记录页面。
```

------

### 12.9 第九阶段：测试、部署与交付

目标：

```text
补充测试，清理敏感信息，完成 Docker 启动和文档同步。
```

------

## 13. 启动方式概览

详细启动方式见：

```text
00_环境配置说明.md
```

------

### 13.1 后端本地启动概览

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

Windows PowerShell 示例：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

------

### 13.2 前端本地启动概览

```bash
cd frontend
npm install
npm run dev
```

------

### 13.3 Docker Compose 启动概览

```bash
docker compose up -d
```

启动后常用地址：

| 服务          | 地址                                          |
| ------------- | --------------------------------------------- |
| 前端          | `http://localhost` 或 `http://localhost:5173` |
| 后端 API      | `http://localhost:8000`                       |
| API 文档      | `http://localhost:8000/docs`                  |
| ChromaDB      | `http://localhost:8001`                       |
| MinIO Console | `http://localhost:9001`                       |

------

## 14. 环境变量说明

详细环境变量见：

```text
00_环境配置说明.md
.env.example
```

新版智能体平台建议新增：

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

注意：

1. `.env` 不得提交。
2. `api-key.txt` 不得提交。
3. 真实密钥不得写入文档。
4. 前端不得保存模型 API Key。
5. 管理后台不得直接展示真实密钥。

------

## 15. 最小验收清单

### 15.1 基础业务验收

| 编号    | 验收项     | 通过标准                               |
| ------- | ---------- | -------------------------------------- |
| BASE-01 | 注册登录   | 学生和教师可注册登录                   |
| BASE-02 | Token 刷新 | 登录返回 refresh_token，前端可自动刷新 |
| BASE-03 | 课程管理   | 教师可创建课程，学生可加入课程         |
| BASE-04 | 资源上传   | 教师可上传课程资料                     |
| BASE-05 | 资源处理   | 资源最终变为 ready 或 failed           |
| BASE-06 | 智能问答   | 学生可基于资料问答                     |
| BASE-07 | 引用来源   | 问答返回 sources                       |
| BASE-08 | 任务生成   | 教师可生成任务草稿                     |
| BASE-09 | 报告生成   | 教师可生成报告                         |
| BASE-10 | 权限控制   | 学生不能访问教师和管理员能力           |

------

### 15.2 智能体平台验收

| 编号     | 验收项             | 通过标准                                |
| -------- | ------------------ | --------------------------------------- |
| AGENT-01 | Agent Orchestrator | 可统一调度 Intent、Planner、Skill、Tool |
| AGENT-02 | Intent Router      | 可识别主要教学意图                      |
| AGENT-03 | Planner            | 可拆解复杂教学任务                      |
| AGENT-04 | Skill Router       | 可选择正确 Skill                        |
| AGENT-05 | Tool Router        | 可选择 MCP / RAG / Local Tool           |
| AGENT-06 | AgentState         | 可记录执行过程                          |
| AGENT-07 | Agent Runs         | 可查询执行记录                          |
| AGENT-08 | Mock 清理          | 生产链路不使用 Mock LLM 节点            |

------

### 15.3 Skills 验收

| 编号     | 验收项            | 通过标准                   |
| -------- | ----------------- | -------------------------- |
| SKILL-01 | Skill Registry    | 可注册和列出内置 Skill     |
| SKILL-02 | Skill Executor    | 可执行授权 Skill           |
| SKILL-03 | course_qa         | 可基于课程资料问答         |
| SKILL-04 | resource_analysis | 可分析资源摘要和知识点     |
| SKILL-05 | task_generation   | 可生成教学任务             |
| SKILL-06 | report_generation | 可生成教学报告             |
| SKILL-07 | 权限控制          | 学生不能执行教师专属 Skill |

------

### 15.4 MCP 验收

| 编号   | 验收项         | 通过标准                       |
| ------ | -------------- | ------------------------------ |
| MCP-01 | MCP Registry   | 可注册和列出 MCP Server / Tool |
| MCP-02 | MCP Client     | 可调用内部 MCP Tool            |
| MCP-03 | RAG Tool       | 可检索课程知识库               |
| MCP-04 | Course DB Tool | 可查询课程统计                 |
| MCP-05 | File Tool      | 可分析当前课程资源             |
| MCP-06 | 权限控制       | MCP Tool 不越权                |
| MCP-07 | 调用记录       | MCP 调用可审计                 |

------

## 16. 常见错误提醒

### 16.1 不要把项目做成普通聊天机器人

错误方向：

```text
用户输入问题
→ 调用 LLM
→ 返回回答
```

正确方向：

```text
用户请求
→ Intent Router
→ Planner
→ Skill Router
→ Tool Router
→ MCP / RAG / Skills
→ LLM
→ Guardrails
→ Service 落库
→ 返回结果
```

------

### 16.2 不要混淆两类 Skills

```text
codebuddy-docs/skills/
= 给 CodeBuddy 使用的开发规范 Skill

backend/app/skills/
= EduAgent 运行时可调用的业务 Skill
```

------

### 16.3 不要让 LLM 判断权限

错误：

```text
把全部工具传给 LLM，让 LLM 判断能不能用。
```

正确：

```text
代码先根据 user_role、course_role、course_id 过滤可用 Tools 和 Skills。
LLM 只能在允许范围内选择。
```

------

### 16.4 不要让 MCP Tool 执行原始 SQL

MCP Tool 应提供受控业务工具，例如：

```text
get_course_stats
query_qa_records
search_course_knowledge
list_course_files
```

而不是：

```text
execute_sql
query_database_raw
```

------

### 16.5 不要让 Mock 工作流进入生产链路

当前 `backend/app/agent/workflows/` 中部分节点可能仍是 Mock。

CodeBuddy 必须确认：

1. Mock 不进入生产 API。
2. 主链路使用真实 Service。
3. 接入 Agent 时必须使用真实 LLM、真实 Skill、真实 Tool。
4. 返回的 ID 必须是真实数据库 ID。

------

## 17. 文档维护规则

CodeBuddy 修改代码后必须同步文档。

| 修改内容       | 必须同步文档                               |
| -------------- | ------------------------------------------ |
| 环境变量       | `00_环境配置说明.md`                       |
| 项目定位       | `overview.md`、`README.md`                 |
| 功能需求       | `01_项目需求规格文档.md`                   |
| 技术架构       | `02_技术架构文档.md`                       |
| 数据库字段     | `03_数据模型与数据库设计.md`               |
| API 路径或字段 | `04_API接口文档.md`                        |
| Agent 工作流   | `05_AI智能体行为定义.md`                   |
| Prompt         | `06_提示词模板.md`                         |
| 前端页面       | `07_页面流程图.md`                         |
| 开发任务       | `08_CodeBuddy开发任务书.md`                |
| Docker 部署    | `00_环境配置说明.md`、`02_技术架构文档.md` |

------

## 18. 给 CodeBuddy 的项目级执行提示词

可以将以下内容作为 CodeBuddy 项目级提示词：

```text
你正在维护 EduAgent 课程资源与教学任务智能体项目。

这是一个已有代码项目，不是空项目。你必须先读取现有代码，再根据 codebuddy-docs 中的文档进行修复、扩展和验收。

项目目标不是简单 RAG 聊天机器人，而是课程智能体平台：

EduAgent = 课程业务系统 + RAG 知识库 + MCP 工具生态 + Skills 技能系统 + Agent Orchestrator + Planner + Tool Router + Skill Router + 多智能体协作 + 教学业务落库 + 执行审计。

开发规则：

1. 不得删除现有 backend、frontend、codebuddy-docs 后重新生成项目。
2. 以当前代码为事实来源，文档与代码冲突时先指出冲突，再修复。
3. 后端使用 FastAPI + SQLAlchemy Async + PostgreSQL + Redis + Celery + ChromaDB。
4. 前端使用 Vue 3 + TypeScript + Pinia + Vue Router + Axios + Tailwind CSS。
5. AI 能力使用 RAG + LLM + LangGraph + MCP + Skills。
6. 不得写入真实 API Key、JWT Secret、数据库密码。
7. 修改 API 时必须同步前端 API、TypeScript 类型和 API 文档。
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

## 19. 本文档总结

本资料包的目标是让 CodeBuddy 明确：

```text
EduAgent 不是普通 RAG 聊天项目，
而是课程智能体平台项目。
```

当前项目已有：

```text
FastAPI 后端
Vue 3 前端
PostgreSQL
Redis
Celery
ChromaDB
RAG 主链路
课程管理
资源管理
智能问答
教学任务
教学报告
管理后台
Agent 原型
Docker Compose
```

后续重点是补齐：

```text
backend/app/skills/
backend/app/mcp/
Agent Orchestrator
Intent Router
Planner
Skill Router
Tool Router
Skill Registry
Skill Executor
MCP Client
MCP Registry
Agent / Skill / MCP 执行审计
资源分析智能体
代码辅导智能体
教学设计智能体
学习路径智能体
前端智能体平台页面
```

CodeBuddy 应遵循：

```text
先修复现有系统
再建设 Skills
再建设 MCP
再建设 Agent 编排
最后扩展多智能体和前端管理页面
```

完成这些工作后，EduAgent 才能真正成为一个可展示、可教学、可扩展、可落库、可审计的课程智能体平台。