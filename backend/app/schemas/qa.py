# backend/app/schemas/qa.py — M04 智能问答 Pydantic Schema（请求/响应模型）
from pydantic import BaseModel, Field
from typing import Optional


# ── 请求 Schema ──

class QAAskRequest(BaseModel):
    """问答请求体（对应 04 §5.1）"""
    question: str = Field(..., min_length=1, max_length=2000, description="问题文本")
    conversation_id: Optional[str] = Field(None, description="对话ID（多轮对话），不传则新建")


class QAFeedbackRequest(BaseModel):
    """反馈请求体（对应 04 §5.5）"""
    feedback: str = Field(..., description="like / dislike / none")


# ── 响应内嵌 Schema ──

class QASourceItem(BaseModel):
    """引用来源项"""
    resource_id: str
    resource_name: str
    chunk_id: str
    chunk_index: int
    score: float
    text_preview: Optional[str] = None


# ── 响应 Schema ──

class QAResponse(BaseModel):
    """问答响应（对应 04 §5.1 data）"""
    id: str
    conversation_id: str
    question: str
    answer: str
    sources: list[QASourceItem] = []
    feedback: str = "none"
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class QAStreamSource(BaseModel):
    """SSE sources 事件中的来源（不含 text_preview）"""
    resource_id: str
    resource_name: str
    chunk_id: str
    chunk_index: int
    score: float


class QAStreamDoneData(BaseModel):
    """SSE done 事件数据"""
    id: str
    conversation_id: str
    sources: list[QAStreamSource] = []
    created_at: Optional[str] = None


class QAHistoryItemResponse(BaseModel):
    """问答历史列表项（对应 04 §5.3 data[]，含 answer_excerpt）"""
    id: str
    conversation_id: str = ""
    question: str
    answer_excerpt: str = ""
    feedback: str = "none"
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


# QADetailResponse 复用 QAResponse（含完整 answer + sources）
