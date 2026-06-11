# 04_database-rules.md

## 1. 规则文件用途

本文件是 EduAgent 项目的数据库开发规则文件。

文件位置：

```text
.codebuddy/rules/04_database-rules.md
```

本文件用于约束 CodeBuddy 在 EduAgent 项目中进行数据库模型设计、SQLAlchemy Async Model 编写、Alembic 迁移、字段调整、索引设计、外键设计、审计表设计、RAG 元数据设计、Agent / Skill / MCP 执行记录设计时的行为。

本文件不是完整数据库设计文档。完整数据库设计应同时阅读：

```text
CODEBUDDY.md
.codebuddy/rules/01_project-overview.md
.codebuddy/rules/02_backend-rules.md
codebuddy-docs/specs/03_数据模型与数据库设计.md
codebuddy-docs/specs/04_API接口文档.md
.codebuddy/skills/postgres-sqlalchemy-patterns/SKILL.md
```

------

## 2. 数据库总体定位

EduAgent 的数据库不是普通业务表集合。

EduAgent 数据库需要同时支撑：

1. 用户认证。
2. 用户角色。
3. 课程管理。
4. 课程成员关系。
5. 课程资源管理。
6. 文档解析状态。
7. 文档切片元数据。
8. RAG 检索关联。
9. 问答记录。
10. 教学任务。
11. 教学报告。
12. Agent 执行记录。
13. Agent Step 记录。
14. Runtime Skill 定义。
15. Runtime Skill 执行记录。
16. MCP Server 管理。
17. MCP Tool 调用记录。
18. 平台审计。
19. 权限隔离。
20. 后续智能体能力扩展。

CodeBuddy 在设计数据库时，必须始终把数据库理解为：

```text
业务数据存储
+ RAG 元数据存储
+ 智能体执行审计存储
+ 工具调用审计存储
+ 权限边界数据基础
```

不得只把数据库设计成普通 CRUD 表。

------

## 3. 数据库技术栈约束

EduAgent 数据库相关开发必须使用：

```text
PostgreSQL
SQLAlchemy Async
Alembic
UUID 主键
Pydantic Schema
AsyncSession
```

禁止随意替换为：

1. SQLite，除非是单元测试临时数据库。
2. MySQL。
3. MongoDB。
4. 纯 JSON 文件。
5. 同步 SQLAlchemy Session。
6. 手写无迁移 SQL 直接改库。
7. 临时内存存储替代正式数据表。

如果确实需要引入其他存储，例如 Elasticsearch、MinIO、对象存储、向量数据库，应作为辅助存储，不能替代 PostgreSQL 中的核心业务数据和审计数据。

------

## 4. 数据库设计总原则

### 4.1 一致性原则

数据库结构必须与以下内容保持一致：

1. SQLAlchemy Models。
2. Alembic Migrations。
3. Pydantic Schemas。
4. Service 层读写逻辑。
5. API 文档。
6. 前端 TypeScript Types。
7. 页面展示字段。
8. 测试数据。

禁止只修改 Model 而不修改 Migration。

禁止只修改数据库字段而不修改 Schema。

禁止只修改后端字段而不同步前端类型。

### 4.2 课程隔离原则

所有课程内数据都必须能够通过 `course_id` 进行隔离。

课程内数据包括：

1. 课程资源。
2. 文档切片。
3. 问答记录。
4. 教学任务。
5. 教学报告。
6. 资源分析结果。
7. 教学设计结果。
8. 学习路径结果。
9. Agent 执行记录。
10. Skill 执行记录。
11. MCP Tool 调用记录。

如果某张表保存的是课程级业务数据，通常必须包含：

```text
course_id
```

如果确实不包含 `course_id`，必须说明原因，并通过其他外键间接保证课程隔离。

### 4.3 审计优先原则

Agent、Skill、MCP 等智能体相关能力必须可审计。

以下行为必须有数据库记录：

