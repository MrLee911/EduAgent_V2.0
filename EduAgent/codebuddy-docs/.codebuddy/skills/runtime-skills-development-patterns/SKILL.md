# Runtime Skills Development Patterns

```yaml
name: runtime-skills-development-patterns
description: Use when developing runtime Skills, Skill Registry, Skill Executor, Skill permissions, or skill execution audit logs.
```

------

## 1. Skill 目的

本 Skill 用于指导 CodeBuddy 在 EduAgent 项目中开发 **运行时 Skills 系统**。

注意：

```text
codebuddy-docs/skills/
= 给 CodeBuddy 使用的开发规范 Skill

backend/app/skills/
= EduAgent 项目运行时可调用的业务 Skill
```

本文档讨论的是第二类：

```text
backend/app/skills/
```

也就是 EduAgent 系统运行时真正会被 Agent、Service、API 调用的教学业务技能。

运行时 Skill 的目标是把复杂教学能力封装成可注册、可调用、可测试、可审计的能力单元，例如：

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

CodeBuddy 开发 Skills 时，必须保证：

1. Skill 有明确输入 Schema。
2. Skill 有明确输出 Schema。
3. Skill 有权限控制。
4. Skill 可被 Agent Orchestrator 调用。
5. Skill 可调用 MCP Tool。
6. Skill 可调用 RAG 能力。
7. Skill 可调用 LLM。
8. Skill 执行可记录。
9. Skill 失败可降级。
10. Skill 不绕过 Service 层权限边界。

------

## 2. 适用场景

CodeBuddy 在以下场景中应使用本 Skill：

1. 新增 `backend/app/skills/` 目录。
2. 开发 `BaseSkill`。
3. 开发 `SkillRegistry`。
4. 开发 `SkillExecutor`。
5. 开发内置教学 Skill。
6. 开发 Skill 输入输出 Schema。
7. 开发 Skill 权限校验。
8. 开发 Skill 执行记录。
9. 开发 Agent 调用 Skill 的逻辑。
10. 开发 Skill 调用 MCP Tool 的逻辑。
11. 开发 Skill 调用 RAG 的逻辑。
12. 开发 Skill 专用 Prompt。
13. 开发 Skill API。
14. 开发 Skill 测试。
15. 开发前端 Skills 管理页面或课程技能页面。

------

## 3. 核心设计原则

### 3.1 Skill 是业务能力单元，不是普通函数集合

Skill 应封装一个完整业务能力，而不是随意拆分的小函数。

正确示例：

```text
course_qa：基于课程资料回答问题
resource_analysis：分析课程资源摘要和知识点
task_generation：生成教学任务
report_generation：生成教学报告
lesson_design：生成教学设计
study_path：生成学习路径
```

错误示例：

```text
call_llm
format_text
read_file
query_db
get_user
```

这些小函数应放入 Service、工具模块或 MCP Adapter，不应作为业务 Skill 暴露。

------

### 3.2 Skill 必须有输入输出 Schema

每个 Skill 必须声明：

1. 输入字段。
2. 字段类型。
3. 必填字段。
4. 默认值。
5. 输出结构。
6. 错误结构。

禁止让 Skill 接收任意 dict 后随意处理。

错误做法：

```python
async def run(self, input_data: dict):
    ...
```

正确做法：

```python
class TaskGenerationInput(BaseModel):
    topic: str
    task_type: Literal["class_exercise", "homework", "lab_guide"]
    difficulty: Literal["easy", "medium", "hard"]
    additional_instructions: str | None = None
```

------

### 3.3 Skill 必须受权限控制

Skill 执行前必须校验：

1. 用户是否登录。
2. 用户系统角色是否允许。
3. 用户是否属于当前课程。
4. 用户课程角色是否允许。
5. Skill 是否启用。
6. Skill 是否高风险。
7. 输入参数是否试图跨课程访问。

禁止让 LLM 判断用户能不能执行 Skill。

------

### 3.4 Skill 不得绕过 Service 层

推荐链路：

```text
API
→ Service
→ Agent Orchestrator
→ Skill Executor
→ Skill
→ MCP / RAG / LLM
→ Service 落库
```

