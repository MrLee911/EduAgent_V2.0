# 03_frontend-rules.md

## 1. 规则文件用途

本文件是 EduAgent 项目的前端开发规则文件。

文件位置：

```text
.codebuddy/rules/03_frontend-rules.md
```

本文件用于约束 CodeBuddy 在 EduAgent 项目中进行前端页面开发、前端组件开发、路由调整、API 封装、状态管理、权限展示、页面流程修复、AI 输出展示、Markdown 渲染、文件上传、流式问答展示时的行为。

本文件不是完整前端页面设计文档。完整页面流程、接口契约和项目规则应同时阅读：

```text
CODEBUDDY.md
.codebuddy/rules/01_project-overview.md
.codebuddy/rules/02_backend-rules.md
codebuddy-docs/specs/04_API接口文档.md
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
.codebuddy/skills/vue3-tailwind-component-patterns/SKILL.md
```

------

## 2. 前端项目定位

EduAgent 前端不是普通管理后台页面，也不是简单聊天页面。

EduAgent 前端应承担以下职责：

1. 用户登录、注册和认证状态管理。
2. 课程列表、课程详情和课程成员展示。
3. 课程资源上传、批量上传、状态展示和重新处理。
4. 课程知识库问答页面。
5. AI 回答 Markdown 渲染。
6. RAG 引用来源展示。
7. 教学任务生成、查看、发布、归档和删除。
8. 教学报告生成、查看和导出。
9. 课程资源分析页面。
10. 教学设计页面。
11. 学习路径页面。
12. Runtime Skills 执行页面。
13. 代码辅导页面。
14. Agent 执行记录页面。
15. 管理员用户管理页面。
16. 管理员系统设置页面。
17. MCP 管理页面。
18. Skills 管理页面。
19. Agent Runs 审计页面。

前端开发时必须理解：

```text
前端 = 教学业务操作入口 + AI 能力交互界面 + 智能体执行过程展示界面
```

不要把 EduAgent 前端只开发成：

```text
普通登录页面
普通课程列表
普通聊天窗口
普通 CRUD 表格
```

------

## 3. 前端技术栈约束

EduAgent 前端必须继续使用当前技术栈。

### 3.1 必须使用

```text
Vue 3
TypeScript
Vue Router
Pinia
Tailwind CSS
Axios
marked
DOMPurify
lucide
```

### 3.2 不得替换

禁止将当前前端替换为：

1. React。
2. Next.js。
3. Angular。
4. Svelte。
5. Nuxt。
6. 纯 HTML + JavaScript。
7. 其他非当前项目技术栈。

### 3.3 不得破坏

不得破坏：

1. 当前 Vue 3 项目结构。
2. 当前 TypeScript 类型体系。
3. 当前 API 封装方式。
4. 当前 Router 结构。
5. 当前 Pinia 状态管理方式。
6. 当前 Tailwind CSS 风格体系。
7. 当前前后端接口契约。

------

## 4. 推荐前端目录结构

前端代码应保持或逐步整理为以下结构：

