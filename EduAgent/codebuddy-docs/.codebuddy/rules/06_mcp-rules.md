# 06_mcp-rules.md

## 1. 规则文件用途

本文件是 EduAgent 项目的 MCP 开发规则文件。

文件位置：

```text
.codebuddy/rules/06_mcp-rules.md
```

本文件用于约束 CodeBuddy 在 EduAgent 项目中进行以下任务时的行为：

1. 编写 `.mcp.json`。
2. 配置 CodeBuddy MCP Server。
3. 开发 EduAgent 后端 MCP Server。
4. 开发 MCP Client。
5. 开发 MCP Registry。
6. 开发 MCP Tool。
7. 开发 MCP Adapter。
8. 设计 MCP Tool 输入输出 Schema。
9. 设计 MCP Tool 权限控制。
10. 设计 MCP Tool 调用审计。
11. 将 MCP Tool 接入 Agent Orchestrator。
12. 将 MCP Tool 接入 Runtime Skills。
13. 将 MCP Tool 接入 LangGraph Workflow。
14. 开发管理员 MCP 管理页面相关后端接口。
15. 修复 MCP 权限、安全、超时、错误处理问题。

本文件不是完整 MCP 技术教程。完整设计应同时阅读：

```text
CODEBUDDY.md
.codebuddy/rules/01_project-overview.md
.codebuddy/rules/02_backend-rules.md
.codebuddy/rules/04_database-rules.md
.codebuddy/rules/05_ai-agent-rules.md
.codebuddy/rules/07_runtime-skills-rules.md
codebuddy-docs/specs/02_技术架构文档.md
codebuddy-docs/specs/03_数据模型与数据库设计.md
codebuddy-docs/specs/04_API接口文档.md
codebuddy-docs/specs/05_AI智能体行为定义.md
.codebuddy/skills/mcp-tool-development-patterns/SKILL.md
```

------

## 2. MCP 在 EduAgent 中的定位

MCP 是 EduAgent 智能体平台中的工具连接层。

在 EduAgent 中，MCP 不应被理解为简单的外部工具配置文件，而应被理解为：

```text
Agent 可调用工具的标准化接入层
```

EduAgent 中 MCP 的作用包括：

1. 向 Agent 暴露课程知识库检索工具。
2. 向 Agent 暴露课程资源查询工具。
3. 向 Agent 暴露资源分析工具。
4. 向 Agent 暴露任务生成辅助工具。
5. 向 Agent 暴露报告生成辅助工具。
6. 向 Agent 暴露代码辅导工具。
7. 向 Agent 暴露执行状态查询工具。
8. 向 CodeBuddy 暴露项目级辅助开发工具。
9. 统一工具输入输出 Schema。
10. 统一工具权限控制。
11. 统一工具调用审计。
12. 统一工具风险等级管理。

MCP 不能绕过 EduAgent 的后端权限系统。

MCP 不能替代 Service Layer。

MCP 不能让大模型直接访问数据库、文件系统、密钥或未授权课程数据。

------

## 3. MCP 与其他模块的关系

### 3.1 MCP 与 Agent 的关系

Agent 可以通过 Tool Router 选择 MCP Tool。

推荐链路：

```text
Agent Orchestrator
  ↓
Tool Router
  ↓
MCP Client
  ↓
MCP Server
  ↓
MCP Tool
  ↓
Permission Check
  ↓
Service Layer
  ↓
Database / Vector Store / File Storage
```

禁止链路：

```text
Agent
  ↓
MCP Tool
  ↓
Database
```

禁止 MCP Tool 直接绕过后端 Service 和权限校验访问数据库。

### 3.2 MCP 与 Runtime Skills 的关系

Runtime Skill 可以调用 MCP Tool，但必须通过统一 MCP Client。

推荐链路：

```text
Runtime Skill
  ↓
MCP Client
  ↓
MCP Tool
  ↓
Service Layer
  ↓
Result
```

Runtime Skill 不得直接调用外部工具绕过 MCP 审计。

### 3.3 MCP 与 LangGraph 的关系

LangGraph Workflow 可以在节点中调用 MCP Tool。

但 Workflow 不得直接访问 MCP Server，必须经过：

```text
Tool Router / MCP Client
```

这样才能统一：

1. 权限。
2. 超时。
3. 审计。
4. 错误处理。
5. 输出脱敏。
6. 风险控制。

### 3.4 MCP 与 RAG 的关系

课程知识库检索可以封装为 MCP Tool。

例如：

```text
search_course_knowledge
```

但该工具必须限定：

```text
course_id
user_id
resource scope
permission scope
```

不得允许跨课程检索。

### 3.5 MCP 与 CodeBuddy 本地配置的关系

`.mcp.json` 是 CodeBuddy 项目级 MCP 配置文件。

`backend/app/mcp/` 是 EduAgent 后端运行时代码目录。

两者不要混淆。