不推荐链路：

```text
API
→ Skill
→ 直接写数据库
```

对于需要落库的业务，例如问答、任务、报告、教学设计，最终保存应由 Service 层控制。

------

### 3.5 Skill 可以调用 MCP Tool

Skill 不应直接访问所有底层能力。

推荐：

```text
Skill
→ MCPClient
→ search_course_knowledge
→ 返回课程资料
```

而不是：

```text
Skill
→ 直接访问 ChromaDB
→ 直接拼接数据库查询
```

当然，在项目早期阶段，为了简化实现，某些 Skill 可以暂时复用现有 Service 或 RAG 模块，但应保持可替换为 MCP Tool 的结构。

------

### 3.6 Skill 必须可审计

每次 Skill 执行应记录：

1. Skill 名称。
2. 调用用户。
3. 所属课程。
4. 输入摘要。
5. 输出摘要。
6. 执行状态。
7. 执行耗时。
8. 错误信息。
9. AgentRun ID，可选。
10. 调用时间。

不得记录：

1. API Key。
2. JWT。
3. 密码。
4. 数据库连接。
5. 完整系统 Prompt。
6. 高敏感学生隐私全文。
7. 大段完整模型输出，除非业务表本身需要保存。

------

## 4. 推荐目录结构

CodeBuddy 应按以下结构新增运行时 Skills 代码：

```text
backend/app/skills/
├── __init__.py
├── base.py
├── schemas.py
├── registry.py
├── loader.py
├── executor.py
├── exceptions.py
├── builtin/
│   ├── __init__.py
│   ├── course_qa/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   ├── resource_analysis/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   ├── task_generation/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   ├── report_generation/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   ├── code_explanation/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   ├── lesson_design/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   ├── quiz_generation/
│   │   ├── __init__.py
│   │   ├── SKILL.md
│   │   ├── skill.py
│   │   └── prompts.py
│   └── study_path/
│       ├── __init__.py
│       ├── SKILL.md
│       ├── skill.py
│       └── prompts.py
└── custom/
```

说明：

| 文件                   | 作用                                          |
| ---------------------- | --------------------------------------------- |
| `base.py`              | 定义 BaseSkill 抽象基类                       |
| `schemas.py`           | 定义 SkillContext、SkillResult、SkillMetadata |
| `registry.py`          | 定义 SkillRegistry                            |
| `loader.py`            | 加载内置和自定义 Skill                        |
| `executor.py`          | 统一执行 Skill                                |
| `exceptions.py`        | Skill 专用异常                                |
| `builtin/*/SKILL.md`   | 单个 Skill 的说明文档                         |
| `builtin/*/skill.py`   | 单个 Skill 的实现                             |
| `builtin/*/prompts.py` | 单个 Skill 的提示词                           |

------

## 5. 核心 Schema 设计

### 5.1 SkillContext

所有 Skill 执行必须携带上下文。

```python
from pydantic import BaseModel
from typing import Literal
from uuid import UUID


class SkillContext(BaseModel):
    request_id: str
    user_id: UUID
    user_role: Literal["student", "teacher", "admin"]
    course_id: UUID | None = None
    course_role: Literal["student", "teacher"] | None = None
    course_name: str | None = None
    conversation_id: str | None = None
    agent_run_id: UUID | None = None
```

要求：

1. 课程内 Skill 必须有 `course_id`。
2. 教师类 Skill 必须校验 `course_role == "teacher"` 或 `user_role == "admin"`。
3. 学生类 Skill 只能访问自己的数据。
4. 上下文必须来自后端认证和权限校验结果，不得来自前端任意传值。

------

### 5.2 SkillMetadata

```python
from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    name: str
    display_name: str
    description: str
    version: str = "1.0.0"
    enabled: bool = True
    allowed_roles: list[str] = Field(default_factory=list)
    required_course_roles: list[str] = Field(default_factory=list)
    input_schema: dict = Field(default_factory=dict)
    output_schema: dict = Field(default_factory=dict)
    high_risk: bool = False
```

------

### 5.3 SkillResult

