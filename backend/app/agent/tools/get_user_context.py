# Tool: get_user_context — 获取学生历史问答记录和学习上下文
# 对应文档：05 §3.5

import json
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy import desc
from app.database import async_session
from app.models.qa_record import QARecord


class GetUserContextInput(BaseModel):
    """用户上下文查询参数"""
    user_id: str = Field(description="用户 ID")
    limit: int = Field(default=10, description="返回最近 N 条问答记录")


async def get_user_context(
    user_id: str,
    limit: int = 10,
    course_id: str = ""
) -> str:
    """
    获取指定学生在当前课程中的最近问答历史和学习上下文。
    用于：
    - 理解学生的知识薄弱点
    - 避免重复回答已经解释过的问题
    - 追踪学生的学习进度

    返回值包含：最近 N 条问答的 question、answer_excerpt、feedback、created_at
    """
    async with async_session() as session:
        stmt = (
            select(QARecord)
            .where(
                QARecord.course_id == course_id,
                QARecord.user_id == user_id
            )
            .order_by(desc(QARecord.created_at))
            .limit(limit)
        )
        result = await session.execute(stmt)
        records = result.scalars().all()

        data = [
            {
                "question": (r.question or "")[:200],
                "answer_excerpt": (r.answer or "")[:100],
                "feedback": r.feedback,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in records
        ]
        return json.dumps(data, ensure_ascii=False)
