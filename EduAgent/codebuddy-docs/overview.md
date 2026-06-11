# EduAgent 项目总体概览

> 项目名称：EduAgent 课程资源与教学任务智能体
> 文档类型：项目总体概览文档
> 适用对象：CodeBuddy / AI 编程助手 / 项目开发人员 / 教学项目负责人 / 测试人员
> 对应代码：`backend/`、`frontend/`、`codebuddy-docs/`
> 文档版本：v2.0
> 优化日期：2026-06-10

------

## 1. 项目一句话说明

EduAgent 是一个面向教学场景的 **课程智能体平台**，用于帮助教师和学生围绕课程资料完成知识问答、资源分析、教学任务生成、教学报告生成、代码辅导、教学设计、学习路径推荐等工作。

新版 EduAgent 不再只是一个简单的 RAG 聊天机器人，而是：

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
```

------

## 2. 项目定位升级

### 2.1 原始定位

项目早期更接近：

```text
课程管理系统
+ 课程资料上传
+ RAG 知识库问答
+ 教学任务生成
+ 教学报告生成
```

这种定位可以完成基础教学辅助，但智能体能力偏弱，整体更像：

```text
带课程知识库的 AI 聊天助手
```

------

### 2.2 新版定位

新版 EduAgent 的目标定位是：

```text
面向教学场景的课程智能体平台
```

它应具备以下特点：

1. 不只是回答问题，还能完成教学任务。
2. 不只是调用大模型，还能调用工具。
3. 不只是 RAG 检索，还能通过 MCP 扩展外部能力。
4. 不只是写 Prompt，而是通过 Skills 封装可复用教学能力。
5. 不只是单个 Agent，而是多个教学智能体协同。
6. 不只是生成内容，还要保存任务、报告、问答、执行记录。
7. 不只是演示功能，还要有权限控制、课程隔离、日志审计和测试验收。

------

## 3. 项目建设目标

EduAgent 的建设目标是构建一个可用于教学演示、课程项目实践和智能体开发训练的完整系统。

### 3.1 面向教师

系统应帮助教师完成：

1. 创建和管理课程。
2. 上传课程资料。
3. 分析课程资源内容和知识点。
4. 基于资料生成课堂练习。
5. 基于资料生成课后作业。
6. 基于资料生成实验指导。
7. 基于课程数据生成教学报告。
8. 基于课程主题生成教学设计。
9. 查看学生问答热点和学习问题。
10. 管理课程成员和课程设置。

------

### 3.2 面向学生

系统应帮助学生完成：

1. 加入课程。
2. 查看课程资料。
3. 基于课程资料进行智能问答。
4. 查看已发布教学任务。
5. 获得学习路径建议。
6. 对课程代码进行解释和理解。
7. 通过 AI 助教获得引导式学习帮助。

学生侧重点是：

```text
理解知识
+ 引导学习
+ 不直接代写作业
```

------

### 3.3 面向管理员

系统应帮助管理员完成：

1. 用户管理。
2. 系统设置查看。
3. MCP 工具管理。
4. Skills 能力管理。
5. Agent 执行记录查看。
6. 系统运行状态审计。

管理员侧重点是：

```text
平台配置
+ 能力管理
+ 安全审计
+ 运维监控
```

------

## 4. 核心业务闭环

EduAgent 的基础业务闭环如下：

```text
教师创建课程
→ 学生加入课程
→ 教师上传课程资料
→ 系统构建课程知识库
→ 学生基于资料提问
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

------

## 5. 当前项目已实现能力

当前项目已经具备以下基础能力。

### 5.1 用户认证

已实现：

1. 用户注册。
2. 用户登录。
3. JWT access token。
4. 当前用户信息获取。
5. 用户资料修改。
6. 学生、教师、管理员角色区分。

需要修复或完善：

1. 登录接口应返回 `refresh_token`。
2. 前端自动刷新 Token 链路需要与后端保持一致。
3. 服务端 Token 黑名单机制目前仍是预留能力。

------

### 5.2 课程管理

已实现：

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

------

### 5.3 课程资源管理

已实现：

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

需要修复或完善：

1. 前端批量上传路径应统一为 `/upload-batch`。
2. 配置中的 `xlsx` 支持与实际解析器需要统一。
3. MinIO 与本地文件存储策略需要进一步明确。

------

### 5.4 RAG 知识库

已实现：

1. PDF / DOCX / PPTX / Markdown / TXT 解析。
2. 文本切片。
3. BGE-M3 Embedding。
4. ChromaDB 向量写入。
5. PostgreSQL chunks 写入。
6. 向量检索。
7. MMR 选择。
8. Reranker 精排。
9. 检索失败降级。
10. 引用来源返回。