```python
from pydantic import BaseModel
from typing import Literal


class SkillResult(BaseModel):
    skill_name: str
    status: Literal["success", "failed", "denied"]
    data: dict | list | str | None = None
    sources: list[dict] = []
    error_message: str | None = None
    metadata: dict | None = None
```

说明：

1. `data` 保存 Skill 的主要输出。
2. `sources` 保存引用来源。
3. `metadata` 保存耗时、模型、Tool 调用数量等摘要。
4. 失败时返回用户可理解的错误。
5. 不返回内部 traceback。

------

### 5.4 SkillRunRequest

如果开放 Skill API，可以使用：

```python
class SkillRunRequest(BaseModel):
    course_id: UUID | None = None
    input: dict
```

------

## 6. BaseSkill 设计

### 6.1 基础接口

```python
from abc import ABC, abstractmethod


class BaseSkill(ABC):
    metadata: SkillMetadata

    @abstractmethod
    async def run(
        self,
        input_data: dict,
        context: SkillContext,
    ) -> SkillResult:
        raise NotImplementedError

    def validate_input(self, input_data: dict) -> None:
        ...

    def validate_permission(self, context: SkillContext) -> None:
        ...
```

------

### 6.2 BaseSkill 要求

每个 Skill 必须：

1. 继承 `BaseSkill`。
2. 定义 `metadata`。
3. 实现 `run()`。
4. 校验输入。
5. 校验权限。
6. 返回 `SkillResult`。
7. 不直接抛出未处理异常给 API 层。
8. 不返回敏感信息。

------

## 7. Skill Registry 设计

### 7.1 基本职责

`SkillRegistry` 负责：

1. 注册 Skill。
2. 获取 Skill。
3. 列出 Skill。
4. 按角色过滤 Skill。
5. 判断 Skill 是否启用。
6. 为 Skill Router 提供可用技能列表。

------

### 7.2 推荐接口

```python
class SkillRegistry:
    def register(self, skill: BaseSkill) -> None:
        ...

    def get(self, skill_name: str) -> BaseSkill:
        ...

    def list_skills(
        self,
        user_role: str,
        course_role: str | None = None,
        include_disabled: bool = False,
    ) -> list[SkillMetadata]:
        ...

    def exists(self, skill_name: str) -> bool:
        ...
```

------

### 7.3 注册示例

```python
registry.register(CourseQASkill())
registry.register(TaskGenerationSkill())
registry.register(ReportGenerationSkill())
registry.register(ResourceAnalysisSkill())
```

------

## 8. Skill Loader 设计

### 8.1 基本职责

`SkillLoader` 负责加载：

1. 内置 Skill。
2. 可选自定义 Skill。
3. 数据库中启用的 Skill 配置。
4. Skill 文档元数据。

------

### 8.2 推荐策略

第一阶段建议只加载内置 Skill：

```text
SKILLS_LOAD_MODE=builtin
```

自定义 Skill 默认关闭：

```text
SKILLS_ALLOW_CUSTOM=false
```

原因：

1. 自定义 Skill 有安全风险。
2. 自定义 Skill 可能绕过权限。
3. 自定义 Skill 可能读取敏感配置。
4. 自定义 Skill 需要额外沙箱和审批。

------

## 9. Skill Executor 设计

### 9.1 基本职责

`SkillExecutor` 是执行 Skill 的统一入口。

职责：

1. 获取 Skill。
2. 检查 Skill 是否启用。
3. 校验用户权限。
4. 校验课程权限。
5. 校验输入 Schema。
6. 执行 Skill。
7. 捕获异常。
8. 记录 SkillRun。
9. 返回标准结果。

------

### 9.2 推荐接口

```python
class SkillExecutor:
    def __init__(self, registry, audit_logger):
        self.registry = registry
        self.audit_logger = audit_logger

    async def run(
        self,
        skill_name: str,
        input_data: dict,
        context: SkillContext,
    ) -> SkillResult:
        ...
```

------

### 9.3 执行流程

```text
Agent / API 发起 Skill 调用
→ SkillExecutor.run()
→ SkillRegistry 获取 Skill
→ 校验 Skill enabled
→ 校验用户角色
→ 校验课程角色
→ 校验输入 Schema
→ 执行 Skill.run()
→ 记录 skill_runs
→ 返回 SkillResult
```

