# 04 API 接口文档

> 项目名称：EduAgent 课程资源与教学任务智能体
> 文档类型：API 接口设计文档
> 适用对象：CodeBuddy / AI 编程助手 / 后端开发 / 前端开发 / Agent 开发 / MCP 开发 / Skills 开发 / 测试人员
> 对应代码：`backend/app/api/`、`backend/app/schemas/`、`backend/app/services/`、`frontend/src/api/`
> 文档版本：v2.0
> 优化日期：2026-06-10

------

## 1. 文档目的

本文档用于定义 EduAgent 项目的后端 API 设计，包括：

1. 当前已实现的基础业务 API。
2. 当前已实现但需要修复的一致性问题。
3. 新版课程智能体平台需要新增的 Skills API。
4. 新版课程智能体平台需要新增的 MCP API。
5. 新版课程智能体平台需要新增的 Agent 执行记录 API。
6. 资源分析、教学设计、学习路径等智能体能力 API。
7. 前后端接口字段一致性要求。
8. CodeBuddy 修改 API 时必须遵守的规则。

新版 EduAgent 的定位已经从：

```text
课程管理系统 + RAG 问答助手
```

升级为：

```text
课程智能体平台
= 课程业务系统
+ RAG 知识库
+ MCP 工具生态
+ Skills 技能系统
+ Agent Orchestrator
+ 多智能体协作
+ 执行审计
```

因此，API 不仅要支持课程、资源、问答、任务、报告，还要逐步支持：

```text
Skills 管理与调用
MCP Server / Tool 管理
Agent 执行记录查询
课程资源分析
教学设计生成
学习路径推荐
代码辅导
智能体能力配置
```

------

## 2. API 基础约定

### 2.1 服务地址

本地开发默认地址：

```text
http://localhost:8000
```

API 统一前缀：

```text
/api/v1
```

完整示例：

```text
http://localhost:8000/api/v1/auth/login
```

------

### 2.2 认证方式

受保护接口统一使用 JWT Bearer Token。

请求头：

```http
Authorization: Bearer <access_token>
```

------

### 2.3 Content-Type

JSON 请求：

```http
Content-Type: application/json
```

文件上传：

```http
Content-Type: multipart/form-data
```

SSE 流式问答：

```http
Accept: text/event-stream
```

------

### 2.4 统一响应结构

普通接口建议统一返回：

```json
{
  "success": true,
  "data": {},
  "message": "操作成功"
}
```

错误响应建议统一返回：

```json
{
  "success": false,
  "error": {
    "type": "validation_error",
    "message": "参数校验失败",
    "details": {}
  }
}
```

------

### 2.5 常见 HTTP 状态码

| 状态码 | 说明                |
| ------ | ------------------- |
| `200`  | 请求成功            |
| `201`  | 创建成功            |
| `202`  | 已接受异步任务      |
| `400`  | 参数错误            |
| `401`  | 未登录或 Token 无效 |
| `403`  | 无权限              |
| `404`  | 资源不存在          |
| `409`  | 资源冲突            |
| `422`  | 请求体校验失败      |
| `500`  | 服务端错误          |

------

## 3. API 模块总览

### 3.1 当前已实现模块

| 模块 | 路由前缀                                | 说明                             | 状态                                |
| ---- | --------------------------------------- | -------------------------------- | ----------------------------------- |
| 认证 | `/api/v1/auth`                          | 注册、登录、刷新 Token、当前用户 | 已实现，需补 refresh_token 一致性   |
| 课程 | `/api/v1/courses`                       | 课程创建、加入、成员管理         | 已实现                              |
| 资源 | `/api/v1/courses/{course_id}/resources` | 上传、列表、搜索、处理状态       | 已实现，需修复批量上传路径          |
| 问答 | `/api/v1/courses/{course_id}/qa`        | 非流式问答、流式问答、历史、反馈 | 已实现，需补 conversation_id 持久化 |
| 任务 | `/api/v1/courses/{course_id}/tasks`     | 任务生成、发布、归档、删除       | 已实现，需统一字段                  |
| 报告 | `/api/v1/courses/{course_id}/reports`   | 报告生成、列表、详情、导出       | 已实现，PDF 导出需明确边界          |
| 管理 | `/api/v1/admin`                         | 用户管理、系统设置               | 已实现，更新用户参数需统一          |

------

### 3.2 新版智能体平台扩展模块

| 模块           | 路由前缀                                                     | 说明                              | 状态     |
| -------------- | ------------------------------------------------------------ | --------------------------------- | -------- |
| Skills         | `/api/v1/skills`                                             | Skills 列表、详情、运行、执行记录 | 规划新增 |
| MCP 管理       | `/api/v1/admin/mcp`                                          | MCP Server、Tool、调用记录管理    | 规划新增 |
| Agent 执行记录 | `/api/v1/admin/agent-runs`、`/api/v1/courses/{course_id}/agent-runs` | Agent 执行审计                    | 规划新增 |
| 资源分析       | `/api/v1/courses/{course_id}/analysis`                       | 资源摘要、知识点、资料缺口分析    | 规划新增 |
| 教学设计       | `/api/v1/courses/{course_id}/lesson-designs`                 | 教学设计生成、列表、详情          | 规划新增 |
| 学习路径       | `/api/v1/courses/{course_id}/study-path`                     | 学生学习路径推荐                  | 规划新增 |
| 代码辅导       | `/api/v1/courses/{course_id}/code-tutor`                     | 代码解释、错误分析                | 规划新增 |

------

## 4. 权限约定

### 4.1 系统角色

```text
student
teacher
admin
```

------

### 4.2 课程内角色

```text
student
teacher
```

------

### 4.3 权限原则

1. 未登录用户只能访问登录和注册接口。
2. 学生只能访问自己加入课程的数据。
3. 教师只能管理自己课程的数据。
4. 管理员可以访问管理接口。
5. 所有课程内接口必须校验 `course_id`。
6. 前端权限只是体验层，后端必须最终校验。
7. Agent、Skill、MCP 调用不能绕过权限校验。
8. MCP Tool 调用前必须校验用户角色和课程角色。
9. 权限必须由代码判断，不能交给 LLM 判断。

------

## 5. 认证 API

路由前缀：

```text
/api/v1/auth
```

------

### 5.1 用户注册

