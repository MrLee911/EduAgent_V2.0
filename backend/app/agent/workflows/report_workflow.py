# Report 报告生成工作流：7 节点 StateGraph
# 对应文档：05 §4.4

import json
import asyncio
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage, HumanMessage

from ..state import AgentState
from ..prompts.system import REPORT_SYSTEM_PROMPT
from ..prompts.report import REPORT_GENERATION_TEMPLATE


# === 节点函数 ===

def validate_report_input_node(state: AgentState) -> AgentState:
    """参数校验：report_type, start_date, end_date"""
    valid_types = {"weekly", "monthly", "semester"}
    # report_type 从额外参数获取
    state["step_count"] += 1
    return state


async def query_stats_node(state: AgentState) -> AgentState:
    """并发查询统计数据：query_qa_stats + get_course_resources + get_course_stats"""
    from ..tools.query_qa_stats import query_qa_stats
    from ..tools.get_course_resources import get_course_resources
    from ..tools.get_course_stats import get_course_stats

    course_id = state["course_id"]

    # 从 state 获取日期范围，未设置则使用合理的默认值（近30天）
    start_date = state.get("start_date")
    end_date = state.get("end_date")
    if not start_date or not end_date:
        from datetime import timedelta
        now = datetime.now(timezone.utc)
        end_date = now.strftime("%Y-%m-%d")
        start_date = (now - timedelta(days=30)).strftime("%Y-%m-%d")

    # 并发调用三个工具（互相独立，无依赖）
    qa_stats_task = query_qa_stats(
        start_date=start_date, end_date=end_date, course_id=course_id
    )
    resources_task = get_course_resources(limit=20, course_id=course_id)
    course_stats_task = get_course_stats(course_id=course_id)

    qa_stats, resources, course_stats = await asyncio.gather(
        qa_stats_task, resources_task, course_stats_task
    )

    state["tool_calls"].append({
        "tool_name": "query_stats_concurrent",
        "input": {"course_id": course_id},
        "output": "3 工具并发完成",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # 存储原始数据到 final_answer 临时字段（供 aggregate 使用）
    state["final_answer"] = json.dumps({
        "qa_stats": json.loads(qa_stats) if isinstance(qa_stats, str) else qa_stats,
        "resources": json.loads(resources) if isinstance(resources, str) else resources,
        "course_stats": json.loads(course_stats) if isinstance(course_stats, str) else course_stats,
    }, ensure_ascii=False)

    state["step_count"] += 1
    return state


def route_has_data(state: AgentState) -> str:
    """检查统计数据是否为空"""
    if state["final_answer"]:
        try:
            data = json.loads(state["final_answer"]) if isinstance(state["final_answer"], str) else {}
            qa_total = data.get("qa_stats", {}).get("total_qa", 0)
            if qa_total < 1:
                state["error"] = "NO_DATA_IN_RANGE"
                return "no_data"
            return "has_data"
        except (json.JSONDecodeError, KeyError, TypeError):
            return "no_data"
    return "no_data"


def aggregate_data_node(state: AgentState) -> AgentState:
    """聚合三个工具的结果为 statistics JSON"""
    try:
        raw_data = json.loads(state["final_answer"]) if isinstance(state["final_answer"], str) else {}
    except json.JSONDecodeError:
        raw_data = {}

    statistics = {
        "total_qa": raw_data.get("qa_stats", {}).get("total_qa", 0),
        "active_students": raw_data.get("qa_stats", {}).get("active_students", 0),
        "feedback_distribution": raw_data.get("qa_stats", {}).get("feedback_distribution", {}),
        "resource_count": raw_data.get("course_stats", {}).get("resource_count", 0),
        "member_count": raw_data.get("course_stats", {}).get("member_count", 0),
        "published_task_count": raw_data.get("course_stats", {}).get("published_task_count", 0),
        "daily_qa_trend": raw_data.get("qa_stats", {}).get("daily_qa_trend", {}),
        "resources": raw_data.get("resources", []),
    }

    state["final_answer"] = json.dumps(statistics, ensure_ascii=False)
    state["step_count"] += 1
    return state


def build_report_prompt_node(state: AgentState) -> AgentState:
    """构建报告生成提示词"""
    # 从 state 获取报告周期，未设置则使用日期范围
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    report_period = state.get("report_period") or f"{start_date} ~ {end_date}"

    system_prompt = REPORT_SYSTEM_PROMPT.format(
        course_name=state.get("course_name", ""),
        report_period=report_period,
        statistics=state["final_answer"] or "{}",
        qa_hotspots="{}",
        task_stats="{}",
    )
    state["messages"].append(SystemMessage(content=system_prompt))
    state["step_count"] += 1
    return state


def llm_generate_report_node(state: AgentState) -> AgentState:
    """LLM 生成报告
    
    ⚠️ MOCK IMPLEMENTATION — 此节点当前返回占位内容，不能用于生产主链路。
    生产环境必须替换为真实 LLM Client 调用。
    当前报告主链路由 ReportService 通过 httpx 直接调用 LLM API，
    此工作流仅用于 Agent 编排演示和后续 Skill 接入。
    """
    # TODO: 替换为真实 LLM 调用
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    report_period = state.get("report_period") or f"{start_date} ~ {end_date}"
    mock_report = {
        "title": f"{state.get('course_name', '课程')} - 教学总结报告",
        "course_name": state.get("course_name", ""),
        "report_period": report_period,
        "overview": "（报告概览占位 — 需要绑定 LLM Client）",
        "resource_analysis": "（资源分析占位）",
        "task_completion": "（任务完成情况占位）",
        "hot_questions": [],
        "suggestions": [],
        "outlook": "（展望占位）"
    }
    state["final_answer"] = json.dumps(mock_report, ensure_ascii=False)
    state["step_count"] += 1
    return state


def parse_report_output_node(state: AgentState) -> AgentState:
    """解析 LLM 输出 → 提取 content"""
    state["step_count"] += 1
    return state


def save_report_node(state: AgentState) -> AgentState:
    """保存报告到数据库（在 workflow 中做轻量记录，实际持久化由 API 层负责）"""
    state["step_count"] += 1
    return state


# === 工作流构建 ===

def create_report_workflow() -> StateGraph:
    """创建报告生成工作流"""
    workflow = StateGraph(AgentState)

    workflow.add_node("validate_input", validate_report_input_node)
    workflow.add_node("query_stats", query_stats_node)
    workflow.add_node("aggregate_data", aggregate_data_node)
    workflow.add_node("build_prompt", build_report_prompt_node)
    workflow.add_node("llm_generate", llm_generate_report_node)
    workflow.add_node("parse_output", parse_report_output_node)
    workflow.add_node("save_report", save_report_node)

    workflow.set_entry_point("validate_input")
    workflow.add_edge("validate_input", "query_stats")

    workflow.add_conditional_edges(
        "query_stats",
        route_has_data,
        {"has_data": "aggregate_data", "no_data": END}
    )

    workflow.add_edge("aggregate_data", "build_prompt")
    workflow.add_edge("build_prompt", "llm_generate")
    workflow.add_edge("llm_generate", "parse_output")
    workflow.add_edge("parse_output", "save_report")
    workflow.add_edge("save_report", END)

    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)