```text
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts
│   │   ├── auth.ts
│   │   ├── courses.ts
│   │   ├── resources.ts
│   │   ├── qa.ts
│   │   ├── tasks.ts
│   │   ├── reports.ts
│   │   ├── skills.ts
│   │   ├── mcp.ts
│   │   ├── agent.ts
│   │   ├── analysis.ts
│   │   ├── lessonDesigns.ts
│   │   ├── studyPath.ts
│   │   └── codeTutor.ts
│   │
│   ├── components/
│   │   ├── common/
│   │   ├── layout/
│   │   ├── course/
│   │   ├── resource/
│   │   ├── qa/
│   │   ├── task/
│   │   ├── report/
│   │   ├── agent/
│   │   ├── skills/
│   │   └── mcp/
│   │
│   ├── router/
│   │   └── index.ts
│   │
│   ├── stores/
│   │   ├── auth.ts
│   │   ├── course.ts
│   │   ├── qa.ts
│   │   ├── task.ts
│   │   ├── report.ts
│   │   ├── agent.ts
│   │   └── ui.ts
│   │
│   ├── types/
│   │   ├── auth.ts
│   │   ├── course.ts
│   │   ├── resource.ts
│   │   ├── qa.ts
│   │   ├── task.ts
│   │   ├── report.ts
│   │   ├── agent.ts
│   │   ├── skill.ts
│   │   └── mcp.ts
│   │
│   ├── views/
│   │   ├── LoginView.vue
│   │   ├── RegisterView.vue
│   │   ├── HomeView.vue
│   │   ├── CourseListView.vue
│   │   ├── CourseDetailView.vue
│   │   ├── CourseResourcesView.vue
│   │   ├── CourseQAView.vue
│   │   ├── CourseTasksView.vue
│   │   ├── TaskDetailView.vue
│   │   ├── CourseReportsView.vue
│   │   ├── ReportDetailView.vue
│   │   ├── CourseAnalysisView.vue
│   │   ├── CourseLessonDesignView.vue
│   │   ├── CourseStudyPathView.vue
│   │   ├── CourseSkillsView.vue
│   │   ├── CourseCodeTutorView.vue
│   │   ├── CourseAgentRunsView.vue
│   │   └── admin/
│   │       ├── AdminUsersView.vue
│   │       ├── AdminSettingsView.vue
│   │       ├── AdminSkillsView.vue
│   │       ├── AdminMCPView.vue
│   │       ├── AdminMCPToolCallsView.vue
│   │       └── AdminAgentRunsView.vue
│   │
│   ├── utils/
│   │   ├── format.ts
│   │   ├── markdown.ts
│   │   ├── permission.ts
│   │   └── error.ts
│   │
│   ├── App.vue
│   └── main.ts
│
├── package.json
├── vite.config.ts
├── tailwind.config.js
└── tsconfig.json
```

如果当前项目尚未完全符合该结构，应采用**增量整理**方式，不得删除现有前端后重建。

------

## 5. 前端分层规则

前端代码应遵守以下分层：

```text
View 页面
  ↓
Component 组件
  ↓
Store 状态管理
  ↓
API Wrapper
  ↓
Axios Client
  ↓
Backend API
```

### 5.1 View 层职责

View 页面负责：

1. 页面级布局。
2. 页面级数据加载。
3. 路由参数读取。
4. 调用 Store 或 API。
5. 组合业务组件。
6. 处理页面级 loading / empty / error。
7. 页面级权限展示。
8. 页面跳转。

View 页面不得：

1. 写大量重复 API 请求逻辑。
2. 写复杂数据转换逻辑。
3. 写复杂权限判断逻辑。
4. 硬编码大量接口路径。
5. 直接拼接后端响应字段而不使用类型。
6. 直接渲染未清洗 HTML。

### 5.2 Component 层职责

Component 组件负责：

1. 展示具体 UI。
2. 接收 props。
3. 发出 emits。
4. 保持可复用。
5. 保持低耦合。
6. 不直接依赖过多业务上下文。

组件应优先拆分为：

```text
common 通用组件
layout 布局组件
course 课程组件
resource 资源组件
qa 问答组件
task 任务组件
report 报告组件
agent 智能体组件
skills 技能组件
mcp 工具组件
```

### 5.3 Store 层职责

Pinia Store 负责：

1. 登录状态。
2. 当前用户。
3. Token 管理。
4. 当前课程上下文。
5. 需要跨页面共享的数据。
6. 全局 UI 状态。
7. 必要的缓存状态。

Store 不应成为所有业务逻辑的堆积处。

如果逻辑只属于单个页面，可放在页面的组合式函数或页面内部。

### 5.4 API Wrapper 层职责

API wrapper 负责：

1. 统一封装后端接口。
2. 隐藏 Axios 细节。
3. 统一接口路径。
4. 统一请求参数。
5. 统一响应类型。
6. 统一错误处理入口。

页面不应直接写：

```ts
axios.get('/api/v1/...')
```

推荐写法：

```ts
const resources = await resourceApi.listResources(courseId)
```

------

## 6. 路由设计规则

### 6.1 路由类型

前端路由至少分为：

1. 公开路由。
2. 登录后路由。
3. 课程内路由。
4. 管理员路由。
5. 404 路由。

### 6.2 推荐路由

推荐路由结构：

```text
/login
/register
/
/courses
/courses/:courseId
/courses/:courseId/resources
/courses/:courseId/qa
/courses/:courseId/tasks
/courses/:courseId/tasks/:taskId
/courses/:courseId/reports
/courses/:courseId/reports/:reportId
/courses/:courseId/analysis
/courses/:courseId/lesson-design
/courses/:courseId/study-path
/courses/:courseId/skills
/courses/:courseId/code-tutor
/courses/:courseId/agent-runs
/settings

/admin/users
/admin/settings
/admin/skills
/admin/skills/runs
/admin/mcp
/admin/mcp/tool-calls
/admin/agent-runs
```