```http
POST /api/v1/auth/register
```

请求体：

```json
{
  "username": "student01",
  "email": "student01@example.com",
  "password": "123456",
  "role": "student",
  "display_name": "学生01"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "student01",
    "email": "student01@example.com",
    "role": "student",
    "display_name": "学生01",
    "is_active": true,
    "created_at": "2026-06-10T10:00:00"
  },
  "message": "注册成功"
}
```

规则：

1. 普通用户只能注册 `student` 或 `teacher`。
2. 不允许普通注册创建 `admin`。
3. 用户名唯一。
4. 邮箱唯一。
5. 密码必须哈希存储。

------

### 5.2 用户登录

```http
POST /api/v1/auth/login
```

请求体：

```json
{
  "username": "student01",
  "password": "123456"
}
```

推荐响应：

```json
{
  "success": true,
  "data": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": {
      "id": "uuid",
      "username": "student01",
      "email": "student01@example.com",
      "role": "student",
      "display_name": "学生01",
      "is_active": true
    }
  },
  "message": "登录成功"
}
```

当前需修复：

```text
前端 client.ts 支持 refresh_token 自动刷新，但后端登录响应可能未返回 refresh_token。
必须统一为登录接口返回 refresh_token。
```

------

### 5.3 刷新 Token

```http
POST /api/v1/auth/refresh
```

请求体：

```json
{
  "refresh_token": "jwt-refresh-token"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "access_token": "new-access-token",
    "refresh_token": "new-refresh-token",
    "token_type": "bearer",
    "expires_in": 1800
  },
  "message": "刷新成功"
}
```

要求：

1. 必须校验 token 类型为 refresh。
2. refresh_token 过期后返回 401。
3. 用户被禁用后刷新失败。
4. 前端刷新失败后自动退出登录。

------

### 5.4 获取当前用户

```http
GET /api/v1/auth/me
```

权限：

```text
登录用户
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "username": "student01",
    "email": "student01@example.com",
    "role": "student",
    "display_name": "学生01",
    "is_active": true
  }
}
```

------

### 5.5 修改当前用户资料

```http
PATCH /api/v1/auth/me
```

请求体：

```json
{
  "display_name": "新的显示名称",
  "email": "new_email@example.com",
  "password": "new_password"
}
```

要求：

1. 允许修改显示名称。
2. 允许修改邮箱。
3. 允许修改密码。
4. 修改密码时必须重新哈希。
5. 邮箱不能重复。

------

### 5.6 退出登录

```http
POST /api/v1/auth/logout
```

说明：

1. 前端必须清理 access_token、refresh_token、用户信息。
2. 后端 Token 黑名单机制可作为后续增强。
3. 当前阶段即使后端不做黑名单，也必须返回成功响应。

------

## 6. 课程 API

路由前缀：

```text
/api/v1/courses
```

------

### 6.1 创建课程

```http
POST /api/v1/courses
```

权限：

```text
teacher / admin
```

请求体：

```json
{
  "name": "Python 程序设计",
  "description": "面向初学者的 Python 课程",
  "semester": "2026 春"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "Python 程序设计",
    "code": "ABC123",
    "description": "面向初学者的 Python 课程",
    "semester": "2026 春",
    "teacher_id": "uuid",
    "status": "active"
  }
}
```

------

### 6.2 获取课程列表

```http
GET /api/v1/courses
```

权限：

```text
登录用户
```

查询参数：

| 参数        | 类型   | 必填 | 说明              |
| ----------- | ------ | ---- | ----------------- |
| `page`      | int    | 否   | 页码              |
| `page_size` | int    | 否   | 每页数量          |
| `status`    | string | 否   | active / archived |
| `keyword`   | string | 否   | 搜索关键词        |

规则：

1. 学生只能看到自己加入的课程。
2. 教师只能看到自己创建或加入的课程。
3. 管理员可以看到全部课程。

------

### 6.3 获取课程详情

```http
GET /api/v1/courses/{course_id}
```

权限：

```text
课程成员 / admin
```

------

### 6.4 更新课程

```http
PATCH /api/v1/courses/{course_id}
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "name": "Python 程序设计进阶",
  "description": "更新后的课程描述",
  "semester": "2026 春"
}
```

------

### 6.5 删除课程

```http
DELETE /api/v1/courses/{course_id}
```

权限：

```text
课程教师 / admin
```

建议请求体：

```json
{
  "confirm_name": "Python 程序设计"
}
```

要求：

1. 删除课程必须二次确认。
2. 删除课程应清理课程成员、资源、chunks、问答、任务、报告。
3. ChromaDB collection 也应清理。
4. 生产环境可考虑归档优先于物理删除。

------

### 6.6 通过课程码加入课程

```http
POST /api/v1/courses/join
```

权限：

```text
登录用户
```

请求体：

```json
{
  "course_code": "ABC123"
}
```

要求：

1. 课程码必须存在。
2. 用户不能重复加入同一课程。
3. 归档课程是否允许加入由业务策略决定。

------

### 6.7 获取课程成员

```http
GET /api/v1/courses/{course_id}/members
```

权限：

```text
课程教师 / admin
```

------

### 6.8 添加课程成员

```http
POST /api/v1/courses/{course_id}/members
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "username_or_email": "student01@example.com",
  "role": "student"
}
```

------

### 6.9 学生退出课程

```http
DELETE /api/v1/courses/{course_id}/members/me
```

权限：

```text
课程成员
```

------

### 6.10 移除课程成员

```http
DELETE /api/v1/courses/{course_id}/members/{member_id}
```

权限：

```text
课程教师 / admin
```

------

## 7. 课程资源 API

路由前缀：

```text
/api/v1/courses/{course_id}/resources
```

------

### 7.1 上传单个资源

```http
POST /api/v1/courses/{course_id}/resources/upload
```

权限：

```text
课程教师 / admin
```

请求类型：

```text
multipart/form-data
```

字段：

