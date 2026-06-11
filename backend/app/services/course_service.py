# backend/app/services/course_service.py — M02 课程管理业务逻辑
import uuid
import secrets
import string
import shutil
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.course import Course, CourseMember
from app.models.enums import UserRole, CourseStatus, CourseMemberRole
from app.models.resource import Resource
from app.models.qa_record import QARecord
from app.models.task import Task
from app.models.report import Report
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseDeleteConfirm, CourseJoinRequest,
    CourseListResponse, CourseDetailResponse, CourseCreateResponse,
    CourseJoinResponse, CourseMemberResponse, CourseStats, TeacherBrief,
    CourseMemberAddRequest,
)
from app.exceptions import (
    NotFoundException, ForbiddenException, ConflictException, ValidationException,
)
from app.rag.vector_store import get_or_create_collection, delete_collection

LOCAL_RESOURCE_ROOT = Path(__file__).resolve().parent.parent.parent / "storage" / "resources"


def _generate_course_code() -> str:
    """生成6位随机课程码（大写字母+数字）"""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(6))


def _course_to_list_response(course: Course, member_count: int = 0, my_role: str | None = None) -> dict:
    """将 Course 模型转换为列表响应 dict"""
    return {
        "id": str(course.id),
        "name": course.name,
        "code": course.code,
        "semester": course.semester,
        "teacher": {
            "id": str(course.teacher.id),
            "display_name": course.teacher.display_name,
            "username": course.teacher.username,
        } if course.teacher else None,
        "member_count": member_count,
        "my_role": my_role,
        "status": course.status.value if hasattr(course.status, 'value') else str(course.status),
        "created_at": str(course.created_at) if course.created_at else None,
    }


async def create_course(db: AsyncSession, teacher: User, data: CourseCreate) -> dict:
    """创建课程：生成课程码 → 写入 courses → 写入 course_members → 创建 ChromaDB Collection"""
    # 生成唯一课程码
    for _ in range(10):  # 最多重试 10 次
        code = _generate_course_code()
        exists = await db.execute(select(Course).where(Course.code == code))
        if not exists.scalar_one_or_none():
            break
    else:
        raise ValidationException(message="生成课程码失败，请重试")

    course = Course(
        id=uuid.uuid4(),
        name=data.name,
        code=code,
        description=data.description or "",
        semester=data.semester or "",
        teacher_id=teacher.id,
        cover_image=data.cover_image,
        status=CourseStatus.ACTIVE,
    )
    db.add(course)

    # 自动将教师加入为成员
    member = CourseMember(
        id=uuid.uuid4(),
        course_id=course.id,
        user_id=teacher.id,
        role=CourseMemberRole.TEACHER,
    )
    db.add(member)

    await db.flush()

    # 创建 ChromaDB Collection（非阻塞，失败不影响主流程）
    try:
        await get_or_create_collection(str(course.id))
    except Exception:
        pass

    await db.commit()
    await db.refresh(course)

    return {
        "id": str(course.id),
        "name": course.name,
        "code": course.code,
        "description": course.description,
        "semester": course.semester,
        "teacher_id": str(course.teacher_id),
        "cover_image": course.cover_image,
        "status": course.status.value,
        "created_at": str(course.created_at) if course.created_at else None,
        "updated_at": str(course.updated_at) if course.updated_at else None,
    }


