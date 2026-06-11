# 工具模块汇总导出
# 对应文档：05 §3 工具定义

from .search_knowledge import search_knowledge, SearchKnowledgeInput
from .get_course_resources import get_course_resources, GetCourseResourcesInput
from .get_course_stats import get_course_stats
from .get_user_context import get_user_context, GetUserContextInput
from .query_qa_stats import query_qa_stats, QueryQAStatsInput
from .calculate_difficulty import calculate_difficulty, CalculateDifficultyInput
from .registry import (
    create_tool_registry,
    QA_AGENT_TOOLS,
    TASK_AGENT_TOOLS,
    REPORT_AGENT_TOOLS,
)

__all__ = [
    "search_knowledge",
    "SearchKnowledgeInput",
    "get_course_resources",
    "GetCourseResourcesInput",
    "get_course_stats",
    "get_user_context",
    "GetUserContextInput",
    "query_qa_stats",
    "QueryQAStatsInput",
    "calculate_difficulty",
    "CalculateDifficultyInput",
    "create_tool_registry",
    "QA_AGENT_TOOLS",
    "TASK_AGENT_TOOLS",
    "REPORT_AGENT_TOOLS",
]
