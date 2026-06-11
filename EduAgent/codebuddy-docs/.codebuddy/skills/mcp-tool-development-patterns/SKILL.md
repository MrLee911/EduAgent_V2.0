# MCP Tool Development Patterns

```yaml
name: mcp-tool-development-patterns
description: Use when developing MCP tools, MCP adapters, MCP permissions, MCP audit logs, or tool-calling integration.
```

------

## 1. Skill 目的

本 Skill 用于指导 CodeBuddy 在 EduAgent 项目中开发 MCP 工具生态相关代码。

EduAgent 的 MCP 不是普通函数调用，也不是让大模型随意访问外部系统，而是一个受权限控制、受课程边界约束、可审计、可扩展的工具调用体系。

CodeBuddy 在开发 MCP 功能时，必须遵守以下目标：

```text
MCP = 智能体工具生态接入层
```

MCP 主要用于让 Agent 和 Skills 安全调用以下能力：

1. 课程知识库检索。
2. 课程数据库安全查询。
3. 课程资源文件分析。
4. 教学报告统计分析。
5. 代码沙箱执行。
6. 外部教学平台工具。
7. 外部知识库工具。
8. 其他可控工具服务。

MCP Tool 不得成为绕过权限、绕过 Service 层、绕过数据库安全边界的入口。

------

## 2. 适用场景

CodeBuddy 在以下场景中应使用本 Skill：

1. 新增 `backend/app/mcp/` 目录。
2. 开发 MCP Client。
3. 开发 MCP Registry。
4. 开发 MCP Tool Schema。
5. 开发 MCP 权限校验。
6. 开发内部 MCP Adapter。
7. 开发 RAG MCP Tool。
8. 开发 Course DB MCP Tool。
9. 开发 File Resource MCP Tool。
10. 开发 Report Analysis MCP Tool。
11. 开发 Code Sandbox MCP Tool。
12. 开发 MCP Tool 调用日志。
13. 开发 MCP 管理 API。
14. 前端需要展示 MCP Server、MCP Tool、MCP 调用记录。
15. Agent / Skill 需要调用工具。

------

## 3. 核心原则

### 3.1 MCP Tool 必须受控

MCP Tool 不能设计成任意执行工具。

禁止设计：

```text
execute_sql
run_shell_command
read_any_file
call_any_url
execute_python_unrestricted
```

推荐设计：

```text
search_course_knowledge
get_course_stats
query_qa_records
list_course_files
summarize_file
analyze_qa_hotspots
run_python_code_in_sandbox
```

------

### 3.2 权限必须由代码判断

错误做法：

```text
把所有工具列表交给 LLM，让 LLM 自己判断用户能不能调用。
```

正确做法：

```text
后端代码先根据 user_role、course_role、course_id 过滤可用 MCP Tool，
LLM 只能从允许的工具中选择。
```

权限检查必须发生在：

1. Tool 列表返回前。
2. Tool 调用前。
3. Tool 参数执行前。
4. Tool 结果返回前。

------

### 3.3 所有 Tool 必须限定课程边界

所有课程内 MCP Tool 必须携带：

```text
course_id
user_id
user_role
course_role
```

任何工具不得跨课程访问数据。

例如，学生在 A 课程中调用问答工具，不得检索 B 课程资料。

------

### 3.4 MCP 不替代 Service 层

MCP Tool 可以调用 Service 层能力，但不应绕过 Service 层。

推荐链路：

```text
Agent / Skill
→ MCP Client
→ MCP Tool Adapter
→ Service / RAG / Repository
→ 数据库或向量库
```

不推荐链路：

```text
Agent / Skill
→ MCP Tool
→ 直接随意查询数据库
```

------

### 3.5 MCP 调用必须可审计

每一次 MCP Tool 调用都应记录：

1. 调用用户。
2. 调用课程。
3. Server 名称。
4. Tool 名称。
5. 参数摘要。
6. 结果摘要。
7. 调用状态。
8. 耗时。
9. 错误信息。
10. 调用时间。

不应记录：

