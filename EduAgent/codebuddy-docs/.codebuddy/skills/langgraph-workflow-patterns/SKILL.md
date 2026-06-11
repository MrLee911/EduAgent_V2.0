---
name: langgraph-workflow-patterns
description: >
  LangGraph 工作流实施模式——当 CodeBuddy 开始编写 StateGraph、Conditional Edge、
  ToolNode、Checkpointer 或 Human-in-the-Loop 中断点时触发。覆盖：State 类型定义规范、
  条件边路由函数写法、ToolMessage 正确格式、中断点位置、MemorySaver 配置、
  本项目 3 条工作流（QA/Task/Report）参考实现骨架。这是教学智能体 Agent 模块的核心实施指南。
agent_created: true
---

# LangGraph Workflow Implementation Patterns

## Purpose

本 Skill 提供基于 LangGraph 的 Agent 工作流专家级实施模式。当 CodeBuddy 需要编写 StateGraph、
节点（Node）、条件边（Conditional Edge）、工具调用或检查点（Checkpointer）时，
应使用本 Skill 中的模式，避免 LangGraph 常见陷阱。

本 Skill 的代码模式直接对应项目文档 `docs/05_AI智能体行为定义.md` 中的工作流定义。

## When to Use

在以下场景中触发本 Skill：

- CodeBuddy 开始编写 `StateGraph` 的 `add_node` / `add_edge` / `add_conditional_edges`
- CodeBuddy 需要定义 `AgentState`（TypedDict + Annotated）
- CodeBuddy 需要编写条件路由函数（`route_*` 返回字符串的路由函数）
- CodeBuddy 需要在工作流中集成 Tool Calling
- CodeBuddy 需要添加 Human-in-the-Loop 中断点
- CodeBuddy 需要编译工作流（`.compile(checkpointer=...)`）
- CodeBuddy 在节点中调用 LLM 或工具后需要更新 State

## Core Patterns

### Pattern 1: AgentState 定义规范

**规则**：用 `TypedDict` 定义 State，消息列表用 `Annotated[list, add_messages]`。

```python
from typing import Annotated, Any, TypedDict, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """所有工作流共享的 State 结构。每个字段必须有默认值。"""

    # === 输入参数（必须） ===
    course_id: str          # 课程 ID
    user_id: str            # 用户 ID
    course_name: str        # 课程名称

    # === 消息流（必须用 Annotated + add_messages） ===
    messages: Annotated[list[BaseMessage], add_messages]
    # ⚠️ 不用 add_messages 则每次都会覆盖而非追加！

    # === RAG 检索中间结果 ===
    retrieved_docs: list[dict]     # 默认空列表

    # === 工具调用记录 ===
    tool_calls: list[dict]         # [{tool_name, input, output, timestamp}]

    # === 安全护栏 ===
    guardrail_checks: list[dict]   # [{check_name, passed, reason, timestamp}]

    # === 最终输出 ===
    final_answer: Optional[str]    # 默认 None
    final_sources: list[dict]      # 默认空列表

    # === 元数据 ===
    workflow_type: str             # "qa" | "task_gen" | "report_gen"
    step_count: int               # 默认 0
    error: Optional[str]          # 默认 None
```

**关键约束**：
1. `messages` 字段 **必须** 用 `Annotated[list[BaseMessage], add_messages]`，否则 LangGraph 会覆盖消息而非追加
2. 每个字段必须有默认值（list 用 `[]`，Optional 用 `None`，int 用 `0`）
3. 所有工作流共用一个 `AgentState`，通过 `workflow_type` 区分
4. State 中的 list/dict 字段在节点中 **原地修改后必须返回整个 state**

### Pattern 2: 条件路由函数写法（CRITICAL）

**规则**：路由函数必须返回 **字符串**，不是布尔值。返回的字符串必须匹配 `add_conditional_edges` 中的映射 key。

```python
# ✅ 正确：返回字符串
def route_guardrail(state: AgentState) -> str:
    """根据护栏检查结果决定去向"""
    last_check = state["guardrail_checks"][-1]
    if last_check["passed"]:
        return "passed"       # ← 字符串
    else:
        return "blocked"      # ← 字符串

# ❌ 错误：返回布尔值
def route_guardrail_wrong(state: AgentState) -> bool:
    return state["guardrail_checks"][-1]["passed"]  # ← 布尔值，LangGraph 报错！
```

