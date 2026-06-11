# Tool: get_course_resources — 获取课程资源列表
# 对应文档：05 §3.3

import json
from pydantic import BaseModel, Field
from typing import Optional


class GetCourseResourcesInput(BaseModel):
    """课程资源查询参数"""
    resource_type: Optional[str] = Field(
        default=None,
        description="资源类型：pdf/docx/pptx/md/txt，不传返回全部"
    )
    limit: int = Field(default=10, description="返回数量上限")


async def get_course_resources(
    resource_type: Optional[str] = None,
    limit: int = 10,
    course_id: str = ""
) -> str:
    """
    获取课程已上传的资源列表（仅返回 status=ready 的资源）。
    用于了解课程有哪些教学资料可供参考。
    """
    from app.database import async_session
    from app.models.resource import Resource
    from sqlalchemy import select

    async with async_session() as session:
        stmt = select(Resource).where(
            Resource.course_id == course_id,
            Resource.status == "ready"
        )
        if resource_type:
            stmt = stmt.where(Resource.file_type == resource_type)
        stmt = stmt.order_by(Resource.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        resources = result.scalars().all()

        data = [
            {
                "id": r.id,
                "file_name": r.file_name,
                "file_type": r.file_type,
                "summary": r.summary or "",
                "chunk_count": r.chunk_count,
                "created_at": r.created_at.isoformat() if r.created_at else ""
            }
            for r in resources
        ]
        return json.dumps(data, ensure_ascii=False)