1. API Key。
2. JWT。
3. 密码。
4. 数据库连接。
5. 服务器真实绝对路径。
6. 完整系统 Prompt。
7. 敏感学生隐私全文。

------

## 4. 推荐目录结构

CodeBuddy 应按以下结构新增 MCP 代码：

```text
backend/app/mcp/
├── __init__.py
├── client.py
├── registry.py
├── schemas.py
├── permissions.py
├── exceptions.py
└── adapters/
    ├── __init__.py
    ├── internal_rag.py
    ├── course_db.py
    ├── file_resource.py
    ├── report_analysis.py
    └── code_sandbox.py
```

说明：

| 文件                          | 作用                         |
| ----------------------------- | ---------------------------- |
| `client.py`                   | MCP Tool 调用入口            |
| `registry.py`                 | MCP Server 和 Tool 注册中心  |
| `schemas.py`                  | MCP 相关 Pydantic Schema     |
| `permissions.py`              | MCP 权限校验逻辑             |
| `exceptions.py`               | MCP 专用异常                 |
| `adapters/internal_rag.py`    | RAG 检索工具                 |
| `adapters/course_db.py`       | 课程数据库安全查询工具       |
| `adapters/file_resource.py`   | 课程资源文件工具             |
| `adapters/report_analysis.py` | 报告统计分析工具             |
| `adapters/code_sandbox.py`    | 代码沙箱工具，默认关闭或受限 |

------

## 5. MCP Schema 设计

### 5.1 MCPContext

所有 MCP Tool 调用必须携带上下文。

```python
from pydantic import BaseModel
from typing import Literal
from uuid import UUID


class MCPContext(BaseModel):
    request_id: str
    user_id: UUID
    user_role: Literal["student", "teacher", "admin"]
    course_id: UUID | None = None
    course_role: Literal["student", "teacher"] | None = None
    conversation_id: str | None = None
    agent_run_id: UUID | None = None
    skill_run_id: UUID | None = None
```

要求：

1. 课程内工具必须有 `course_id`。
2. 课程内工具必须校验 `course_role`。
3. 管理员工具必须校验 `user_role == "admin"`。
4. 不得仅依赖前端传入角色，角色必须来自后端认证上下文。

------

### 5.2 MCPToolDefinition

```python
from pydantic import BaseModel, Field


class MCPToolDefinition(BaseModel):
    server_name: str
    tool_name: str
    display_name: str
    description: str
    input_schema: dict
    output_schema: dict
    allowed_roles: list[str] = Field(default_factory=list)
    required_course_role: list[str] = Field(default_factory=list)
    enabled: bool = True
    high_risk: bool = False
```

字段说明：

| 字段                   | 说明            |
| ---------------------- | --------------- |
| `server_name`          | MCP Server 名称 |
| `tool_name`            | Tool 唯一名称   |
| `display_name`         | 前端展示名称    |
| `description`          | 工具说明        |
| `input_schema`         | 输入参数 Schema |
| `output_schema`        | 输出结果 Schema |
| `allowed_roles`        | 允许系统角色    |
| `required_course_role` | 允许课程角色    |
| `enabled`              | 是否启用        |
| `high_risk`            | 是否高风险工具  |

------

### 5.3 MCPToolCallRequest

```python
from pydantic import BaseModel


class MCPToolCallRequest(BaseModel):
    server_name: str
    tool_name: str
    arguments: dict
```

------

### 5.4 MCPToolResult

```python
from pydantic import BaseModel
from typing import Literal


class MCPToolResult(BaseModel):
    server_name: str
    tool_name: str
    status: Literal["success", "failed", "denied", "timeout"]
    data: dict | list | None = None
    error_message: str | None = None
    metadata: dict | None = None
```

要求：

1. 成功时 `status=success`。
2. 权限不足时 `status=denied`。
3. 超时时 `status=timeout`。
4. 失败时不得暴露内部异常堆栈。
5. 返回给 LLM 的结果应是脱敏后的数据。

------

## 6. MCP Registry 设计

### 6.1 基本职责

`MCPRegistry` 负责：