**路由函数注册时必须提供完整映射**：

```python
workflow.add_conditional_edges(
    "guardrail_input",       # 源节点名
    route_guardrail,         # 路由函数
    {                        # 映射表：路由返回值 → 目标节点
        "passed": "rewrite_query",
        "blocked": "guardrail_output"
    }
)
# ⚠️ 映射表必须覆盖路由函数所有可能的返回值，否则 LangGraph 运行时崩
```

### Pattern 3: 节点函数的标准模板

**规则**：节点函数接收 `AgentState`，必须返回更新后的 `AgentState`（或只返回需要更新的字段的 dict）。

```python
# ✅ 风格 A：接收并返回整个 state（推荐，适合复杂节点）
def rewrite_query_node(state: AgentState) -> AgentState:
    """查询改写节点"""
    last_message = state["messages"][-1]
    rewrite_prompt = f"将以下问题改写为检索查询：{last_message.content}"

    rewritten = llm.invoke(rewrite_prompt)
    state["messages"].append(rewritten)   # 原地修改
    state["step_count"] += 1
    return state                          # 返回整个 state

# ✅ 风格 B：只返回需要更新的字段（适合简单节点）
def increment_step(state: AgentState) -> dict:
    return {"step_count": state["step_count"] + 1}
    # LangGraph 会自动 merge

# ❌ 错误：修改了 state 但不返回
def broken_node(state: AgentState) -> AgentState:
    state["step_count"] += 1  # 修改了...
    # 忘记 return state！LangGraph 不会自动保存修改
```

### Pattern 4: Tool Calling 在节点中的正确写法

**规则**：工具调用结果必须用 `ToolMessage` 包装，不能直接拼字符串。

```python
from langchain_core.messages import ToolMessage
import json

def rag_search_node(state: AgentState) -> AgentState:
    """RAG 检索节点"""
    query = state["messages"][-1].content

    # 调用工具（LangChain Tool）
    results_raw = search_knowledge.invoke({
        "query": query,
        "top_k": 5,
        "course_id": state["course_id"]
    })

    results = json.loads(results_raw)
    state["retrieved_docs"] = results

    # ✅ 正确：用 ToolMessage 记录工具调用
    state["messages"].append(ToolMessage(
        content=f"返回 {len(results)} 条结果",
        tool_call_id="search_knowledge_001",
        name="search_knowledge"
    ))

    # 同时记录到工具调用日志
    state["tool_calls"].append({
        "tool_name": "search_knowledge",
        "input": {"query": query, "top_k": 5},
        "output": f"返回 {len(results)} 条结果",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    state["step_count"] += 1
    return state
```

### Pattern 5: Checkpointer（MemorySaver）配置

**规则**：所有生产工作流必须用 `MemorySaver` 编译，支持中断/恢复。

```python
from langgraph.checkpoint.memory import MemorySaver

# ✅ 正确
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# ❌ 错误：忘记 checkpointer，中断点会失效
app = workflow.compile()  # interrupt_before 不会生效
```

对于需要持久化的场景，使用 `SqliteSaver`：
```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

conn = sqlite3.connect("checkpoints.db", check_same_thread=False)
memory = SqliteSaver(conn)
app = workflow.compile(checkpointer=memory)
```

### Pattern 6: Human-in-the-Loop 中断点

**规则**：在需要人工确认的节点之前设置中断点。

```python
# 场景：任务生成后需要教师确认才能发布
workflow.add_node("save_draft", save_task_draft_node)

# 在 save_draft 之后设置中断点
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["publish_task"]  # 发布前暂停
)

# 恢复执行
# 通过 thread_id 恢复，传入人工确认结果
app.invoke(
    {"approval": "approved"},
    config={"configurable": {"thread_id": thread_id}}
)
```

### Pattern 7: 完整工作流创建模板

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