```text
.mcp.json
= CodeBuddy 用来连接 MCP Server 的配置文件

backend/app/mcp/
= EduAgent 后端中 MCP Client、Registry、Adapter、权限和审计代码
```

------

## 4. MCP 相关文件和目录

### 4.1 项目级 MCP 配置文件

项目根目录推荐放置：

```text
.mcp.json
```

用途：

1. 配置 CodeBuddy 可连接的 MCP Server。
2. 指定 MCP Server 类型。
3. 指定启动命令或 HTTP 地址。
4. 指定环境变量。
5. 指定描述信息。
6. 控制是否延迟加载。

`.mcp.json` 中不得写入真实密钥。

### 4.2 CodeBuddy 设置文件

项目级 CodeBuddy 设置文件：

```text
.codebuddy/settings.json
```

适合放：

1. 是否启用项目 MCP Server。
2. MCP Server allow / ask / deny 权限。
3. 工具权限。
4. 环境变量。
5. 安全限制。

### 4.3 后端 MCP 代码目录

推荐新增：

```text
backend/app/mcp/
├── __init__.py
├── client.py
├── registry.py
├── schemas.py
├── permissions.py
├── audit.py
├── errors.py
└── adapters/
    ├── internal_rag.py
    ├── course_db.py
    ├── file_resource.py
    ├── report_analysis.py
    ├── task_generation.py
    ├── code_sandbox.py
    └── agent_status.py
```

### 4.4 MCP API 目录

推荐后端 API：

```text
backend/app/api/v1/mcp.py
backend/app/api/v1/admin_mcp.py
```

或按现有项目路由结构组织。

管理员 MCP 管理接口推荐路径：

```text
/api/v1/admin/mcp/servers
/api/v1/admin/mcp/tools
/api/v1/admin/mcp/tool-calls
```

------

## 5. `.mcp.json` 编写规则

### 5.1 文件位置

CodeBuddy 项目级 MCP 配置文件应放在项目根目录：

```text
.mcp.json
```

不要放在：

```text
codebuddy-docs/.mcp.json
.codebuddy/.mcp.json
backend/.mcp.json
frontend/.mcp.json
```

除非工具有明确特殊要求。

### 5.2 基础结构

`.mcp.json` 应包含：

```jsonc
{
  "mcpServers": {
    "server-name": {
      "type": "stdio",
      "command": "python",
      "args": ["-m", "backend.app.mcp.server"],
      "env": {},
      "description": "MCP Server description",
      "defer_loading": true
    }
  }
}
```

### 5.3 Server 命名规则

MCP Server 名称应使用英文小写短横线命名：

```text
eduagent-local
eduagent-http
eduagent-rag
eduagent-tools
```

禁止使用：

```text
EduAgentServer
我的工具
server 1
test
```

### 5.4 传输类型

MCP Server 类型可包括：

```text
stdio
http
sse
```

本地开发阶段推荐：

```text
stdio
```

如果后端提供 HTTP MCP Server，可使用：

```text
http
```

### 5.5 环境变量规则

密钥必须通过环境变量引用。

推荐：

```jsonc
{
  "headers": {
    "Authorization": "Bearer ${EDUAGENT_API_TOKEN}"
  }
}
```

禁止：

```jsonc
{
  "headers": {
    "Authorization": "Bearer sk-real-secret-key"
  }
}
```

### 5.6 defer_loading 规则

如果 MCP Server 工具较多，应启用：

```jsonc
"defer_loading": true
```

这样可以减少上下文消耗，避免 CodeBuddy 一次性加载过多工具信息。

### 5.7 当前阶段建议

如果 EduAgent 后端尚未实现真实 MCP Server，则 `.mcp.json` 中应保留注释模板，不要启用不存在的 server。

不要配置无法启动的 MCP Server，避免 CodeBuddy 连接失败。

------

## 6. EduAgent 推荐 MCP Server

EduAgent 后续可提供以下 MCP Server。

### 6.1 eduagent-local

用途：

```text
本地 stdio MCP Server
```

适合开发环境。

建议命令：

```jsonc
{
  "type": "stdio",
  "command": "python",
  "args": ["-m", "backend.app.mcp.server"],
  "env": {
    "PYTHONPATH": "${PROJECT_ROOT:-.}",
    "EDUAGENT_ENV": "${EDUAGENT_ENV:-development}",
    "EDUAGENT_API_BASE_URL": "${EDUAGENT_API_BASE_URL:-http://localhost:8000}",
    "EDUAGENT_API_TOKEN": "${EDUAGENT_API_TOKEN}"
  },
  "description": "EduAgent 本地 MCP Server",
  "defer_loading": true
}
```

启用前必须确认：

```text
backend.app.mcp.server
```

已经真实存在。

### 6.2 eduagent-http

用途：

```text
通过 HTTP 调用 EduAgent 后端 MCP Server
```

适合后端提供 HTTP MCP Endpoint 的场景。

示例：

