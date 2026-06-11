# 提示词模块汇总导出
# 对应文档：06 §1.3 文件映射

from .system import QA_SYSTEM_PROMPT, TASK_SYSTEM_PROMPT, REPORT_SYSTEM_PROMPT
from .qa import (
    QA_QUERY_REWRITE_TEMPLATE,
    QA_INTENT_CLASSIFY_TEMPLATE,
    QA_ANSWER_WITH_RAG_TEMPLATE,
    QA_NO_RAG_FALLBACK_TEMPLATE,
    QA_TITLE_GENERATION_TEMPLATE,
)
from .task_gen import (
    TASK_GENERATION_TEMPLATE,
    TASK_APPEND_TEMPLATE,
    DIFFICULTY_ASSESSMENT_TEMPLATE,
)
from .report import (
    REPORT_GENERATION_TEMPLATE,
    QA_TREND_DESCRIPTION_TEMPLATE,
    REPORT_EXECUTIVE_SUMMARY_TEMPLATE,
)
from .guardrails import (
    COURSE_SCOPE_CHECK_PROMPT,
    ANSWER_LEAK_CHECK_PROMPT,
    CONTENT_SAFETY_CHECK_PROMPT,
    JAILBREAK_PATTERNS,
)
from .few_shot import (
    QA_FEW_SHOT_EXAMPLES,
    TASK_FEW_SHOT_EXAMPLES,
    select_few_shots,
    format_few_shots,
)
from .output_schemas import (
    TaskQuestion,
    TaskOutput,
    HotQuestion,
    TeachingSuggestion,
    ReportOutput,
    STRUCTURED_OUTPUT_INSTRUCTION,
    inject_schema_instruction,
)
from .utils import PromptContext, inject_variables, format_knowledge_for_prompt

__all__ = [
    # System Prompts
    "QA_SYSTEM_PROMPT",
    "TASK_SYSTEM_PROMPT",
    "REPORT_SYSTEM_PROMPT",
    # QA Templates
    "QA_QUERY_REWRITE_TEMPLATE",
    "QA_INTENT_CLASSIFY_TEMPLATE",
    "QA_ANSWER_WITH_RAG_TEMPLATE",
    "QA_NO_RAG_FALLBACK_TEMPLATE",
    "QA_TITLE_GENERATION_TEMPLATE",
    # Task Templates
    "TASK_GENERATION_TEMPLATE",
    "TASK_APPEND_TEMPLATE",
    "DIFFICULTY_ASSESSMENT_TEMPLATE",
    # Report Templates
    "REPORT_GENERATION_TEMPLATE",
    "QA_TREND_DESCRIPTION_TEMPLATE",
    "REPORT_EXECUTIVE_SUMMARY_TEMPLATE",
    # Guardrail Prompts
    "COURSE_SCOPE_CHECK_PROMPT",
    "ANSWER_LEAK_CHECK_PROMPT",
    "CONTENT_SAFETY_CHECK_PROMPT",
    "JAILBREAK_PATTERNS",
    # Few-Shot
    "QA_FEW_SHOT_EXAMPLES",
    "TASK_FEW_SHOT_EXAMPLES",
    "select_few_shots",
    "format_few_shots",
    # Output Schemas
    "TaskQuestion",
    "TaskOutput",
    "HotQuestion",
    "TeachingSuggestion",
    "ReportOutput",
    "STRUCTURED_OUTPUT_INSTRUCTION",
    "inject_schema_instruction",
    # Utils
    "PromptContext",
    "inject_variables",
    "format_knowledge_for_prompt",
]