------

## 10. Skill 权限设计

### 10.1 权限维度

Skill 权限至少包含两层：

```text
系统角色 user_role
课程角色 course_role
```

系统角色：

```text
student
teacher
admin
```

课程角色：

```text
student
teacher
```

------

### 10.2 推荐权限表

| Skill               | student | teacher | admin | 说明     |
| ------------------- | ------- | ------- | ----- | -------- |
| `course_qa`         | ✅       | ✅       | ✅     | 课程问答 |
| `study_path`        | ✅ 自己  | ✅ 聚合  | ✅     | 学习路径 |
| `code_explanation`  | ✅ 受限  | ✅       | ✅     | 代码解释 |
| `resource_analysis` | ❌       | ✅       | ✅     | 资源分析 |
| `task_generation`   | ❌       | ✅       | ✅     | 任务生成 |
| `report_generation` | ❌       | ✅       | ✅     | 报告生成 |
| `lesson_design`     | ❌       | ✅       | ✅     | 教学设计 |
| `quiz_generation`   | ❌       | ✅       | ✅     | 测验生成 |

------

### 10.3 权限校验示例

```python
def validate_permission(metadata: SkillMetadata, context: SkillContext) -> None:
    if not metadata.enabled:
        raise SkillPermissionDenied("该技能未启用")

    if context.user_role not in metadata.allowed_roles:
        raise SkillPermissionDenied("当前用户角色无权使用该技能")

    if metadata.required_course_roles:
        if context.course_role not in metadata.required_course_roles:
            raise SkillPermissionDenied("当前课程角色无权使用该技能")
```

------

## 11. 内置 Skill 设计

------

# 11.1 course_qa Skill

用途：

基于当前课程资料回答用户问题。

适用角色：

```text
student
teacher
admin
```

输入：

```python
class CourseQAInput(BaseModel):
    question: str
    conversation_id: str | None = None
    use_history: bool = True
```

输出：

```python
class CourseQAOutput(BaseModel):
    answer: str
    sources: list[dict]
    conversation_id: str
```

调用链路：

```text
course_qa Skill
→ RAG MCP Tool: search_course_knowledge
→ LLM
→ 返回 answer + sources
```

安全要求：

1. 必须限定当前课程。
2. 资料不足时明确说明。
3. 学生作业问题只提供思路，不直接给完整答案。
4. sources 必须结构化。
5. 不跨课程检索。

------

# 11.2 resource_analysis Skill

用途：

分析课程资源摘要、知识点、难度、缺失内容和教学建议。

适用角色：

```text
teacher
admin
```

输入：

```python
class ResourceAnalysisInput(BaseModel):
    resource_ids: list[str]
    analysis_type: Literal["summary", "knowledge_points", "quality_check", "gap_analysis"] = "summary"
```

输出：

```python
class ResourceAnalysisOutput(BaseModel):
    summary: str
    knowledge_points: list[str]
    difficulty_level: str | None = None
    missing_topics: list[str] = []
    duplicate_topics: list[str] = []
    teaching_suggestions: list[str] = []
```

调用链路：

```text
resource_analysis Skill
→ File Resource MCP Tool
→ RAG / LLM
→ 资源分析结果
```

安全要求：

1. 只能分析当前课程资源。
2. 不能分析未 ready 的资源。
3. 不能编造文件内容。
4. 不返回服务器真实文件路径。

------

# 11.3 task_generation Skill

用途：

根据课程资料生成教学任务。

适用角色：

```text
teacher
admin
```

输入：

```python
class TaskGenerationInput(BaseModel):
    topic: str
    task_type: Literal["class_exercise", "homework", "lab_guide"]
    difficulty: Literal["easy", "medium", "hard"]
    additional_instructions: str | None = None
```

输出：

```python
class TaskGenerationOutput(BaseModel):
    title: str
    content: str
    estimated_time: str | None = None
    reference_resources: list[dict] = []
```

调用链路：

```text
task_generation Skill
→ RAG MCP Tool
→ LLM
→ Task Service 保存 draft
```