```jsonc
{
  "type": "http",
  "url": "${EDUAGENT_MCP_URL:-http://localhost:8000/mcp}",
  "headers": {
    "Authorization": "Bearer ${EDUAGENT_API_TOKEN}"
  },
  "description": "EduAgent HTTP MCP Server",
  "defer_loading": true
}
```

### 6.3 eduagent-rag

用途：

```text
只暴露课程知识库检索相关工具
```

适合低风险只读工具。

### 6.4 eduagent-admin

用途：

```text
暴露管理员级 MCP 工具
```

该 Server 默认不应启用。

只有管理员任务、明确授权和高安全配置下才能使用。

------

## 7. 推荐 MCP Tool 列表

EduAgent 推荐逐步实现以下 MCP Tool。

### 7.1 课程知识库检索工具

工具名：

```text
search_course_knowledge
```

用途：

```text
在指定课程范围内检索课程知识库。
```

输入：

```json
{
  "course_id": "uuid",
  "query": "用户问题",
  "top_k": 5
}
```

输出：

```json
{
  "results": [
    {
      "resource_id": "uuid",
      "resource_name": "chapter1.pdf",
      "chunk_id": "uuid",
      "page_number": 3,
      "score": 0.87,
      "excerpt": "..."
    }
  ]
}
```

风险等级：

```text
low
```

权限要求：

```text
当前用户必须是该课程成员。
```

### 7.2 课程资源列表工具

工具名：

```text
list_course_resources
```

用途：

```text
查询指定课程下的资源列表。
```

输入：

```json
{
  "course_id": "uuid",
  "status": "ready"
}
```

输出：

```json
{
  "items": [
    {
      "resource_id": "uuid",
      "filename": "chapter1.pdf",
      "status": "ready",
      "file_type": "pdf",
      "created_at": "datetime"
    }
  ]
}
```

风险等级：

```text
low
```

### 7.3 课程资源摘要工具

工具名：

```text
get_course_resource_summary
```

用途：

```text
获取课程资源的摘要信息。
```

输入：

```json
{
  "course_id": "uuid",
  "resource_id": "uuid"
}
```

输出：

```json
{
  "resource_id": "uuid",
  "summary": "...",
  "key_points": ["...", "..."],
  "status": "ready"
}
```

风险等级：

```text
low
```

### 7.4 资源分析工具

工具名：

```text
analyze_course_resource
```

用途：

```text
对课程资源进行知识点、难度、教学价值分析。
```

输入：

```json
{
  "course_id": "uuid",
  "resource_id": "uuid",
  "analysis_type": "summary"
}
```

输出：

```json
{
  "resource_id": "uuid",
  "summary": "...",
  "key_points": ["..."],
  "difficulty": "medium",
  "teaching_suggestions": ["..."]
}
```

风险等级：

```text
medium
```

权限要求：

```text
教师或管理员。
```

### 7.5 教学任务草稿生成工具

工具名：

```text
generate_course_task_draft
```

用途：

```text
基于课程资料生成教学任务草稿。
```

输入：

```json
{
  "course_id": "uuid",
  "task_type": "homework",
  "difficulty": "medium",
  "additional_instructions": "..."
}
```

输出：

```json
{
  "title": "...",
  "description": "...",
  "requirements": ["..."],
  "evaluation_criteria": ["..."]
}
```

风险等级：

```text
medium
```

权限要求：

```text
教师或管理员。
```

注意：

```text
该工具只生成草稿，不直接发布任务。
```

### 7.6 教学报告草稿生成工具

工具名：

```text
generate_teaching_report_draft
```

用途：

```text
基于课程资料、任务和问答记录生成教学报告草稿。
```

输入：

```json
{
  "course_id": "uuid",
  "report_type": "course_summary",
  "time_range": {
    "start": "datetime",
    "end": "datetime"
  }
}
```

输出：

```json
{
  "title": "...",
  "summary": "...",
  "key_findings": ["..."],
  "suggestions": ["..."]
}
```

风险等级：

```text
medium
```

权限要求：

```text
教师或管理员。
```

### 7.7 Agent 执行状态查询工具

工具名：

```text
get_agent_run_status
```

用途：

```text
查询 Agent 执行状态。
```

输入：

```json
{
  "agent_run_id": "uuid"
}
```

输出：

```json
{
  "agent_run_id": "uuid",
  "status": "running",
  "steps": [
    {
      "step_index": 1,
      "step_name": "retrieve_context",
      "status": "success"
    }
  ]
}
```

风险等级：

```text
low
```

### 7.8 课程成员角色查询工具

工具名：

```text
get_course_member_role
```

用途：

```text
查询当前用户在课程中的角色。
```

输入：

```json
{
  "course_id": "uuid",
  "user_id": "uuid"
}
```

输出：

```json
{
  "course_id": "uuid",
  "user_id": "uuid",
  "role": "teacher"
}
```

风险等级：

```text
low
```

注意：

```text
该工具只能查询当前用户自己或后端已授权范围内的角色信息。
```

------

