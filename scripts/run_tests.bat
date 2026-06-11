@echo off
echo ==========================================
echo  EduAgent 集成测试运行器
echo ==========================================
echo.
echo 前提：后端服务需在 http://localhost:8000 运行
echo       基础设施需已启动 (docker compose up -d)
echo.

cd /d "d:\agent_project_v2\backend"
call venv\Scripts\activate.bat

echo ==========================================
echo  [1/4] 冒烟测试（快速健康检查）
echo ==========================================
pytest tests/test_smoke.py -v -m smoke --tb=short 2>&1
if errorlevel 1 (
    echo.
    echo [警告] 冒烟测试未通过，后端可能未启动！
    echo 请先运行：docker compose up -d postgres redis chromadb minio
    echo 然后：venv\Scripts\activate ^&^& set POSTGRES_HOST=localhost ^&^& set REDIS_HOST=localhost ^&^& set CHROMA_HOST=localhost ^&^& uvicorn app.main:app --reload
    pause
    exit /b 1
)

echo.
echo ==========================================
echo  [2/4] API 集成测试（认证+课程+资源+权限）
echo ==========================================
set POSTGRES_HOST=localhost
set REDIS_HOST=localhost
set CHROMA_HOST=localhost
pytest tests/test_api.py -v --tb=short -x 2>&1

echo.
echo ==========================================
echo  [3/4] RAG 问答测试
echo ==========================================
pytest tests/test_rag.py -v --tb=short -x 2>&1

echo.
echo ==========================================
echo  [4/4] Agent/工作流测试（任务+报告）
echo ==========================================
pytest tests/test_agent/test_workflows.py -v --tb=short -x 2>&1

echo.
echo ==========================================
echo  全部测试完成！
echo  查看详细报告：docs/09_验收清单.md
echo ==========================================
pause