RAG 流程：

```text
课程资料
→ 文档解析
→ 文本切片
→ Embedding
→ ChromaDB
→ Retriever
→ Reranker
→ Prompt
→ LLM
→ Answer + Sources
```

需要修复或完善：

1. 查询改写函数签名和调用方式需要统一。
2. RAG Tool 应进一步封装为 Agent / Skill / MCP 可复用能力。
3. 引用来源格式需要在后端、前端、文档中统一。

------

### 5.5 智能问答

已实现：

1. 非流式问答。
2. SSE 流式问答。
3. 问答历史。
4. 问答详情。
5. 点赞 / 点踩反馈。
6. 清空对话上下文。
7. 回答引用来源。

SSE 事件包括：

```text
thinking
sources
token
done
error
```

需要修复或完善：

1. `qa_records` 需要补充 `conversation_id`。
2. 多轮对话记忆需要统一 Redis 与数据库。
3. 未来应改造为 `course_qa` Skill，由 CourseQAAgent 调用。

------

### 5.6 教学任务生成

已实现：

1. 教师输入主题。
2. 选择任务类型。
3. 选择难度。
4. 填写额外要求。
5. 基于课程资料检索。
6. 调用 LLM 生成 Markdown 任务。
7. 保存为 `draft`。
8. 支持发布、归档、重新生成、删除。

任务类型包括：

```text
class_exercise
homework
lab_guide
```

需要修复或完善：

1. 前端字段应统一为 `additional_instructions`。
2. 后续应改造为 `task_generation` Skill。
3. 测验题生成应扩展为独立 `quiz_generation` Skill。

------

### 5.7 教学报告生成

已实现：

1. 教师选择报告类型。
2. 选择开始日期和结束日期。
3. 统计课程数据。
4. 生成 Markdown 报告。
5. 保存报告记录。
6. 查看报告详情。
7. Markdown 导出。

报告类型包括：

```text
weekly
monthly
semester
```

需要修复或完善：

1. PDF 导出目前不是完整生产级能力。
2. 报告统计应严格使用真实数据。
3. 后续应改造为 `report_generation` Skill。
4. 报告分析能力可通过 Report Analysis MCP Tool 增强。

------

### 5.8 前端页面

当前已实现页面包括：

```text
登录页
注册页
首页
课程列表页
课程资源页
智能问答页
教学任务页
任务详情页
教学报告页
报告详情页
课程设置页
个人中心
用户管理页
系统设置页
404 页面
```

需要扩展页面包括：

```text
课程资源分析页
教学设计页
学习路径页
课程技能页
Skills 管理页
MCP 管理页
Agent 执行记录页
```

------

## 6. 新版智能体平台能力

新版 EduAgent 需要新增或完善以下智能体能力。

------

### 6.1 Agent Orchestrator

Agent Orchestrator 是智能体编排器，负责统一调度智能体能力。

职责：

1. 接收 Service 层请求。
2. 加载用户和课程上下文。
3. 执行输入护栏。
4. 调用 Intent Router。
5. 调用 Planner。
6. 调用 Skill Router。
7. 调用 Tool Router。
8. 执行 Skill 或 LangGraph Workflow。
9. 执行输出护栏。
10. 将结果交回 Service 层落库。

目标文件：

```text
backend/app/agent/orchestrator.py
```

------

### 6.2 Intent Router

Intent Router 用于识别用户意图。

支持意图：

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

目标文件：

```text
backend/app/agent/router.py
backend/app/agent/prompts/intent.py
```

------

### 6.3 Planner

Planner 用于拆解复杂教学任务。

示例：

用户请求：

```text
请根据 Python 函数课件，设计一节 45 分钟课程，并生成 5 道课堂练习。
```

Planner 应拆解为：

```text
分析课程资源
→ 生成教学设计
→ 生成课堂练习
→ 汇总最终结果
```

目标文件：

```text
backend/app/agent/planner.py
backend/app/agent/prompts/planner.py
```

------

### 6.4 Skill Router

Skill Router 用于根据用户意图选择合适 Skill。

例如：

| 意图                | Skill               |
| ------------------- | ------------------- |
| `course_qa`         | `course_qa`         |
| `resource_analysis` | `resource_analysis` |
| `task_generation`   | `task_generation`   |
| `quiz_generation`   | `quiz_generation`   |
| `report_generation` | `report_generation` |
| `code_explanation`  | `code_explanation`  |
| `lesson_design`     | `lesson_design`     |
| `study_path`        | `study_path`        |

目标文件：

```text
backend/app/agent/prompts/skill_router.py
```

