# Celery 异步任务模块汇总导出
from .rag_tasks import process_document, rebuild_index, delete_resource_vectors

__all__ = [
    "process_document",
    "rebuild_index",
    "delete_resource_vectors",
]