| 字段   | 类型 | 必填 | 说明     |
| ------ | ---- | ---- | -------- |
| `file` | File | 是   | 上传文件 |

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "file_name": "Python基础.pdf",
    "file_type": "pdf",
    "file_size": 1024000,
    "status": "uploading",
    "file_url": "/files/resources/xxx.pdf"
  },
  "message": "上传成功，正在处理"
}
```

------

### 7.2 批量上传资源

```http
POST /api/v1/courses/{course_id}/resources/upload-batch
```

权限：

```text
课程教师 / admin
```

请求类型：

```text
multipart/form-data
```

字段：

| 字段    | 类型   | 必填 | 说明         |
| ------- | ------ | ---- | ------------ |
| `files` | File[] | 是   | 上传文件列表 |

当前必须修复：

```text
前端曾使用 /resources/batch-upload。
后端真实路径应统一为 /resources/upload-batch。
```

------

### 7.3 获取资源列表

```http
GET /api/v1/courses/{course_id}/resources
```

权限：

```text
课程成员 / admin
```

查询参数：

| 参数        | 类型   | 必填 | 说明         |
| ----------- | ------ | ---- | ------------ |
| `page`      | int    | 否   | 页码         |
| `page_size` | int    | 否   | 每页数量     |
| `status`    | string | 否   | 资源状态     |
| `file_type` | string | 否   | 文件类型     |
| `keyword`   | string | 否   | 文件名关键词 |

------

### 7.4 搜索资源

```http
GET /api/v1/courses/{course_id}/resources/search
```

权限：

```text
课程成员 / admin
```

查询参数建议：

| 参数    | 类型   | 必填 | 说明       |
| ------- | ------ | ---- | ---------- |
| `q`     | string | 是   | 搜索关键词 |
| `top_k` | int    | 否   | 返回数量   |

当前必须注意：

```text
后端路由中 /resources/search 必须定义在 /resources/{resource_id} 之前，
否则 search 可能被当成 resource_id 解析。
```

------

### 7.5 获取资源详情

```http
GET /api/v1/courses/{course_id}/resources/{resource_id}
```

权限：

```text
课程成员 / admin
```

------

### 7.6 获取资源处理状态

```http
GET /api/v1/courses/{course_id}/resources/{resource_id}/status
```

权限：

```text
课程成员 / admin
```

响应：

```json
{
  "success": true,
  "data": {
    "resource_id": "uuid",
    "status": "embedding",
    "chunk_count": 20,
    "error_message": null
  }
}
```

------

### 7.7 重新处理资源

```http
POST /api/v1/courses/{course_id}/resources/{resource_id}/reprocess
```

权限：

```text
课程教师 / admin
```

------

### 7.8 删除资源

```http
DELETE /api/v1/courses/{course_id}/resources/{resource_id}
```

权限：

```text
课程教师 / admin
```

要求：

1. 删除资源记录。
2. 删除本地文件或对象存储文件。
3. 删除 chunks。
4. 删除 ChromaDB 向量。
5. 删除或标记资源分析结果。

------

## 8. 智能问答 API

路由前缀：

```text
/api/v1/courses/{course_id}/qa
```

------

### 8.1 非流式问答

```http
POST /api/v1/courses/{course_id}/qa/ask
```

权限：

```text
课程成员 / admin
```

请求体：

```json
{
  "question": "列表推导式是什么意思？",
  "conversation_id": "uuid",
  "use_history": true
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "conversation_id": "uuid",
    "question": "列表推导式是什么意思？",
    "answer": "列表推导式是……",
    "sources": [
      {
        "resource_id": "uuid",
        "resource_name": "Python基础.pdf",
        "chunk_id": "uuid",
        "chunk_index": 3,
        "score": 0.91,
        "text_preview": "引用片段..."
      }
    ],
    "created_at": "2026-06-10T10:00:00"
  }
}
```

需求：

1. 必须限定当前课程。
2. 必须返回 sources。
3. 必须保存 qa_records。
4. 需要补充 `conversation_id` 数据库字段。
5. 后续应由 `CourseQAAgent` + `course_qa` Skill 实现。

------

### 8.2 流式问答

```http
POST /api/v1/courses/{course_id}/qa/ask-stream
```

权限：

```text
课程成员 / admin
```

请求体：

```json
{
  "question": "列表推导式是什么意思？",
  "conversation_id": "uuid",
  "use_history": true
}
```

SSE 事件：

```text
event: thinking
data: {"message":"正在检索课程资料"}

event: sources
data: {"sources":[...]}

event: token
data: {"content":"列表"}

event: done
data: {"qa_id":"uuid","conversation_id":"uuid"}