1. Agent 执行。
2. Agent Step 执行。
3. Runtime Skill 执行。
4. MCP Tool 调用。
5. 重要 AI 生成任务。
6. 资源解析失败。
7. RAG 检索异常。
8. 权限拒绝，视具体需求决定是否落库。
9. 管理员关键操作。

审计数据应记录摘要，不应无节制保存敏感信息或超长内容。

### 4.4 最小必要数据原则

数据库不应保存不必要的敏感数据。

禁止保存：

1. 明文密码。
2. 明文 Token。
3. 明文 API Key。
4. JWT Secret。
5. 数据库密码。
6. 模型供应商密钥。
7. 未脱敏的系统 Prompt。
8. 未脱敏的完整工具参数。
9. 用户无权访问的跨课程数据副本。

------

## 5. 命名规范

### 5.1 表名规范

表名使用小写蛇形命名法：

```text
users
courses
course_members
resources
chunks
qa_records
tasks
reports
agent_runs
agent_steps
skill_definitions
skill_runs
mcp_servers
mcp_tool_calls
```

禁止使用：

```text
User
CourseMember
courseMember
tbl_user
T_USER
```

### 5.2 字段名规范

字段名使用小写蛇形命名法：

```text
id
user_id
course_id
resource_id
created_at
updated_at
deleted_at
status
metadata
error_message
```

禁止混用：

```text
userId
courseID
createdAt
updatedAt
```

### 5.3 外键字段命名

外键字段统一使用：

```text
<entity>_id
```

示例：

```text
user_id
course_id
resource_id
task_id
report_id
agent_run_id
skill_run_id
mcp_server_id
```

### 5.4 时间字段命名

推荐统一使用：

```text
created_at
updated_at
deleted_at
started_at
finished_at
last_login_at
```

不要混用：

```text
create_time
createdTime
updateDate
```

------

## 6. 主键与 UUID 规则

### 6.1 主键规则

主要业务表推荐使用 UUID 主键：

```text
id UUID PRIMARY KEY
```

适用表：

1. users。
2. courses。
3. resources。
4. chunks。
5. qa_records。
6. tasks。
7. reports。
8. agent_runs。
9. agent_steps。
10. skill_definitions。
11. skill_runs。
12. mcp_servers。
13. mcp_tool_calls。

### 6.2 UUID 默认值规则

如果 PostgreSQL 使用：

```sql
gen_random_uuid()
```

Alembic migration 必须确保启用：

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

当前项目中凡是 migration 使用 `gen_random_uuid()` 的地方，都必须检查 `pgcrypto` 扩展是否存在。

### 6.3 Python 侧 UUID

SQLAlchemy Model 中 UUID 字段应保持一致。

示例：

```python
id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
```

如果数据库层使用 server default，也应确保 migration 和 Model 不冲突。

------

## 7. 时间字段规则

### 7.1 基础时间字段

主要业务表推荐包含：

```text
created_at
updated_at
```

如果支持软删除，增加：

```text
deleted_at
```

### 7.2 执行类时间字段

执行类表推荐包含：

```text
created_at
started_at
finished_at
latency_ms
```

适用表：

1. agent_runs。
2. agent_steps。
3. skill_runs。
4. mcp_tool_calls。
5. 异步任务执行记录。

### 7.3 时区规则

后端应统一使用 UTC 或项目明确配置的时间策略。

数据库时间字段应避免混用本地时间和 UTC 时间。

前端展示时再转换为用户可读时间。

------

## 8. 用户与认证数据规则

### 8.1 users 表

`users` 表应保存用户基础信息。

推荐字段：

```text
id
username
email
password_hash
full_name
role
is_active
is_superuser
last_login_at
created_at
updated_at
```

### 8.2 密码字段规则

禁止保存：

```text
password
plain_password
raw_password
```

必须保存哈希结果，例如：

```text
password_hash
```

### 8.3 用户角色

用户角色可包含：

```text
student
teacher
admin
```

角色值必须与后端 Enum、前端 TypeScript 类型、API 文档保持一致。

### 8.4 Token 数据

