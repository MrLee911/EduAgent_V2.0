# backend/app/schemas/common.py — 统一 API 响应 Schema（与 04 §1.2 格式完全一致）
from pydantic import BaseModel
from typing import Any, Optional, Generic, TypeVar

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """错误详情项"""
    field: Optional[str] = None
    message: str


class ErrorInfo(BaseModel):
    """错误信息对象"""
    type: str
    details: list[ErrorDetail] = []


class PaginationMeta(BaseModel):
    """分页元数据（仅分页接口出现）"""
    page: int
    page_size: int
    total: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    """统一成功/错误响应格式

    成功：{"code": 200, "message": "success", "data": {...}, "meta": {...}}
    错误：{"code": 404, "message": "课程不存在", "data": null, "error": {...}}
    """
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    meta: Optional[PaginationMeta] = None
    error: Optional[ErrorInfo] = None


class ApiResponseNoData(BaseModel):
    """无 data 字段的简化响应（用于 204 等场景）"""
    code: int = 200
    message: str = "success"
