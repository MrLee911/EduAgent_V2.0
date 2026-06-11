# backend/app/schemas/report.py — M06 教学报告 Pydantic Schema（请求/响应模型）
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date


# ── 请求 Schema ──

class ReportGenerateRequest(BaseModel):
    """生成报告请求体（对应 04 §7.1）"""
    report_type: str = Field(..., description="weekly / monthly / semester")
    start_date: Optional[str] = Field(None, description="统计起始日期，ISO 8601 格式如 2026-06-02")
    end_date: Optional[str] = Field(None, description="统计截止日期，不能晚于今天")


# ── 响应内嵌 Schema ──

class ReportGeneratorBrief(BaseModel):
    """生成者简要信息"""
    id: str
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TopQuestionItem(BaseModel):
    """热点问题项"""
    question: str
    count: int


class ReportStatistics(BaseModel):
    """报告统计数据"""
    total_tasks: int = 0
    published_tasks: int = 0
    total_qa: int = 0
    active_students: int = 0
    top_questions: list[TopQuestionItem] = []
    total_resources: int = 0
    new_resources: int = 0
    suggestions: list[str] = []


# ── 响应 Schema ──

class ReportResponse(BaseModel):
    """报告详情/生成响应（对应 04 §7.1 data / §7.3 data）"""
    id: str
    course_id: Optional[str] = None
    report_type: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    content: str = ""
    statistics: Optional[ReportStatistics] = None
    generated_by: Optional[ReportGeneratorBrief] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ReportListResponse(BaseModel):
    """报告列表项（对应 04 §7.2 data[]）"""
    id: str
    title: str
    report_type: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    generated_by: Optional[ReportGeneratorBrief] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}
