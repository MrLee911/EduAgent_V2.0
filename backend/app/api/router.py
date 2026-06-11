# backend/app/api/router.py — API 路由汇总注册（include_router × 模块）
from fastapi import APIRouter
from app.api import auth
from app.api import courses
from app.api import resources
from app.api import qa
from app.api import tasks
from app.api import reports
from app.api import admin

api_router = APIRouter()

# M01: 认证模块
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
# M02: 课程模块
api_router.include_router(courses.router, prefix="/courses", tags=["课程"])
# M03: 资源模块
api_router.include_router(resources.router, prefix="/courses", tags=["资源"])
# M04: 问答模块
api_router.include_router(qa.router, prefix="/courses", tags=["问答"])
# M05: 任务模块
api_router.include_router(tasks.router, prefix="/courses", tags=["任务"])
# M06: 报告模块
api_router.include_router(reports.router, prefix="/courses", tags=["报告"])
# M07: 管理模块
api_router.include_router(admin.router, prefix="/admin", tags=["管理"])
