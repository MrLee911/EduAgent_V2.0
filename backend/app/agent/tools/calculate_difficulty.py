# Tool: calculate_difficulty — 根据知识点和资料深度推荐难度等级
# 对应文档：05 §3.7

import json
from pydantic import BaseModel, Field
from sqlalchemy import select
from app.database import async_session
from app.models.resource import Resource, Chunk


class CalculateDifficultyInput(BaseModel):
    """难度推荐参数"""
    topic: str = Field(description="出题主题/章节")
    resource_ids: list[str] = Field(description="关联资源 ID 列表")
    task_type: str = Field(description="任务类型：class_exercise/homework/lab_guide")


async def calculate_difficulty(
    topic: str,
    resource_ids: list[str],
    task_type: str,
    course_id: str = ""
) -> str:
    """
    根据知识点主题和关联资料的深度，推荐合适的任务难度。
    评估维度：
    - 关联资源的数量和质量
    - 知识点的抽象程度（LLM 判断）
    - 知识点在课程中的位置（靠后 → 更难）
    - 任务类型的预期难度

    返回值：{"recommended": "medium", "confidence": 0.85, "reasoning": "..."}
    """
    # 获取关联资源的摘要信息用于分析
    async with async_session() as session:
        stmt = select(Resource).where(
            Resource.id.in_(resource_ids),
            Resource.course_id == course_id
        )
        result = await session.execute(stmt)
        resources = result.scalars().all()

    resource_summaries = []
    total_chunks = 0
    for r in resources:
        resource_summaries.append({
            "name": r.file_name,
            "type": r.file_type,
            "summary": r.summary or "",
            "chunk_count": r.chunk_count or 0
        })
        total_chunks += r.chunk_count or 0

    # 基本启发式评分
    # 资料越丰富 → 倾向于更难
    # 资源数越多 → 知识点可能越深
    base_score = min(len(resources), 5) + min(total_chunks / 10, 5)  # 0-10

    # 任务类型调整
    type_bonus = {"class_exercise": -2, "homework": 0, "lab_guide": 1}

    final_score = base_score + type_bonus.get(task_type, 0)

    if final_score <= 4:
        recommended = "easy"
        confidence = 0.7
    elif final_score <= 7:
        recommended = "medium"
        confidence = 0.75
    else:
        recommended = "hard"
        confidence = 0.8

    reasoning = f"关联{len(resources)}份资源({total_chunks}个片段)，任务类型{task_type}，综合评分{final_score:.1f}"

    result_dict = {
        "recommended": recommended,
        "confidence": confidence,
        "reasoning": reasoning,
        "resource_count": len(resources),
        "total_chunks": total_chunks,
    }
    return json.dumps(result_dict, ensure_ascii=False)