## 8. 禁止实现的 MCP Tool

以下 MCP Tool 默认禁止实现或禁止启用。

### 8.1 任意 SQL 执行工具

禁止工具名：

```text
execute_sql
run_sql
query_database_raw
database_shell
```

原因：

```text
容易绕过权限和数据隔离。
```

如果确实需要数据库只读查询，应实现受控查询工具，而不是任意 SQL。

### 8.2 任意文件读取工具

禁止工具名：

```text
read_any_file
filesystem_read
read_env
read_secret_file
```

原因：

```text
可能读取 .env、api-key.txt、服务器敏感路径或用户隐私文件。
```

### 8.3 任意命令执行工具

禁止工具名：

```text
run_shell
execute_command
bash_exec
```

原因：

```text
可能执行危险系统命令。
```

### 8.4 直接删除数据工具

默认禁止：

```text
delete_course
delete_user
delete_resource
truncate_table
drop_database
```

如果后续需要删除能力，必须通过后端业务 API、权限校验、确认机制和审计记录实现，不得作为通用 MCP Tool 直接暴露给模型。

### 8.5 密钥读取工具

禁止：

```text
get_api_key
read_token
read_secret
get_env
```

MCP Tool 绝不能向模型返回密钥。

------

## 9. MCP Tool 设计规范

### 9.1 每个 Tool 必须定义

每个 MCP Tool 必须明确：

1. tool name。
2. display name。
3. description。
4. input schema。
5. output schema。
6. required permissions。
7. risk level。
8. timeout。
9. side effects。
10. audit fields。
11. error format。
12. examples。

### 9.2 Tool 命名规范

使用小写蛇形命名：

```text
search_course_knowledge
list_course_resources
analyze_course_resource
generate_course_task_draft
get_agent_run_status
```

禁止：

```text
SearchKnowledge
searchKnowledge
tool1
doSomething
```

### 9.3 输入 Schema 规则

输入 Schema 必须明确字段类型。

示例：

```json
{
  "type": "object",
  "properties": {
    "course_id": {
      "type": "string",
      "description": "课程 ID"
    },
    "query": {
      "type": "string",
      "description": "检索问题"
    },
    "top_k": {
      "type": "integer",
      "default": 5
    }
  },
  "required": ["course_id", "query"]
}
```

禁止使用无限制输入：

```json
{
  "input": "any"
}
```

### 9.4 输出 Schema 规则

输出 Schema 必须稳定。

不得同一个 Tool 在不同场景返回完全不同结构。

错误示例：

```json
{
  "result": "有时是字符串，有时是数组，有时是对象"
}
```

推荐：

```json
{
  "success": true,
  "data": {},
  "error": null
}
```

或业务明确的结构。

### 9.5 工具副作用声明

每个 Tool 必须声明是否有副作用。

副作用类型：

```text
none
read_only
generate_draft
write_database
modify_state
delete_data
external_request
```

默认应优先实现：

```text
read_only
generate_draft
```

不要把高风险写操作暴露给模型自动调用。

------

## 10. MCP 权限规则

### 10.1 权限必须后端校验

MCP Tool 权限必须由后端代码校验。

禁止：

```text
让大模型判断用户是否能调用工具。
```

正确流程：

```text
MCP Tool Request
  ↓
解析 user_id / course_id
  ↓
后端权限校验
  ↓
调用 Service
  ↓
返回结果
```

### 10.2 课程级工具权限

课程级工具必须校验：

1. 当前用户是否登录。
2. 当前用户是否 active。
3. 当前用户是否属于课程。
4. 当前用户课程角色。
5. Tool 是否允许该角色使用。
6. 数据是否属于当前 course_id。

### 10.3 管理员级工具权限

管理员级 Tool 必须校验：

```text
user.role == admin
```

管理员工具包括：

1. MCP Server 管理。
2. MCP Tool 管理。
3. 平台级 MCP Tool Call 查看。
4. 平台级 Agent Runs 查看。
5. Skills 管理。
6. 用户管理相关工具。

### 10.4 Tool 权限矩阵

推荐默认权限：

| Tool                           | 学生       | 教师       | 管理员 |
| ------------------------------ | ---------- | ---------- | ------ |
| search_course_knowledge        | 可，课程内 | 可，课程内 | 可     |
| list_course_resources          | 可，课程内 | 可，课程内 | 可     |
| get_course_resource_summary    | 可，课程内 | 可，课程内 | 可     |
| analyze_course_resource        | 不可       | 可，课程内 | 可     |
| generate_course_task_draft     | 不可       | 可，课程内 | 可     |
| generate_teaching_report_draft | 不可       | 可，课程内 | 可     |
| get_agent_run_status           | 受限       | 课程内可   | 可     |
| get_course_member_role         | 仅自己     | 课程内可   | 可     |
| manage_mcp_servers             | 不可       | 不可       | 可     |
| view_mcp_tool_calls            | 不可       | 课程内可   | 可     |

------

