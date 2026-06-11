# Tool: get_course_stats — 获取课程基本统计数据
# 对应文档：05 §3.4

import json
from sqlalchemy import select, func
from app.database import async_session
from app.models.course import Course, CourseMember
from app.models.resource import Resource
from app.models.task import Task
from app.models.qa_record import QARecord


async def get_course_stats(course_id: str = "") -> str:
    """
    获取课程基本统计数据：学生人数、资源数、任务数、问答总数。
    用于让 Agent 了解课程规模和活跃度。

    返回值示例：
    {
        "member_count": 35,
        "resource_count": 12,
        "published_task_count": 8,
        "total_qa_count": 120
    }
    """
    async with async_session() as session:
        # 学生人数
        member_count = await session.scalar(
            select(func.count()).select_from(CourseMember).where(
                CourseMember.course_id == course_id,
                CourseMember.role == "student"
            )
        ) or 0

        # 资源数
        resource_count = await session.scalar(
            select(func.count()).select_from(Resource).where(
                Resource.course_id == course_id,
                Resource.status == "ready"
            )
        ) or 0

        # 已发布任务数
        published_task_count = await session.scalar(
            select(func.count()).select_from(Task).where(
                Task.course_id == course_id,
                Task.status == "published"
            )
        ) or 0

        # 问答总数
        total_qa_count = await session.scalar(
            select(func.count()).select_from(QARecord).where(
                QARecord.course_id == course_id
            )
        ) or 0

        stats = {
            "member_count": member_count,
            "resource_count": resource_count,
            "published_task_count": published_task_count,
            "total_qa_count": total_qa_count,
        }
        return json.dumps(stats, ensure_ascii=False)
