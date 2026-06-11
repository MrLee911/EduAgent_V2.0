# backend/app/config.py — 全局配置管理（Pydantic Settings，从 .env 读取）
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """EduAgent 全局配置。所有变量从 .env 自动加载。"""

    # ========== 项目 ==========
    APP_NAME: str = "edu-agent"
    APP_ENV: str = "development"
    DEBUG: bool = True

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "production", "prod", "false", "0", "no"}:
                return False
            if normalized in {"debug", "development", "dev", "true", "1", "yes"}:
                return True
        return value

    # ========== 服务端口 ==========
    NGINX_PORT: int = 80
    BACKEND_PORT: int = 8000
    MINIO_PORT: int = 9000
    MINIO_CONSOLE_PORT: int = 9001

    # ========== 数据库 ==========
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "edu_agent"
    POSTGRES_USER: str = "edu_agent"
    POSTGRES_PASSWORD: str = "change-me"

    @property
    def DATABASE_URL(self) -> str:
        """异步数据库 URL（SQLAlchemy async_sessionmaker 使用）。"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """同步数据库 URL（Alembic 迁移使用，不支持 asyncpg）。"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # ========== Redis ==========
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0  # type: ignore[assignment]  # pydantic coerce

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ========== Celery ==========
    @property
    def CELERY_BROKER_URL(self) -> str:
        return self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        return self.REDIS_URL

    # ========== ChromaDB ==========
    CHROMA_HOST: str = "chromadb"
    CHROMA_PORT: int = 8000

    # ========== 对象存储 (MinIO) ==========
    MINIO_ENDPOINT: str = "minio:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "edu-agent-files"
    MINIO_SECURE: bool = False

    # ========== LLM 配置 ==========
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_API_KEY: str = "sk-your-api-key-here"
    LLM_TEMPERATURE: float = 0.3
    LLM_MAX_TOKENS: int = 2048
    LLM_MAX_TASKS_TOKENS: int = 4096  # 任务生成/报告生成专用

    # ========== 护栏 LLM（可复用主 LLM） ==========
    GUARD_LLM_BASE_URL: Optional[str] = None
    GUARD_LLM_MODEL_NAME: Optional[str] = None
    GUARD_LLM_API_KEY: Optional[str] = None

    # ========== 查询改写 LLM（可复用主 LLM） ==========
    REWRITE_LLM_BASE_URL: Optional[str] = None
    REWRITE_LLM_MODEL_NAME: Optional[str] = None
    REWRITE_LLM_API_KEY: Optional[str] = None

    # ========== Embedding 模型（本地 BGE-M3） ==========
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DIMENSION: int = 1024
    EMBEDDING_DEVICE: str = "cpu"
    EMBEDDING_LOCAL_ONLY: bool = True

    # ========== Reranker 模型（本地 BGE-Reranker） ==========
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_DEVICE: str = "cpu"
    RERANKER_LOCAL_ONLY: bool = True

    # ========== JWT ==========
    JWT_SECRET_KEY: str = "change-me-jwt-secret-min-32-chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    # ========== 文件上传 ==========
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: str = "pdf,docx,pptx,md,txt,xlsx"

    # ========== CORS ==========
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173,http://localhost"

    # ========== 安全 ==========
    GUARDRAIL_INPUT_ENABLED: bool = True
    GUARDRAIL_OUTPUT_ENABLED: bool = True

    @property
    def ALLOWED_EXTENSIONS_LIST(self) -> list[str]:
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": (".env", "../.env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",
    }


settings = Settings()
