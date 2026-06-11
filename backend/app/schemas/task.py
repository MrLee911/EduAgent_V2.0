# backend/app/schemas/task.py — M05 教学任务 Pydantic Schema（请求/响应模型）
from pydantic import BaseModel, Field
from typing import Optional


# ── 请求 Schema ──

class TaskGenerateRequest(BaseModel):
    """生成任务请求体（对应 04 §6.1）"""
    topic: str = Field(..., min_length=1, max_length=200, description="主题/章节")
    task_type: str = Field(..., description="class_exercise / homework / lab_guide")
    difficulty: str = Field(default="medium", description="easy / medium / hard")
    additional_instructions: Optional[str] = Field(None, max_length=1000, description="额外要求")


class TaskUpdateRequest(BaseModel):
    """更新任务请求体（对应 04 §6.4，全部可选）"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="任务标题")
    content: Optional[str] = Field(None, description="任务内容（Markdown）")
    difficulty: Optional[str] = Field(None, description="easy / medium / hard")
    estimated_time: Optional[str] = Field(None, max_length=20, description="预计完成时间")


class TaskDeleteConfirm(BaseModel):
    """删除任务二次确认（对应 04 §6.8）"""
    confirm: bool = Field(..., description="是否确认删除")


# ── 响应内嵌 Schema ──

class TaskCreatorBrief(BaseModel):
    """创建者简要信息"""
    id: str
    display_name: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskReferenceResource(BaseModel):
    """任务生成的参考资源"""
    resource_id: str
    resource_name: str
    chunk_id: str


# ── 响应 Schema ──

class TaskResponse(BaseModel):
    """任务详情/生成响应（对应 04 §6.1 data / §6.3 data）"""
    id: str
    course_id: Optional[str] = None
    title: str
    task_type: str
    topic: str
    content: str = ""
    difficulty: str = "medium"
    estimated_time: str = ""
    reference_resources: list[TaskReferenceResource] = []
    status: str = "draft"
    created_by: Optional[TaskCreatorBrief] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """任务列表项（对应 04 §6.2 data[]，不含 content）"""
    id: str
    title: str
    task_type: str
    topic: str
    difficulty: str = "medium"
    estimated_time: str = ""
    status: str = "draft"
    created_by: Optional[TaskCreatorBrief] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class TaskStatusResponse(BaseModel):
    """任务状态变更响应（发布 / 归档）"""
    id: str
    status: str
    updated_at: Optional[str] = None