默认不建议把 access token 明文保存到数据库。

如果实现 refresh token 或 token blacklist，应设计专门表，例如：

```text
refresh_tokens
token_blacklist
```

并且保存哈希或摘要，而不是明文 Token。

------

## 9. 课程与成员关系规则

### 9.1 courses 表

`courses` 表用于保存课程基础信息。

推荐字段：

```text
id
name
description
course_code
owner_id
status
created_at
updated_at
deleted_at
```

### 9.2 course_members 表

`course_members` 表用于保存用户与课程关系。

推荐字段：

```text
id
course_id
user_id
role
joined_at
created_at
updated_at
```

### 9.3 唯一约束

应保证同一个用户不能重复加入同一课程：

```text
unique(course_id, user_id)
```

课程码应唯一：

```text
unique(course_code)
```

### 9.4 课程权限基础

课程权限判断必须基于：

1. users.role。
2. courses.owner_id。
3. course_members.user_id。
4. course_members.course_id。
5. course_members.role。

不得只依赖前端传来的角色字段。

------

## 10. 课程资源表规则

### 10.1 resources 表

`resources` 表用于保存课程资料的元数据。

推荐字段：

```text
id
course_id
uploaded_by
filename
original_filename
file_path
file_url
file_type
mime_type
file_size
status
error_message
chunk_count
embedding_count
metadata
created_at
updated_at
deleted_at
```

### 10.2 uploaded_by 规则

当前项目需要特别注意：

```text
Resource.uploaded_by
```

Model 和 Alembic migration 中的 nullable 必须一致。

如果业务允许系统导入资源，可以设计为 nullable。

如果所有资源都必须有上传用户，则必须设置为 non-null。

不得出现 Model 允许为空、migration 不允许为空，或反过来的不一致情况。

### 10.3 文件状态

资源状态建议统一为：

```text
uploading
parsing
chunking
embedding
ready
failed
```

前端、后端、数据库、API 文档必须使用同一组状态值。

### 10.4 文件类型

文件类型应与解析器能力一致。

如果数据库中允许：

```text
pdf
docx
pptx
md
txt
xlsx
```

则后端必须有对应解析器。

如果没有 xlsx 解析器，不得在前端或配置中宣称支持 xlsx。

### 10.5 文件路径安全

数据库中保存的文件路径不得暴露服务器敏感路径。

推荐保存：

1. 相对路径。
2. 对象存储 key。
3. 受控访问 URL。
4. 资源 ID。

不推荐保存：

```text
/root/project/backend/storage/...
C:\Users\xxx\secret\...
```

------

## 11. 文档切片与 RAG 元数据规则

### 11.1 chunks 表

`chunks` 表用于保存文档切片元数据，不一定保存完整向量。

推荐字段：

```text
id
course_id
resource_id
chunk_index
content
content_hash
token_count
page_number
section_title
metadata
vector_id
created_at
updated_at
```

### 11.2 course_id 必须存在

`chunks` 表必须包含：

```text
course_id
```

原因：

1. 方便课程级隔离。
2. 方便课程级删除。
3. 方便权限校验。
4. 方便与 ChromaDB metadata 对齐。

### 11.3 vector_id 规则

如果向量存储在 ChromaDB，PostgreSQL 中应保存可追踪字段：

```text
vector_id
```

或通过：

```text
resource_id + chunk_index
```

与向量库 metadata 对齐。

### 11.4 ChromaDB metadata 对齐

向量数据库 metadata 应至少包含：

```text
course_id
resource_id
chunk_id
chunk_index
resource_name
file_type
page_number
section_title
```

PostgreSQL 和 ChromaDB 必须能互相定位。

### 11.5 删除同步

删除 resource 时，必须同步处理：

1. resources 表记录。
2. chunks 表记录。
3. ChromaDB 向量记录。
4. 文件存储对象。
5. 相关处理状态。
6. 相关错误信息。

不得只删除数据库记录而保留孤立向量。

------

## 12. 问答记录表规则

