# backend/app/services/report_service.py — M06 教学报告业务逻辑
import uuid
import json
from datetime import date, datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
from app.models.user import User
from app.models.course import Course, CourseMember
from app.models.resource import Resource
from app.models.qa_record import QARecord
from app.models.task import Task
from app.models.report import Report
from app.models.enums import ReportType, TaskStatus, QAFeedback, CourseMemberRole
from app.schemas.report import ReportResponse, ReportListResponse
from app.exceptions import NotFoundException, ValidationException, AIServiceException
from app.config import settings
import httpx


def _format_report_list_item(report: Report) -> dict:
    """格式化报告列表项"""
    return {
        "id": str(report.id),
        "title": report.title,
        "report_type": report.report_type.value if hasattr(report.report_type, 'value') else str(report.report_type),
        "start_date": str(report.start_date) if report.start_date else None,
        "end_date": str(report.end_date) if report.end_date else None,
        "generated_by": {
            "id": str(report.generator.id),
            "display_name": report.generator.display_name,
        } if report.generator else None,
        "created_at": str(report.created_at) if report.created_at else None,
    }


def _format_report_detail(report: Report) -> dict:
    """格式化报告详情"""
    stats = report.statistics if isinstance(report.statistics, dict) else {}

    top_questions = [
        {"question": q.get("question", ""), "count": q.get("count", 0)}
        for q in stats.get("top_questions", [])
    ]
    suggestions = stats.get("suggestions", [])

    return {
        "id": str(report.id),
        "course_id": str(report.course_id),
        "report_type": report.report_type.value if hasattr(report.report_type, 'value') else str(report.report_type),
        "title": report.title,
        "start_date": str(report.start_date) if report.start_date else None,
        "end_date": str(report.end_date) if report.end_date else None,
        "content": report.content,
        "statistics": {
            "total_tasks": stats.get("total_tasks", 0),
            "published_tasks": stats.get("published_tasks", 0),
            "total_qa": stats.get("total_qa", 0),
            "active_students": stats.get("active_students", 0),
            "top_questions": top_questions,
            "total_resources": stats.get("total_resources", 0),
            "new_resources": stats.get("new_resources", 0),
            "suggestions": suggestions,
        },
        "generated_by": {
            "id": str(report.generator.id),
            "display_name": report.generator.display_name,
        } if report.generator else None,
        "created_at": str(report.created_at) if report.created_at else None,
    }


async def _collect_statistics(
    db: AsyncSession,
    course_id: str,
    start_date: date,
    end_date: date,
) -> dict:
    """收集课程统计数据"""
    # 任务统计
    total_tasks_q = select(func.count(Task.id)).where(
        Task.course_id == course_id,
    )
    total_tasks = (await db.execute(total_tasks_q)).scalar() or 0

    published_tasks_q = select(func.count(Task.id)).where(
        Task.course_id == course_id,
        Task.status == TaskStatus.PUBLISHED,
    )
    published_tasks = (await db.execute(published_tasks_q)).scalar() or 0

    # 问答统计（时间段内）
    total_qa_q = select(func.count(QARecord.id)).where(
        QARecord.course_id == course_id,
    )
    total_qa = (await db.execute(total_qa_q)).scalar() or 0

    # 活跃学生数
    active_q = select(func.count(func.distinct(CourseMember.user_id))).where(
        CourseMember.course_id == course_id,
        CourseMember.role == CourseMemberRole.STUDENT,
    )
    active_students = (await db.execute(active_q)).scalar() or 0

    # 资源统计
    total_res_q = select(func.count(Resource.id)).where(
        Resource.course_id == course_id,
    )
    total_resources = (await db.execute(total_res_q)).scalar() or 0

    new_res_q = select(func.count(Resource.id)).where(
        Resource.course_id == course_id,
    )
    new_resources = (await db.execute(new_res_q)).scalar() or 0

    # 热点问题 Top 5
    questions_result = await db.execute(
        select(QARecord.question, func.count(QARecord.id).label("cnt"))
        .where(QARecord.course_id == course_id)
        .group_by(QARecord.question)
        .order_by(desc("cnt"))
        .limit(5)
    )
    top_questions = [
        {"question": row[0][:50], "count": row[1]}
        for row in questions_result.all()
    ]

    return {
        "total_tasks": total_tasks,
        "published_tasks": published_tasks,
        "total_qa": total_qa,
        "active_students": active_students,
        "top_questions": top_questions,
        "total_resources": total_resources,
        "new_resources": new_resources,
    }


async def _call_report_llm(
    course_name: str,
    report_type: str,
    start_date: str,
    end_date: str,
    statistics: dict,
) -> tuple[str, list[str]]:
    """调用 LLM 生成报告内容"""
    type_names = {"weekly": "周报", "monthly": "月报", "semester": "学期总结"}
    type_name = type_names.get(report_type, report_type)

    system_prompt = (
        f"你是一个专业的教学助理。请根据提供的统计数据生成一份{type_name}。\n\n"
        "报告结构：\n"
        "1. 教学进度概览\n"
        "2. 资源使用情况\n"
        "3. 任务完成统计\n"
        "4. 学生提问热点分析\n"
        "5. 下阶段建议\n\n"
        "使用 Markdown 格式输出。"
    )

    stats_json = json.dumps(statistics, ensure_ascii=False, indent=2)
    user_prompt = (
        f"# 课程名称\n{course_name}\n\n"
        f"# 报告类型\n{type_name}\n"
        f"# 统计区间\n{start_date} ~ {end_date}\n\n"
        f"# 统计数据\n{stats_json}\n\n"
        "请生成完整的教学总结报告。在最后给出 2-3 条下阶段教学建议。"
    )

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.LLM_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.LLM_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": settings.LLM_MAX_TOKENS,
                "temperature": 0.7,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # 从报告中提取建议（简单解析）
        suggestions = []
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("- ") or line.startswith("* "):
                if len(line) > 10 and ("建议" in line or "应" in line or "建议" in line or "注意" in line):
                    suggestions.append(line[2:])
        if not suggestions:
            suggestions = ["建议持续关注学生的学习反馈，优化教学内容"]

        return content, suggestions[:3]