1. 注册 MCP Server。
2. 注册 MCP Tool。
3. 查询 Server。
4. 查询 Tool。
5. 按角色过滤 Tool。
6. 按课程角色过滤 Tool。
7. 判断 Tool 是否启用。
8. 判断 Tool 是否高风险。

------

### 6.2 推荐接口

```python
class MCPRegistry:
    def register_tool(self, tool: MCPToolDefinition, handler) -> None:
        ...

    def get_tool(self, server_name: str, tool_name: str) -> MCPToolDefinition:
        ...

    def get_handler(self, server_name: str, tool_name: str):
        ...

    def list_tools(
        self,
        user_role: str,
        course_role: str | None = None,
        include_disabled: bool = False,
    ) -> list[MCPToolDefinition]:
        ...
```

------

### 6.3 注册工具示例

```python
registry.register_tool(
    MCPToolDefinition(
        server_name="rag_search",
        tool_name="search_course_knowledge",
        display_name="检索课程知识库",
        description="在当前课程的知识库中检索相关内容",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        },
        output_schema={
            "type": "object",
            "properties": {
                "results": {"type": "array"}
            }
        },
        allowed_roles=["student", "teacher", "admin"],
        required_course_role=["student", "teacher"],
        enabled=True,
        high_risk=False,
    ),
    handler=search_course_knowledge,
)
```

------

## 7. MCP Client 设计

### 7.1 基本职责

`MCPClient` 是 Agent / Skill 调用工具的统一入口。

职责：

1. 接收工具调用请求。
2. 查询 Tool Definition。
3. 执行权限校验。
4. 执行参数校验。
5. 调用 Tool Handler。
6. 处理超时。
7. 捕获异常。
8. 记录调用日志。
9. 返回标准结果。

------

### 7.2 推荐接口

```python
class MCPClient:
    def __init__(self, registry, permission_checker, audit_logger):
        self.registry = registry
        self.permission_checker = permission_checker
        self.audit_logger = audit_logger

    async def list_tools(self, context: MCPContext) -> list[MCPToolDefinition]:
        ...

    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict,
        context: MCPContext,
    ) -> MCPToolResult:
        ...
```

------

### 7.3 调用流程

```text
Agent / Skill 发起 Tool 调用
→ MCPClient.call_tool()
→ MCPRegistry 查找 Tool
→ MCPPermissionChecker 校验权限
→ 参数 Schema 校验
→ 执行 Tool Handler
→ 记录 mcp_tool_calls
→ 返回 MCPToolResult
```

------

## 8. MCP 权限校验设计

### 8.1 权限校验文件

```text
backend/app/mcp/permissions.py
```

------

### 8.2 权限校验内容

每次工具调用前必须检查：

1. Tool 是否存在。
2. Tool 是否启用。
3. 用户是否登录。
4. 用户系统角色是否允许。
5. 课程内工具是否传入 `course_id`。
6. 用户是否属于该课程。
7. 用户课程角色是否允许。
8. 参数中是否包含其他课程 ID。
9. Tool 是否高风险。
10. 高风险 Tool 是否被配置允许。
11. 是否超过调用次数限制。
12. 是否超过超时限制。

------

### 8.3 权限校验示例

```python
class MCPPermissionChecker:
    async def check(
        self,
        tool: MCPToolDefinition,
        arguments: dict,
        context: MCPContext,
    ) -> None:
        if not tool.enabled:
            raise MCPPermissionDenied("工具未启用")

        if context.user_role not in tool.allowed_roles:
            raise MCPPermissionDenied("当前用户角色无权调用该工具")

        if tool.required_course_role:
            if context.course_role not in tool.required_course_role:
                raise MCPPermissionDenied("当前课程角色无权调用该工具")

        if "course_id" in arguments:
            if str(arguments["course_id"]) != str(context.course_id):
                raise MCPPermissionDenied("禁止跨课程调用工具")

        if tool.high_risk and context.user_role != "admin":
            raise MCPPermissionDenied("高风险工具仅允许管理员调用")
```

------

### 8.4 重要约束

禁止让 LLM 自己判断：

```text
这个用户是不是有权限？
这个 Tool 能不能调用？
这个 course_id 是否属于当前用户？
```