event: error
data: {"message":"生成失败"}
```

要求：

1. SSE 格式必须与前端 `useSSE` 保持一致。
2. Nginx 不能缓存 SSE。
3. 生成失败时必须返回 error 事件。
4. 流式完成后必须能查询历史记录。

------

### 8.3 获取问答历史

```http
GET /api/v1/courses/{course_id}/qa/history
```

权限：

```text
课程成员 / admin
```

查询参数：

| 参数              | 类型   | 必填 | 说明     |
| ----------------- | ------ | ---- | -------- |
| `page`            | int    | 否   | 页码     |
| `page_size`       | int    | 否   | 每页数量 |
| `conversation_id` | string | 否   | 会话 ID  |

规则：

1. 学生只能看自己的问答历史。
2. 教师是否能看课程聚合问答，需要按产品策略限制。
3. 管理员可按审计需求查看。

------

### 8.4 获取问答详情

```http
GET /api/v1/courses/{course_id}/qa/history/{qa_id}
```

------

### 8.5 问答反馈

```http
POST /api/v1/courses/{course_id}/qa/history/{qa_id}/feedback
```

请求体：

```json
{
  "feedback": "like"
}
```

反馈值：

```text
like
dislike
none
```

------

### 8.6 清空对话上下文

```http
DELETE /api/v1/courses/{course_id}/qa/conversation/{conversation_id}
```

说明：

1. 用于清理 Redis 对话记忆。
2. 不一定物理删除 qa_records。
3. 后续需要统一 Redis key 与数据库 conversation_id。

------

## 9. 教学任务 API

路由前缀：

```text
/api/v1/courses/{course_id}/tasks
```

------

### 9.1 生成教学任务

```http
POST /api/v1/courses/{course_id}/tasks/generate
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "topic": "Python 函数",
  "task_type": "homework",
  "difficulty": "medium",
  "additional_instructions": "包含选择题和编程题"
}
```

当前必须修复：

```text
前端字段曾使用 extra_instructions。
后端字段应统一为 additional_instructions。
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "课后作业：Python 函数",
    "task_type": "homework",
    "topic": "Python 函数",
    "difficulty": "medium",
    "estimated_time": "45分钟",
    "content": "# Markdown 任务内容",
    "reference_resources": [],
    "status": "draft"
  }
}
```

后续目标：

```text
Task Service
→ Agent Orchestrator
→ task_generation Skill
→ RAG MCP Tool
→ LLM
→ Service 保存 task draft
```

------

### 9.2 获取任务列表

```http
GET /api/v1/courses/{course_id}/tasks
```

权限：

```text
课程成员 / admin
```

查询参数：

| 参数        | 类型   | 必填 | 说明                                  |
| ----------- | ------ | ---- | ------------------------------------- |
| `status`    | string | 否   | draft / published / archived          |
| `task_type` | string | 否   | class_exercise / homework / lab_guide |
| `page`      | int    | 否   | 页码                                  |
| `page_size` | int    | 否   | 每页数量                              |

规则：

1. 学生只能看到 `published`。
2. 教师可以看到全部状态。
3. 管理员可以看到全部状态。

------

### 9.3 获取任务详情

```http
GET /api/v1/courses/{course_id}/tasks/{task_id}
```

------

### 9.4 更新任务

```http
PATCH /api/v1/courses/{course_id}/tasks/{task_id}
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "title": "新的任务标题",
  "content": "# 修改后的 Markdown",
  "difficulty": "medium",
  "estimated_time": "60分钟"
}
```

------

### 9.5 重新生成任务

```http
POST /api/v1/courses/{course_id}/tasks/{task_id}/regenerate
```

权限：

```text
课程教师 / admin
```

------

### 9.6 发布任务

```http
POST /api/v1/courses/{course_id}/tasks/{task_id}/publish
```

权限：

```text
课程教师 / admin
```

------

### 9.7 归档任务

```http
POST /api/v1/courses/{course_id}/tasks/{task_id}/archive
```

权限：

```text
课程教师 / admin
```

------

### 9.8 删除任务

```http
DELETE /api/v1/courses/{course_id}/tasks/{task_id}
```

权限：

```text
课程教师 / admin
```

------

## 10. 教学报告 API

路由前缀：

```text
/api/v1/courses/{course_id}/reports
```

------

### 10.1 生成报告

```http
POST /api/v1/courses/{course_id}/reports/generate
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "report_type": "weekly",
  "start_date": "2026-06-01",
  "end_date": "2026-06-07"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "Python 程序设计周报",
    "report_type": "weekly",
    "start_date": "2026-06-01",
    "end_date": "2026-06-07",
    "content": "# Markdown 报告内容",
    "statistics": {}
  }
}
```

后续目标：

```text
Report Service
→ Agent Orchestrator
→ report_generation Skill
→ Course DB / Report Analysis MCP Tools
→ LLM
→ Service 保存 report
```

------

### 10.2 获取报告列表

```http
GET /api/v1/courses/{course_id}/reports
```

权限：

```text
课程教师 / admin
```

查询参数：

| 参数          | 类型   | 必填 | 说明                        |
| ------------- | ------ | ---- | --------------------------- |
| `report_type` | string | 否   | weekly / monthly / semester |
| `page`        | int    | 否   | 页码                        |
| `page_size`   | int    | 否   | 每页数量                    |

------

### 10.3 获取报告详情

```http
GET /api/v1/courses/{course_id}/reports/{report_id}
```

权限：

```text
课程教师 / admin
```

------

### 10.4 导出报告

```http
GET /api/v1/courses/{course_id}/reports/{report_id}/export
```

权限：

```text
课程教师 / admin
```

查询参数：

| 参数     | 类型   | 必填 | 说明         |
| -------- | ------ | ---- | ------------ |
| `format` | string | 否   | `md` / `pdf` |

当前边界：

1. Markdown 导出应作为稳定能力。
2. PDF 导出当前可能是 HTML 兜底，不是生产级 PDF。
3. 前端应对 PDF 导出失败做友好提示。

------

### 10.5 删除报告，规划接口

```http
DELETE /api/v1/courses/{course_id}/reports/{report_id}
```

状态：

```text
规划功能，当前后端如果未实现，则前端不应展示删除报告按钮。
```

权限：

```text
课程教师 / admin
```

------

## 11. 管理后台 API

路由前缀：

```text
/api/v1/admin
```

权限：

```text
admin
```

------

### 11.1 获取用户列表

```http
GET /api/v1/admin/users
```

查询参数：

| 参数        | 类型    | 必填 | 说明                      |
| ----------- | ------- | ---- | ------------------------- |
| `page`      | int     | 否   | 页码                      |
| `page_size` | int     | 否   | 每页数量                  |
| `role`      | string  | 否   | student / teacher / admin |
| `is_active` | boolean | 否   | 是否启用                  |
| `keyword`   | string  | 否   | 用户名或邮箱              |

------

### 11.2 创建用户

```http
POST /api/v1/admin/users
```

请求体：

```json
{
  "username": "teacher02",
  "email": "teacher02@example.com",
  "password": "123456",
  "role": "teacher",
  "display_name": "教师02"
}
```

------

### 11.3 更新用户

```http
PATCH /api/v1/admin/users/{user_id}
```

推荐统一为 JSON Body：

```json
{
  "role": "teacher",
  "is_active": true,
  "display_name": "教师02"
}
```

当前需修复：

```text
前端 adminApi.updateUser() 使用 JSON Body。
如果后端当前使用 Query 参数，应改为接收 JSON Body。
```

------

### 11.4 获取系统设置

```http
GET /api/v1/admin/settings
```

要求：

1. 不返回真实 API Key。
2. 不返回真实 JWT Secret。
3. 密钥类字段必须脱敏。

------

### 11.5 更新系统设置

```http
PUT /api/v1/admin/settings
```

说明：

1. 当前阶段可以只做有限配置更新。
2. 如果不持久化，必须在接口响应或文档中说明。
3. 不建议通过前端直接修改真实模型密钥。

------

## 12. Skills API，规划新增

路由前缀：

```text
/api/v1/skills
```

说明：

1. Skills 是 EduAgent 的运行时教学能力单元。
2. 第一阶段可以只由 Agent 内部调用。
3. 如果前端需要展示 Skills 或手动运行 Skill，则开放以下 API。
4. Skill 权限必须由后端校验。

------

### 12.1 获取可用 Skills

```http
GET /api/v1/skills
```

权限：

```text
登录用户
```

规则：

1. 学生只看到学生可用 Skill。
2. 教师看到教学类 Skill。
3. 管理员看到全部 Skill。

响应：

```json
{
  "success": true,
  "data": [
    {
      "name": "course_qa",
      "display_name": "课程问答",
      "description": "基于课程资料进行问答",
      "enabled": true,
      "allowed_roles": ["student", "teacher", "admin"]
    }
  ]
}
```

------

### 12.2 获取 Skill 详情

```http
GET /api/v1/skills/{skill_name}
```

权限：

```text
登录用户，且该用户有权限查看该 Skill
```

响应：

```json
{
  "success": true,
  "data": {
    "name": "task_generation",
    "display_name": "教学任务生成",
    "description": "根据课程资料生成教学任务",
    "input_schema": {},
    "output_schema": {},
    "allowed_roles": ["teacher", "admin"],
    "enabled": true
  }
}
```

------

### 12.3 运行 Skill

```http
POST /api/v1/skills/{skill_name}/run
```

权限：

```text
登录用户，且具备该 Skill 权限
```

请求体通用结构：

```json
{
  "course_id": "uuid",
  "input": {}
}
```

响应：

```json
{
  "success": true,
  "data": {
    "skill_run_id": "uuid",
    "skill_name": "resource_analysis",
    "status": "success",
    "result": {},
    "sources": [],
    "metadata": {
      "latency_ms": 1200,
      "tool_calls": []
    }
  }
}
```

重要要求：

1. 后端必须校验 `course_id` 权限。
2. 后端必须校验 Skill 权限。
3. 不能让前端直接运行高风险 Skill。
4. Skill 执行必须记录 `skill_runs` 或结构化日志。

------

### 12.4 获取 Skill 执行记录

```http
GET /api/v1/skills/runs
```

权限：

```text
admin 查看全部
teacher 查看自己课程范围
student 默认不可查看或只看自己的
```

查询参数：

| 参数         | 类型   | 必填 | 说明             |
| ------------ | ------ | ---- | ---------------- |
| `course_id`  | string | 否   | 课程 ID          |
| `skill_name` | string | 否   | Skill 名称       |
| `status`     | string | 否   | success / failed |
| `page`       | int    | 否   | 页码             |
| `page_size`  | int    | 否   | 每页数量         |

------

### 12.5 获取 Skill 执行详情

```http
GET /api/v1/skills/runs/{run_id}
```

权限：

```text
admin 或对应课程教师
```

------

## 13. MCP 管理 API，规划新增

路由前缀：

```text
/api/v1/admin/mcp
```

权限：

```text
admin
```

说明：

1. MCP 管理接口只允许管理员访问。
2. 普通用户不能直接管理 MCP Server。
3. 普通用户不能直接调用 MCP Tool。
4. Agent / Skill 内部调用 MCP Tool 必须经过后端权限检查。

------

### 13.1 获取 MCP Server 列表

```http
GET /api/v1/admin/mcp/servers
```

响应：

```json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "rag_search",
      "description": "课程知识库检索工具",
      "transport": "internal",
      "enabled": true,
      "allowed_roles": ["student", "teacher", "admin"]
    }
  ]
}
```

------

### 13.2 创建 MCP Server 配置

```http
POST /api/v1/admin/mcp/servers
```

请求体：

```json
{
  "name": "rag_search",
  "description": "课程知识库检索工具",
  "transport": "internal",
  "endpoint": null,
  "enabled": true,
  "allowed_roles": ["student", "teacher", "admin"],
  "config": {}
}
```

要求：

1. `config` 不得保存真实密钥。
2. 外部 MCP Server 的密钥应通过环境变量或安全密钥管理系统配置。
3. 高风险 Server 默认关闭。

------

### 13.3 更新 MCP Server

```http
PATCH /api/v1/admin/mcp/servers/{server_id}
```

------

### 13.4 删除 MCP Server

```http
DELETE /api/v1/admin/mcp/servers/{server_id}
```

要求：

1. 不建议物理删除有调用记录的 Server。
2. 可优先设置 `enabled=false`。

------

### 13.5 获取 MCP Tool 列表

```http
GET /api/v1/admin/mcp/tools
```

查询参数：

| 参数          | 类型    | 必填 | 说明            |
| ------------- | ------- | ---- | --------------- |
| `server_name` | string  | 否   | MCP Server 名称 |
| `enabled`     | boolean | 否   | 是否启用        |

响应：

```json
{
  "success": true,
  "data": [
    {
      "server_name": "rag_search",
      "tool_name": "search_course_knowledge",
      "description": "检索当前课程知识库",
      "input_schema": {},
      "output_schema": {},
      "allowed_roles": ["student", "teacher", "admin"]
    }
  ]
}
```

------

### 13.6 获取 MCP Tool 调用记录

```http
GET /api/v1/admin/mcp/tool-calls
```

查询参数：

| 参数          | 类型   | 必填 | 说明                                |
| ------------- | ------ | ---- | ----------------------------------- |
| `course_id`   | string | 否   | 课程 ID                             |
| `server_name` | string | 否   | Server 名称                         |
| `tool_name`   | string | 否   | Tool 名称                           |
| `status`      | string | 否   | success / failed / denied / timeout |
| `page`        | int    | 否   | 页码                                |
| `page_size`   | int    | 否   | 每页数量                            |

要求：

1. 不返回敏感参数全文。
2. 不返回服务器真实路径。
3. 不返回 API Key。
4. 只返回 `arguments_summary` 和 `result_summary`。

------

### 13.7 获取 MCP Tool 调用详情

```http
GET /api/v1/admin/mcp/tool-calls/{call_id}
```

权限：

```text
admin
```

------

## 14. Agent 执行记录 API，规划新增

### 14.1 管理员获取全局 Agent 执行记录

```http
GET /api/v1/admin/agent-runs
```

权限：

```text
admin
```

查询参数：

| 参数         | 类型   | 必填 | 说明             |
| ------------ | ------ | ---- | ---------------- |
| `course_id`  | string | 否   | 课程 ID          |
| `agent_type` | string | 否   | Agent 类型       |
| `intent`     | string | 否   | 意图             |
| `status`     | string | 否   | success / failed |
| `page`       | int    | 否   | 页码             |
| `page_size`  | int    | 否   | 每页数量         |

响应：

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "agent_type": "course_qa",
        "course_id": "uuid",
        "user_id": "uuid",
        "intent": "course_qa",
        "selected_skill": "course_qa",
        "status": "success",
        "step_count": 8,
        "latency_ms": 2300,
        "created_at": "2026-06-10T10:00:00"
      }
    ],
    "total": 1
  }
}
```