------

### 6.5 Tool Router

Tool Router 用于选择 RAG Tool、Local Tool、MCP Tool。

例如：

| 需求         | 工具                                  |
| ------------ | ------------------------------------- |
| 检索课程资料 | `search_course_knowledge`             |
| 查询课程统计 | `get_course_stats`                    |
| 分析问答热点 | `analyze_qa_hotspots`                 |
| 分析资源文件 | `summarize_file`                      |
| 解释代码     | `explain_code`                        |
| 运行代码     | `run_python_code`，默认高风险，需沙箱 |

目标文件：

```text
backend/app/agent/prompts/tool_router.py
```

------

## 7. MCP 工具生态

### 7.1 MCP 定位

MCP 是 EduAgent 的工具生态接入层。

它用于将智能体连接到：

1. 课程数据库。
2. 课程文件系统。
3. RAG 检索系统。
4. 代码执行沙箱。
5. 报告分析工具。
6. 外部教学平台。
7. 外部知识库。
8. Web 搜索工具。

------

### 7.2 推荐新增目录

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

### 7.3 优先实现的内部 MCP 工具

| MCP Adapter          | 工具示例                              | 用途                       |
| -------------------- | ------------------------------------- | -------------------------- |
| `internal_rag.py`    | `search_course_knowledge`             | 检索课程知识库             |
| `course_db.py`       | `get_course_stats`                    | 安全查询课程统计           |
| `file_resource.py`   | `list_course_files`、`summarize_file` | 课程资源分析               |
| `report_analysis.py` | `analyze_qa_hotspots`                 | 教学报告分析               |
| `code_sandbox.py`    | `run_python_code`                     | 代码执行，默认关闭或沙箱化 |

------

### 7.4 MCP 安全要求

MCP Tool 必须遵守：

1. 不执行原始 SQL。
2. 不返回服务器真实文件路径。
3. 不跨课程访问数据。
4. 不泄露 API Key。
5. 不暴露内部异常堆栈。
6. 高风险工具默认关闭。
7. 所有工具调用必须有权限校验。
8. 所有工具调用必须可审计。

------

## 8. Skills 技能系统

### 8.1 Skills 定位

Skills 是 EduAgent 的可复用教学能力单元。

它用于封装复杂教学任务，例如：

```text
课程问答
资源分析
任务生成
报告生成
代码解释
教学设计
测验生成
学习路径推荐
```

------

### 8.2 推荐新增目录

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

### 8.3 推荐内置 Skills

| Skill               | 说明                               |
| ------------------- | ---------------------------------- |
| `course_qa`         | 基于课程资料进行问答               |
| `resource_analysis` | 分析课程资源摘要、知识点、缺失内容 |
| `task_generation`   | 生成课堂练习、课后作业、实验指导   |
| `report_generation` | 生成教学报告                       |
| `code_explanation`  | 解释代码、分析报错、生成学习建议   |
| `lesson_design`     | 生成教学设计、课堂活动和教学流程   |
| `quiz_generation`   | 生成测验题、选择题、简答题、编程题 |
| `study_path`        | 根据学生学习记录生成学习路径       |

------

### 8.4 每个 Skill 必须包含

```text
SKILL.md
skill.py
prompts.py
```

其中：

| 文件         | 作用                                     |
| ------------ | ---------------------------------------- |
| `SKILL.md`   | 描述技能用途、输入、输出、工具、安全限制 |
| `skill.py`   | 实现技能逻辑                             |
| `prompts.py` | 保存该技能专用 Prompt                    |

------

## 9. 多智能体设计

新版 EduAgent 应支持以下智能体。

| Agent                   | 中文名称           | 主要职责                         |
| ----------------------- | ------------------ | -------------------------------- |
| `CourseQAAgent`         | 课程问答智能体     | 基于课程资料回答学生问题         |
| `ResourceAnalysisAgent` | 课程资源分析智能体 | 分析课程资料摘要、知识点和缺口   |
| `TaskGenerationAgent`   | 教学任务生成智能体 | 生成课堂练习、课后作业、实验指导 |
| `ReportGenerationAgent` | 教学报告生成智能体 | 生成周报、月报、学期报告         |
| `CodeTutorAgent`        | 代码辅导智能体     | 解释代码、分析错误、生成示例     |
| `LessonDesignAgent`     | 教学设计智能体     | 生成教案和课堂活动               |
| `StudyPathAgent`        | 学习路径智能体     | 推荐学生学习路径                 |
| `AdminAnalysisAgent`    | 管理分析智能体     | 分析系统和用户数据               |
| `MCPToolAgent`          | MCP 工具智能体     | 发现、选择和调用 MCP 工具        |
| `SkillExecutionAgent`   | 技能执行智能体     | 选择并执行 Skills                |

