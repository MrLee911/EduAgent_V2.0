# QA 问答工作流：8 节点 StateGraph + 条件路由
# 对应文档：05 §4.2, S1 Pattern 7

import json
import re
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from ..state import AgentState
from ..prompts.system import QA_SYSTEM_PROMPT
from ..prompts.qa import (
    QA_QUERY_REWRITE_TEMPLATE,
    QA_INTENT_CLASSIFY_TEMPLATE,
    QA_ANSWER_WITH_RAG_TEMPLATE,
    QA_NO_RAG_FALLBACK_TEMPLATE,
)
from ..prompts.utils import format_knowledge_for_prompt


# === 节点函数 ===

def guardrail_input_node(state: AgentState) -> AgentState:
    """输入护栏节点：越狱检测 + 课程范围检查"""
    from ..guardrails import InputGuardrail
    from ..prompts.guardrails import COURSE_SCOPE_CHECK_PROMPT

    last_message = state["messages"][-1]
    question = last_message.content

    guardrail = InputGuardrail()

    # 1. 越狱检测（正则，快）
    jailbreak_result = guardrail.check_jailbreak(question)
    state["guardrail_checks"].append({
        "check_name": "jailbreak_detect",
        "passed": jailbreak_result["passed"],
        "reason": jailbreak_result.get("reason", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    if not jailbreak_result["passed"]:
        state["final_answer"] = "抱歉，我无法处理这个请求。请提出与课程学习相关的问题。"
        state["step_count"] += 1
        return state

    # 2. 课程范围检查（LLM 分类）
    scope_result = guardrail.check_scope(question, state.get("course_name", ""))
    state["guardrail_checks"].append({
        "check_name": "course_scope",
        "passed": scope_result["passed"],
        "reason": scope_result.get("reason", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    if not scope_result["passed"]:
        state["final_answer"] = scope_result.get("reason", "问题超出课程范围")
        state["step_count"] += 1

    state["step_count"] += 1
    return state


def route_guardrail(state: AgentState) -> str:
    """护栏路由判断"""
    for check in state["guardrail_checks"]:
        if not check["passed"]:
            return "blocked"
    return "passed"


def rewrite_query_node(state: AgentState) -> AgentState:
    """查询改写节点（HyDE 策略）"""
    last_message = state["messages"][-1]
    question = last_message.content

    # 将改写后的结果作为 AIMessage 追加
    rewritten = f"[改写的检索查询] {question}"
    state["messages"].append(AIMessage(content=rewritten))
    state["step_count"] += 1
    return state


async def rag_search_node(state: AgentState) -> AgentState:
    """RAG 检索节点：调用 search_knowledge"""
    from ..tools.search_knowledge import search_knowledge

    query = state["messages"][-1].content
    course_id = state["course_id"]

    # 正确 await 异步检索
    results_str = await search_knowledge(query=query, top_k=10, course_id=course_id)
    results = json.loads(results_str) if isinstance(results_str, str) else []

    state["retrieved_docs"] = results
    state["tool_calls"].append({
        "tool_name": "search_knowledge",
        "input": {"query": query, "top_k": 10},
        "output": f"返回 {len(results)} 条结果",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
    state["step_count"] += 1
    return state


def route_after_rag(state: AgentState) -> str:
    """RAG 结果路由：有结果 → build_prompt，无结果 → handle_no_sources"""
    if len(state["retrieved_docs"]) >= 1:
        return "has_sources"
    return "no_sources"


def handle_no_sources_node(state: AgentState) -> AgentState:
    """无 RAG 结果降级处理"""
    last_message = state["messages"][-1]
    question = last_message.content if hasattr(last_message, 'content') else str(last_message)

    state["final_answer"] = (
        "我在课程资料中未找到与这个问题直接相关的内容。"
        "建议你在课堂上向老师确认这个知识点，或者查阅教材相关章节。"
    )
    state["step_count"] += 1
    return state


def build_prompt_node(state: AgentState) -> AgentState:
    """构建 LLM 调用提示词"""
    docs_text = format_knowledge_for_prompt(state["retrieved_docs"])

    system_prompt = QA_SYSTEM_PROMPT.format(
        course_name=state.get("course_name", ""),
        current_date=datetime.now().strftime("%Y-%m-%d")
    )
    state["messages"].append(SystemMessage(content=system_prompt))
    state["step_count"] += 1
    return state


def llm_answer_node(state: AgentState) -> AgentState:
    """LLM 生成回答
    
    ⚠️ MOCK IMPLEMENTATION — 此节点当前返回占位内容，不能用于生产主链路。
    生产环境必须替换为真实 LLM Client 调用。
    当前 QA 主链路由 QAService 通过 httpx 直接调用 LLM API，
    此工作流仅用于 Agent 编排演示和后续 Skill 接入。
    """
    # TODO: 替换为真实 LLM 调用
    # from ..llm_config import get_llm
    # llm = get_llm()
    # response = llm.invoke(state["messages"])

    mock_answer = "（LLM 回答占位 — 需要在运行时绑定 LLM Client）"
    state["final_answer"] = mock_answer
    state["final_sources"] = state["retrieved_docs"][:10] if state["retrieved_docs"] else []
    state["step_count"] += 1
    return state


def guardrail_output_node(state: AgentState) -> AgentState:
    """输出护栏节点：内容安全 + 答案泄露检测"""
    from ..guardrails import OutputGuardrail

    guardrail = OutputGuardrail()
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if hasattr(msg, 'type') and msg.type == "human":
            last_user_msg = msg.content
            break

    answer = state["final_answer"] or ""

    # 内容安全检查
    safety_result = guardrail.check_content_safety(answer)
    state["guardrail_checks"].append({
        "check_name": "content_safety",
        "passed": safety_result["passed"],
        "reason": safety_result.get("reason", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    if not safety_result["passed"]:
        state["final_answer"] = "抱歉，我无法回答此问题。请提出与课程学习相关的内容。"
        state["step_count"] += 1
        return state

    # 答案泄露检测
    leak_result = guardrail.check_answer_leak(last_user_msg, answer)
    state["guardrail_checks"].append({
        "check_name": "answer_leak",
        "passed": leak_result["passed"],
        "reason": leak_result.get("reason", ""),
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    state["step_count"] += 1
    return state


def route_after_output_guard(state: AgentState) -> str:
    """输出护栏路由：通过 → save，未通过 → regenerate"""
    for check in state["guardrail_checks"]:
        if check["check_name"] == "answer_leak" and not check["passed"]:
            return "regenerate"
    return "passed"


def save_record_node(state: AgentState) -> AgentState:
    """保存问答记录到数据库（在 workflow 中做轻量记录，实际持久化由 API 层负责）"""
    state["step_count"] += 1
    return state


# === 工作流构建 ===

def create_qa_workflow() -> StateGraph:
    """创建问答工作流"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("guardrail_input", guardrail_input_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("rag_search", rag_search_node)
    workflow.add_node("handle_no_sources", handle_no_sources_node)
    workflow.add_node("build_prompt", build_prompt_node)
    workflow.add_node("llm_answer", llm_answer_node)
    workflow.add_node("guardrail_output", guardrail_output_node)
    workflow.add_node("save_record", save_record_node)

    # 设置入口
    workflow.set_entry_point("guardrail_input")

    # 条件边
    workflow.add_conditional_edges(
        "guardrail_input",
        route_guardrail,
        {"passed": "rewrite_query", "blocked": "guardrail_output"}
    )

    workflow.add_edge("rewrite_query", "rag_search")

    workflow.add_conditional_edges(
        "rag_search",
        route_after_rag,
        {"has_sources": "build_prompt", "no_sources": "handle_no_sources"}
    )

    workflow.add_edge("handle_no_sources", "guardrail_output")
    workflow.add_edge("build_prompt", "llm_answer")
    workflow.add_edge("llm_answer", "guardrail_output")

    workflow.add_conditional_edges(
        "guardrail_output",
        route_after_output_guard,
        {"passed": "save_record", "regenerate": "llm_answer"}
    )

    workflow.add_edge("save_record", END)

    # 编译（带内存检查点）
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
