# backend/app/main.py — FastAPI 应用入口（lifespan + CORS + 异常处理器 + 路由注册）
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.api.router import api_router
from app.config import settings
from app.exceptions import AppException
from app.schemas.common import ErrorInfo, ErrorDetail


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。
    启动时：不做额外操作（生产用 Alembic 迁移）。
    关闭时：释放数据库连接池。
    """
    yield
    # 释放连接池（如已初始化 engine）
    try:
        from app.database import engine
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="EduAgent API",
    description="课程资源与教学任务智能体后端接口",
    version="1.0.0",
    lifespan=lifespan,
)

# ============================================================
# CORS 配置
# ============================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS_LIST,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

LOCAL_STORAGE_DIR = Path(__file__).resolve().parent.parent / "storage"
LOCAL_STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/files", StaticFiles(directory=str(LOCAL_STORAGE_DIR)), name="files")

# ============================================================
# 全局异常处理器
# ============================================================


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """捕获所有 AppException 子类，转换为统一错误格式。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": exc.status_code,
            "message": exc.message,
            "data": None,
            "error": {
                "type": exc.error_type,
                "details": exc.details,
            },
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：未预期的异常统一返回 500。"""
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "data": None,
            "error": {
                "type": "INTERNAL_ERROR",
                "details": [{"message": str(exc)}],
            },
        },
    )

# ============================================================
# 路由注册
# ============================================================
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """健康检查端点。"""
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}
