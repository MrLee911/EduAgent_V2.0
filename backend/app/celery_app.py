# backend/app/celery_app.py — Celery 异步任务队列配置（双队列 default + rag）
from celery import Celery
from app.config import settings

celery_app = Celery(
    "eduagent",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,            # 任务执行完成后才确认（防止崩溃丢失）
    worker_prefetch_multiplier=1,   # 每次只取 1 个任务（公平调度）
    task_soft_time_limit=300,       # 软超时 5 分钟
    task_time_limit=600,            # 硬超时 10 分钟
    # 队列路由
    task_routes={
        "app.tasks.rag_tasks.*": {"queue": "rag"},
    },
)

# 自动发现 tasks/ 目录下的任务
celery_app.autodiscover_tasks(["app.tasks"])