这些必须由后端代码判断。

------

## 9. 内置 MCP Adapter 设计

------

# 9.1 internal_rag.py

用途：

提供课程知识库检索能力。

推荐工具：

| Tool                      | 说明               | 角色                        |
| ------------------------- | ------------------ | --------------------------- |
| `search_course_knowledge` | 检索当前课程知识库 | student / teacher / admin   |
| `get_chunk_detail`        | 获取切片详情       | teacher / admin，学生可受限 |
| `get_related_chunks`      | 获取相关切片       | student / teacher / admin   |
| `rebuild_resource_index`  | 重建资源索引       | teacher / admin             |

------

### search_course_knowledge

输入：

```json
{
  "query": "Python 函数",
  "top_k": 5
}
```

输出：

```json
{
  "results": [
    {
      "resource_id": "uuid",
      "resource_name": "Python基础.pdf",
      "chunk_id": "uuid",
      "chunk_index": 3,
      "score": 0.91,
      "text_preview": "函数是组织代码的一种方式..."
    }
  ]
}
```

要求：

1. 必须使用 `context.course_id`。
2. 不允许从 arguments 中信任外部 `course_id`。
3. 检索结果必须只来自当前课程。
4. 返回内容应控制长度，避免 Prompt 过长。
5. Reranker 失败时可以降级。

------

# 9.2 course_db.py

用途：

提供课程数据库安全查询能力。

推荐工具：

| Tool               | 说明             | 角色                      |
| ------------------ | ---------------- | ------------------------- |
| `get_course_info`  | 获取课程基础信息 | student / teacher / admin |
| `get_course_stats` | 获取课程统计     | teacher / admin           |
| `query_qa_records` | 查询问答统计     | teacher / admin           |
| `list_tasks`       | 查询课程任务     | teacher / admin           |
| `list_reports`     | 查询课程报告     | teacher / admin           |

------

### get_course_stats

输出示例：

```json
{
  "course_id": "uuid",
  "resource_count": 12,
  "ready_resource_count": 10,
  "task_count": 5,
  "published_task_count": 3,
  "qa_count": 42,
  "active_student_count": 18
}
```

限制：

1. 不允许执行原始 SQL。
2. 不返回学生隐私全文。
3. 不返回其他课程数据。
4. 学生默认不能调用统计类工具。

------

# 9.3 file_resource.py

用途：

提供课程资源文件分析能力。

推荐工具：

| Tool                         | 说明           | 角色            |
| ---------------------------- | -------------- | --------------- |
| `list_course_files`          | 列出课程资源   | teacher / admin |
| `get_file_metadata`          | 获取资源元信息 | teacher / admin |
| `extract_file_text`          | 提取资源文本   | teacher / admin |
| `summarize_file`             | 总结资源内容   | teacher / admin |
| `compare_files`              | 对比资源内容   | teacher / admin |
| `detect_duplicate_resources` | 检测重复资源   | teacher / admin |

限制：

1. 只能访问当前课程资源。
2. 不返回服务器真实路径。
3. 不允许路径穿越。
4. 不读取非课程目录文件。
5. 如果资源未处理完成，应返回明确错误。

------

# 9.4 report_analysis.py

用途：

提供教学报告统计分析能力。

推荐工具：

| Tool                        | 说明         | 角色            |
| --------------------------- | ------------ | --------------- |
| `analyze_qa_hotspots`       | 分析问答热点 | teacher / admin |
| `analyze_resource_usage`    | 分析资源情况 | teacher / admin |
| `analyze_task_distribution` | 分析任务分布 | teacher / admin |
| `calculate_active_students` | 统计活跃学生 | teacher / admin |
| `generate_trend_summary`    | 生成趋势摘要 | teacher / admin |

要求：

1. 所有数字必须来自真实数据库统计。
2. 不得编造学生人数、问答数、资源数。
3. 不返回敏感学生隐私。
4. 日期范围必须来自参数或 Service 层，不得硬编码。

------

# 9.5 code_sandbox.py

用途：

提供代码运行或代码分析能力。

默认状态：