### 12.1 qa_records 表

`qa_records` 表用于保存课程问答记录。

推荐字段：

```text
id
course_id
user_id
conversation_id
question
answer
sources
feedback
rating
created_at
updated_at
```

### 12.2 conversation_id 规则

当前项目需要注意：

```text
qa_records
```

如果服务层和 Schema 中存在 conversation 概念，数据库必须补充：

```text
conversation_id
```

否则前端历史会话、清空会话、连续追问等功能会不一致。

### 12.3 sources 字段

`sources` 可以使用 JSONB 保存引用来源摘要。

示例：

```json
[
  {
    "resource_id": "uuid",
    "resource_name": "chapter1.pdf",
    "chunk_id": "uuid",
    "page_number": 3,
    "score": 0.87,
    "excerpt": "..."
  }
]
```

不得保存伪造来源。

不得保存用户无权访问的跨课程来源。

------

## 13. 教学任务表规则

### 13.1 tasks 表

`tasks` 表用于保存 AI 生成或教师创建的教学任务。

推荐字段：

```text
id
course_id
created_by
title
description
task_type
difficulty
content
requirements
status
additional_instructions
source_resource_ids
metadata
created_at
updated_at
published_at
archived_at
deleted_at
```

### 13.2 字段一致性

当前项目需要特别注意：

```text
additional_instructions
```

不要在数据库、后端、前端之间混用：

```text
extra_instructions
```

如果已经存在混用，必须统一或做兼容映射。

### 13.3 任务状态

任务状态建议包括：

```text
draft
published
archived
deleted
```

具体状态必须与前端和 API 文档一致。

### 13.4 source_resource_ids

如果任务基于课程资源生成，应保存来源资源 ID。

可以使用 JSONB 或关联表。

推荐关联表用于复杂查询：

```text
task_resources
```

字段：

```text
task_id
resource_id
created_at
```

如果当前阶段只需简单存储，可以用 JSONB，但必须说明扩展限制。

------

## 14. 教学报告表规则

### 14.1 reports 表

`reports` 表用于保存教学报告。

推荐字段：

```text
id
course_id
created_by
title
report_type
content
summary
status
source_resource_ids
metadata
created_at
updated_at
exported_at
deleted_at
```

### 14.2 报告状态

报告状态建议包括：

```text
generating
ready
failed
archived
```

如果报告生成是同步完成，也应能记录失败状态。

### 14.3 报告日期规则

报告内容中不得使用硬编码日期。

数据库字段应保存明确时间：

```text
created_at
updated_at
exported_at
```

页面展示时由前端格式化。

### 14.4 删除规则

如果前端有删除报告按钮，数据库和后端应明确支持：

1. 软删除。
2. 硬删除。
3. 归档。

三者必须选择一种，不得前端有删除而后端无 API。

------

## 15. Agent 审计表规则

Agent 执行必须可审计。

### 15.1 agent_runs 表

`agent_runs` 用于记录一次完整 Agent 执行。

推荐字段：

```text
id
user_id
course_id
agent_type
intent
input_summary
plan
status
output_summary
error_message
started_at
finished_at
latency_ms
metadata
created_at
updated_at
```

### 15.2 agent_steps 表

`agent_steps` 用于记录 Agent 内部步骤。

推荐字段：

```text
id
agent_run_id
step_index
step_type
step_name
input_summary
output_summary
status
error_message
latency_ms
metadata
created_at
```

### 15.3 状态值

Agent 状态建议包括：

```text
pending
running
success
failed
cancelled
```

### 15.4 step_type

Step 类型建议包括：

```text
intent_detection
planning
rag_retrieval
skill_call
tool_call
mcp_call
llm_call
validation
finalization
```

### 15.5 审计摘要规则

`input_summary` 和 `output_summary` 应保存摘要。

不得默认保存完整 Prompt、完整用户隐私、完整工具输出。

如果确需保存完整内容，应脱敏并说明用途。

------

## 16. Runtime Skills 数据表规则

### 16.1 skill_definitions 表