## 11. MCP 风险等级规则

每个 Tool 必须有风险等级。

推荐等级：

```text
low
medium
high
forbidden
```

### 11.1 low

说明：

```text
只读，无副作用，不暴露敏感数据。
```

示例：

1. search_course_knowledge。
2. list_course_resources。
3. get_agent_run_status。
4. get_course_resource_summary。

### 11.2 medium

说明：

```text
生成草稿、分析内容、调用模型，但不直接修改业务状态。
```

示例：

1. analyze_course_resource。
2. generate_course_task_draft。
3. generate_teaching_report_draft。
4. generate_lesson_plan_draft。

### 11.3 high

说明：

```text
会修改业务数据、改变状态、影响用户。
```

示例：

1. publish_task。
2. archive_task。
3. update_resource_metadata。
4. disable_skill。
5. enable_mcp_server。

高风险工具不得默认允许模型自动调用。

### 11.4 forbidden

说明：

```text
禁止通过 MCP 暴露。
```

示例：

1. execute_sql。
2. read_env。
3. delete_database。
4. run_shell。
5. read_secret_file。

------

## 12. MCP 审计规则

所有正式 MCP Tool 调用必须记录审计日志。

### 12.1 mcp_tool_calls 表

推荐表：

```text
mcp_tool_calls
```

推荐字段：

```text
id
server_id
server_name
tool_name
user_id
course_id
agent_run_id
skill_run_id
input_summary
output_summary
status
error_message
latency_ms
risk_level
created_at
started_at
finished_at
metadata
```

### 12.2 状态值

推荐状态：

```text
pending
running
success
failed
timeout
denied
cancelled
```

### 12.3 审计摘要规则

审计记录应保存摘要，不应保存完整敏感输入。

`input_summary` 应保存：

1. course_id。
2. tool_name。
3. query 摘要。
4. 资源 ID。
5. 风险等级。
6. 输入长度。

`output_summary` 应保存：

1. 返回结果数量。
2. 是否成功。
3. 输出摘要。
4. 错误类型。
5. 耗时。

### 12.4 不得保存

审计中不得保存：

1. API Key。
2. Bearer Token 原文。
3. Cookie 原文。
4. 数据库密码。
5. `.env` 内容。
6. 文件系统敏感路径。
7. 未脱敏完整 Prompt。
8. 未脱敏模型响应。
9. 未脱敏用户隐私。

------

## 13. MCP 错误处理规则

### 13.1 必须处理的错误

MCP Tool 必须处理：

1. 参数错误。
2. Schema 校验失败。
3. 未登录。
4. 无权限。
5. 课程不存在。
6. 用户不是课程成员。
7. 资源不存在。
8. RAG 检索失败。
9. LLM 调用失败。
10. MCP Server 不可用。
11. Tool 超时。
12. 外部服务异常。
13. 输出格式错误。

### 13.2 错误响应格式

推荐错误格式：

```json
{
  "success": false,
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "当前用户无权调用该工具。",
    "details": {}
  }
}
```

### 13.3 错误信息安全

不得返回：

1. Python traceback。
2. 数据库连接串。
3. API Key。
4. 服务器真实敏感路径。
5. `.env` 内容。
6. 未脱敏工具参数。
7. 内部系统 Prompt。

### 13.4 超时处理

所有 MCP Tool 必须设置超时。

推荐默认：

```text
5s - 30s
```

长任务不应直接阻塞 MCP Tool。

长任务应返回 task_id 或 agent_run_id，让前端或 Agent 查询状态。

------

## 14. MCP 与 Service Layer 规则

MCP Tool 不得直接替代 Service Layer。

### 14.1 正确做法

MCP Tool 应调用已有 Service：

```text
MCP Tool
  ↓
Permission Check
  ↓
CourseService / ResourceService / QAService / TaskService / ReportService
  ↓
Database / RAG / File Storage
```

### 14.2 错误做法

禁止：

```text
MCP Tool
  ↓
直接 db.execute
  ↓
直接返回数据库结果
```

除非是专门设计的、受控的只读内部查询，并且经过权限和审计处理。

### 14.3 好处

通过 Service Layer 可以保证：

1. 权限一致。
2. 业务规则一致。
3. 事务一致。
4. 错误处理一致。
5. 日志一致。
6. 审计一致。
7. API 和 MCP 行为一致。

------

## 15. MCP 与 RAG 工具规则

### 15.1 search_course_knowledge

这是 EduAgent 最重要的低风险 MCP Tool。

必须满足：

1. 输入必须包含 course_id。
2. 输入必须包含 query。
3. 后端根据当前用户校验课程权限。
4. 检索只在当前课程范围内执行。
5. 只检索 ready 状态资源。
6. 返回 sources。
7. 不编造结果。
8. 检索失败时返回稳定错误。

### 15.2 RAG Tool 输出

输出应包含：