------

### 14.2 获取 Agent 执行详情

```http
GET /api/v1/admin/agent-runs/{run_id}
```

权限：

```text
admin
```

响应应包含：

1. AgentRun 基础信息。
2. AgentSteps。
3. SkillCalls 摘要。
4. MCPToolCalls 摘要。
5. GuardrailChecks 摘要。
6. 错误信息。

禁止返回：

1. 完整系统 Prompt。
2. API Key。
3. JWT。
4. 数据库连接。
5. 敏感学生隐私全文。

------

### 14.3 教师查看课程内 Agent 执行记录

```http
GET /api/v1/courses/{course_id}/agent-runs
```

权限：

```text
课程教师 / admin
```

规则：

1. 教师只能查看自己课程的 Agent 执行记录。
2. 学生默认不能查看该接口。
3. 返回内容应脱敏。

------

### 14.4 获取课程内 Agent 执行详情

```http
GET /api/v1/courses/{course_id}/agent-runs/{run_id}
```

权限：

```text
课程教师 / admin
```

------

## 15. 资源分析 API，规划新增

路由前缀：

```text
/api/v1/courses/{course_id}/analysis
```

------

### 15.1 分析课程资源

```http
POST /api/v1/courses/{course_id}/analysis/resources
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "resource_ids": ["uuid"],
  "analysis_type": "summary"
}
```