要求：

1. Skill 只生成结构化任务内容。
2. 保存数据库由 TaskService 完成。
3. 默认生成草稿。
4. reference_resources 格式必须与 API 文档一致。
5. 字段统一使用 `additional_instructions`。

------

# 11.4 report_generation Skill

用途：

生成课程教学报告。

适用角色：

```text
teacher
admin
```

输入：

```python
class ReportGenerationInput(BaseModel):
    report_type: Literal["weekly", "monthly", "semester"]
    start_date: date
    end_date: date
```

输出：

```python
class ReportGenerationOutput(BaseModel):
    title: str
    content: str
    statistics: dict
```

调用链路：

```text
report_generation Skill
→ Course DB MCP Tool
→ Report Analysis MCP Tool
→ LLM
→ Report Service 保存 report
```

要求：

1. 数字必须来自真实数据库统计。
2. 不得编造学生人数、问答数、资源数、任务数。
3. 日期范围必须来自输入参数，不得硬编码。
4. 报告内容使用 Markdown。

------

# 11.5 code_explanation Skill

用途：

解释代码、分析报错、生成学习建议。

适用角色：

```text
student 受限
teacher
admin
```

输入：

```python
class CodeExplanationInput(BaseModel):
    language: str
    code: str
    question: str | None = None
    error_message: str | None = None
    explain_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
```

输出：

```python
class CodeExplanationOutput(BaseModel):
    explanation: str
    key_concepts: list[str]
    step_by_step: list[str] = []
    common_mistakes: list[str] = []
    practice_suggestions: list[str] = []
```

安全要求：

1. 学生侧不直接给完整作业代码。
2. 不运行代码，除非 Code Sandbox 开启并通过权限检查。
3. 不输出危险命令。
4. 不生成恶意代码。
5. 不鼓励绕过课程规则。

------

# 11.6 lesson_design Skill

用途：

生成教学设计、课堂活动和教学流程。

适用角色：

```text
teacher
admin
```

输入：

```python
class LessonDesignInput(BaseModel):
    topic: str
    duration_minutes: int
    student_level: Literal["beginner", "intermediate", "advanced"]
    teaching_goal: str
    additional_instructions: str | None = None
```

输出：

```python
class LessonDesignOutput(BaseModel):
    title: str
    content: str
    reference_resources: list[dict] = []
```

内容应包含：

```text
教学目标
教学重点
教学难点
教学准备
教学流程
课堂活动
课堂练习
教学评价
课后任务
```

------

# 11.7 quiz_generation Skill

用途：

生成测验题、课堂小测、选择题、简答题、编程题。

适用角色：

```text
teacher
admin
```

输入：

```python
class QuizGenerationInput(BaseModel):
    topic: str
    question_types: list[Literal["single_choice", "multiple_choice", "short_answer", "coding"]]
    difficulty: Literal["easy", "medium", "hard"]
    question_count: int = 5
```

输出：

```python
class QuizGenerationOutput(BaseModel):
    title: str
    questions: list[dict]
    reference_resources: list[dict] = []
```

要求：

1. 题目应基于课程资料。
2. 答案解析应清楚。
3. 难度应符合输入要求。
4. 编程题不得过度复杂。

------

# 11.8 study_path Skill

用途：

根据学生学习记录和课程资源生成学习路径。

适用角色：

```text
student
teacher
admin
```

学生侧输入：

```python
class StudyPathInput(BaseModel):
    target_topic: str
```

输出：

```python
class StudyPathOutput(BaseModel):
    current_level: str
    weak_points: list[str]
    recommended_resources: list[dict]
    learning_steps: list[dict]
    practice_suggestions: list[str]
    encouragement: str
```

安全要求：

1. 学生只能分析自己的数据。
2. 教师只能查看聚合分析。
3. 不泄露其他学生问答记录。
4. 推荐资源必须来自当前课程。
5. 表达应积极、具体、可执行。

------

## 12. 每个 Skill 的 SKILL.md 要求

每个运行时 Skill 必须包含独立 `SKILL.md`。

示例路径：

```text
backend/app/skills/builtin/course_qa/SKILL.md
```