```json
{
  "success": true,
  "results": [
    {
      "resource_id": "uuid",
      "resource_name": "xxx.pdf",
      "chunk_id": "uuid",
      "score": 0.82,
      "page_number": 3,
      "excerpt": "..."
    }
  ]
}
```

### 15.3 RAG Tool 禁止

禁止：

1. 跨课程检索。
2. 返回无权访问的资源。
3. 返回完整文档全文。
4. 返回未脱敏资料。
5. 编造 sources。
6. 无限制 top_k。
7. 返回超长内容撑爆上下文。

### 15.4 top_k 限制

推荐限制：

```text
1 <= top_k <= 20
```

默认：

```text
top_k = 5
```

------

## 16. MCP 与任务生成工具规则

### 16.1 generate_course_task_draft

该工具只生成草稿，不直接发布任务。

输入：

```json
{
  "course_id": "uuid",
  "task_type": "homework",
  "difficulty": "medium",
  "additional_instructions": "..."
}
```

输出：

```json
{
  "success": true,
  "draft": {
    "title": "...",
    "description": "...",
    "requirements": ["..."],
    "evaluation_criteria": ["..."]
  }
}
```

### 16.2 禁止直接发布

MCP Tool 不应自动执行：

```text
publish_task
```

除非：

1. 用户明确确认。
2. 后端权限校验通过。
3. 风险等级为 high。
4. 调用被记录。
5. 前端或后端有确认流程。

### 16.3 字段一致性

必须使用：

```text
additional_instructions
```

不得使用：

```text
extra_instructions
```

除非做兼容映射。

------

## 17. MCP 与报告生成工具规则

### 17.1 generate_teaching_report_draft

该工具生成报告草稿，不直接替换或发布正式报告。

必须注意：

1. 不得使用硬编码日期。
2. 必须基于明确的 course_id。
3. 必须校验教师或管理员权限。
4. 必须说明资料不足情况。
5. 输出结构稳定。
6. 调用过程审计。

### 17.2 报告输出建议

输出：

```json
{
  "success": true,
  "draft": {
    "title": "...",
    "summary": "...",
    "key_findings": ["..."],
    "teaching_suggestions": ["..."],
    "next_steps": ["..."]
  }
}
```

------

## 18. MCP 与代码沙箱规则

如果 EduAgent 后续提供代码辅导或代码运行能力，MCP 可接入代码沙箱。

但代码沙箱工具必须严格受限。

### 18.1 禁止默认启用

代码执行类 MCP Tool 默认不应启用。

例如：

```text
run_python_code
run_shell_command
execute_student_code
```

必须经过严格隔离后才能启用。

### 18.2 沙箱要求

代码沙箱必须满足：

1. 限制执行时间。
2. 限制内存。
3. 限制文件系统。
4. 禁止访问网络，除非明确允许。
5. 禁止访问 `.env`。
6. 禁止访问项目源代码敏感文件。
7. 捕获 stdout / stderr。
8. 不返回宿主机敏感路径。
9. 记录执行审计。

### 18.3 风险等级

代码执行类工具至少为：

```text
high
```

未隔离的代码执行工具应为：

```text
forbidden
```

------

## 19. `.codebuddy/settings.json` 中的 MCP 权限规则

MCP 工具权限更适合写在：

```text
.codebuddy/settings.json
```

推荐使用：

```json
{
  "enableAllProjectMcpServers": false,
  "enabledMcpjsonServers": [
    "eduagent-local"
  ],
  "permissions": {
    "allow": [
      "mcp__eduagent-local__search_course_knowledge",
      "mcp__eduagent-local__list_course_resources",
      "mcp__eduagent-local__get_course_resource_summary",
      "mcp__eduagent-local__get_agent_run_status"
    ],
    "ask": [
      "mcp__eduagent-local__analyze_course_resource",
      "mcp__eduagent-local__generate_course_task_draft",
      "mcp__eduagent-local__generate_teaching_report_draft"
    ],
    "deny": [
      "mcp__eduagent-local__execute_sql",
      "mcp__eduagent-local__read_env",
      "mcp__eduagent-local__run_shell",
      "mcp__eduagent-local__delete_course",
      "mcp__eduagent-local__delete_resource"
    ]
  }
}
```

### 19.1 默认不要启用所有 MCP Server

推荐：

```json
"enableAllProjectMcpServers": false
```

这样可以避免自动启用高风险工具。

### 19.2 allow / ask / deny 原则

推荐原则：

```text
低风险只读工具 → allow
中风险生成草稿工具 → ask
高风险写操作工具 → ask 或 deny
危险工具 → deny
```

------

## 20. MCP 管理接口规则

EduAgent 后端建议提供管理员 MCP 管理接口。

推荐路径：

```text
GET    /api/v1/admin/mcp/servers
POST   /api/v1/admin/mcp/servers
PATCH  /api/v1/admin/mcp/servers/{server_id}
GET    /api/v1/admin/mcp/tools
GET    /api/v1/admin/mcp/tool-calls
GET    /api/v1/admin/mcp/tool-calls/{call_id}
```