`analysis_type` 可选：

```text
summary
knowledge_points
quality_check
gap_analysis
```

响应：

```json
{
  "success": true,
  "data": {
    "skill_run_id": "uuid",
    "analysis_type": "summary",
    "summary": "资源摘要",
    "knowledge_points": [],
    "difficulty_level": "medium",
    "missing_topics": [],
    "duplicate_topics": [],
    "teaching_suggestions": []
  }
}
```

后端目标链路：

```text
ResourceAnalysis API
→ resource_analysis Skill
→ File Resource MCP Tool
→ RAG / LLM
→ 返回分析结果
```

------

### 15.2 获取资源分析记录

```http
GET /api/v1/courses/{course_id}/analysis/resources
```

权限：

```text
课程教师 / admin
```

------

### 15.3 获取资源分析详情

```http
GET /api/v1/courses/{course_id}/analysis/resources/{analysis_id}
```

权限：

```text
课程教师 / admin
```

------

## 16. 教学设计 API，规划新增

路由前缀：

```text
/api/v1/courses/{course_id}/lesson-designs
```

------

### 16.1 生成教学设计

```http
POST /api/v1/courses/{course_id}/lesson-designs/generate
```

权限：

```text
课程教师 / admin
```

请求体：

```json
{
  "topic": "Python 函数",
  "duration_minutes": 45,
  "student_level": "beginner",
  "teaching_goal": "让学生掌握函数定义和调用",
  "additional_instructions": "包含课堂互动和练习"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "title": "教学设计：Python 函数",
    "topic": "Python 函数",
    "duration_minutes": 45,
    "content": "# Markdown 教学设计",
    "reference_resources": [],
    "status": "draft",
    "skill_run_id": "uuid"
  }
}
```

后端目标链路：

```text
LessonDesign API
→ lesson_design Skill
→ RAG MCP Tool
→ LLM
→ 保存 lesson_designs
```

------

### 16.2 获取教学设计列表

```http
GET /api/v1/courses/{course_id}/lesson-designs
```

权限：

```text
课程教师 / admin
```

------

### 16.3 获取教学设计详情

```http
GET /api/v1/courses/{course_id}/lesson-designs/{lesson_design_id}
```

权限：

```text
课程教师 / admin
```

------

### 16.4 更新教学设计

```http
PATCH /api/v1/courses/{course_id}/lesson-designs/{lesson_design_id}
```

权限：

```text
课程教师 / admin
```

------

### 16.5 删除教学设计

```http
DELETE /api/v1/courses/{course_id}/lesson-designs/{lesson_design_id}
```

权限：

```text
课程教师 / admin
```

------

## 17. 学习路径 API，规划新增

路由前缀：

```text
/api/v1/courses/{course_id}/study-path
```

------

### 17.1 生成学习路径

```http
POST /api/v1/courses/{course_id}/study-path/generate
```

权限：

```text
课程成员 / admin
```

请求体：

```json
{
  "target_topic": "面向对象编程"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "current_level": "基础一般",
    "weak_points": ["类和对象的关系"],
    "recommended_resources": [
      {
        "resource_id": "uuid",
        "resource_name": "Python面向对象.pdf",
        "reason": "该资源覆盖类和对象基础概念"
      }
    ],
    "learning_steps": [
      {
        "step": 1,
        "title": "复习类的定义",
        "description": "阅读课程资料第 2 章",
        "estimated_time": "30分钟"
      }
    ],
    "practice_suggestions": [],
    "encouragement": "继续保持练习，会逐步掌握。"
  }
}
```

规则：

1. 学生只能生成自己的学习路径。
2. 教师可以查看课程聚合学习建议，但不能随意查看单个学生隐私明细。
3. 推荐资源必须来自当前课程。
4. 不泄露其他学生数据。

------

### 17.2 获取我的学习路径记录

```http
GET /api/v1/courses/{course_id}/study-path/my
```

权限：

```text
课程成员
```

------

### 17.3 教师查看课程学习路径概览，规划

```http
GET /api/v1/courses/{course_id}/study-path/overview
```

权限：

```text
课程教师 / admin
```

说明：

1. 返回聚合数据。
2. 不返回学生隐私全文。
3. 可用于学情分析。

------

## 18. 代码辅导 API，规划新增

路由前缀：

```text
/api/v1/courses/{course_id}/code-tutor
```

------

### 18.1 解释代码