async def _generate_report_title(
    course_name: str,
    report_type: str,
    start_date: date,
    end_date: date,
) -> str:
    """生成报告标题"""
    type_names = {"weekly": "周教学总结", "monthly": "月度教学总结", "semester": "学期教学总结"}
    type_name = type_names.get(report_type, report_type)
    return f"{course_name} - {type_name}（{start_date} ~ {end_date}）"


def _default_report_dates(report_type: str) -> tuple[date, date]:
    end_date = date.today()
    days = {
        "weekly": 7,
        "monthly": 30,
        "semester": 180,
    }.get(report_type, 7)
    return end_date - timedelta(days=days - 1), end_date


async def _load_report_with_generator(db: AsyncSession, report_id: uuid.UUID | str) -> Report:
    result = await db.execute(
        select(Report)
        .options(selectinload(Report.generator))
        .where(Report.id == report_id)
    )
    return result.scalar_one()


async def generate_report(
    db: AsyncSession,
    course: Course,
    user: User,
    report_type: str,
    start_date_str: str | None,
    end_date_str: str | None,
) -> dict:
    """生成教学报告"""
    # 解析日期
    default_start, default_end = _default_report_dates(report_type)
    try:
        start_date = date.fromisoformat(start_date_str) if start_date_str else default_start
        end_date = date.fromisoformat(end_date_str) if end_date_str else default_end
    except ValueError:
        raise ValidationException(message="日期格式不正确，请使用 ISO 8601 格式")

    if end_date > date.today():
        raise ValidationException(message="截止日期不能晚于今天")
    if start_date > end_date:
        raise ValidationException(message="开始日期不能晚于结束日期")

    # 收集统计数据
    statistics = await _collect_statistics(db, str(course.id), start_date, end_date)

    # 检查是否有数据
    if (
        statistics["total_qa"] == 0
        and statistics["total_tasks"] == 0
        and statistics["total_resources"] == 0
    ):
        raise ValidationException(
            message="时间范围内无数据",
            details=[{"field": "start_date", "message": "所选时间范围内没有资源、问答和任务数据"}],
        )

    # LLM 生成报告
    try:
        content, suggestions = await _call_report_llm(
            course_name=course.name,
            report_type=report_type,
            start_date=str(start_date),
            end_date=str(end_date),
            statistics=statistics,
        )
    except Exception as e:
        raise AIServiceException(message=f"报告生成失败: {str(e)}")

    statistics["suggestions"] = suggestions

    # 生成标题
    title = await _generate_report_title(course.name, report_type, start_date, end_date)

    # 写入数据库
    report = Report(
        id=uuid.uuid4(),
        course_id=course.id,
        report_type=ReportType(report_type),
        start_date=start_date,
        end_date=end_date,
        title=title,
        content=content,
        statistics=statistics,
        generated_by=user.id,
    )
    db.add(report)
    await db.commit()
    report = await _load_report_with_generator(db, report.id)

    return _format_report_detail(report)


async def list_reports(
    db: AsyncSession,
    course_id: str,
    page: int = 1,
    page_size: int = 20,
    report_type: str | None = None,
) -> tuple[list[dict], int]:
    """获取报告列表"""
    conditions = [Report.course_id == course_id]

    if report_type:
        conditions.append(Report.report_type == report_type)

    total_q = select(func.count(Report.id)).where(and_(*conditions))
    total = (await db.execute(total_q)).scalar() or 0

    q = (
        select(Report)
        .options(selectinload(Report.generator))
        .where(and_(*conditions))
        .order_by(Report.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    reports = (await db.execute(q)).scalars().all()

    result = [_format_report_list_item(r) for r in reports]
    return result, total


async def get_report_detail(
    db: AsyncSession,
    report: Report,
) -> dict:
    """获取报告详情"""
    report = await _load_report_with_generator(db, report.id)
    return _format_report_detail(report)


async def export_report(
    report: Report,
    export_format: str = "md",
) -> tuple[bytes, str, str]:
    """导出报告为 MD 或 PDF 格式"""
    if export_format == "md":
        content = report.content.encode("utf-8")
        media_type = "text/markdown; charset=utf-8"
        filename = f"{report.title}.md"
        return content, media_type, filename
    elif export_format == "pdf":
        # 使用简单的 Markdown → PDF 转换（可使用 markdown2 + weasyprint）
        try:
            import markdown
            md_html = markdown.markdown(report.content)
            html = f"""
            <html><head><meta charset="utf-8"><title>{report.title}</title>
            <style>body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #333; }} pre {{ background: #f5f5f5; padding: 10px; }}</style></head>
            <body><h1>{report.title}</h1>{md_html}</body></html>"""

            # 简单返回 HTML 作为 PDF（生产环境使用 weasyprint）
            content = html.encode("utf-8")
            media_type = "text/html; charset=utf-8"
            filename = f"{report.title}.html"
            return content, media_type, filename
        except ImportError:
            content = report.content.encode("utf-8")
            media_type = "text/markdown; charset=utf-8"
            filename = f"{report.title}.md"
            return content, media_type, filename
    else:
        raise ValidationException(message=f"不支持的导出格式: {export_format}，支持 md / pdf")