```text
默认关闭或严格受限。
```

推荐工具：

| Tool                  | 说明             | 默认角色                       |
| --------------------- | ---------------- | ------------------------------ |
| `analyze_code_error`  | 分析代码错误     | student / teacher / admin      |
| `explain_code`        | 解释代码         | student / teacher / admin      |
| `generate_test_cases` | 生成测试用例     | teacher / admin                |
| `run_python_code`     | 运行 Python 代码 | 默认 teacher / admin，学生受限 |

限制：

1. 禁止网络访问。
2. 禁止访问宿主机文件。
3. 限制运行时间。
4. 限制内存。
5. 禁止危险系统命令。
6. 学生侧默认不开放真实代码执行。
7. 所有执行必须在沙箱中完成。
8. 工具结果必须脱敏。

------

## 10. MCP 调用日志设计

### 10.1 推荐数据库表

```text
mcp_tool_calls
```

字段建议：

```text
id
server_name
tool_name
user_id
course_id
agent_run_id
skill_run_id
arguments_summary
result_summary
status
latency_ms
error_message
created_at
```

------

### 10.2 arguments_summary 要求

只能保存参数摘要。

示例：

```json
{
  "query": "Python 函数",
  "top_k": 5
}
```

禁止保存：

1. API Key。
2. JWT。
3. 密码。
4. 完整文件内容。
5. 原始 SQL。
6. 服务器真实路径。

------

### 10.3 result_summary 要求

示例：

```json
{
  "result_count": 5,
  "status": "success"
}
```

不建议保存完整大文本结果。

------

## 11. MCP 与 Agent / Skill 的关系

### 11.1 推荐调用关系

```text
Agent Orchestrator
→ Skill Router
→ Skill Executor
→ MCP Client
→ MCP Tool Adapter
→ Service / RAG / Repository
```

------

### 11.2 CourseQAAgent 调用示例

```text
CourseQAAgent
→ course_qa Skill
→ MCPClient.call_tool("rag_search", "search_course_knowledge")
→ Retriever
→ LLM
→ QARecord 落库
```

------

### 11.3 ReportGenerationAgent 调用示例

```text
ReportGenerationAgent
→ report_generation Skill
→ MCPClient.call_tool("course_db", "get_course_stats")
→ MCPClient.call_tool("report_analysis", "analyze_qa_hotspots")
→ LLM
→ Report 落库
```

------

## 12. MCP API 设计建议

管理员 MCP 管理接口建议放在：

```text
/api/v1/admin/mcp
```

推荐接口：

```text
GET    /api/v1/admin/mcp/servers
POST   /api/v1/admin/mcp/servers
PATCH  /api/v1/admin/mcp/servers/{server_id}
DELETE /api/v1/admin/mcp/servers/{server_id}
GET    /api/v1/admin/mcp/tools
GET    /api/v1/admin/mcp/tool-calls
GET    /api/v1/admin/mcp/tool-calls/{call_id}
```

要求：

1. 所有接口仅管理员可访问。
2. 不返回真实密钥。
3. 不返回完整敏感参数。
4. Tool 调用记录只返回摘要。
5. 删除 Server 优先改为禁用。

------

## 13. MCP 配置要求

### 13.1 环境变量

```env
MCP_ENABLED=true
MCP_MODE=internal
MCP_TOOL_TIMEOUT_SECONDS=30
MCP_MAX_TOOL_CALLS_PER_RUN=20
MCP_RECORD_TOOL_CALLS=true
MCP_SERVER_CONFIG_PATH=backend/app/mcp/servers.yaml
```

------

### 13.2 servers.yaml

建议文件：

```text
backend/app/mcp/servers.yaml
```

示例：

```yaml
servers:
  - name: rag_search
    description: 课程知识库检索工具
    transport: internal
    enabled: true
    allowed_roles:
      - student
      - teacher
      - admin

  - name: course_db
    description: 课程数据库安全查询工具
    transport: internal
    enabled: true
    allowed_roles:
      - teacher
      - admin

  - name: file_resource
    description: 课程资源文件分析工具
    transport: internal
    enabled: true
    allowed_roles:
      - teacher
      - admin

  - name: report_analysis
    description: 教学报告统计分析工具
    transport: internal
    enabled: true
    allowed_roles:
      - teacher
      - admin

  - name: code_sandbox
    description: 代码运行和代码分析工具
    transport: internal
    enabled: false
    allowed_roles:
      - teacher
      - admin
```