def create_qa_workflow() -> StateGraph:
    """创建问答工作流 —— 完整模板"""

    # Step 1: 实例化 StateGraph
    workflow = StateGraph(AgentState)

    # Step 2: 添加所有节点
    workflow.add_node("guardrail_input", guardrail_input_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("rag_search", rag_search_node)
    workflow.add_node("handle_no_sources", handle_no_sources_node)
    workflow.add_node("build_prompt", build_prompt_node)
    workflow.add_node("llm_answer", llm_answer_node)
    workflow.add_node("guardrail_output", guardrail_output_node)
    workflow.add_node("save_record", save_record_node)

    # Step 3: 设置入口
    workflow.set_entry_point("guardrail_input")

    # Step 4: 添加条件边（需要路由判断的地方）
    workflow.add_conditional_edges(
        "guardrail_input", route_guardrail,
        {"passed": "rewrite_query", "blocked": "guardrail_output"}
    )
    workflow.add_conditional_edges(
        "rag_search", route_after_rag,
        {"has_sources": "build_prompt", "no_sources": "handle_no_sources"}
    )
    workflow.add_conditional_edges(
        "guardrail_output", route_after_output_guard,
        {"passed": "save_record", "regenerate": "llm_answer"}
    )

    # Step 5: 添加普通边（线性流程）
    workflow.add_edge("rewrite_query", "rag_search")
    workflow.add_edge("handle_no_sources", "guardrail_output")
    workflow.add_edge("build_prompt", "llm_answer")
    workflow.add_edge("llm_answer", "guardrail_output")
    workflow.add_edge("save_record", END)

    # Step 6: 编译（带 checkpointer）
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
```

## Project-Specific Constraints

本项目的 3 条 LangGraph 工作流在 `docs/05_AI智能体行为定义.md` 中有完整定义，以下为关键约束：

### 约束 1：3 条工作流共用 AgentState

QA（问答）、Task（任务生成）、Report（报告生成）三条工作流共用同一个 `AgentState` 类型定义，通过 `workflow_type` 字段区分。

### 约束 2：QA 工作流的关键路由决策

| 检查点 | 路由函数 | 分支 | 条件 |
|--------|---------|------|------|
| guardrail_input → | `route_guardrail` | passed / blocked | 越狱检测 + 课程范围检查 |
| rag_search → | `route_after_rag` | has_sources / no_sources | `len(retrieved_docs) >= 1` |
| guardrail_output → | `route_after_output_guard` | passed / regenerate | 答案泄露检测 |

### 约束 3：Task 工作流的降级策略

如果没有足够资料（`retrieved_docs < 2`），**不允许**用 LLM 凭空生成任务，必须返回 `INSUFFICIENT_KNOWLEDGE` 错误。

### 约束 4：Report 工作流的工具并发

`query_stats` 节点中三个工具调用（`query_qa_stats` / `get_course_resources` / `get_course_stats`）是互相独立的，应并发执行：

```python
import asyncio

async def query_stats_node(state: AgentState) -> AgentState:
    # 并发调用三个工具
    qa_stats, resources, course_stats = await asyncio.gather(
        query_qa_stats_async(state["start_date"], state["end_date"]),
        get_course_resources_async(state["course_id"]),
        get_course_stats_async(state["course_id"])
    )
    # ... 聚合
```

### 约束 5：节点调用详情速查

| 工作流 | 节点 | LLM调用 | 工具调用 | 产出 |
|--------|------|:--:|:--:|------|
| QA | guardrail_input | ✅ | - | pass/block |
| QA | rewrite_query | ✅ | - | 改写后 query |
| QA | rag_search | - | ✅ search_knowledge | retrieved_docs |
| QA | handle_no_sources | ✅ | - | 降级回复 |
| QA | build_prompt | - | - | 组装 system prompt |
| QA | llm_answer | ✅ | - | 最终回答 |
| QA | guardrail_output | ✅ | - | pass/regenerate |
| QA | save_record | - | ✅ DB INSERT | qa_record |
| Task | validate_input | - | - | 通过/报错 |
| Task | rag_search | - | ✅ search_knowledge | retrieved_docs |
| Task | assess_difficulty | ✅ | ✅ calculate_difficulty | 推荐难度 |
| Task | build_prompt | - | - | task prompt |
| Task | llm_generate | ✅ | - | 任务内容 |
| Task | parse_output | - | - | title+content+refs |
| Task | save_draft | - | ✅ DB INSERT | task 记录 |
| Report | validate_input | - | - | 通过/报错 |
| Report | query_stats | - | ✅ ×3 并发 | 原始数据 |
| Report | aggregate_data | - | - | statistics JSON |
| Report | build_prompt | - | - | report prompt |
| Report | llm_generate | ✅ | - | 报告内容 |
| Report | parse_output | - | - | content |
| Report | save_report | - | ✅ DB INSERT | report 记录 |

### 约束 6：目录结构

```
backend/app/agent/workflows/
├── __init__.py          # 导出 create_qa_workflow, create_task_workflow, create_report_workflow
├── state.py             # AgentState TypedDict 定义
├── qa_workflow.py       # QA 问答工作流
├── task_workflow.py     # Task 任务生成工作流
├── report_workflow.py   # Report 报告生成工作流
├── nodes/               # 节点函数（按功能拆分）
│   ├── __init__.py
│   ├── guardrail.py     # guardrail_input / guardrail_output 节点
│   ├── rag.py           # rag_search / handle_no_sources 节点
│   ├── prompt.py        # build_prompt / rewrite_query 节点
│   ├── llm.py           # llm_answer / llm_generate 节点
│   └── storage.py       # save_record / save_draft / save_report 节点
└── routes/              # 条件路由函数
    ├── __init__.py
    └── router.py        # route_guardrail / route_after_rag / route_after_output_guard
```

### 约束 7：LangGraph Workflow 不得绕过 Agent Orchestrator

新版 EduAgent 中，LangGraph Workflow 应作为 Agent 编排的一部分，而不是绕过 Agent Orchestrator、Skill Router、Tool Router 的独立入口。

推荐链路：

```text
Service
→ Agent Orchestrator
→ Intent Router
→ Planner
→ Skill Router
→ Tool Router
→ LangGraph Workflow
→ Skill Executor / MCP Client
→ Service 落库
```

## Anti-Patterns (What NOT to Do)

### ❌ 错误 1：忘记 add_messages

```python
# 错误：不用 add_messages，每次节点更新都会覆盖消息列表
class AgentState(TypedDict):
    messages: list[BaseMessage]  # ❌ 缺少 Annotated + add_messages
```

**后果**：`state["messages"].append(msg)` 在下一个节点中丢失。

### ❌ 错误 2：条件路由返回布尔值

```python
# 错误
def route_guardrail(state):
    return state["check"]["passed"]  # 返回 True/False，LangGraph 报错
```

**修复**：
```python
def route_guardrail(state):
    return "passed" if state["check"]["passed"] else "blocked"
```

### ❌ 错误 3：映射表不完整

```python
# 错误：映射表缺少 "blocked" 分支
workflow.add_conditional_edges(
    "guardrail_input", route_guardrail,
    {"passed": "rewrite_query"}  # ❌ 缺少 blocked 分支
)
```

**后果**：当路由函数返回 `"blocked"` 时，LangGraph 引发 `ValueError`。

### ❌ 错误 4：节点中忘记 return state

```python
# 错误
def my_node(state):
    state["step_count"] += 1
    # 忘记 return！LangGraph 不会保存修改
```

### ❌ 错误 5：直接用 str 而非 ToolMessage

```python
# 错误
state["messages"].append(f"工具返回了 {count} 条结果")  # ❌ 普通字符串
```

**修复**：参见 Pattern 4。

### ❌ 错误 6：忘记 compile(checkpointer=memory)

```python
# 错误
app = workflow.compile()  # ❌ 没有 checkpointer
```

**后果**：`interrupt_before` 不生效，无法暂停/恢复工作流。

### ❌ 错误 7：Task 工作流无资料时硬生成

```python
# 错误：retrieved_docs 为空时仍调 LLM
if len(state["retrieved_docs"]) < 2:
    # 不要硬生成！
    state["error"] = "INSUFFICIENT_KNOWLEDGE"
    return state
```

**正确做法**：返回错误，不调用 LLM。

## References

详细参考文档位于项目目录：
- `docs/05_AI智能体行为定义.md` — 第 4 章：完整工作流定义（ASCII 流程图 + 代码骨架 + 节点详情表）
- `docs/05_AI智能体行为定义.md` — 第 6 章：安全护栏与工作流集成
- `docs/06_提示词模板.md` — 第 8 章：提示词链式编排与工作流调用链
- `docs/02_技术架构文档.md` — 项目目录结构中的 `backend/app/agent/workflows/`
