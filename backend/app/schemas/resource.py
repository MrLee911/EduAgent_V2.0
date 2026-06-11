# backend/app/schemas/resource.py — M03 资源管理 Pydantic Schema（请求/响应模型）
from pydantic import BaseModel, Field
from typing import Optional


# ── 请求 Schema ──

class ResourceDeleteConfirm(BaseModel):
    """删除资源二次确认（对应 04 §4.8）"""
    confirm: bool = Field(..., description="是否确认删除")


# ── 响应内嵌 Schema ──

class UploaderBrief(BaseModel):
    """上传者简要信息"""
    id: str
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ResourceProgressInfo(BaseModel):
    """资源处理进度信息"""
    stage: str = ""
    stage_index: int = 0
    total_stages: int = 5
    chunk_count_done: int = 0
    chunk_count_total: int = 0


# ── 响应 Schema ──

class ResourceUploadResponseInner(BaseModel):
    """单个上传响应（对应 04 §4.1 data.resources[]）"""
    id: str
    file_name: str
    file_type: str
    file_size: int
    file_url: str = ""
    status: str
    created_at: Optional[str] = None


class ResourceUploadResponse(BaseModel):
    """上传/批量上传响应（对应 04 §4.1/4.2 data）"""
    resources: list[ResourceUploadResponseInner] = []


class ResourceListResponse(BaseModel):
    """资源列表项（对应 04 §4.3 data[]）"""
    id: str
    file_name: str
    file_type: str
    file_size: int
    file_url: str = ""
    status: str
    chunk_count: int = 0
    summary: str = ""
    uploaded_by: Optional[UploaderBrief] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ResourceDetailResponse(BaseModel):
    """资源详情（对应 04 §4.4 data）"""
    id: str
    file_name: str
    file_type: str
    file_size: int
    file_url: str = ""
    status: str
    chunk_count: int = 0
    summary: str = ""
    error_message: Optional[str] = None
    uploaded_by: Optional[UploaderBrief] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ResourceSearchResponse(BaseModel):
    """资源搜索结果项（同 04 §4.3 data[]）"""
    id: str
    file_name: str
    file_type: str
    file_size: int
    file_url: str = ""
    status: str
    chunk_count: int = 0
    summary: str = ""
    uploaded_by: Optional[UploaderBrief] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class ResourceStatusResponse(BaseModel):
    """资源处理状态（对应 04 §4.6 data）"""
    id: str
    status: str
    progress: Optional[ResourceProgressInfo] = None


class ResourceReprocessResponse(BaseModel):
    """重新处理响应（对应 04 §4.7 data）"""
    id: str
    status: str
