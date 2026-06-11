@echo off
echo ==========================================
echo  EduAgent - 完整重启
echo ==========================================
echo.

REM ========== 0. 清理残留进程 ==========
echo [0/6] 清理残留进程...
taskkill //F //FI "WINDOWTITLE eq EduAgent*" //T 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000"') do taskkill //F //PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173"') do taskkill //F //PID %%a 2>nul
echo [OK] 进程已清理

REM ========== 1. 等待 Docker 就绪 ==========
echo.
echo [1/6] 等待 Docker 就绪...
:wait_docker
docker info >nul 2>&1
if errorlevel 1 (
    echo   等待 Docker Desktop 启动...
    timeout /t 3 /nobreak >nul
    goto wait_docker
)
echo [OK] Docker 已就绪

REM ========== 2. 启动基础设施 ==========
echo.
echo [2/6] 启动基础设施服务...
cd /d "d:\agent_project_v2"
docker compose up -d postgres redis chromadb minio 2>&1
if errorlevel 1 (
    echo [错误] 启动失败，请检查 Docker Desktop
    pause
    exit /b 1
)
echo [OK] 基础设施已启动

REM ========== 3. 等待服务健康 ==========
echo.
echo [3/6] 等待服务健康检查...
timeout /t 5 /nobreak >nul
echo [OK]

REM ========== 4. 数据库迁移 ==========
echo.
echo [4/6] 运行数据库迁移...
cd /d "d:\agent_project_v2\backend"
call venv\Scripts\activate
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set REDIS_HOST=localhost
set REDIS_PORT=6379
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
set MINIO_ENDPOINT=localhost:9000
alembic upgrade head
if errorlevel 1 (
    echo [错误] 迁移失败！
    pause
    exit /b 1
)
echo [OK] 迁移完成

REM ========== 5. 启动后端 ==========
echo.
echo [5/6] 启动后端服务...
start "EduAgent-Backend" cmd /k "cd /d d:\agent_project_v2\backend && set POSTGRES_HOST=localhost && set POSTGRES_PORT=5432 && set REDIS_HOST=localhost && set REDIS_PORT=6379 && set CHROMA_HOST=localhost && set CHROMA_PORT=8001 && set MINIO_ENDPOINT=localhost:9000 && venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo [OK] 后端已在新窗口启动

REM ========== 6. 启动前端 ==========
echo.
echo [6/6] 启动前端服务...
start "EduAgent-Frontend" cmd /k "cd /d d:\agent_project_v2\frontend && npm run dev"
echo [OK] 前端已在新窗口启动

echo.
echo ==========================================
echo  重启完成！
echo  前端: http://localhost:5173
echo  后端: http://localhost:8000
echo  API文档: http://localhost:8000/docs
echo ==========================================
pause