### 6.3 路由权限规则

路由守卫必须处理：

1. 未登录访问受保护页面。
2. 已登录访问登录页。
3. 普通用户访问管理员页面。
4. 未加入课程访问课程内页面。
5. 课程角色不满足页面要求。
6. Token 过期。
7. 用户信息加载失败。

前端路由守卫只用于体验优化，不是安全边界。

后端必须重新校验权限。

### 6.4 路由参数规则

课程内页面统一使用：

```text
courseId
```

任务详情页面使用：

```text
taskId
```

报告详情页面使用：

```text
reportId
```

不得同一项目中混用：

```text
id
course_id
courseID
courseId
```

前端路由参数名、API 参数名和类型定义应保持清晰映射。

------

## 7. API 封装规则

### 7.1 API 文件命名

每个业务模块应有独立 API 文件：

```text
src/api/auth.ts
src/api/courses.ts
src/api/resources.ts
src/api/qa.ts
src/api/tasks.ts
src/api/reports.ts
src/api/skills.ts
src/api/mcp.ts
src/api/agent.ts
```

### 7.2 API 路径规则

前端 API 路径必须与后端一致。

当前项目需要特别注意：

```text
批量上传接口
```

后端如果是：

```text
POST /api/v1/courses/{course_id}/resources/upload-batch
```

前端不得写成：

```text
/resources/batch-upload
```

任务生成字段如果后端是：

```text
additional_instructions
```

前端不得写成：

```text
extra_instructions
```

除非后端已经明确兼容两个字段。

### 7.3 Axios Client 规则

应有统一 Axios Client，例如：

```text
src/api/client.ts
```

统一处理：

1. baseURL。
2. Authorization Header。
3. access token 注入。
4. refresh token 逻辑。
5. 401 处理。
6. 403 处理。
7. 通用错误提示。
8. 请求超时。
9. 文件上传 Content-Type。
10. 流式请求特殊处理。

页面不得重复写 token 注入逻辑。

### 7.4 响应类型规则

所有 API 函数应有 TypeScript 返回类型。

示例：

```ts
export async function getCourse(courseId: string): Promise<CourseDetail> {
  const { data } = await client.get<CourseDetail>(`/courses/${courseId}`)
  return data
}
```

禁止：

```ts
export async function getCourse(courseId: string): Promise<any> {
  return client.get(`/courses/${courseId}`)
}
```

除非接口确实返回动态结构，且需要在注释中说明原因。

------

## 8. TypeScript 类型规则

### 8.1 类型文件位置

推荐类型文件位置：

```text
src/types/auth.ts
src/types/course.ts
src/types/resource.ts
src/types/qa.ts
src/types/task.ts
src/types/report.ts
src/types/agent.ts
src/types/skill.ts
src/types/mcp.ts
```

### 8.2 类型命名规则

推荐命名：

```text
User
LoginRequest
LoginResponse
Course
CourseDetail
Resource
ResourceStatus
QARequest
QAResponse
Task
TaskGenerateRequest
TaskGenerateResponse
Report
AgentRun
AgentStep
SkillDefinition
SkillRun
MCPServer
MCPToolCall
```

### 8.3 禁止滥用 any

禁止在核心业务类型中大量使用：

```ts
any
```

如果必须使用动态结构，应优先使用：

```ts
Record<string, unknown>
unknown
```

并在使用前做类型判断。

### 8.4 枚举值一致性

前端状态枚举必须与后端一致。

资源状态：

```ts
type ResourceStatus =
  | 'uploading'
  | 'parsing'
  | 'chunking'
  | 'embedding'
  | 'ready'
  | 'failed'
```

任务状态、报告状态、Agent 状态、Skill 状态、MCP Tool Call 状态也应保持一致。

不得前端写一套、后端写一套。

------

## 9. 页面状态规则

所有需要请求数据的页面都必须处理以下状态：

1. loading。
2. empty。
3. error。
4. success。
5. permission denied。
6. network error。
7. retry。
8. partial success，若存在批量操作。

### 9.1 Loading 状态

数据加载时应展示 loading，不应空白。