每份 `SKILL.md` 至少包含：

```text
# Skill 名称

## 1. 技能定位
## 2. 适用角色
## 3. 适用场景
## 4. 输入参数
## 5. 输出结果
## 6. 可调用工具
## 7. 执行流程
## 8. 安全限制
## 9. 失败处理
## 10. 示例
```

------

## 13. Skill 与 Prompt 的关系

### 13.1 Prompt 存放位置

每个 Skill 的专用 Prompt 应放在：

```text
backend/app/skills/builtin/{skill_name}/prompts.py
```

例如：

```text
backend/app/skills/builtin/task_generation/prompts.py
```

------

### 13.2 Prompt 要求

Prompt 必须包含：

1. 角色定位。
2. 当前课程上下文。
3. 当前用户角色。
4. 输入任务。
5. 可用资料。
6. 输出格式。
7. 安全限制。
8. 不确定时的回答方式。

------

### 13.3 Prompt 不得包含

1. 真实 API Key。
2. JWT。
3. 数据库连接。
4. 系统内部路径。
5. 服务器绝对路径。
6. 用户无权访问的数据。
7. 其他课程资料。

------

## 14. Skill 与 MCP 的关系

### 14.1 推荐关系

```text
Skill
→ MCPClient
→ MCP Tool
→ RAG / Course DB / File Resource / Report Analysis / Code Sandbox
```

------

### 14.2 示例：course_qa

```text
course_qa Skill
→ MCPClient.call_tool("rag_search", "search_course_knowledge")
→ 得到课程资料
→ 构造 Prompt
→ LLM 生成回答
```

------

### 14.3 示例：report_generation

```text
report_generation Skill
→ MCPClient.call_tool("course_db", "get_course_stats")
→ MCPClient.call_tool("report_analysis", "analyze_qa_hotspots")
→ LLM 生成报告
```

------

### 14.4 MCP 调用要求

Skill 调用 MCP Tool 时必须：

1. 传入 `SkillContext`。
2. 继承 `user_id`。
3. 继承 `course_id`。
4. 继承 `agent_run_id`。
5. 关联 `skill_run_id`，如果已经创建。
6. 不传入任意其他课程 ID。
7. 处理 Tool 调用失败。

------

## 15. Skill 执行记录设计

### 15.1 推荐数据库表

```text
skill_runs
```

字段建议：

```text
id
skill_name
user_id
course_id
agent_run_id
input_summary
output_summary
status
latency_ms
error_message
created_at
```

------

### 15.2 input_summary 示例

```json
{
  "topic": "Python 函数",
  "task_type": "homework",
  "difficulty": "medium"
}
```

------

### 15.3 output_summary 示例

```json
{
  "title": "课后作业：Python 函数",
  "content_length": 3200,
  "reference_count": 5
}
```

------

### 15.4 禁止记录

1. API Key。
2. JWT。
3. 明文密码。
4. 完整系统 Prompt。
5. 数据库连接。
6. 完整学生隐私。
7. 服务器真实路径。

------

## 16. Skill API 设计建议

如果需要开放前端 Skill 页面，建议新增：

```text
/api/v1/skills
```

推荐接口：

```text
GET  /api/v1/skills
GET  /api/v1/skills/{skill_name}
POST /api/v1/skills/{skill_name}/run
GET  /api/v1/skills/runs
GET  /api/v1/skills/runs/{run_id}
```

规则：

1. Skill 列表按角色过滤。
2. Skill 详情不返回敏感 Prompt。
3. Skill 运行必须校验权限。
4. 学生不能运行教师专属 Skill。
5. Skill 执行记录必须脱敏。
6. 高风险 Skill 默认不开放给前端直接调用。

------

## 17. 错误处理规范

### 17.1 Skill 专用异常

推荐定义：

```python
class SkillError(Exception):
    pass


class SkillNotFound(SkillError):
    pass


class SkillDisabled(SkillError):
    pass


class SkillPermissionDenied(SkillError):
    pass


class SkillValidationError(SkillError):
    pass


class SkillExecutionError(SkillError):
    pass
```

------

### 17.2 错误返回

Skill 失败时返回：

