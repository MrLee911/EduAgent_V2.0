# Agent 执行器入口：所有 Agent 调用的统一入口
# 对应文档：05 §8

import json
import uuid
from typing import AsyncGenerator, Optional
from langchain_core.messages import HumanMessage

from .state import AgentState
from .workflows.qa_workflow import create_qa_workflow
from .workflows.task_workflow import create_task_workflow
from .workflows.report_workflow import create_report_workflow
from .tools.registry import create_tool_registry


class AgentExecutor:
    """
    智能体执行器 — 所有 Agent 调用的统一入口。

    被 FastAPI 路由层调用：
    - POST /api/v1/courses/{id}/qa/ask        → executor.run_qa()
    - POST /api/v1/courses/{id}/qa/ask-stream → executor.stream_qa()
    - POST /api/v1/courses/{id}/tasks/generate → executor.run_task()
    - POST /api/v1/courses/{id}/reports/generate → executor.run_report()
    """

    def __init__(self, course_id: str, user_id: str, course_name: str):
        self.course_id = course_id
        self.user_id = user_id
        self.course_name = course_name
        self.tools = create_tool_registry(course_id, user_id)

    async def run_qa(self, question: str, conversation_id: str = "") -> dict:
        """同步问答（非流式）"""
        initial_state: AgentState = {
            "course_id": self.course_id,
            "user_id": self.user_id,
            "course_name": self.course_name,
            "messages": [HumanMessage(content=question)],
            "retrieved_docs": [],
            "tool_calls": [],
            "guardrail_checks": [],
            "final_answer": None,
            "final_sources": [],
            "workflow_type": "qa",
            "step_count": 0,
            "error": None,
        }

        workflow = create_qa_workflow()
        result = await workflow.ainvoke(initial_state)

        return {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id or str(uuid.uuid4()),
            "question": question,
            "answer": result.get("final_answer", ""),
            "sources": result.get("final_sources", []),
            "step_count": result.get("step_count", 0),
            "guardrail_checks": result.get("guardrail_checks", []),
        }

    async def stream_qa(self, question: str, conversation_id: str = "") -> AsyncGenerator[str, None]:
        """流式问答（SSE）"""
        initial_state: AgentState = {
            "course_id": self.course_id,
            "user_id": self.user_id,
            "course_name": self.course_name,
            "messages": [HumanMessage(content=question)],
            "retrieved_docs": [],
            "tool_calls": [],
            "guardrail_checks": [],
            "final_answer": None,
            "final_sources": [],
            "workflow_type": "qa",
            "step_count": 0,
            "error": None,
        }

        workflow = create_qa_workflow()

        # 使用 astream_events 实现流式输出
        async for event in workflow.astream_events(initial_state, version="v2"):
            kind = event.get("event", "")
            name = event.get("name", "")
            data = event.get("data", {})

            if kind == "on_chat_model_stream":
                # LLM token 流
                chunk = data.get("chunk", {})
                if hasattr(chunk, "content") and chunk.content:
                    yield json.dumps({"type": "token", "content": chunk.content}, ensure_ascii=False)
            elif kind == "on_tool_start":
                yield json.dumps({"type": "tool_start", "tool_name": name}, ensure_ascii=False)
            elif kind == "on_tool_end":
                yield json.dumps({"type": "tool_end", "tool_name": name}, ensure_ascii=False)
            elif kind == "on_chain_end" and name == "LangGraph":
                output = data.get("output", {})
                yield json.dumps({
                    "type": "done",
                    "answer": output.get("final_answer", ""),
                    "sources": output.get("final_sources", []),
                    "step_count": output.get("step_count", 0),
                }, ensure_ascii=False)

    async def run_task(self, topic: str, task_type: str,
                       difficulty: str = "medium",
                       additional_instructions: str = "") -> dict:
        """生成教学任务"""
        initial_state: AgentState = {
            "course_id": self.course_id,
            "user_id": self.user_id,
            "course_name": self.course_name,
            "messages": [HumanMessage(content=topic)],
            "retrieved_docs": [],
            "tool_calls": [],
            "guardrail_checks": [],
            "final_answer": None,
            "final_sources": [],
            "workflow_type": task_type,
            "step_count": 0,
            "error": None,
        }

        workflow = create_task_workflow()
        result = await workflow.ainvoke(initial_state)

        # 解析 LLM 输出
        content = {}
        if result.get("final_answer"):
            try:
                content = json.loads(result["final_answer"]) if isinstance(result["final_answer"], str) else result["final_answer"]
            except json.JSONDecodeError:
                content = {"raw": result.get("final_answer", "")}

        return {
            "id": str(uuid.uuid4()),
            "topic": topic,
            "task_type": task_type,
            "difficulty": difficulty,
            "content": content,
            "reference_resources": result.get("final_sources", []),
            "step_count": result.get("step_count", 0),
        }

    async def run_report(self, report_type: str,
                         start_date: str, end_date: str) -> dict:
        """生成教学总结报告"""
        initial_state: AgentState = {
            "course_id": self.course_id,
            "user_id": self.user_id,
            "course_name": self.course_name,
            "messages": [HumanMessage(content=f"生成 {report_type} 报告：{start_date} ~ {end_date}")],
            "retrieved_docs": [],
            "tool_calls": [],
            "guardrail_checks": [],
            "final_answer": None,
            "final_sources": [],
            "workflow_type": "report_gen",
            "step_count": 0,
            "error": None,
        }

        workflow = create_report_workflow()
        result = await workflow.ainvoke(initial_state)

        # 解析 LLM 输出
        content = {}
        if result.get("final_answer"):
            try:
                content = json.loads(result["final_answer"]) if isinstance(result["final_answer"], str) else result["final_answer"]
            except json.JSONDecodeError:
                content = {"raw": result.get("final_answer", "")}

        return {
            "id": str(uuid.uuid4()),
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "content": content,
            "statistics": result.get("final_answer", {}),
            "step_count": result.get("step_count", 0),
        }


def get_agent_executor(course_id: str, user_id: str, course_name: str) -> AgentExecutor:
    """创建 AgentExecutor 实例的工厂函数（供 FastAPI Dependency 调用）"""
    return AgentExecutor(
        course_id=course_id,
        user_id=user_id,
        course_name=course_name
    )