```http
POST /api/v1/courses/{course_id}/code-tutor/explain
```

权限：

```text
课程成员 / admin
```

请求体：

```json
{
  "language": "python",
  "code": "print([x * x for x in range(10)])",
  "question": "这段代码是什么意思？",
  "explain_level": "beginner"
}
```

响应：

```json
{
  "success": true,
  "data": {
    "explanation": "这段代码用于生成 0 到 9 的平方列表并打印。",
    "key_concepts": ["列表推导式", "range 函数"],
    "step_by_step": [],
    "common_mistakes": [],
    "practice_suggestions": [],
    "skill_run_id": "uuid"
  }
}
```

规则：

1. 学生侧只提供解释和引导。
2. 不直接生成完整可提交作业答案。
3. 不执行代码，除非代码沙箱启用且通过权限检查。

------

### 18.2 分析代码报错

```http
POST /api/v1/courses/{course_id}/code-tutor/debug
```

权限：

```text
课程成员 / admin
```

请求体：

```json
{
  "language": "python",
  "code": "print(x)",
  "error_message": "NameError: name 'x' is not defined"
}
```

------

### 18.3 运行代码，默认关闭或受限

```http
POST /api/v1/courses/{course_id}/code-tutor/run
```

权限：

```text
默认仅 teacher / admin，学生侧需单独配置
```

说明：

1. 该接口属于高风险能力。
2. 默认可以不开放。
3. 如开放，必须使用沙箱。
4. 必须限制运行时间、内存、网络和文件系统。
5. 不得执行危险系统命令。

------

## 19. 前端 API 封装要求

当前前端 API 目录：

```text
frontend/src/api/
├── client.ts
├── admin.ts
├── qa.ts
├── reports.ts
├── resources.ts
└── tasks.ts
```

建议新增：

```text
frontend/src/api/skills.ts
frontend/src/api/mcp.ts
frontend/src/api/agent.ts
frontend/src/api/analysis.ts
frontend/src/api/lessonDesigns.ts
frontend/src/api/studyPath.ts
frontend/src/api/codeTutor.ts
```

------

### 19.1 必须修复的前端 API 问题

| 优先级 | 文件           | 当前问题                                     | 修复建议                        |
| ------ | -------------- | -------------------------------------------- | ------------------------------- |
| P0     | `resources.ts` | 批量上传路径使用 `batch-upload`              | 改为 `upload-batch`             |
| P0     | `tasks.ts`     | 生成任务字段使用 `extra_instructions`        | 改为 `additional_instructions`  |
| P0     | `client.ts`    | 自动刷新依赖 `refresh_token`                 | 后端登录接口返回 refresh_token  |
| P1     | `admin.ts`     | 更新用户使用 JSON Body，但后端可能接收 Query | 后端改为 JSON Body              |
| P1     | `reports.ts`   | 前端有删除报告 UI，但后端可能无接口          | 移除按钮或补接口                |
| P1     | `resources.ts` | 搜索参数可能不一致                           | 统一为 `q` / `top_k` 或后端兼容 |

------

## 20. API 安全要求

### 20.1 认证安全

1. 受保护接口必须校验 JWT。
2. Token 过期返回 401。
3. 用户禁用后不能继续访问。
4. refresh_token 必须单独校验。
5. 登出时前端必须清理 Token。

------

### 20.2 课程权限安全

1. 所有 `/courses/{course_id}/...` 接口必须校验课程成员。
2. 上传、删除资源必须校验教师权限。
3. 生成任务、报告、教学设计必须校验教师权限。
4. 学生只能查看已发布任务。
5. 学生不能查看教学报告。
6. 学生不能访问其他课程数据。

------

### 20.3 Skills 安全

1. Skill 执行前必须校验角色权限。
2. Skill 执行前必须校验课程权限。
3. 高风险 Skill 不应开放给学生。
4. Skill 不能绕过 Service 层权限。
5. Skill 执行结果不得泄露敏感信息。

------

### 20.4 MCP 安全

1. MCP 管理接口仅 admin 可访问。
2. 普通用户不能直接调用 MCP Tool。
3. MCP Tool 只能由后端 Agent / Skill 调用。
4. MCP Tool 调用前必须校验权限。
5. MCP Tool 不得执行原始 SQL。
6. MCP Tool 不得返回服务器真实路径。
7. MCP Tool 调用必须记录审计日志。

------

### 20.5 Agent 安全

1. Agent 不能绕过 API 权限。
2. Agent 不能跨课程检索。
3. Agent 不能调用未授权 Tool。
4. Agent 执行记录必须脱敏。
5. 生产链路不得使用 Mock LLM 节点。

------

## 21. 当前已知 API 问题与修复优先级

### 21.1 P0 问题

| 编号      | 问题                               | 影响                      | 修复                             |
| --------- | ---------------------------------- | ------------------------- | -------------------------------- |
| API-P0-01 | `/auth/login` 未返回 refresh_token | 前端自动刷新不可用        | 登录响应补充 refresh_token       |
| API-P0-02 | 批量上传路径不一致                 | 批量上传失败              | 统一为 `/upload-batch`           |
| API-P0-03 | 任务字段不一致                     | 额外要求丢失              | 统一为 `additional_instructions` |
| API-P0-04 | 资源搜索路由顺序风险               | search 被当成 resource_id | 调整路由顺序                     |
| API-P0-05 | Mock Agent 接口风险                | AI 输出不可用             | Mock 不进入生产链路              |

------

### 21.2 P1 问题

| 编号      | 问题                              | 影响                  | 修复                             |
| --------- | --------------------------------- | --------------------- | -------------------------------- |
| API-P1-01 | `qa_records` 缺少 conversation_id | 历史会话不完整        | 数据库新增字段                   |
| API-P1-02 | 管理员更新用户参数格式不一致      | 用户管理失败          | 统一 JSON Body                   |
| API-P1-03 | 报告删除 UI 无接口                | 前端误导              | 移除按钮或补 DELETE 接口         |
| API-P1-04 | PDF 导出边界不清晰                | 用户预期不一致        | 明确 Markdown 稳定，PDF 后续增强 |
| API-P1-05 | Skills API 缺失                   | 无法管理和调用 Skills | 后续新增                         |
| API-P1-06 | MCP API 缺失                      | 无法管理 MCP          | 后续新增                         |
| API-P1-07 | Agent Runs API 缺失               | 执行不可审计          | 后续新增                         |