`skill_definitions` 用于保存 Runtime Skill 定义。

推荐字段：

```text
id
name
display_name
description
version
enabled
risk_level
input_schema
output_schema
permission_scope
metadata
created_at
updated_at
```

### 16.2 skill_runs 表

`skill_runs` 用于保存 Runtime Skill 执行记录。

推荐字段：

```text
id
skill_id
skill_name
user_id
course_id
agent_run_id
input_summary
output_summary
status
error_message
latency_ms
metadata
created_at
started_at
finished_at
```

### 16.3 skill_name 唯一性

`skill_definitions.name` 应唯一。

示例：

```text
course_qa
resource_analysis
task_generation
report_generation
code_explanation
lesson_design
quiz_generation
study_path
```

### 16.4 Runtime Skill 与 CodeBuddy Skill 区分

不要混淆：

```text
.codebuddy/skills/
```

和：

```text
backend/app/skills/
```

前者是给 CodeBuddy 用的开发规范文件。

后者是 EduAgent 运行时技能系统。

数据库表记录的是运行时技能，不是 CodeBuddy 本地开发 Skill。

------

## 17. MCP 数据表规则

### 17.1 mcp_servers 表

`mcp_servers` 用于保存 MCP Server 配置摘要或管理状态。

推荐字段：

```text
id
name
display_name
description
server_type
endpoint
enabled
risk_level
metadata
created_at
updated_at
```

敏感字段不得明文保存。

如果需要保存 Token 或密钥，应使用安全 Secret 管理，不应直接放在数据库普通字段中。

### 17.2 mcp_tool_calls 表

