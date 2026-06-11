# 工具注册表：partial 注入 course_id/user_id，各 Agent 工具子集定义
# 对应文档：05 §3.8

from functools import partial
from typing import Dict
from .search_knowledge import search_knowledge
from .get_course_resources import get_course_resources
from .get_course_stats import get_course_stats
from .get_user_context import get_user_context
from .query_qa_stats import query_qa_stats
from .calculate_difficulty import calculate_difficulty


def create_tool_registry(course_id: str, user_id: str = "") -> Dict[str, callable]:
    """
    为指定课程创建工具注册表。
    通过 partial 注入 course_id 和 user_id，工具函数无需在调用时传递这些参数。

    返回：{tool_name: callable} 字典，供 LangGraph Agent 使用。
    """
    registry = {
        "search_knowledge": partial(search_knowledge, course_id=course_id),
        "get_course_resources": partial(get_course_resources, course_id=course_id),
        "get_course_stats": partial(get_course_stats, course_id=course_id),
        "get_user_context": partial(get_user_context, course_id=course_id, user_id=user_id),
        "query_qa_stats": partial(query_qa_stats, course_id=course_id),
        "calculate_difficulty": partial(calculate_difficulty, course_id=course_id),
    }
    return registry


# 各 Agent 使用的工具子集
QA_AGENT_TOOLS = [
    "search_knowledge",
    "get_course_stats",
    "get_user_context",
]

TASK_AGENT_TOOLS = [
    "search_knowledge",
    "get_course_resources",
    "calculate_difficulty",
]

REPORT_AGENT_TOOLS = [
    "get_course_stats",
    "get_course_resources",
    "query_qa_stats",
]