### 9.2 Empty 状态

数据为空时应明确提示用户下一步操作。

示例：

```text
当前课程还没有上传资料，请先上传课程资源。
```

### 9.3 Error 状态

接口失败时应展示用户可理解的错误，不应直接展示后端 traceback。

示例：

```text
资源加载失败，请稍后重试。
```

### 9.4 Retry 机制

对于资源处理状态、AI 生成状态、异步任务状态，应提供刷新或重试入口。

------

## 10. 权限展示规则

前端需要根据用户角色和课程角色控制页面展示，但这不是安全边界。

### 10.1 前端可做的权限控制

前端可以控制：

1. 菜单是否显示。
2. 按钮是否显示。
3. 页面入口是否显示。
4. 禁用某些操作。
5. 展示权限不足提示。

### 10.2 前端不能做的事情

前端不能替代后端权限。

禁止：

1. 只隐藏按钮但后端不校验。
2. 学生通过手动调用接口完成教师操作。
3. 管理页面只靠前端路由守卫保护。
4. MCP 管理只靠前端页面隐藏。
5. Agent 审计数据只靠前端过滤。

### 10.3 角色展示规则

典型规则：

| 功能            | 学生 | 教师     | 管理员   |
| --------------- | ---- | -------- | -------- |
| 查看课程        | 可   | 可       | 可       |
| 上传课程资源    | 不可 | 可       | 可       |
| 删除课程资源    | 不可 | 可       | 可       |
| 课程问答        | 可   | 可       | 可       |
| 生成教学任务    | 不可 | 可       | 可       |
| 发布教学任务    | 不可 | 可       | 可       |
| 查看任务        | 可   | 可       | 可       |
| 生成教学报告    | 不可 | 可       | 可       |
| 查看 Agent Runs | 受限 | 课程内可 | 平台级可 |
| MCP 管理        | 不可 | 不可     | 可       |
| Skills 管理     | 不可 | 不可     | 可       |

------

## 11. 表单设计规则

前端表单必须包含：

1. 字段标签。
2. 必填提示。
3. 输入校验。
4. 错误提示。
5. 提交 loading。
6. 禁止重复提交。
7. 成功提示。
8. 失败提示。

### 11.1 表单字段名

表单字段名必须与 API Schema 对齐。

例如任务生成：

```ts
interface TaskGenerateRequest {
  task_type: string
  difficulty: string
  additional_instructions?: string
}
```

不得写成：

```ts
interface TaskGenerateRequest {
  taskType: string
  difficulty: string
  extraInstructions?: string
}
```

除非 API wrapper 做了明确转换。

### 11.2 表单提交规则

提交时必须：

1. 校验必填字段。
2. 设置 submitting 状态。
3. 禁用提交按钮。
4. 捕获异常。
5. 展示错误。
6. 成功后更新页面数据。
7. 必要时跳转页面。

------

## 12. 文件上传页面规则

课程资源上传是 EduAgent 的核心入口之一。

### 12.1 上传能力

上传页面应支持：

1. 单文件上传。
2. 批量文件上传。
3. 上传进度展示。
4. 上传失败提示。
5. 上传后状态轮询。
6. 文件处理状态展示。
7. 失败资源重新处理。
8. 删除资源。
9. 查看资源详情。

### 12.2 文件类型一致性

前端允许上传的文件类型必须与后端一致。

如果后端支持：

```text
pdf
docx
pptx
md
txt
```

前端不得额外显示支持：

```text
xlsx
```

除非后端已经实现 xlsx parser。

### 12.3 上传接口一致性

前端上传接口必须与后端文档一致。

重点检查：

```text
POST /api/v1/courses/{course_id}/resources/upload
POST /api/v1/courses/{course_id}/resources/upload-batch
```

不得自行发明路径。

### 12.4 状态轮询

资源上传后应轮询资源状态。

状态包括：

```text
uploading
parsing
chunking
embedding
ready
failed
```

前端应根据状态展示：

1. 正在上传。
2. 正在解析。
3. 正在切片。
4. 正在向量化。
5. 处理完成。
6. 处理失败。
7. 可重新处理。

------

## 13. 课程问答页面规则

课程问答页面是 EduAgent 的核心 AI 页面。

### 13.1 问答页面必须支持

