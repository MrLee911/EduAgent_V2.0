# backend/app/schemas/__init__.py — Pydantic Schema 汇总导出
from .common import ApiResponse, ApiResponseNoData, ErrorInfo, ErrorDetail, PaginationMeta
from .user import (
    UserCreate, LoginRequest, TokenResponse, UserResponse,
    RefreshRequest, TokenRefreshResponse, UserUpdate,
)
from .course import (
    CourseCreate, CourseUpdate, CourseDeleteConfirm, CourseJoinRequest,
    TeacherBrief, CourseMemberUserBrief, CourseStats,
    CourseListResponse, CourseDetailResponse, CourseCreateResponse,
    CourseJoinResponse, CourseMemberResponse,
)
from .resource import (
    ResourceDeleteConfirm, UploaderBrief, ResourceProgressInfo,
    ResourceUploadResponseInner, ResourceUploadResponse, ResourceListResponse,
    ResourceDetailResponse, ResourceSearchResponse,
    ResourceStatusResponse, ResourceReprocessResponse,
)
from .qa import (
    QAAskRequest, QAFeedbackRequest, QASourceItem,
    QAResponse, QAStreamSource, QAStreamDoneData, QAHistoryItemResponse,
)
from .task import (
    TaskGenerateRequest, TaskUpdateRequest, TaskDeleteConfirm,
    TaskCreatorBrief, TaskReferenceResource,
    TaskResponse, TaskListResponse, TaskStatusResponse,
)
from .report import (
    ReportGenerateRequest, ReportGeneratorBrief, TopQuestionItem,
    ReportStatistics, ReportResponse, ReportListResponse,
)

__all__ = [
    "ApiResponse", "ApiResponseNoData", "ErrorInfo", "ErrorDetail", "PaginationMeta",
    "UserCreate", "LoginRequest", "TokenResponse", "UserResponse",
    "RefreshRequest", "TokenRefreshResponse", "UserUpdate",
    "CourseCreate", "CourseUpdate", "CourseDeleteConfirm", "CourseJoinRequest",
    "TeacherBrief", "CourseMemberUserBrief", "CourseStats",
    "CourseListResponse", "CourseDetailResponse", "CourseCreateResponse",
    "CourseJoinResponse", "CourseMemberResponse",
    "ResourceDeleteConfirm", "UploaderBrief", "ResourceProgressInfo",
    "ResourceUploadResponseInner", "ResourceUploadResponse", "ResourceListResponse",
    "ResourceDetailResponse", "ResourceSearchResponse",
    "ResourceStatusResponse", "ResourceReprocessResponse",
    "QAAskRequest", "QAFeedbackRequest", "QASourceItem",
    "QAResponse", "QAStreamSource", "QAStreamDoneData", "QAHistoryItemResponse",
    "TaskGenerateRequest", "TaskUpdateRequest", "TaskDeleteConfirm",
    "TaskCreatorBrief", "TaskReferenceResource",
    "TaskResponse", "TaskListResponse", "TaskStatusResponse",
    "ReportGenerateRequest", "ReportGeneratorBrief", "TopQuestionItem",
    "ReportStatistics", "ReportResponse", "ReportListResponse",
]
