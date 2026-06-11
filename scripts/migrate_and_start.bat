@echo off
echo ==========================================
echo  EduAgent - 数据库迁移 & 后端启动
echo ==========================================
echo.
cd /d "d:\agent_project_v2\backend"

REM ========== 设置本地环境变量 ==========
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set REDIS_HOST=localhost
set REDIS_PORT=6379
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
set MINIO_ENDPOINT=localhost:9000

REM ========== 激活虚拟环境 ==========
call venv\Scripts\activate

REM ========== 运行数据库迁移 ==========
echo [1/2] 运行数据库迁移...
alembic upgrade head
if errorlevel 1 (
    echo.
    echo [错误] 数据库迁移失败！
    echo 请确认 Docker 基础设施是否正在运行：
    echo   docker compose up -d postgres redis chromadb minio
    pause
    exit /b 1
)
echo [OK] 数据库迁移完成
echo.

REM ========== 启动后端 ==========
echo [2/2] 启动后端服务...
echo.
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