------

## 10. 系统技术架构概览

### 10.1 后端架构

```text
FastAPI API
  ↓
Dependencies 权限校验
  ↓
Service 业务层
  ↓
Agent Orchestrator
  ↓
Intent Router / Planner / Skill Router / Tool Router
  ↓
Skills / MCP / RAG / LLM
  ↓
Service 落库
  ↓
PostgreSQL / Redis / ChromaDB / 文件存储
```

------

### 10.2 前端架构

```text
Vue 3 页面
  ↓
Vue Router 路由守卫
  ↓
Pinia 状态管理
  ↓
Axios API 封装
  ↓
FastAPI 后端
```

当前前端页面主要支撑基础业务，后续需要补充智能体平台页面。

------

### 10.3 RAG 架构

```text
文件上传
→ Celery 异步任务
→ 文档解析
→ 文本切片
→ Embedding
→ ChromaDB
→ Retriever
→ Reranker
→ Prompt
→ LLM
→ Answer + Sources
```

------

### 10.4 Agent 架构

```text
用户请求
→ 输入护栏
→ 意图识别
→ 任务规划
→ Skill 选择
→ Tool 选择
→ MCP / RAG / Local Tool
→ LLM 生成
→ 输出护栏
→ 结果落库
```

------

## 11. 当前项目实现边界

### 11.1 已经具备

当前项目已经具备：

1. FastAPI 后端框架。
2. Vue 3 前端框架。
3. PostgreSQL 业务数据库。
4. Redis。
5. Celery。
6. ChromaDB。
7. 课程资料上传和异步处理。
8. RAG 检索问答。
9. 任务生成。
10. 报告生成。
11. 管理后台基础页面。
12. Agent 目录原型。
13. LangGraph 工作流原型。
14. Docker Compose 编排。

------

### 11.2 尚未具备

当前项目尚未具备：

1. `backend/app/mcp/`。
2. `backend/app/skills/`。
3. Agent Orchestrator。
4. Intent Router。
5. Planner。
6. Skill Router。
7. Tool Router。
8. MCP Client。
9. MCP Registry。
10. MCP 权限层。
11. Skill Registry。
12. Skill Executor。
13. Skill 执行记录。
14. MCP 工具调用记录。
15. Agent 执行记录。
16. 资源分析智能体。
17. 代码辅导智能体。
18. 教学设计智能体。
19. 学习路径智能体。
20. 智能体相关前端管理页面。

------

## 12. 当前优先修复问题

在开发 MCP 和 Skills 之前，必须先修复当前 P0 问题。

| 优先级 | 问题                                | 影响                   |
| ------ | ----------------------------------- | ---------------------- |
| P0     | 登录接口未返回 `refresh_token`      | 前端刷新 Token 不完整  |
| P0     | 批量上传路径不一致                  | 批量上传失败           |
| P0     | 任务生成字段不一致                  | 额外要求无法传递       |
| P0     | 资源搜索路由顺序风险                | 搜索接口可能不可用     |
| P0     | Agent Tool 缺少 `await`             | Agent 检索不可用       |
| P0     | Workflow LLM 节点仍是 Mock          | Agent 不能进入生产链路 |
| P1     | `qa_records` 缺少 `conversation_id` | 多轮对话历史不完整     |
| P1     | Report Workflow 日期硬编码          | 报告周期错误           |
| P1     | MinIO 与本地存储不一致              | 文件访问策略不清晰     |
| P1     | xlsx 支持不完整                     | 上传 Excel 可能失败    |

------

## 13. 推荐开发路线

### 13.1 第一阶段：稳定现有主链路

先保证以下功能稳定：

```text
用户登录
课程管理
资源上传
资源处理
RAG 问答
任务生成
报告生成
前端联调
```

------

### 13.2 第二阶段：实现 Skills 基础框架

新增：

```text
backend/app/skills/base.py
backend/app/skills/schemas.py
backend/app/skills/registry.py
backend/app/skills/executor.py
```

优先实现：

```text
course_qa
task_generation
report_generation
resource_analysis
```

------

### 13.3 第三阶段：实现 MCP 基础框架

新增：

```text
backend/app/mcp/client.py
backend/app/mcp/registry.py
backend/app/mcp/schemas.py
backend/app/mcp/permissions.py
backend/app/mcp/adapters/
```

优先实现：

```text
internal_rag
course_db
file_resource
report_analysis
```

------

### 13.4 第四阶段：实现 Agent Orchestrator

新增：