```json
{
  "skill_name": "resource_analysis",
  "status": "failed",
  "data": null,
  "sources": [],
  "error_message": "资源分析失败，请稍后重试",
  "metadata": {
    "latency_ms": 1200
  }
}
```

不得返回：

```text
完整 traceback
数据库连接
API Key
内部 Prompt
服务器文件路径
```

------

## 18. 测试要求

### 18.1 建议新增测试文件

```text
backend/tests/test_skill_registry.py
backend/tests/test_skill_executor.py
backend/tests/test_course_qa_skill.py
backend/tests/test_task_generation_skill.py
backend/tests/test_report_generation_skill.py
backend/tests/test_resource_analysis_skill.py
backend/tests/test_skill_permissions.py
```

------

### 18.2 必测场景

| 编号       | 测试场景                   | 通过标准                     |
| ---------- | -------------------------- | ---------------------------- |
| SKILL-T-01 | 注册 Skill                 | Registry 可获取 Skill        |
| SKILL-T-02 | 列出 Skill                 | 按角色过滤正确               |
| SKILL-T-03 | 学生执行 course_qa         | 允许                         |
| SKILL-T-04 | 学生执行 task_generation   | 拒绝                         |
| SKILL-T-05 | 教师执行 task_generation   | 允许                         |
| SKILL-T-06 | 教师执行 report_generation | 允许                         |
| SKILL-T-07 | 学生执行 study_path        | 只能访问自己数据             |
| SKILL-T-08 | 输入 Schema 错误           | 返回校验错误                 |
| SKILL-T-09 | MCP Tool 失败              | Skill 返回可理解错误         |
| SKILL-T-10 | 执行日志                   | 写入 skill_runs 或结构化日志 |
| SKILL-T-11 | 敏感信息                   | 输出不包含 API Key / JWT     |
| SKILL-T-12 | 跨课程访问                 | 被拒绝                       |

------

## 19. 常见错误与禁止做法

### 19.1 禁止把 Skill 做成工具后门

错误：

```text
database_query_skill
file_read_skill
shell_command_skill
```

正确：

```text
resource_analysis
report_generation
lesson_design
```

------

### 19.2 禁止在 Skill 中直接信任前端 course_id

错误：

```python
course_id = input_data["course_id"]
```

正确：

```python
course_id = context.course_id
```

------

### 19.3 禁止 Skill 直接保存业务数据

错误：

```text
task_generation Skill 直接写 tasks 表
```

更推荐：

```text
task_generation Skill 返回任务内容
TaskService 负责保存为 draft
```

------

### 19.4 禁止把完整 Prompt 写入执行记录

错误：

```json
{
  "system_prompt": "完整系统提示词..."
}
```

正确：

```json
{
  "prompt_template": "task_generation_v1",
  "input_summary": {
    "topic": "Python 函数"
  }
}
```

------

### 19.5 禁止学生侧直接生成完整作业答案

对于学生的代码解释、作业辅导、问答请求，应提供：

1. 思路。
2. 步骤。
3. 局部示例。
4. 知识点解释。
5. 练习建议。

不应直接提供：

1. 完整可提交作业。
2. 完整实验报告。
3. 完整课程考核答案。
4. 绕过学习过程的内容。

------

## 20. CodeBuddy 开发检查清单

CodeBuddy 完成 Skills 相关开发后，必须检查：

