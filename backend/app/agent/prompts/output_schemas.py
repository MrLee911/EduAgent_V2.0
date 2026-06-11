# LLM 结构化输出 Schema：Pydantic BaseModel 定义 + JSON 格式注入工具
# 对应文档：06 §7

import json
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# === 7.1 任务生成输出 Schema ===

class TaskQuestion(BaseModel):
    """单道题目的结构"""
    number: int = Field(description="题号")
    type: Literal["choice", "short_answer", "programming", "fill_blank", "true_false"] = Field(description="题型")
    points: int = Field(description="分值")
    difficulty: Literal["easy", "medium", "hard"] = Field(description="难度标记")
    content: str = Field(description="题目正文，Markdown 格式")
    options: Optional[List[str]] = Field(default=None, description="选择题的选项（仅选择题需要）")
    correct_answer: str = Field(description="正确答案（放在教师审阅区）")
    answer_explanation: Optional[str] = Field(default=None, description="答案解析（1-2 句）")
    related_knowledge: str = Field(description="关联的知识点")
    source: str = Field(description="出题依据的来源：课件/教材名称 + 页数")


class TaskOutput(BaseModel):
    """任务生成的完整输出"""
    title: str = Field(description="任务标题")
    task_type: Literal["class_exercise", "homework", "lab_guide"]
    description: str = Field(description="任务说明（题量、总分、建议时间）")
    estimated_time: str = Field(description="建议用时（如：20分钟）")
    total_points: int = Field(description="总分")
    questions: List[TaskQuestion] = Field(description="题目列表")
    answer_section: str = Field(description="参考答案区（整个合并的 Markdown）")


# === 7.2 报告生成输出 Schema ===

class HotQuestion(BaseModel):
    """热点问题"""
    rank: int = Field(description="排名")
    topic: str = Field(description="知识点/主题")
    count: int = Field(description="提问次数")
    percentage: float = Field(description="占比（%）")
    trend: Literal["rising", "falling", "stable"] = Field(description="趋势")


class TeachingSuggestion(BaseModel):
    """教学改进建议"""
    target: str = Field(description="针对的章节/知识点")
    action: str = Field(description="建议的教学动作")
    expected_effect: str = Field(description="预期效果")


class ReportOutput(BaseModel):
    """教学报告的完整输出"""
    title: str = Field(description="报告标题")
    course_name: str
    report_period: str = Field(description="统计周期，如：2026春 第1-8周")
    overview: str = Field(description="教学进度概览")
    resource_analysis: str = Field(description="资源使用分析")
    task_completion: str = Field(description="任务完成情况")
    hot_questions: List[HotQuestion] = Field(description="学生提问热点 Top 5")
    suggestions: List[TeachingSuggestion] = Field(description="教学改进建议（3-5 条）")
    outlook: str = Field(description="下阶段教学展望")
    data_note: Optional[str] = Field(default=None, description="数据不足标注（如有）")


# === 7.3 结构化输出格式指令 ===

STRUCTURED_OUTPUT_INSTRUCTION = """
## 输出格式
你必须以严格的 JSON 格式输出，不要包含任何额外的解释文字或 markdown 代码块标记。
JSON 必须符合以下 schema：

{schema_json}

正确输出示例：
```json
{schema_example}
```

记住：只输出 JSON，不要输出 ```json 标记。"""


def inject_schema_instruction(prompt: str, schema_class) -> str:
    """
    将 Pydantic schema 注入到 prompt 中，强制 LLM 输出 JSON。
    """
    schema_json = json.dumps(schema_class.model_json_schema(), indent=2, ensure_ascii=False)
    example = _generate_example(schema_class)
    example_json = json.dumps(example, indent=2, ensure_ascii=False)

    instruction = STRUCTURED_OUTPUT_INSTRUCTION.format(
        schema_json=schema_json,
        schema_example=example_json
    )
    return prompt + "\n\n" + instruction


def _generate_example(schema_class) -> dict:
    """根据 schema 生成一个填充了示例值的 dict"""
    if schema_class.__name__ == "TaskOutput":
        return {
            "title": "Python 函数与递归 课堂练习",
            "task_type": "class_exercise",
            "description": "本次课堂练习共 5 题，满分 50 分，建议 20 分钟内完成",
            "estimated_time": "20分钟",
            "total_points": 50,
            "questions": [
                {
                    "number": 1,
                    "type": "choice",
                    "points": 10,
                    "difficulty": "easy",
                    "content": "以下哪个 Python 关键字用于定义函数？\nA. func\nB. def\nC. function\nD. define",
                    "options": ["A. func", "B. def", "C. function", "D. define"],
                    "correct_answer": "B",
                    "answer_explanation": "def 是 Python 定义函数的关键字",
                    "related_knowledge": "Python 函数定义",
                    "source": "课件《Python 函数》第 3 页"
                }
            ],
            "answer_section": "## 参考答案（仅供教师审阅）\n\n1. B ..."
        }
    elif schema_class.__name__ == "ReportOutput":
        return {
            "title": "Python 程序设计 2026春 第1-8周 教学总结",
            "course_name": "Python 程序设计",
            "report_period": "2026春 第1-8周",
            "overview": "本周期课程进展顺利，已完成前8章教学...",
            "resource_analysis": "累计上传资源 15 份...",
            "task_completion": "共发布任务 8 次...",
            "hot_questions": [
                {
                    "rank": 1,
                    "topic": "装饰器",
                    "count": 25,
                    "percentage": 20.8,
                    "trend": "rising"
                }
            ],
            "suggestions": [
                {
                    "target": "第5章 装饰器",
                    "action": "增加 15 分钟互动式案例讲解",
                    "expected_effect": "学生掌握装饰器原理，提问频次下降 50%"
                }
            ],
            "outlook": "下阶段重点攻克面向对象编程...",
            "data_note": None
        }
    return {}