`mcp_tool_calls` 用于保存 MCP Tool 调用记录。

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
metadata
created_at
started_at
finished_at
```

### 17.3 MCP 调用状态

状态建议包括：

```text
pending
running
success
failed
timeout
denied
```

### 17.4 MCP 安全记录

不得保存：

1. API Key。
2. Authorization Header 原文。
3. Cookie 原文。
4. 数据库密码。
5. `.env` 内容。
6. 完整敏感工具输入。

必须保存时，应保存脱敏摘要。

------

## 18. JSONB 字段规则

PostgreSQL JSONB 可用于保存灵活结构，但不得滥用。

### 18.1 适合使用 JSONB 的场景

适合保存：

1. metadata。
2. sources。
3. input_schema。
4. output_schema。
5. plan。
6. 工具调用摘要。
7. UI 展示配置。
8. 模型调用参数摘要。

### 18.2 不适合使用 JSONB 的场景

不适合把以下内容全部塞进 JSONB：

1. 核心业务字段。
2. 需要频繁过滤的字段。
3. 需要外键关联的字段。
4. 需要排序分页的字段。
5. 需要权限校验的字段。
6. 可明确建模的用户、课程、资源、任务关系。

错误示例：

```text
tasks.metadata 里保存 title、status、course_id、created_by
```

正确做法：

```text
title、status、course_id、created_by 单独建字段
metadata 只保存扩展信息
```

### 18.3 JSONB 大小控制

不要无节制保存超长大模型输出、完整文件内容、完整 Prompt。

长文本应放在专门字段中。

大文件应放文件存储。

向量应放向量数据库。

------

## 19. 索引设计规则

### 19.1 常用索引

常用查询字段应建立索引。

推荐索引字段：

```text
users.email
users.username
courses.owner_id
courses.course_code
course_members.course_id
course_members.user_id
resources.course_id
resources.status
chunks.course_id
chunks.resource_id
qa_records.course_id
qa_records.user_id
tasks.course_id
tasks.status
reports.course_id
agent_runs.course_id
agent_runs.user_id
agent_runs.status
skill_runs.course_id
skill_runs.skill_name
mcp_tool_calls.course_id
mcp_tool_calls.tool_name
```

### 19.2 联合索引

推荐联合索引：

```text
course_members(course_id, user_id)
resources(course_id, status)
chunks(course_id, resource_id)
qa_records(course_id, user_id)
tasks(course_id, status)
reports(course_id, created_at)
agent_runs(course_id, status)
skill_runs(course_id, skill_name)
mcp_tool_calls(course_id, tool_name)
```

### 19.3 唯一索引

推荐唯一约束：

```text
users.email
users.username
courses.course_code
course_members(course_id, user_id)
skill_definitions.name
mcp_servers.name
```

是否允许 email 或 username 为空，应根据认证规则明确。

### 19.4 索引谨慎原则

不要给每个字段都加索引。

索引会增加写入成本。

只给高频查询、过滤、排序、唯一约束字段加索引。

------

## 20. 外键与级联规则

### 20.1 外键规则

核心关系应使用外键约束。

推荐关系：

```text
courses.owner_id -> users.id
course_members.course_id -> courses.id
course_members.user_id -> users.id
resources.course_id -> courses.id
resources.uploaded_by -> users.id
chunks.course_id -> courses.id
chunks.resource_id -> resources.id
qa_records.course_id -> courses.id
qa_records.user_id -> users.id
tasks.course_id -> courses.id
tasks.created_by -> users.id
reports.course_id -> courses.id
reports.created_by -> users.id
agent_runs.user_id -> users.id
agent_runs.course_id -> courses.id
agent_steps.agent_run_id -> agent_runs.id
skill_runs.course_id -> courses.id
mcp_tool_calls.course_id -> courses.id
```

### 20.2 级联删除谨慎

不得随意设置 `CASCADE DELETE`。

尤其以下表应谨慎：

1. agent_runs。
2. agent_steps。
3. skill_runs。
4. mcp_tool_calls。
5. qa_records。
6. reports。

这些表可能属于审计数据，删除策略应明确。

### 20.3 推荐删除策略

| 数据           | 推荐策略                   |
| -------------- | -------------------------- |
| 用户           | 禁用或软删除               |
| 课程           | 软删除或归档               |
| 资源           | 软删除 + 清理向量和文件    |
| chunks         | 资源删除时同步删除         |
| qa_records     | 默认保留，必要时按课程清理 |
| tasks          | 软删除或归档               |
| reports        | 软删除或归档               |
| agent_runs     | 默认保留审计记录           |
| skill_runs     | 默认保留审计记录           |
| mcp_tool_calls | 默认保留审计记录           |

------

## 21. 软删除规则

如果使用软删除，推荐字段：

```text
deleted_at
```

可选字段：

```text
deleted_by
delete_reason
```

使用软删除时，所有查询必须默认排除：

```text
deleted_at IS NOT NULL
```

除非是管理员审计或回收站功能。

不要只加 `deleted_at` 字段，却忘记在查询中排除。

------

## 22. 枚举设计规则

状态、角色、类型应统一使用 Enum。

推荐枚举：

```text
UserRole
CourseMemberRole
ResourceStatus
ResourceType
TaskStatus
TaskType
ReportStatus
ReportType
AgentRunStatus
AgentStepType
SkillRunStatus
MCPToolCallStatus
RiskLevel
```

枚举值必须与以下内容一致：

1. 数据库。
2. SQLAlchemy Model。
3. Pydantic Schema。
4. API 文档。
5. 前端 TypeScript 类型。
6. 页面显示逻辑。

禁止后端一个值、前端另一个值。

------

## 23. Alembic 迁移规则

### 23.1 什么时候必须写 migration

以下修改必须写 Alembic migration：

1. 新增表。
2. 删除表。
3. 新增字段。
4. 删除字段。
5. 修改字段类型。
6. 修改 nullable。
7. 修改默认值。
8. 新增索引。
9. 删除索引。
10. 新增外键。
11. 修改外键。
12. 新增唯一约束。
13. 新增 enum。
14. 修改 enum。
15. 新增 PostgreSQL extension。

### 23.2 迁移命令

推荐命令：

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### 23.3 迁移检查清单

生成 migration 后必须检查：

1. 是否误删表。
2. 是否误删字段。
3. 是否正确处理 nullable。
4. 是否正确处理默认值。
5. 是否正确创建索引。
6. 是否正确创建外键。
7. 是否需要数据迁移。
8. 是否需要 PostgreSQL extension。
9. downgrade 是否合理。
10. 是否影响已有数据。

### 23.4 禁止行为

禁止：

1. 只改 Model 不写 Migration。
2. 手动直接连数据库改表但不提交 migration。
3. 在 migration 中写入真实敏感数据。
4. 在生产数据表上执行危险不可逆操作而不说明。
5. 生成 migration 后不检查直接提交。

------

## 24. 数据一致性规则

### 24.1 Model 与 Migration 一致

SQLAlchemy Model 必须与 Alembic Migration 一致。

重点检查：

1. 字段类型。
2. nullable。
3. default。
4. server_default。
5. index。
6. unique。
7. foreign key。
8. enum。

当前特别注意：

```text
Resource.uploaded_by nullable
```

不得出现 Model 和 Migration 不一致。

### 24.2 Schema 与 Model 一致

Pydantic Schema 必须与 Model 一致。

如果数据库字段改名，必须同步：

1. Pydantic Request。
2. Pydantic Response。
3. Service。
4. API 文档。
5. 前端 types。

### 24.3 前后端字段一致

字段名必须统一。

当前特别注意：

```text
additional_instructions
```

不得混用：

```text
extra_instructions
```

------

## 25. 数据安全规则

数据库不得保存以下明文内容：

1. 用户明文密码。
2. API Key。
3. JWT Secret。
4. Refresh Token 明文。
5. 数据库连接密码。
6. 模型供应商密钥。
7. MinIO Secret Key。
8. Authorization Header 原文。
9. Cookie 原文。
10. 未脱敏的系统 Prompt。
11. 未脱敏的敏感工具输入输出。

### 25.1 脱敏规则

保存审计信息时应脱敏：

```text
sk-******abcd
Bearer ******abcd
postgresql://user:******@host/db
```

### 25.2 Prompt 保存规则

默认不保存完整系统 Prompt。

如需保存，必须：

1. 脱敏。
2. 限制长度。
3. 说明用途。
4. 只允许管理员查看。
5. 遵守安全审计要求。

------

## 26. 性能与分页规则

### 26.1 列表查询必须分页

以下接口必须分页：

1. 用户列表。
2. 课程列表。
3. 资源列表。
4. 问答历史。
5. 任务列表。
6. 报告列表。
7. Agent Runs。
8. Skill Runs。
9. MCP Tool Calls。
10. 管理员审计日志。

禁止一次性返回大量数据。

### 26.2 分页字段

推荐分页请求字段：

```text
page
page_size
```

或：

```text
limit
offset
```

同一项目中应统一。

推荐响应字段：

```text
items
total
page
page_size
```

### 26.3 排序规则

常见默认排序：

```text
created_at DESC
updated_at DESC
```

Agent、Skill、MCP 审计记录默认按：

```text
created_at DESC
```

------

## 27. 数据初始化规则

### 27.1 初始化内容

项目可提供初始化脚本，用于创建：

1. 默认管理员。
2. 示例教师。
3. 示例学生。
4. 示例课程。
5. 示例配置。
6. 默认 Skill Definitions。
7. 默认 MCP Server 配置摘要。

### 27.2 敏感信息

初始化脚本不得包含真实密码。

如果需要默认密码，应仅用于开发环境，并写入 `.env.example` 或说明文档。

生产环境不得使用默认密码。

### 27.3 初始化脚本位置

推荐位置：

```text
backend/scripts/
```

或：

```text
backend/app/core/init_data.py
```

具体以项目现有结构为准。

------

## 28. 测试数据规则

测试数据应满足：

1. 不包含真实用户隐私。
2. 不包含真实密钥。
3. 不包含生产课程资料。
4. 能覆盖学生、教师、管理员。
5. 能覆盖课程成员关系。
6. 能覆盖资源状态。
7. 能覆盖 RAG 问答。
8. 能覆盖 Agent / Skill / MCP 审计。

测试数据应与正式初始化数据分离。

------

## 29. 与向量数据库的关系

PostgreSQL 保存业务元数据和可追踪关系。

ChromaDB 保存向量索引。

两者必须通过 metadata 对齐。

### 29.1 PostgreSQL 负责

1. 用户。
2. 课程。
3. 资源。
4. chunks 元数据。
5. 问答记录。
6. 任务。
7. 报告。
8. Agent 审计。
9. Skill 审计。
10. MCP 审计。

### 29.2 ChromaDB 负责

1. chunk embedding。
2. 向量检索。
3. 向量 metadata。
4. 相似度查询。

### 29.3 同步规则

写入 ChromaDB 前，应确保 PostgreSQL 中已有 resource 和 chunk 记录。

删除资源时，应同步删除 ChromaDB 中对应向量。

重处理资源时，应避免旧向量残留。

------

## 30. 数据库任务执行流程

CodeBuddy 执行数据库任务时，应按以下流程：

```text
1. 阅读 CODEBUDDY.md
2. 阅读本规则文件
3. 阅读 03_数据模型与数据库设计.md
4. 检查现有 SQLAlchemy Models
5. 检查现有 Alembic Migrations
6. 判断是否需要新增或修改表
7. 判断是否影响 API Schema
8. 判断是否影响前端 TypeScript Types
9. 修改 Model
10. 生成或修改 Migration
11. 同步 Schema / Service / API 文档
12. 运行 alembic upgrade head 或说明无法运行原因
13. 输出修改说明和风险
```

------

## 31. 数据库禁止事项清单

CodeBuddy 数据库开发时禁止：

1. 绕过 Alembic 直接改库。
2. 只改 Model 不写 Migration。
3. 只写 Migration 不改 Model。
4. 随意删除已有表。
5. 随意删除已有字段。
6. 随意修改字段类型导致数据丢失。
7. 直接保存明文密码。
8. 直接保存明文 API Key。
9. 审计表保存完整敏感输入。
10. RAG 跨课程共享 chunk。
11. 删除 resource 后保留孤立向量。
12. 不加 course_id 导致课程数据无法隔离。
13. 不分页返回审计记录。
14. 枚举值前后端不一致。
15. 数据库字段名和 API 字段名不一致。
16. 没有索引就查询大表。
17. 滥用 JSONB 保存所有业务数据。
18. 误把 CodeBuddy Skill 当成 Runtime Skill 入库。
19. 声称未运行的 migration 已经通过。
20. 在 migration 中写入真实敏感信息。

------

## 32. 数据库输出要求

完成数据库相关任务后，必须说明：

1. 修改了哪些 Model。
2. 修改了哪些 Migration。
3. 新增了哪些表。
4. 新增或修改了哪些字段。
5. 字段类型、nullable、default 是否说明清楚。
6. 是否新增索引。
7. 是否新增外键。
8. 是否影响 Pydantic Schema。
9. 是否影响 Service 层。
10. 是否影响 API 文档。
11. 是否影响前端类型。
12. 是否运行了 `alembic upgrade head`。
13. 如果未运行，原因是什么。
14. 是否存在数据迁移风险。
15. 是否存在兼容性风险。

不得只回答：

```text
已完成数据库修改
```

必须给出可审查的数据库变更说明。

------

## 33. 最终原则

EduAgent 数据库必须保持：

```text
结构清晰
关系明确
权限可控
课程隔离
审计完整
迁移可追踪
字段一致
查询高效
安全可靠
```

所有数据库修改都必须优先保证：

1. 数据安全。
2. 课程隔离。
3. 权限正确。
4. Model 与 Migration 一致。
5. 后端 Schema 一致。
6. 前端 TypeScript 类型一致。
7. API 文档一致。
8. RAG 元数据可追踪。
9. Agent / Skill / MCP 执行可审计。
10. 迁移可执行、可回滚、可解释。