1. 输入问题。
2. 发送问题。
3. 展示 AI 回答。
4. 展示 Markdown。
5. 展示代码块。
6. 展示引用来源。
7. 展示生成中状态。
8. 展示失败提示。
9. 支持历史记录。
10. 支持清空会话，若后端支持。
11. 支持反馈，若后端支持。

### 13.2 流式输出规则

如果使用 SSE 或 fetch stream，前端必须处理：

1. 连接开始。
2. token 增量输出。
3. sources 到达。
4. 结束事件。
5. 错误事件。
6. 连接中断。
7. 用户取消。
8. 超时。

不得在流式输出失败时让页面卡死。

### 13.3 Markdown 安全渲染

AI 回答可能包含 Markdown。

必须使用：

```text
marked
DOMPurify
```

处理 Markdown 和 HTML。

禁止直接使用：

```vue
<div v-html="rawHtml"></div>
```

而不做清洗。

### 13.4 引用来源展示

RAG 回答 sources 应清晰展示。

来源信息建议包括：

1. 资源名称。
2. 页码或章节。
3. 片段摘要。
4. 相似度或相关度。
5. 可点击查看资源详情，若支持。

不得展示伪造来源。

如果没有 sources，应明确显示：

```text
当前回答未返回引用来源。
```

------

## 14. 教学任务页面规则

任务模块应支持：

1. 任务生成。
2. 任务列表。
3. 任务详情。
4. 任务编辑。
5. 任务重新生成。
6. 任务发布。
7. 任务归档。
8. 任务删除。

### 14.1 字段一致性

任务生成请求字段必须与后端一致。

重点字段：

```text
task_type
difficulty
additional_instructions
```

不得使用：

```text
extra_instructions
```

除非 API wrapper 明确转换。

### 14.2 生成状态

AI 生成任务时必须展示：

1. 正在生成。
2. 生成成功。
3. 生成失败。
4. 重新生成。
5. 保存草稿，若后端支持。
6. 发布任务。

### 14.3 权限控制

学生通常不能生成、编辑、发布、删除任务。

教师和管理员可以执行对应管理操作。

前端隐藏按钮的同时，后端也必须校验权限。

------

## 15. 教学报告页面规则

报告模块应支持：

1. 报告生成。
2. 报告列表。
3. 报告详情。
4. 报告导出。
5. 报告删除，若后端支持。
6. 生成失败提示。
7. Markdown 或结构化报告展示。

### 15.1 前后端一致性

如果前端展示删除按钮，后端必须有对应删除 API。

如果后端没有删除 API，前端不得显示删除按钮，或必须标记为暂不可用。

### 15.2 报告内容展示

报告内容可能包含：

1. Markdown。
2. 课程总结。
3. 学习情况分析。
4. 资源使用情况。
5. 教学建议。
6. 后续改进建议。

Markdown 渲染必须安全清洗。

------

## 16. Agent Runs 页面规则

Agent Runs 页面用于展示智能体执行过程。

### 16.1 页面应展示

1. agent_run_id。
2. 触发用户。
3. 课程。
4. 任务类型。
5. 意图。
6. 状态。
7. 开始时间。
8. 结束时间。
9. 耗时。
10. 错误信息。
11. Step 列表。
12. Tool 调用。
13. Skill 调用。
14. MCP 调用。

### 16.2 状态展示

Agent 状态建议包括：

```text
pending
running
success
failed
cancelled
```

前端应使用统一 Badge 或 Tag 展示状态。

### 16.3 审计数据展示限制

学生不应看到平台级 Agent 审计数据。

教师只能查看自己课程范围内的 Agent 执行记录。

管理员可查看平台级执行记录。

------

## 17. Skills 页面规则

Skills 页面分为课程内 Skills 使用页面和管理员 Skills 管理页面。

### 17.1 课程内 Skills 页面

应支持：

1. 查看当前课程可用 Skills。
2. 运行某个 Skill。
3. 填写 Skill 输入参数。
4. 展示 Skill 输出结果。
5. 查看 Skill 执行记录。
6. 展示执行失败原因。

### 17.2 管理员 Skills 页面

应支持：

1. Skill 列表。
2. Skill 启用 / 禁用。
3. Skill 描述。
4. 输入 Schema。
5. 输出 Schema。
6. 权限范围。
7. Skill Runs 审计。

------

## 18. MCP 页面规则

MCP 页面主要面向管理员。

### 18.1 MCP 管理页面