async def list_courses(
    db: AsyncSession,
    user: User,
    page: int = 1,
    page_size: int = 20,
    role_filter: str | None = None,
    status: str | None = None,
    keyword: str | None = None,
) -> tuple[list[dict], int]:
    """获取课程列表（支持角色筛选、状态筛选、关键词搜索）"""
    conditions = []

    if role_filter:
        if user.role == UserRole.ADMIN:
            # 管理员查看所有课程
            pass
        elif role_filter == "teaching":
            conditions.append(Course.teacher_id == user.id)
        elif role_filter == "joined":
            member_course_ids = (
                select(CourseMember.course_id)
                .where(CourseMember.user_id == user.id)
            )
            conditions.append(Course.id.in_(member_course_ids))
    elif user.role == UserRole.STUDENT:
        # 学生端默认展示全部可加入课程，方便自主选择学习。
        conditions.append(Course.status == CourseStatus.ACTIVE)
    elif user.role != UserRole.ADMIN:
        # 非管理员默认只看自己相关的课程
        member_course_ids = (
            select(CourseMember.course_id)
            .where(CourseMember.user_id == user.id)
        )
        conditions.append(
            or_(Course.teacher_id == user.id, Course.id.in_(member_course_ids))
        )

    if status:
        conditions.append(Course.status == status)

    if keyword:
        conditions.append(Course.name.ilike(f"%{keyword}%"))

    # 总数
    total_q = select(func.count(Course.id))
    if conditions:
        total_q = total_q.where(*conditions)
    total = (await db.execute(total_q)).scalar() or 0

    # 分页查询
    q = select(Course).options(selectinload(Course.teacher))
    if conditions:
        q = q.where(*conditions)
    q = q.order_by(Course.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    courses = (await db.execute(q)).scalars().all()

    # 统计每个课程的成员数
    result = []
    for course in courses:
        member_count_q = select(func.count(CourseMember.id)).where(CourseMember.course_id == course.id)
        member_count = (await db.execute(member_count_q)).scalar() or 0
        my_role = None
        if course.teacher_id == user.id:
            my_role = "teacher"
        elif user.role == UserRole.ADMIN:
            my_role = "admin"
        else:
            member = (await db.execute(
                select(CourseMember).where(
                    CourseMember.course_id == course.id,
                    CourseMember.user_id == user.id,
                )
            )).scalar_one_or_none()
            if member:
                my_role = member.role.value if hasattr(member.role, 'value') else str(member.role)
        result.append(_course_to_list_response(course, member_count, my_role))

    return result, total


async def get_course_detail(
    db: AsyncSession,
    course: Course,
    user: User,
) -> dict:
    """获取课程详情（含统计信息和当前用户角色）"""
    course = (await db.execute(
        select(Course)
        .options(selectinload(Course.teacher))
        .where(Course.id == course.id)
    )).scalar_one()

    # 统计信息
    member_count = (await db.execute(
        select(func.count(CourseMember.id)).where(CourseMember.course_id == course.id)
    )).scalar() or 0
    resource_count = (await db.execute(
        select(func.count(Resource.id)).where(Resource.course_id == course.id)
    )).scalar() or 0
    task_count = (await db.execute(
        select(func.count(Task.id)).where(Task.course_id == course.id)
    )).scalar() or 0
    qa_count = (await db.execute(
        select(func.count(QARecord.id)).where(QARecord.course_id == course.id)
    )).scalar() or 0

    # 当前用户角色
    my_role = None
    if course.teacher_id == user.id:
        my_role = "teacher"
    elif user.role == UserRole.ADMIN:
        my_role = "admin"
    else:
        member_result = await db.execute(
            select(CourseMember).where(
                CourseMember.course_id == course.id,
                CourseMember.user_id == user.id,
            )
        )
        member = member_result.scalar_one_or_none()
        if member:
            my_role = member.role.value if hasattr(member.role, 'value') else str(member.role)

    return {
        "id": str(course.id),
        "name": course.name,
        "code": course.code,
        "description": course.description,
        "semester": course.semester,
        "cover_image": course.cover_image,
        "status": course.status.value if hasattr(course.status, 'value') else str(course.status),
        "teacher": {
            "id": str(course.teacher.id),
            "display_name": course.teacher.display_name,
            "username": course.teacher.username,
            "email": course.teacher.email,
        } if course.teacher else None,
        "stats": {
            "member_count": member_count,
            "resource_count": resource_count,
            "task_count": task_count,
            "qa_count": qa_count,
        },
        "my_role": my_role,
        "created_at": str(course.created_at) if course.created_at else None,
        "updated_at": str(course.updated_at) if course.updated_at else None,
    }


async def update_course(
    db: AsyncSession,
    course: Course,
    data: CourseUpdate,
) -> dict:
    """更新课程信息"""
    if data.name is not None:
        course.name = data.name
    if data.description is not None:
        course.description = data.description
    if data.semester is not None:
        course.semester = data.semester
    if data.cover_image is not None:
        course.cover_image = data.cover_image
    if data.status is not None:
        if data.status not in ("active", "archived"):
            raise ValidationException(message="status 必须是 active 或 archived")
        course.status = CourseStatus(data.status)

    await db.commit()
    await db.refresh(course)

    return {
        "id": str(course.id),
        "name": course.name,
        "code": course.code,
        "description": course.description,
        "semester": course.semester,
        "cover_image": course.cover_image,
        "status": course.status.value if hasattr(course.status, 'value') else str(course.status),
        "teacher": {
            "id": str(course.teacher.id),
            "display_name": course.teacher.display_name,
            "username": course.teacher.username,
            "email": course.teacher.email,
        } if course.teacher else None,
        "stats": None,
        "my_role": "teacher",
        "created_at": str(course.created_at) if course.created_at else None,
        "updated_at": str(course.updated_at) if course.updated_at else None,
    }


async def delete_course(
    db: AsyncSession,
    course: Course,
    confirm: bool,
    confirm_text: str,
) -> None:
    """删除课程及所有关联数据（级联清理）"""
    allowed_confirm_texts = {course.name, "我确认删除此课程及其所有数据"}
    if not confirm or confirm_text not in allowed_confirm_texts:
        raise ValidationException(message="未通过二次确认校验")

    course_id = str(course.id)

    # 1. 删除 ChromaDB Collection
    try:
        delete_collection(course_id)
    except Exception:
        pass

    # 2. 删除本地保存的课程资源文件夹：
    # storage/resources/{user_id}/{course_id}/{resource_id}/file
    if LOCAL_RESOURCE_ROOT.exists():
        for user_dir in LOCAL_RESOURCE_ROOT.iterdir():
            course_dir = user_dir / course_id
            if course_dir.exists():
                shutil.rmtree(course_dir, ignore_errors=True)

    # 3-6. 数据库级联删除（ORM cascade="all, delete-orphan" 自动处理
    #     resources, chunks, qa_records, tasks, reports, course_members）
    # 7. 删除 course 自身
    await db.delete(course)
    await db.commit()

    # MinIO 文件删除由 Celery 后台任务处理


async def join_course(
    db: AsyncSession,
    user: User,
    data: CourseJoinRequest,
) -> dict:
    """通过课程码加入课程"""
    code_upper = data.course_code.upper()

    result = await db.execute(
        select(Course).where(Course.code == code_upper)
    )
    course = result.scalar_one_or_none()
    if not course:
        raise NotFoundException(resource="课程码", id=data.course_code)

    if user.role == UserRole.ADMIN:
        raise ValidationException(message="管理员不需要加入课程")

    # 检查是否已是成员
    existing = await db.execute(
        select(CourseMember).where(
            CourseMember.course_id == course.id,
            CourseMember.user_id == user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(message="你已是该课程成员")

    # 检查课程是否已归档
    if course.status == CourseStatus.ARCHIVED:
        raise ValidationException(message="课程已归档，不允许新成员加入")

    # 学生不能加入自己的课程
    if course.teacher_id == user.id:
        raise ConflictException(message="你已是该课程的教师")

    member = CourseMember(
        id=uuid.uuid4(),
        course_id=course.id,
        user_id=user.id,
        role=CourseMemberRole.STUDENT,
    )
    db.add(member)
    await db.commit()

    return {
        "course_id": str(course.id),
        "course_name": course.name,
        "role": "student",
        "joined_at": str(member.joined_at) if member.joined_at else None,
    }


async def get_course_members(
    db: AsyncSession,
    course: Course,
) -> list[dict]:
    """获取课程成员列表"""
    result = await db.execute(
        select(CourseMember)
        .options(selectinload(CourseMember.user))
        .where(CourseMember.course_id == course.id)
        .order_by(CourseMember.joined_at.asc())
    )
    members = result.scalars().all()

    return [
        {
            "id": str(member.id),
            "user": {
                "id": str(member.user.id),
                "username": member.user.username,
                "display_name": member.user.display_name,
                "email": member.user.email,
            } if member.user else None,
            "role": member.role.value if hasattr(member.role, 'value') else str(member.role),
            "joined_at": str(member.joined_at) if member.joined_at else None,
        }
        for member in members
    ]


async def add_course_student(
    db: AsyncSession,
    course: Course,
    data: CourseMemberAddRequest,
) -> dict:
    """教师按用户名或邮箱添加学生到课程。"""
    identifier = data.identifier.strip()
    if not identifier:
        raise ValidationException(message="请输入学生用户名或邮箱")

    user_result = await db.execute(
        select(User).where(
            or_(User.username == identifier, User.email == identifier)
        )
    )
    student = user_result.scalar_one_or_none()
    if not student:
        raise NotFoundException(resource="学生", id=identifier)
    if student.role != UserRole.STUDENT:
        raise ValidationException(message="只能添加学生账号")
    if not student.is_active:
        raise ValidationException(message="该学生账号已被禁用")
    if course.status == CourseStatus.ARCHIVED:
        raise ValidationException(message="课程已归档，不允许添加学生")

    existing = await db.execute(
        select(CourseMember).where(
            CourseMember.course_id == course.id,
            CourseMember.user_id == student.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException(message="该学生已在课程中")

    member = CourseMember(
        id=uuid.uuid4(),
        course_id=course.id,
        user_id=student.id,
        role=CourseMemberRole.STUDENT,
    )
    db.add(member)
    await db.commit()
    await db.refresh(member)

    return {
        "id": str(member.id),
        "user": {
            "id": str(student.id),
            "username": student.username,
            "display_name": student.display_name,
            "email": student.email,
        },
        "role": "student",
        "joined_at": str(member.joined_at) if member.joined_at else None,
    }


async def remove_course_member(
    db: AsyncSession,
    course: Course,
    member_id: str,
) -> None:
    """教师从课程中移出学生成员。"""
    result = await db.execute(
        select(CourseMember).where(
            CourseMember.id == member_id,
            CourseMember.course_id == course.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundException(resource="课程成员", id=member_id)
    if member.role != CourseMemberRole.STUDENT:
        raise ValidationException(message="只能移出学生成员")

    await db.delete(member)
    await db.commit()


async def leave_course(
    db: AsyncSession,
    course: Course,
    user: User,
) -> None:
    """退出课程（学生退出；教师不可退出自己创建的课程）"""
    if course.teacher_id == user.id:
        raise ValidationException(message="教师不能退出自己创建的课程")

    if user.role == UserRole.ADMIN:
        raise ValidationException(message="管理员不能退出课程")

    result = await db.execute(
        select(CourseMember).where(
            CourseMember.course_id == course.id,
            CourseMember.user_id == user.id,
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise NotFoundException(resource="课程成员")

    await db.delete(member)
    await db.commit()
