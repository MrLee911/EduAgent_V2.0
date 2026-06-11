# backend/app/api/reports.py — M06 教学报告接口（4 端点）
from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import (
    get_current_user,
    require_role,
    verify_course_exists,
    verify_course_member,
)
from app.models.user import User
from app.models.course import Course
from app.models.report import Report
from app.schemas.common import ApiResponse, PaginationMeta
from app.schemas.report import (
    ReportGenerateRequest, ReportResponse, ReportListResponse,
)
from app.services import report_service
from app.exceptions import NotFoundException

router = APIRouter()


# ── 7.1 生成教学总结报告 ──
@router.post("/{course_id}/reports/generate", response_model=ApiResponse[ReportResponse], status_code=201)
async def generate_report(
    data: ReportGenerateRequest,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """生成教学总结报告：统计→LLM生成→写入数据库"""
    result = await report_service.generate_report(
        db, course, current_user,
        report_type=data.report_type,
        start_date_str=data.start_date,
        end_date_str=data.end_date,
    )
    return ApiResponse(code=201, message="报告生成成功", data=result)


# ── 7.2 获取报告列表 ──
@router.get("/{course_id}/reports", response_model=ApiResponse[list[ReportListResponse]])
async def list_reports(
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    report_type: str | None = Query(None, description="weekly/monthly/semester"),
):
    """获取报告列表"""
    items, total = await report_service.list_reports(
        db, str(course.id),
        page=page, page_size=page_size,
        report_type=report_type,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return ApiResponse(
        data=items,
        meta=PaginationMeta(page=page, page_size=page_size, total=total, total_pages=total_pages),
    )


# ── 7.3 获取报告详情 ──
@router.get("/{course_id}/reports/{report_id}", response_model=ApiResponse[ReportResponse])
async def get_report_detail(
    report_id: str,
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """获取报告详情（含完整 content + statistics）"""
    from sqlalchemy import select
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.course_id == course.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException(resource="报告", id=report_id)
    detail = await report_service.get_report_detail(db, report)
    return ApiResponse(data=detail)


# ── 7.4 导出报告 ──
@router.get("/{course_id}/reports/{report_id}/export")
async def export_report(
    report_id: str,
    format: str = Query("md", description="md / pdf"),
    course: Course = Depends(verify_course_exists),
    _member=Depends(verify_course_member),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("teacher", "admin")),
):
    """导出报告（md / pdf 格式）"""
    from sqlalchemy import select
    result = await db.execute(
        select(Report).where(Report.id == report_id, Report.course_id == course.id)
    )
    report = result.scalar_one_or_none()
    if not report:
        raise NotFoundException(resource="报告", id=report_id)

    content, media_type, filename = await report_service.export_report(report, format)

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
