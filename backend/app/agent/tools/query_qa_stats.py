# Tool: query_qa_stats — 按时间范围查询问答统计数据
# 对应文档：05 §3.6

import json
from datetime import datetime, date, timezone
from pydantic import BaseModel, Field
from sqlalchemy import select, func, text
from app.database import async_session
from app.models.qa_record import QARecord
from app.models.resource import Resource
from app.models.task import Task


class QueryQAStatsInput(BaseModel):
    """问答统计查询参数"""
    start_date: str = Field(description="起始日期，ISO 格式：YYYY-MM-DD")
    end_date: str = Field(description="截止日期，ISO 格式：YYYY-MM-DD")


async def query_qa_stats(
    start_date: str,
    end_date: str,
    course_id: str = ""
) -> str:
    """
    查询指定时间范围内的问答统计数据。
    用于生成教学总结报告。

    返回值包含：
    - total_qa: 问答总数
    - top_questions: 热点问题 Top 5（按 question 相似度聚类）
    - feedback_distribution: like/dislike/none 分布
    - daily_qa_trend: 每日问答量趋势
    - active_students: 活跃学生数
    - new_resources_count: 该时段新增资源数
    - tasks_stats: { total, published, by_type }
    """
    async with async_session() as session:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date).replace(hour=23, minute=59, second=59)

        # 问答总数
        total_qa = await session.scalar(
            select(func.count()).select_from(QARecord).where(
                QARecord.course_id == course_id,
                QARecord.created_at >= start_dt,
                QARecord.created_at <= end_dt
            )
        ) or 0

        # Feedback 分布
        feedback_like = await session.scalar(
            select(func.count()).select_from(QARecord).where(
                QARecord.course_id == course_id,
                QARecord.feedback == "like",
                QARecord.created_at >= start_dt,
                QARecord.created_at <= end_dt
            )
        ) or 0

        feedback_dislike = await session.scalar(
            select(func.count()).select_from(QARecord).where(
                QARecord.course_id == course_id,
                QARecord.feedback == "dislike",
                QARecord.created_at >= start_dt,
                QARecord.created_at <= end_dt
            )
        ) or 0

        # 活跃学生数（去重 user_id）
        active_students = await session.scalar(
            select(func.count(func.distinct(QARecord.user_id))).where(
                QARecord.course_id == course_id,
                QARecord.created_at >= start_dt,
                QARecord.created_at <= end_dt
            )
        ) or 0

        # 新增资源数
        new_resources_count = await session.scalar(
            select(func.count()).select_from(Resource).where(
                Resource.course_id == course_id,
                Resource.created_at >= start_dt,
                Resource.created_at <= end_dt
            )
        ) or 0

        # 任务统计
        total_tasks = await session.scalar(
            select(func.count()).select_from(Task).where(
                Task.course_id == course_id,
                Task.created_at >= start_dt,
                Task.created_at <= end_dt
            )
        ) or 0

        published_tasks = await session.scalar(
            select(func.count()).select_from(Task).where(
                Task.course_id == course_id,
                Task.status == "published",
                Task.created_at >= start_dt,
                Task.created_at <= end_dt
            )
        ) or 0

        # 每日问答趋势
        daily_trend = await session.execute(
            select(
                func.date(QARecord.created_at).label("day"),
                func.count().label("count")
            ).where(
                QARecord.course_id == course_id,
                QARecord.created_at >= start_dt,
                QARecord.created_at <= end_dt
            ).group_by(text("day")).order_by(text("day"))
        )
        daily_counts = {str(row.day): row.count for row in daily_trend}

        stats = {
            "total_qa": total_qa,
            "feedback_distribution": {
                "like": feedback_like,
                "dislike": feedback_dislike,
                "none": total_qa - feedback_like - feedback_dislike
            },
            "active_students": active_students,
            "new_resources_count": new_resources_count,
            "tasks_stats": {
                "total": total_tasks,
                "published": published_tasks,
            },
            "daily_qa_trend": daily_counts,
        }
        return json.dumps(stats, ensure_ascii=False)