### 20.1 管理接口权限

所有 `/api/v1/admin/mcp/*` 接口必须要求管理员权限。

禁止学生或教师访问平台级 MCP 管理接口。

### 20.2 Tool Calls 查询

MCP Tool Calls 查询必须支持：

1. 分页。
2. 按 server_name 筛选。
3. 按 tool_name 筛选。
4. 按 status 筛选。
5. 按 course_id 筛选。
6. 按 user_id 筛选。
7. 按时间范围筛选。

### 20.3 Tool Calls 返回字段

返回字段应脱敏。

不得返回完整敏感输入。

------

## 21. 前端 MCP 页面规则

前端 MCP 管理页面主要面向管理员。

推荐页面：

```text
/admin/mcp
/admin/mcp/tool-calls
```

### 21.1 MCP Server 页面展示

应展示：

1. Server 名称。
2. Server 类型。
3. 描述。
4. 是否启用。
5. 风险等级。
6. Tool 数量。
7. 最后更新时间。

### 21.2 MCP Tool 页面展示

应展示：

1. Tool 名称。
2. Tool 描述。
3. 输入 Schema。
4. 输出 Schema。
5. 风险等级。
6. 权限要求。
7. 是否启用。

### 21.3 Tool Calls 页面展示

应展示：

1. 调用时间。
2. 用户。
3. 课程。
4. Server。
5. Tool。
6. 状态。
7. 耗时。
8. 输入摘要。
9. 输出摘要。
10. 错误信息。

不得展示：

1. API Key。
2. Token。
3. Cookie。
4. 密码。
5. `.env` 内容。
6. 未脱敏工具参数。

------

## 22. MCP 测试规则

### 22.1 配置测试

测试 `.mcp.json` 时应确认：

1. JSONC 格式有效。
2. Server 名称正确。
3. command 或 url 正确。
4. 环境变量名称正确。
5. 未写入真实密钥。
6. 不存在无法启动的已启用 server。

### 22.2 Tool Schema 测试

每个 Tool 应测试：

1. 缺少必填字段。
2. 字段类型错误。
3. 无效 course_id。
4. 无权限 user。
5. 正常输入。
6. 超长输入。
7. 输出结构。

### 22.3 权限测试

必须测试：

1. 学生能否调用课程内只读工具。
2. 学生是否被拒绝教师工具。
3. 教师是否只能访问自己课程。
4. 管理员是否可访问管理工具。
5. 未登录是否被拒绝。
6. 跨课程访问是否被拒绝。

### 22.4 审计测试

每次 Tool 调用后检查：

1. 是否写入 mcp_tool_calls。
2. status 是否正确。
3. latency_ms 是否记录。
4. error_message 是否记录。
5. 输入输出是否脱敏。
6. course_id 是否正确。
7. user_id 是否正确。

### 22.5 安全测试

必须测试：

1. 不能读取 `.env`。
2. 不能读取 `api-key.txt`。
3. 不能执行任意 SQL。
4. 不能执行 shell。
5. 不能跨课程检索。
6. 不能返回敏感路径。
7. 不能暴露系统 Prompt。

------

## 23. MCP 文档同步规则

修改 MCP 相关能力时必须同步文档。

### 23.1 修改 `.mcp.json`

同步：

```text
CODEBUDDY.md
.codebuddy/rules/06_mcp-rules.md
codebuddy-docs/00_环境配置说明.md
```

### 23.2 新增 MCP Tool

同步：

```text
codebuddy-docs/specs/04_API接口文档.md
codebuddy-docs/specs/05_AI智能体行为定义.md
codebuddy-docs/specs/03_数据模型与数据库设计.md
.codebuddy/skills/mcp-tool-development-patterns/SKILL.md
```

### 23.3 修改 MCP 数据表

同步：

```text
codebuddy-docs/specs/03_数据模型与数据库设计.md
backend/alembic/
backend/app/models/
backend/app/schemas/
```

### 23.4 修改 MCP 管理页面

同步：

```text
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
frontend/src/api/
frontend/src/types/
```

------

## 24. 当前项目 MCP 开发阶段建议

当前 EduAgent 项目如果尚未实现完整 MCP Server，应按阶段建设。

### 24.1 第一阶段：配置和规则

完成：

1. 新增 `.mcp.json`。
2. 新增 `.codebuddy/settings.json` MCP 权限配置。
3. 新增本规则文件。
4. 新增 MCP Skill 文档。
5. 不启用不存在的 server。

### 24.2 第二阶段：内部 MCP 结构

新增：

```text
backend/app/mcp/
```

并实现：

1. schemas.py。
2. permissions.py。
3. registry.py。
4. client.py。
5. audit.py。

### 24.3 第三阶段：低风险只读工具

优先实现：

1. search_course_knowledge。
2. list_course_resources。
3. get_course_resource_summary。
4. get_agent_run_status。

### 24.4 第四阶段：中风险生成草稿工具

