# backend/app/exceptions.py — 统一异常体系（AppException 基类 + 10 个子类）
from typing import Any


class AppException(Exception):
    """应用基础异常——所有自定义异常继承此类。"""

    def __init__(self, status_code: int, error_type: str, message: str, details: list[dict[str, Any]] | None = None):
        self.status_code = status_code
        self.error_type = error_type
        self.message = message
        self.details = details or [{"message": message}]


class NotFoundException(AppException):
    """资源不存在 (404)。用法：raise NotFoundException(resource="课程", id=course_id)"""

    def __init__(self, resource: str, id: str | None = None):
        msg = f"{resource}不存在" + (f": {id}" if id else "")
        super().__init__(status_code=404, error_type=f"{resource.upper()}_NOT_FOUND", message=msg)


class ForbiddenException(AppException):
    """权限不足 (403)。"""

    def __init__(self, message: str = "你没有权限执行此操作"):
        super().__init__(status_code=403, error_type="FORBIDDEN", message=message)


class UnauthorizedException(AppException):
    """未认证 (401)。"""

    def __init__(self, message: str = "请先登录", error_type: str = "UNAUTHORIZED"):
        super().__init__(status_code=401, error_type=error_type, message=message)


class ConflictException(AppException):
    """资源冲突 (409)。如：用户名已存在、已加入课程等。"""

    def __init__(self, message: str = "资源冲突"):
        super().__init__(status_code=409, error_type="CONFLICT", message=message)


class ValidationException(AppException):
    """请求参数校验失败 (422)。"""

    def __init__(self, message: str = "请求参数校验失败", details: list[dict[str, Any]] | None = None):
        super().__init__(status_code=422, error_type="VALIDATION_ERROR", message=message, details=details)


class AIServiceException(AppException):
    """AI 服务异常 (502)。"""

    def __init__(self, message: str = "AI 服务暂不可用，请稍后重试"):
        super().__init__(status_code=502, error_type="AI_SERVICE_ERROR", message=message)


class KnowledgeBaseEmptyException(AppException):
    """知识库为空 (400)。"""

    def __init__(self):
        super().__init__(
            status_code=400,
            error_type="KNOWLEDGE_BASE_EMPTY",
            message="该课程暂无资源，请先上传教学资料",
        )


class ResourceProcessingException(AppException):
    """资源处理失败 (422)。"""

    def __init__(self, message: str = "资源处理失败"):
        super().__init__(status_code=422, error_type="RESOURCE_PROCESSING_ERROR", message=message)


class TaskStatusException(AppException):
    """任务状态异常 (422)。如：归档已归档的任务。"""

    def __init__(self, message: str = "任务状态异常"):
        super().__init__(status_code=422, error_type="TASK_STATUS_ERROR", message=message)


class CourseAccessException(AppException):
    """课程访问异常 (403)。如：非课程成员。"""

    def __init__(self, message: str = "你不是该课程的成员"):
        super().__init__(status_code=403, error_type="COURSE_ACCESS_DENIED", message=message)