应支持：

1. MCP Server 列表。
2. MCP Tool 列表。
3. Server 启用 / 禁用状态。
4. Tool 名称。
5. Tool 描述。
6. Tool 输入 Schema。
7. Tool 输出 Schema。
8. 风险等级。
9. 权限要求。

### 18.2 MCP Tool Calls 页面

应展示：

1. 调用时间。
2. 调用用户。
3. 课程 ID。
4. Server 名称。
5. Tool 名称。
6. 输入摘要。
7. 输出摘要。
8. 状态。
9. 耗时。
10. 错误信息。

### 18.3 安全展示

前端不得展示：

1. API Key。
2. Token。
3. 数据库密码。
4. `.env` 内容。
5. 未脱敏的工具参数。
6. 服务器真实敏感路径。

------

## 19. 管理员页面规则

管理员页面应统一放在：

```text
src/views/admin/
```

管理员页面至少包括：

1. 用户管理。
2. 系统设置。
3. Skills 管理。
4. MCP 管理。
5. MCP Tool Calls。
6. Agent Runs。
7. Skill Runs。

### 19.1 管理员权限

前端应使用路由守卫阻止非管理员进入管理员页面。

但后端必须再次校验管理员权限。

### 19.2 管理页面交互

管理页面必须处理：

1. 搜索。
2. 筛选。
3. 分页。
4. 状态标签。
5. 操作确认。
6. 错误提示。
7. 空数据提示。

------

## 20. UI 与样式规则

### 20.1 Tailwind CSS

样式优先使用 Tailwind CSS。

禁止大量内联 style。

除非组件确实需要动态样式，否则不要写复杂内联样式。

### 20.2 组件风格

界面风格应保持：

1. 简洁。
2. 清晰。
3. 教学场景友好。
4. 重点突出。
5. 状态明确。
6. 操作可理解。

### 20.3 图标

图标优先使用 lucide。

不得混用多个图标库，除非项目已明确引入。

### 20.4 颜色语义

状态颜色应保持一致：

| 状态    | 语义         |
| ------- | ------------ |
| success | 成功、完成   |
| warning | 警告、处理中 |
| error   | 错误、失败   |
| info    | 信息、提示   |
| muted   | 次要信息     |

不要为同一状态在不同页面使用完全不同颜色。

------

## 21. 可访问性与用户体验规则

前端页面应尽量满足：

1. 按钮有明确文本。
2. 表单有 label。
3. 错误提示可读。
4. loading 不阻塞整个系统。
5. 长文本可折叠。
6. AI 输出可复制。
7. 代码块可复制。
8. 表格内容过长可截断或展开。
9. 移动端至少不出现严重布局错乱。
10. 危险操作需要确认。

危险操作包括：

1. 删除课程。
2. 删除资源。
3. 删除任务。
4. 删除报告。
5. 禁用用户。
6. 禁用 MCP Server。
7. 禁用 Skill。

------

## 22. 前端错误处理规则

### 22.1 错误来源

前端必须处理：

1. 网络错误。
2. 401 未登录。
3. 403 无权限。
4. 404 数据不存在。
5. 422 参数错误。
6. 500 服务端错误。
7. AI 生成失败。
8. 文件上传失败。
9. 流式连接中断。
10. 异步任务失败。

### 22.2 错误展示

错误提示应面向用户，不要直接展示技术细节。

错误示例：

```text
请求失败，请稍后重试。
```

比下面更好：

```text
AxiosError: Request failed with status code 500
```

### 22.3 登录失效

如果收到 401：

1. 尝试 refresh token，若项目支持。
2. refresh 失败则清除登录状态。
3. 跳转登录页。
4. 提示用户重新登录。

不得无限循环 refresh。

------

## 23. 前后端契约一致性规则

这是 EduAgent 前端最重要的规则之一。

每次修改前端 API 时必须检查：

1. 后端路由是否存在。
2. HTTP Method 是否一致。
3. 路径参数是否一致。
4. Query 参数是否一致。
5. Request Body 字段是否一致。
6. Response 字段是否一致。
7. 枚举值是否一致。
8. 分页格式是否一致。
9. 错误响应是否可处理。

### 23.1 当前已知风险

需要重点检查：

1. 批量上传路径：
   - 后端可能是 `/upload-batch`
   - 前端可能写成 `/batch-upload`