再实现：

1. analyze_course_resource。
2. generate_course_task_draft。
3. generate_teaching_report_draft。
4. generate_lesson_plan_draft。

### 24.5 第五阶段：管理员管理能力

最后实现：

1. MCP Server 管理。
2. MCP Tool 管理。
3. MCP Tool Calls 审计页面。
4. MCP 风险等级配置。
5. MCP 启用禁用。

不要一开始就实现高风险写操作工具。

------

## 25. MCP 禁止事项清单

CodeBuddy 开发 MCP 功能时禁止：

1. 在 `.mcp.json` 中写真实密钥。
2. 在 `.mcp.json` 中启用不存在的 server。
3. 默认启用所有 MCP Server。
4. 暴露任意 SQL 执行工具。
5. 暴露任意文件读取工具。
6. 暴露任意 shell 执行工具。
7. 通过 MCP Tool 读取 `.env`。
8. 通过 MCP Tool 读取 `api-key.txt`。
9. MCP Tool 绕过 Service Layer。
10. MCP Tool 绕过课程权限。
11. MCP Tool 跨课程检索。
12. MCP Tool 返回未脱敏敏感内容。
13. MCP Tool 无输入 Schema。
14. MCP Tool 无输出 Schema。
15. MCP Tool 无超时控制。
16. MCP Tool 无调用审计。
17. MCP Tool 无错误处理。
18. MCP Tool 直接删除业务数据。
19. MCP Tool 直接发布任务。
20. MCP Tool 将工具原始错误直接返回前端。
21. 在审计表中保存明文 Token。
22. 在审计表中保存完整敏感工具输入。
23. 声称未测试的 MCP Tool 已经可用。
24. 把 MCP 当成绕过后端 API 的捷径。
25. 把 MCP Tool 当成普通函数随意调用而不记录审计。

------

## 26. MCP 开发任务执行流程

CodeBuddy 执行 MCP 任务时，应按以下流程：

```text
1. 阅读 CODEBUDDY.md
2. 阅读本规则文件
3. 阅读 05_AI智能体行为定义.md
4. 阅读 03_数据模型与数据库设计.md
5. 阅读 MCP Skill 文档
6. 判断任务是配置、Tool、Server、Client、权限、审计还是页面
7. 检查是否已有对应 Service
8. 设计输入 Schema
9. 设计输出 Schema
10. 设计权限规则
11. 设计风险等级
12. 设计审计字段
13. 实现最小可用能力
14. 增加错误处理和超时
15. 增加测试或说明验证方式
16. 同步相关文档
17. 输出修改说明和风险
```

------

## 27. 判断是否应该做成 MCP Tool

适合做成 MCP Tool 的能力：

1. Agent 需要调用。
2. Runtime Skill 需要复用。
3. 多个工作流都需要使用。
4. 能力有稳定输入输出。
5. 能力需要统一权限控制。
6. 能力需要统一审计。
7. 能力可能被外部工具复用。
8. 能力是只读或生成草稿型工具。

不适合做成 MCP Tool 的能力：

1. 普通前端页面 API。
2. 简单 CRUD 内部函数。
3. 未稳定的临时代码。
4. 高风险删除操作。
5. 任意 SQL。
6. 任意文件读取。
7. 任意命令执行。
8. 需要复杂人工确认的业务操作。

------

## 28. MCP 输出要求

完成 MCP 相关任务后，必须说明：

1. 是否修改 `.mcp.json`。
2. 是否修改 `.codebuddy/settings.json`。
3. 是否新增 MCP Server。
4. 是否新增 MCP Tool。
5. Tool 名称是什么。
6. Tool 输入 Schema 是什么。
7. Tool 输出 Schema 是什么。
8. Tool 风险等级是什么。
9. Tool 权限规则是什么。
10. Tool 是否有超时。
11. Tool 是否有审计。
12. 是否修改数据库表。
13. 是否新增 Alembic migration。
14. 是否影响 Agent。
15. 是否影响 Runtime Skill。
16. 是否影响前端页面。
17. 是否同步文档。
18. 是否运行测试。
19. 未运行测试的原因。
20. 剩余风险是什么。

不得只回答：

```text
MCP 已完成
```

必须给出可审查的修改说明。

------

## 29. 最终原则

EduAgent 的 MCP 能力必须保持：

```text
安全
受控
可审计
可复用
可扩展
可降级
可测试
```

所有 MCP 开发都必须优先保证：

1. 不泄露密钥。
2. 不绕过权限。
3. 不跨课程访问。
4. 不直接执行危险操作。
5. 不返回未脱敏数据。
6. 输入输出 Schema 稳定。
7. Tool 风险等级明确。
8. Tool 调用有审计。
9. Agent 调用可追踪。
10. Runtime Skill 调用可复用。
11. 管理员能查看调用记录。
12. 文档同步完整。

MCP 是 EduAgent 智能体平台的工具连接层，不是安全边界之外的快捷通道。