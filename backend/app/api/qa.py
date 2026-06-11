# backend/app/api/qa.py — M04 智能问答接口（6 端点，含 SSE 流式）
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import (
    get_current_user,
    verify_course_exists,
    verify_course_member,
)
from app.models.user import User
from app.models.course import Course
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.qa import (
    QAAskRequest, QAFeedbackRequest,
    QAResponse, QAHistoryItemResponse,
)
from app.services import qa_service

router = APIRouter()


# ── 5.1 课程问答（非流式）──
@router.post("/{course_id}/qa/ask", response_model=ApiResponse[QAResponse])
async def ask_question(
    data: QAAskRequest,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """课程问答（RAG 链路：改写→检索→重排→LLM生成→存储）"""
    result = await qa_service.ask_question(
        db, str(course.id), current_user, data,
    )
    return ApiResponse(data=result)


# ── 5.2 流式问答（SSE）──
@router.post("/{course_id}/qa/ask-stream")
async def ask_question_stream(
    data: QAAskRequest,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """流式问答（SSE: thinking→sources→token...→done/error）"""
    async def event_generator():
        async for event in qa_service.ask_question_stream(
            db, str(course.id), current_user, data,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 5.3 获取问答历史 ──
@router.get("/{course_id}/qa/history", response_model=ApiResponse[list[QAHistoryItemResponse]])
async def get_qa_history(
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    conversation_id: str | None = Query(None, description="按对话ID筛选"),
):
    """获取问答历史列表（个人）"""
    items, total = await qa_service.get_qa_history(
        db, str(course.id), current_user,
        page=page, page_size=page_size,
        conversation_id=conversation_id,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 5.4 获取问答详情 ──
@router.get("/{course_id}/qa/history/{qa_id}", response_model=ApiResponse[QAResponse])
async def get_qa_detail(
    qa_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取问答详情（含完整 answer 和 sources）"""
    result = await qa_service.get_qa_detail(db, str(course.id), qa_id)
    return ApiResponse(data=result)


# ── 5.5 提交反馈 ──
@router.post("/{course_id}/qa/history/{qa_id}/feedback", response_model=ApiResponse)
async def submit_feedback(
    qa_id: str,
    data: QAFeedbackRequest,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """提交问答反馈（like/dislike/none）"""
    await qa_service.submit_feedback(db, str(course.id), qa_id, data)
    return ApiResponse(message="反馈已记录", data=None)


# ── 5.6 清空对话 ──
@router.delete("/{course_id}/qa/conversation/{conversation_id}", response_model=ApiResponse)
async def clear_conversation(
    conversation_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    current_user: User = Depends(get_current_user),
):
    """清空对话上下文（Redis 缓存）"""
    await qa_service.clear_conversation(conversation_id)
    return ApiResponse(message="对话上下文已清空", data=None)
