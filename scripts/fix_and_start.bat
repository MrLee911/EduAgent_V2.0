@echo off
echo ==========================================
echo  EduAgent - 修复依赖并重新启动
echo ==========================================
echo.
cd /d "d:\agent_project_v2\backend"

REM ========== 激活虚拟环境 ==========
call venv\Scripts\activate

echo [1/3] 修复 FastAPI 兼容性问题...
pip install --force-reinstall fastapi==0.136.3
if errorlevel 1 (
    echo [错误] FastAPI 安装失败
    pause
    exit /b 1
)

echo.
echo [2/3] 修复 ChromaDB 兼容性问题...
pip install chromadb==0.5.23
if errorlevel 1 (
    echo [错误] ChromaDB 安装失败
    pause
    exit /b 1
)

echo.
echo [3/3] 启动后端服务...
echo.
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set REDIS_HOST=localhost
set REDIS_PORT=6379
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
set MINIO_ENDPOINT=localhost:9000

uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