```text
[ ] 是否新增 backend/app/skills/
[ ] 是否定义 SkillContext
[ ] 是否定义 SkillMetadata
[ ] 是否定义 SkillResult
[ ] 是否实现 BaseSkill
[ ] 是否实现 SkillRegistry
[ ] 是否实现 SkillLoader
[ ] 是否实现 SkillExecutor
[ ] 是否实现 Skill 权限校验
[ ] 是否实现 Skill 输入 Schema 校验
[ ] 是否实现 Skill 执行日志
[ ] 是否实现 course_qa Skill
[ ] 是否实现 resource_analysis Skill
[ ] 是否实现 task_generation Skill
[ ] 是否实现 report_generation Skill
[ ] 是否实现 code_explanation Skill
[ ] 是否实现 lesson_design Skill
[ ] 是否实现 quiz_generation Skill
[ ] 是否实现 study_path Skill
[ ] 每个 Skill 是否有 SKILL.md
[ ] 每个 Skill 是否有 prompts.py
[ ] Skill 是否调用 MCPClient 而不是绕过权限
[ ] Skill 是否避免跨课程访问
[ ] Skill 是否避免保存敏感信息
[ ] 学生是否不能执行教师专属 Skill
[ ] 是否新增 skill_runs 表或结构化日志
[ ] 是否新增 Skills API，如需要
[ ] 是否新增 Skills 测试
[ ] 是否同步 04_API接口文档.md
[ ] 是否同步 05_AI智能体行为定义.md
[ ] 是否同步 06_提示词模板.md
[ ] 是否同步 08_CodeBuddy开发任务书.md
```

------

## 21. 最小可交付版本

Skills 第一阶段最小可交付版本应包含：

```text
backend/app/skills/schemas.py
backend/app/skills/base.py
backend/app/skills/registry.py
backend/app/skills/loader.py
backend/app/skills/executor.py
backend/app/skills/builtin/course_qa/
backend/app/skills/builtin/task_generation/
backend/app/skills/builtin/report_generation/
backend/app/skills/builtin/resource_analysis/
```

至少实现以下 Skill：

```text
course_qa
task_generation
report_generation
resource_analysis
```

最小验收：

1. SkillRegistry 可以列出内置 Skill。
2. SkillExecutor 可以执行授权 Skill。
3. 学生可以执行 `course_qa`。
4. 学生不能执行 `task_generation`。
5. 教师可以执行 `task_generation`。
6. 教师可以执行 `report_generation`。
7. 教师可以执行 `resource_analysis`。
8. Skill 可以调用 RAG MCP Tool。
9. Skill 执行有日志。
10. Skill 失败返回可理解错误。
11. Skill 不跨课程访问。
12. Skill 不泄露敏感信息。

------

## 22. 与其他文档的关系

本 Skill 与以下文档配合使用：

| 文档                                     | 关系                                   |
| ---------------------------------------- | -------------------------------------- |
| `01_项目需求规格文档.md`                 | 定义 Skills 业务需求                   |
| `02_技术架构文档.md`                     | 定义 Skills 在整体架构中的位置         |
| `03_数据模型与数据库设计.md`             | 定义 `skill_definitions`、`skill_runs` |
| `04_API接口文档.md`                      | 定义 Skills API                        |
| `05_AI智能体行为定义.md`                 | 定义 Agent 如何选择和调用 Skill        |
| `06_提示词模板.md`                       | 定义 Skill Prompt                      |
| `07_页面流程图.md`                       | 定义课程技能页和 Skills 管理页         |
| `08_CodeBuddy开发任务书.md`              | 定义 Skills 开发任务                   |
| `mcp-tool-development-patterns/SKILL.md` | 定义 Skills 可调用的 MCP 工具体系      |

------

## 23. 本 Skill 总结

CodeBuddy 开发运行时 Skills 时必须牢记：

```text
Skill 是可复用的教学业务能力单元，不是随意函数集合。
```

每个 Skill 必须满足：

```text
有名称
有说明
有输入 Schema
有输出 Schema
有权限
有上下文
有 Prompt
有执行记录
有错误处理
有测试
不跨课程
不泄露敏感信息
不绕过 Service 层
```

推荐开发顺序：

```text
1. 定义 SkillContext / SkillMetadata / SkillResult
2. 实现 BaseSkill
3. 实现 SkillRegistry
4. 实现 SkillExecutor
5. 实现 course_qa Skill
6. 实现 task_generation Skill
7. 实现 report_generation Skill
8. 实现 resource_analysis Skill
9. 接入 MCPClient
10. 增加 skill_runs 审计
11. 增加 Skills API 和测试
12. 再扩展 code_explanation / lesson_design / quiz_generation / study_path
```

完成该 Skill 中的要求后，EduAgent 才能把课程问答、资源分析、任务生成、报告生成、代码辅导、教学设计和学习路径推荐统一封装为可复用、可管理、可审计的运行时 Skills 系统。