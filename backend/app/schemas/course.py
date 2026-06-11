# backend/app/schemas/course.py — M02 课程管理 Pydantic Schema（请求/响应模型）
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── 请求 Schema ──

class CourseCreate(BaseModel):
    """创建课程请求体（对应 04 §3.1）"""
    name: str = Field(..., min_length=1, max_length=100, description="课程名称")
    description: str = Field(default="", max_length=5000, description="课程描述")
    semester: str = Field(default="", max_length=20, description="学期")
    cover_image: Optional[str] = Field(None, max_length=500, description="封面图 URL")


class CourseUpdate(BaseModel):
    """更新课程请求体（对应 04 §3.4，全部可选）"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="课程名称")
    description: Optional[str] = Field(None, max_length=5000, description="课程描述")
    semester: Optional[str] = Field(None, max_length=20, description="学期")
    cover_image: Optional[str] = Field(None, max_length=500, description="封面图 URL")
    status: Optional[str] = Field(None, description="active / archived")


class CourseDeleteConfirm(BaseModel):
    """删除课程二次确认（对应 04 §3.5）"""
    confirm: bool = Field(..., description="是否确认删除")
    confirm_text: str = Field(..., description="确认文本")


class CourseJoinRequest(BaseModel):
    """加入课程请求体（对应 04 §3.6）"""
    course_code: str = Field(..., min_length=6, max_length=6, description="6位课程码")


class CourseMemberAddRequest(BaseModel):
    """教师添加学生到课程。"""
    identifier: str = Field(..., min_length=1, max_length=255, description="学生用户名或邮箱")


# ── 响应内嵌 Schema ──

class TeacherBrief(BaseModel):
    """教师简要信息"""
    id: str
    display_name: Optional[str] = None
    username: str

    model_config = {"from_attributes": True}


class CourseMemberUserBrief(BaseModel):
    """成员用户简要信息"""
    id: str
    username: str
    display_name: Optional[str] = None
    email: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseStats(BaseModel):
    """课程统计信息"""
    member_count: int = 0
    resource_count: int = 0
    task_count: int = 0
    qa_count: int = 0


# ── 响应 Schema ──

class CourseListResponse(BaseModel):
    """课程列表项（对应 04 §3.2 data[]）"""
    id: str
    name: str
    code: str
    semester: str
    teacher: Optional[TeacherBrief] = None
    member_count: int = 0
    my_role: Optional[str] = None
    status: str
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseDetailResponse(BaseModel):
    """课程详情（对应 04 §3.3 data）"""
    id: str
    name: str
    code: str
    description: str
    semester: str
    cover_image: Optional[str] = None
    status: str
    teacher: Optional[TeacherBrief] = None
    stats: Optional[CourseStats] = None
    my_role: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseCreateResponse(BaseModel):
    """创建课程响应（对应 04 §3.1 data，含 code 字段）"""
    id: str
    name: str
    code: str
    description: str
    semester: str
    teacher_id: str
    cover_image: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    model_config = {"from_attributes": True}


class CourseJoinResponse(BaseModel):
    """加入课程响应（对应 04 §3.6 data）"""
    course_id: str
    course_name: str
    role: str
    joined_at: Optional[str] = None


class CourseMemberResponse(BaseModel):
    """课程成员列表项（对应 04 §3.7 data[]）"""
    id: str
    user: Optional[CourseMemberUserBrief] = None
    role: str
    joined_at: Optional[str] = None

    model_config = {"from_attributes": True}