```text
backend/app/agent/orchestrator.py
backend/app/agent/planner.py
backend/app/agent/router.py
backend/app/agent/context.py
```

------

### 13.5 第五阶段：扩展多智能体能力

按顺序扩展：

```text
CourseQAAgent
TaskGenerationAgent
ReportGenerationAgent
ResourceAnalysisAgent
CodeTutorAgent
LessonDesignAgent
StudyPathAgent
```

------

### 13.6 第六阶段：扩展前端页面

新增或预留：

```text
/courses/:courseId/analysis
/courses/:courseId/lesson-design
/courses/:courseId/study-path
/courses/:courseId/skills
/admin/skills
/admin/mcp
/admin/agent-runs
```

------

## 14. 主要文档关系

新版文档体系如下：

| 文档                         | 作用                                  |
| ---------------------------- | ------------------------------------- |
| `README.md`                  | 项目入口说明                          |
| `overview.md`                | 项目总体定位和能力总览                |
| `00_环境配置说明.md`         | 环境变量、启动方式和部署配置          |
| `01_项目需求规格文档.md`     | 功能需求和业务范围                    |
| `02_技术架构文档.md`         | 系统架构、MCP、Skills、Agent 设计     |
| `03_数据模型与数据库设计.md` | 数据库表、字段、关系和迁移            |
| `04_API接口文档.md`          | 后端 API 和前后端接口契约             |
| `05_AI智能体行为定义.md`     | Agent、MCP、Skills、多智能体行为      |
| `06_提示词模板.md`           | Prompt、Planner、Router、Skill Prompt |
| `07_页面流程图.md`           | 前端页面、路由和交互流程              |
| `08_CodeBuddy开发任务书.md`  | 代码修复和智能体平台开发任务          |

------

## 15. 项目验收视角

EduAgent 最终应从以下四个视角验收。

### 15.1 基础业务验收

1. 用户能注册登录。
2. 教师能创建课程。
3. 学生能加入课程。
4. 教师能上传课程资料。
5. 课程资料能成功处理。
6. 学生能基于资料问答。
7. 教师能生成任务。
8. 学生能查看已发布任务。
9. 教师能生成报告。
10. 管理员能管理用户。

------

### 15.2 RAG 能力验收

1. 文档能解析。
2. 文本能切片。
3. 向量能写入。
4. 检索能限定课程。
5. 回答能返回引用来源。
6. 资料不足时能明确说明。
7. Reranker 失败时能降级。
8. ChromaDB 失败时有兜底策略。

------

### 15.3 智能体平台验收

1. Agent Orchestrator 可运行。
2. Intent Router 能识别教学意图。
3. Planner 能拆解复杂任务。
4. Skill Router 能选择技能。
5. Tool Router 能选择工具。
6. Skills 可注册、可执行、可测试。
7. MCP Tool 可注册、可调用、可审计。
8. AgentState 能记录执行过程。
9. 多 Agent 能协同完成教学任务。
10. 生产链路不使用 Mock LLM 节点。

------

### 15.4 安全验收

1. 未登录访问返回 401。
2. 无权限访问返回 403。
3. 非课程成员不能访问课程数据。
4. 学生不能访问教师或管理员能力。
5. MCP Tool 不能越权。
6. Skill 不能绕过权限。
7. Markdown 渲染经过 DOMPurify。
8. 交付包不包含 `.env` 和真实密钥。
9. 日志不输出敏感信息。
10. Prompt Injection 能被拦截。

------

## 16. 本文档总结

EduAgent 的新版项目目标是从：

```text
课程 RAG 问答系统
```

升级为：

```text
课程智能体平台
```

这个平台应包含：

```text
课程业务系统
+ RAG 知识库
+ MCP 工具生态
+ Skills 技能系统
+ Agent Orchestrator
+ Planner
+ Tool Router
+ Skill Router
+ 多智能体协作
+ 教学业务落库
+ 权限护栏
+ 执行审计
```

当前项目已经具备基础课程系统、RAG 主链路、问答、任务、报告和前端页面，但还需要继续补齐：

```text
backend/app/mcp/
backend/app/skills/
Agent Orchestrator
Planner
Router
Skill Registry
Skill Executor
MCP Client
MCP Registry
Agent / Skill / MCP 执行记录
资源分析智能体
代码辅导智能体
教学设计智能体
学习路径智能体
```

后续开发必须遵循：

```text
先稳定现有业务
再建设 Skills
再建设 MCP
再建设 Agent Orchestrator
最后扩展多智能体和前端页面
```

只有完成以上升级，EduAgent 才能真正体现“智能体开发课程项目”的完整价值，而不是停留在普通 RAG 聊天系统。