2. 任务生成字段：
   - 后端应使用 `additional_instructions`
   - 前端可能使用 `extra_instructions`
3. 登录响应：
   - 前端可能依赖 `refresh_token`
   - 后端响应必须确认是否返回
4. 报告删除：
   - 前端可能有删除 UI
   - 后端必须确认是否有删除 API
5. Admin 用户更新：
   - 前端请求体和后端参数位置必须一致

------

## 24. 前端测试和构建规则

修改前端后，应尽量运行：

```bash
cd frontend
npm run build
```

如果项目配置了 lint 或 test，也应运行：

```bash
cd frontend
npm run lint
npm run test
```

如果无法运行，必须说明：

1. 未运行原因。
2. 可能风险。
3. 手动验证方式。

不得声称未运行的构建已经通过。

------

## 25. 前端文档同步规则

### 25.1 修改页面或路由

同步：

```text
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
```

### 25.2 修改 API 调用

同步：

```text
codebuddy-docs/specs/04_API接口文档.md
src/api/
src/types/
```

### 25.3 修改 AI 展示逻辑

同步：

```text
codebuddy-docs/specs/05_AI智能体行为定义.md
codebuddy-docs/specs/06_提示词模板.md
```

### 25.4 修改管理页面

同步：

```text
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
```

------

## 26. 前端禁止事项清单

CodeBuddy 前端开发时禁止：

1. 删除前端项目后重建。
2. 把 Vue 改成 React。
3. 把 TypeScript 改成纯 JavaScript。
4. 绕过 API wrapper 直接到处写 Axios 路径。
5. 大量使用 `any`。
6. 前端字段名和后端 Schema 不一致。
7. 页面调用不存在的 API。
8. 不处理 loading / empty / error。
9. 直接渲染未经清洗的 HTML。
10. 把前端权限当成安全边界。
11. 在前端硬编码真实 API Key。
12. 在前端暴露 JWT Secret。
13. 在前端写死生产环境地址。
14. 提交 `node_modules`。
15. 声称未运行的 build 已经通过。
16. 用 mock 页面冒充完整功能。
17. 只改页面不检查 API 文档。
18. 只改 API wrapper 不检查后端路由。
19. 删除已有页面功能但不说明原因。
20. 引入大型 UI 框架替代当前设计体系。

------

## 27. 前端任务执行流程

CodeBuddy 执行前端任务时，应按以下流程：

```text
1. 判断任务类型
2. 阅读 CODEBUDDY.md
3. 阅读本规则文件
4. 阅读页面流程文档
5. 阅读 API 文档
6. 检查现有前端代码
7. 检查后端 API 是否存在
8. 制定最小修改方案
9. 修改页面 / 组件 / API wrapper / types
10. 运行 build 或说明无法运行原因
11. 同步相关文档
12. 输出修改说明和风险
```

### 27.1 判断是否需要后端同步

如果前端需要新接口，但后端不存在，应明确指出：

```text
当前前端需求需要后端新增接口。
```

不要在前端写假接口路径。

### 27.2 判断是否需要类型同步

如果 API 响应字段变化，必须同步：

```text
src/types/
```

### 27.3 判断是否需要页面文档同步

如果新增页面、删除页面、修改路由、修改页面流程，必须同步：

```text
codebuddy-docs/specs/07_页面流程图与前端页面设计规范.md
```

------

## 28. 前端输出要求

完成前端任务后，必须说明：

1. 修改了哪些页面。
2. 修改了哪些组件。
3. 修改了哪些 API wrapper。
4. 修改了哪些 TypeScript 类型。
5. 是否影响路由。
6. 是否影响权限展示。
7. 是否影响后端 API 契约。
8. 是否同步了文档。
9. 是否运行了 `npm run build`。
10. 如果没有运行，说明原因。
11. 是否存在剩余风险。

不得只回答：

```text
已完成
```

必须给出可审查的修改说明。

------

## 29. 最终原则

EduAgent 前端必须保持：

```text
清晰
稳定
安全
可维护
可扩展
可验证
```

所有前端修改都必须优先保证：

1. 页面流程正确。
2. 前后端接口一致。
3. 权限展示合理。
4. 用户状态完整。
5. AI 输出安全。
6. RAG sources 可追溯。
7. Agent 执行过程可理解。
8. 错误提示清晰。
9. 构建可通过。
10. 文档同步完整。