@echo off
echo ==========================================
echo  EduAgent 本地开发启动脚本
echo ==========================================
echo.

cd /d "d:\agent_project_v2"

REM ========== 1. 启动基础设施 ==========
echo [1/4] 启动 Docker 基础设施服务...
docker compose up -d postgres redis chromadb minio 2>&1
if errorlevel 1 (
    echo [错误] Docker Desktop 可能未启动，请先启动 Docker Desktop
    pause
    exit /b 1
)
echo [OK] 基础设施已启动

REM ========== 2. 设置本地环境变量 ==========
echo.
echo [2/4] 设置本地开发环境变量...
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set REDIS_HOST=localhost
set REDIS_PORT=6379
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
set MINIO_ENDPOINT=localhost:9000
echo [OK] 环境变量已设置（覆盖 Docker 主机名）

REM ========== 3. 启动后端 ==========
echo.
echo [3/5] 启动后端服务...
start "" "scripts\start_backend.bat"
echo [OK] 后端已在 http://localhost:8000 启动

REM ========== 4. 启动 Celery Worker ==========
echo.
echo [4/5] 启动 Celery Worker...
start "" "scripts\start_celery.bat"
echo [OK] Celery Worker 已启动

REM ========== 5. 启动前端 ==========
echo.
echo [5/5] 启动前端服务...
start "" "scripts\start_frontend.bat"
echo [OK] 前端已在 http://localhost:5173 启动

echo.
echo ==========================================
echo  启动完成！
echo  前端: http://localhost:5173
echo  后端: http://localhost:8000
echo  API文档: http://localhost:8000/docs
echo ==========================================
pause