------

## 14. 错误处理规范

### 14.1 MCP 专用异常

推荐定义：

```python
class MCPError(Exception):
    pass


class MCPToolNotFound(MCPError):
    pass


class MCPPermissionDenied(MCPError):
    pass


class MCPToolTimeout(MCPError):
    pass


class MCPToolExecutionError(MCPError):
    pass
```

------

### 14.2 错误返回

MCP Tool 失败时，应返回：

```json
{
  "server_name": "rag_search",
  "tool_name": "search_course_knowledge",
  "status": "failed",
  "data": null,
  "error_message": "课程知识库检索失败，请稍后重试",
  "metadata": {
    "latency_ms": 1200
  }
}
```

不要返回：

```text
完整 Python traceback
数据库连接字符串
服务器文件路径
API Key
内部 Prompt
```

------

## 15. 测试要求

### 15.1 单元测试

建议新增：

```text
backend/tests/test_mcp_registry.py
backend/tests/test_mcp_permissions.py
backend/tests/test_mcp_client.py
backend/tests/test_mcp_rag_tool.py
backend/tests/test_mcp_course_db_tool.py
```

------

### 15.2 必测场景

| 编号     | 测试场景          | 通过标准             |
| -------- | ----------------- | -------------------- |
| MCP-T-01 | 注册 Tool         | Registry 可获取 Tool |
| MCP-T-02 | 列出 Tool         | 按角色过滤正确       |
| MCP-T-03 | 学生调用 RAG Tool | 允许当前课程检索     |
| MCP-T-04 | 学生调用统计 Tool | 返回权限拒绝         |
| MCP-T-05 | 教师调用课程统计  | 仅返回当前课程数据   |
| MCP-T-06 | 跨课程 course_id  | 返回权限拒绝         |
| MCP-T-07 | Tool 不存在       | 返回 ToolNotFound    |
| MCP-T-08 | Tool 超时         | 返回 timeout         |
| MCP-T-09 | Tool 异常         | 返回脱敏错误         |
| MCP-T-10 | 调用日志          | 记录 mcp_tool_calls  |
| MCP-T-11 | 高风险 Tool       | 默认拒绝             |
| MCP-T-12 | 返回结果          | 不包含敏感信息       |

------

## 16. 常见错误与禁止做法

### 16.1 禁止把 MCP 做成万能后门

禁止：

```text
execute_sql(sql: str)
read_file(path: str)
run_command(command: str)
```

原因：

1. 破坏权限边界。
2. 容易泄露数据。
3. 容易被 Prompt Injection 利用。
4. 无法安全审计。

------

### 16.2 禁止直接信任 LLM 生成的参数

错误：

```python
course_id = arguments["course_id"]
```

正确：

```python
course_id = context.course_id
```

如果 arguments 中出现 course_id，必须和 context.course_id 比对。

------

### 16.3 禁止返回真实文件路径

错误：

```json
{
  "file_path": "/home/app/backend/storage/resources/xxx.pdf"
}
```

正确：

```json
{
  "resource_id": "uuid",
  "resource_name": "Python基础.pdf"
}
```

------

### 16.4 禁止保存敏感参数全文

错误：

```json
{
  "api_key": "sk-xxxx",
  "jwt": "xxxxx"
}
```

正确：

```json
{
  "argument_keys": ["query", "top_k"],
  "safe_summary": "课程知识库检索"
}
```

------

## 17. CodeBuddy 开发检查清单

CodeBuddy 完成 MCP 相关开发后，必须检查：

