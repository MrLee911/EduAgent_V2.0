# Task 任务生成工作流：7 节点 StateGraph + interrupt_before 中断点
# 对应文档：05 §4.3

import json
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from ..state import AgentState
from ..prompts.system import TASK_SYSTEM_PROMPT
from ..prompts.task_gen import TASK_GENERATION_TEMPLATE
from ..prompts.utils import format_knowledge_for_prompt


# === 节点函数 ===

def validate_task_input_node(state: AgentState) -> AgentState:
    """参数校验：topic 非空、task_type 合法"""
    valid_types = {"class_exercise", "homework", "lab_guide"}
    messages = state["messages"]

    task_type = state.get("workflow_type", "task_gen")
    if task_type not in valid_types:
        state["error"] = f"非法的任务类型：{task_type}"
        state["step_count"] += 1
        return state

    state["step_count"] += 1
    return state


async def task_rag_search_node(state: AgentState) -> AgentState:
    """检索 topic 相关课程资料（top_k=8）"""
    from ..tools.search_knowledge import search_knowledge

    last_message = state["messages"][-1]
    topic = last_message.content if hasattr(last_message, 'content') else str(last_message)
    course_id = state["course_id"]

    # 正确 await 异步检索
    results_str = await search_knowledge(query=topic, top_k=8, course_id=course_id)
    results = json.loads(results_str) if isinstance(results_str, str) else []

    state["retrieved_docs"] = results
    state["tool_calls"].append({
        "tool_name": "search_knowledge",
        "input": {"query": topic, "top_k": 8},
        "output": f"返回 {len(results)} 条结果",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["step_count"] += 1
    return state


def route_after_task_rag(state: AgentState) -> str:
    """RAG 结果路由：≥ 2 条 → sufficient，否则 insufficient"""
    if len(state["retrieved_docs"]) >= 2:
        return "sufficient"
    state["error"] = "INSUFFICIENT_KNOWLEDGE"
    return "insufficient"


async def assess_difficulty_node(state: AgentState) -> AgentState:
    """评估推荐难度：调用 calculate_difficulty 工具"""
    from ..tools.calculate_difficulty import calculate_difficulty

    last_message = state["messages"][-1]
    topic = last_message.content if hasattr(last_message, 'content') else str(last_message)
    course_id = state["course_id"]

    # 从 retrieved_docs 提取 resource_ids
    resource_ids = []
    for doc in state["retrieved_docs"]:
        rid = doc.get("metadata", {}).get("resource_id", "")
        if rid and rid not in resource_ids:
            resource_ids.append(rid)

    if resource_ids:
        result_str = await calculate_difficulty(topic=topic, resource_ids=resource_ids,
                                                task_type="class_exercise", course_id=course_id)
        state["tool_calls"].append({
            "tool_name": "calculate_difficulty",
            "input": {"topic": topic, "resource_ids": resource_ids},
            "output": result_str,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    state["step_count"] += 1
    return state


def build_task_prompt_node(state: AgentState) -> AgentState:
    """构建任务生成提示词"""
    docs_text = format_knowledge_for_prompt(state["retrieved_docs"], max_docs=8)

    system_prompt = TASK_SYSTEM_PROMPT.format(
        course_name=state.get("course_name", ""),
        knowledge_context=docs_text,
        task_type="class_exercise",
        difficulty="medium",
        additional_instructions=""
    )
    state["messages"].append(SystemMessage(content=system_prompt))
    state["step_count"] += 1
    return state


def llm_generate_task_node(state: AgentState) -> AgentState:
    """LLM 生成任务
    
    ⚠️ MOCK IMPLEMENTATION — 此节点当前返回占位内容，不能用于生产主链路。
    生产环境必须替换为真实 LLM Client 调用。
    当前任务主链路由 TaskService 通过 httpx 直接调用 LLM API，
    此工作流仅用于 Agent 编排演示和后续 Skill 接入。
    """
    # TODO: 替换为真实 LLM 调用
    mock_task = {
        "title": "（任务生成占位）",
        "task_type": "class_exercise",
        "description": "需要绑定 LLM Client 以生成实际内容",
        "estimated_time": "20分钟",
        "total_points": 50,
        "questions": [],
        "answer_section": ""
    }
    state["final_answer"] = json.dumps(mock_task, ensure_ascii=False)
    state["step_count"] += 1
    return state


def parse_task_output_node(state: AgentState) -> AgentState:
    """解析 LLM 输出 → 提取 title / content / reference_resources"""
    # TODO: 解析 LLM JSON 输出
    state["final_sources"] = state["retrieved_docs"][:5] if state["retrieved_docs"] else []
    state["step_count"] += 1
    return state


def save_task_draft_node(state: AgentState) -> AgentState:
    """保存任务草稿到数据库（在 workflow 中做轻量记录，实际持久化由 API 层负责）"""
    state["step_count"] += 1
    return state


# === 工作流构建 ===

def create_task_workflow() -> StateGraph:
    """创建任务生成工作流"""
    workflow = StateGraph(AgentState)

    workflow.add_node("validate_input", validate_task_input_node)
    workflow.add_node("rag_search", task_rag_search_node)
    workflow.add_node("assess_difficulty", assess_difficulty_node)
    workflow.add_node("build_prompt", build_task_prompt_node)
    workflow.add_node("llm_generate", llm_generate_task_node)
    workflow.add_node("parse_output", parse_task_output_node)
    workflow.add_node("save_draft", save_task_draft_node)

    workflow.set_entry_point("validate_input")
    workflow.add_edge("validate_input", "rag_search")

    workflow.add_conditional_edges(
        "rag_search",
        route_after_task_rag,
        {"sufficient": "assess_difficulty", "insufficient": END}
    )

    workflow.add_edge("assess_difficulty", "build_prompt")
    workflow.add_edge("build_prompt", "llm_generate")
    workflow.add_edge("llm_generate", "parse_output")
    workflow.add_edge("parse_output", "save_draft")
    workflow.add_edge("save_draft", END)

    memory = MemorySaver()
    return workflow.compile(
        checkpointer=memory,
        interrupt_before=["save_draft"]  # 发布前暂停，等待教师确认
    )
