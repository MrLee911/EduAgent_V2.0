# AgentState 共享状态定义：所有 LangGraph 工作流共用的 TypedDict
# 对应文档：05 §4.1, S1 Pattern 1

from typing import Annotated, Any, TypedDict, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class AgentState(TypedDict):
    """所有工作流共享的 State 结构"""

    # === 输入参数 ===
    course_id: str
    user_id: str
    course_name: str

    # === 消息流 ===
    messages: Annotated[list[BaseMessage], add_messages]

    # === RAG 检索中间结果 ===
    retrieved_docs: list[dict]     # search_knowledge 返回的文档列表

    # === 工具调用记录 ===
    tool_calls: list[dict]         # [{tool_name, input, output, timestamp}]

    # === 安全护栏 ===
    guardrail_checks: list[dict]   # [{check_name, passed, reason, timestamp}]

    # === 最终输出 ===
    final_answer: Optional[str]
    final_sources: list[dict]

    # === 元数据 ===
    workflow_type: str             # "qa" | "task_gen" | "report_gen"
    step_count: int
    error: Optional[str]