```text
[ ] 是否新增 backend/app/mcp/
[ ] 是否定义 MCPContext
[ ] 是否定义 MCPToolDefinition
[ ] 是否定义 MCPToolResult
[ ] 是否实现 MCPRegistry
[ ] 是否实现 MCPClient
[ ] 是否实现 MCPPermissionChecker
[ ] 是否实现 internal_rag Adapter
[ ] 是否实现 course_db Adapter
[ ] 是否实现 file_resource Adapter
[ ] 是否实现 report_analysis Adapter
[ ] code_sandbox 是否默认关闭
[ ] Tool 是否有 input_schema
[ ] Tool 是否有 output_schema
[ ] Tool 是否有限定 allowed_roles
[ ] Tool 是否校验 course_id
[ ] Tool 是否避免原始 SQL
[ ] Tool 是否避免真实文件路径
[ ] Tool 是否有超时
[ ] Tool 是否有异常处理
[ ] Tool 调用是否记录日志
[ ] 是否新增 mcp_servers 表或配置
[ ] 是否新增 mcp_tool_calls 表或结构化日志
[ ] 是否新增 MCP 测试
[ ] 是否同步 04_API接口文档.md
[ ] 是否同步 05_AI智能体行为定义.md
[ ] 是否同步 08_CodeBuddy开发任务书.md
```

------

## 18. 最小可交付版本

MCP 第一阶段最小可交付版本应包含：

```text
backend/app/mcp/schemas.py
backend/app/mcp/registry.py
backend/app/mcp/client.py
backend/app/mcp/permissions.py
backend/app/mcp/adapters/internal_rag.py
backend/app/mcp/adapters/course_db.py
backend/app/mcp/adapters/file_resource.py
backend/app/mcp/adapters/report_analysis.py
```

至少实现以下工具：

```text
search_course_knowledge
get_course_stats
list_course_files
analyze_qa_hotspots
```

最小验收：

1. Agent / Skill 可以通过 MCPClient 调用 `search_course_knowledge`。
2. 学生可以调用当前课程 RAG 检索工具。
3. 学生不能调用教师统计工具。
4. 教师可以调用当前课程统计工具。
5. 跨课程调用被拒绝。
6. MCP Tool 调用有日志。
7. 工具失败时返回脱敏错误。
8. 不存在原始 SQL 工具。
9. 不存在任意文件读取工具。
10. 高风险代码沙箱默认关闭。

------

## 19. 与其他文档的关系

本 Skill 与以下文档配合使用：

| 文档                                           | 关系                                 |
| ---------------------------------------------- | ------------------------------------ |
| `01_项目需求规格文档.md`                       | 定义 MCP 业务需求                    |
| `02_技术架构文档.md`                           | 定义 MCP 在整体架构中的位置          |
| `03_数据模型与数据库设计.md`                   | 定义 `mcp_servers`、`mcp_tool_calls` |
| `04_API接口文档.md`                            | 定义 MCP 管理 API                    |
| `05_AI智能体行为定义.md`                       | 定义 Agent 如何调用 MCP              |
| `06_提示词模板.md`                             | 定义 MCP Tool Calling Prompt         |
| `07_页面流程图.md`                             | 定义 MCP 管理页面                    |
| `08_CodeBuddy开发任务书.md`                    | 定义 MCP 开发任务                    |
| `runtime-skills-development-patterns/SKILL.md` | 定义 Skills 如何调用 MCP             |

------

## 20. 本 Skill 总结

CodeBuddy 开发 MCP 时必须牢记：

```text
MCP 是工具生态接入层，不是权限后门。
```

MCP Tool 必须满足：

```text
有 Schema
有权限
有课程边界
有超时
有异常处理
有审计记录
不执行原始 SQL
不读取任意文件
不返回真实路径
不泄露敏感信息
```

推荐开发顺序：

```text
1. 定义 MCP Schema
2. 实现 MCP Registry
3. 实现 MCP Permission Checker
4. 实现 MCP Client
5. 实现 internal_rag Tool
6. 实现 course_db Tool
7. 实现 file_resource Tool
8. 实现 report_analysis Tool
9. 增加 mcp_tool_calls 审计
10. 增加 MCP API 和测试
```

完成该 Skill 中的要求后，EduAgent 才能安全地从普通 RAG 系统扩展为具备工具生态能力的课程智能体平台。