------

## 22. API 测试要求

### 22.1 当前业务 API 测试

必须覆盖：

1. 注册。
2. 登录。
3. Token 刷新。
4. 获取当前用户。
5. 创建课程。
6. 加入课程。
7. 上传资源。
8. 资源状态轮询。
9. 非流式问答。
10. 流式问答。
11. 问答历史。
12. 任务生成。
13. 任务发布。
14. 报告生成。
15. 报告导出。
16. 用户管理。

------

### 22.2 智能体平台 API 测试

后续新增后必须覆盖：

1. Skills 列表。
2. Skill 详情。
3. Skill 运行。
4. Skill 执行记录。
5. MCP Server 列表。
6. MCP Tool 列表。
7. MCP Tool 调用记录。
8. Agent Run 列表。
9. Agent Run 详情。
10. 资源分析。
11. 教学设计生成。
12. 学习路径生成。
13. 代码解释。
14. 代码报错分析。

------

### 22.3 权限测试

必须覆盖：

1. 未登录访问返回 401。
2. 学生访问教师接口返回 403。
3. 学生访问管理员接口返回 403。
4. 非课程成员访问课程数据返回 403。
5. 学生不能运行教师 Skill。
6. 学生不能管理 MCP。
7. 学生不能查看 Agent 全局执行记录。
8. 教师不能查看其他课程数据。
9. MCP Tool 不能跨课程访问。

------

## 23. CodeBuddy 修改 API 的要求

CodeBuddy 修改 API 时必须遵守：

1. 不得随意改变已有接口路径。
2. 修改字段必须同步前端 API 封装。
3. 修改字段必须同步 TypeScript 类型。
4. 修改字段必须同步 Pydantic Schema。
5. 修改字段必须同步本文档。
6. 新增接口必须添加权限说明。
7. 新增接口必须添加请求示例。
8. 新增接口必须添加响应示例。
9. 新增接口必须添加测试。
10. 课程内接口必须包含 `course_id`。
11. 教师接口必须校验教师或管理员权限。
12. 管理接口必须校验 admin。
13. Skill 运行接口必须校验 Skill 权限。
14. MCP 管理接口必须仅 admin 可访问。
15. Agent 执行记录必须脱敏。
16. 不得把真实密钥返回前端。
17. 不得让 API 直接暴露内部异常堆栈。
18. 不得让 Mock LLM 接口进入生产主链路。

------

## 24. API 验收标准

### 24.1 基础 API 验收

| 编号      | 验收项     | 通过标准                           |
| --------- | ---------- | ---------------------------------- |
| API-AC-01 | 注册       | 学生和教师可注册                   |
| API-AC-02 | 登录       | 返回 access_token 和 refresh_token |
| API-AC-03 | 刷新 Token | refresh_token 可换新 token         |
| API-AC-04 | 创建课程   | 教师可创建课程                     |
| API-AC-05 | 加入课程   | 学生可通过课程码加入               |
| API-AC-06 | 上传资源   | 教师可上传资源                     |
| API-AC-07 | 批量上传   | 路径统一为 upload-batch            |
| API-AC-08 | 资源搜索   | search 路由可正常访问              |
| API-AC-09 | 非流式问答 | 返回 answer 和 sources             |
| API-AC-10 | 流式问答   | SSE 正常                           |
| API-AC-11 | 任务生成   | 字段为 additional_instructions     |
| API-AC-12 | 报告生成   | 报告数字来自真实统计               |
| API-AC-13 | 管理用户   | JSON Body 更新用户                 |
| API-AC-14 | 权限控制   | 无权限接口返回 403                 |

------

### 24.2 智能体平台 API 验收

| 编号         | 验收项       | 通过标准                 |
| ------------ | ------------ | ------------------------ |
| AGENT-API-01 | Skills 列表  | 按角色返回可用 Skills    |
| AGENT-API-02 | Skill 运行   | 可执行授权 Skill         |
| AGENT-API-03 | Skill 记录   | 可查询 SkillRun          |
| AGENT-API-04 | MCP Server   | 管理员可查看 MCP Server  |
| AGENT-API-05 | MCP Tools    | 管理员可查看 MCP Tool    |
| AGENT-API-06 | MCP 调用记录 | 管理员可查看调用记录     |
| AGENT-API-07 | Agent Runs   | 可查询 Agent 执行记录    |
| AGENT-API-08 | 资源分析     | 教师可分析课程资源       |
| AGENT-API-09 | 教学设计     | 教师可生成教学设计       |
| AGENT-API-10 | 学习路径     | 学生可生成自己的学习路径 |
| AGENT-API-11 | 代码解释     | 学生可获得教学式代码解释 |
| AGENT-API-12 | 安全审计     | 执行记录不含敏感信息     |

------

## 25. 本文档总结

EduAgent API 体系需要同时支撑：

```text
基础课程业务
+ RAG 问答
+ 教学任务
+ 教学报告
+ Skills 技能系统
+ MCP 工具生态
+ Agent 执行审计
+ 多智能体能力扩展
```

当前已实现 API 重点是：

```text
auth
courses
resources
qa
tasks
reports
admin
```

新版课程智能体平台建议新增 API：

```text
skills
admin/mcp
admin/agent-runs
courses/{course_id}/agent-runs
courses/{course_id}/analysis
courses/{course_id}/lesson-designs
courses/{course_id}/study-path
courses/{course_id}/code-tutor
```

当前优先修复：

```text
1. 登录返回 refresh_token
2. 批量上传路径统一为 upload-batch
3. 任务字段统一为 additional_instructions
4. 资源 search 路由顺序修复
5. 管理员更新用户统一 JSON Body
6. 报告删除 UI 与 API 一致
7. qa_records 增加 conversation_id
```

后续扩展顺序：

```text
1. 先稳定现有 API
2. 再新增 Skills API
3. 再新增 MCP 管理 API
4. 再新增 Agent Runs API
5. 再新增资源分析、教学设计、学习路径、代码辅导 API
6. 最后补充前端页面、测试和审计
```

完成以上改造后，EduAgent 的 API 层才能真正支撑课程智能体平台，而不是只支撑普通 RAG 问答系统。