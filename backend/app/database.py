# backend/app/database.py — 异步数据库会话配置（async_sessionmaker + get_db 依赖）
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import settings

# 异步引擎（连接池配置）
engine = create_async_engine(
    settings.DATABASE_URL,          # postgresql+asyncpg://user:pass@host:5432/db
    echo=settings.DEBUG,            # 开发环境打印 SQL
    pool_size=20,                   # 连接池大小
    max_overflow=10,                # 溢出连接数
    pool_pre_ping=True,             # 连接前检查有效性（避免 stale connection）
)

# 会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,         # commit 后不使对象过期（避免 MissingGreenlet）
)

# 别名 — 兼容内部模块的直接引用
async_session = AsyncSessionLocal


async def get_db() -> AsyncSession:
    """FastAPI 依赖注入：每个请求一个会话，请求结束后自动关闭。"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
