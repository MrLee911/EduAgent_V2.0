# backend/app/models/enums.py — PostgreSQL 枚举类型集中定义（Python Enum → SAEnum 映射）
import enum


class UserRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"
    ADMIN = "admin"


class CourseStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class CourseMemberRole(str, enum.Enum):
    TEACHER = "teacher"
    STUDENT = "student"


class ResourceFileType(str, enum.Enum):
    PDF = "pdf"
    DOCX = "docx"
    PPTX = "pptx"
    MD = "md"
    TXT = "txt"
    XLSX = "xlsx"


class ResourceStatus(str, enum.Enum):
    UPLOADING = "uploading"
    PARSING = "parsing"
    CHUNKING = "chunking"
    EMBEDDING = "embedding"
    READY = "ready"
    FAILED = "failed"


class QAFeedback(str, enum.Enum):
    NONE = "none"
    LIKE = "like"
    DISLIKE = "dislike"


class TaskType(str, enum.Enum):
    CLASS_EXERCISE = "class_exercise"
    HOMEWORK = "homework"
    LAB_GUIDE = "lab_guide"


class TaskDifficulty(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class TaskStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ReportType(str, enum.Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    SEMESTER = "semester"
