@echo off
echo ==========================================
echo  停止 EduAgent 本地开发环境
echo ==========================================
cd /d "d:\agent_project_v2"

echo [1/2] 停止 Docker 基础设施服务...
docker compose down 2>&1
echo [OK] 基础设施已停止

echo.
echo [2/2] 关闭本地进程窗口...
taskkill /FI "WINDOWTITLE eq EduAgent-Backend*" /T 2>nul
taskkill /FI "WINDOWTITLE eq EduAgent-Frontend*" /T 2>nul
echo [OK]

echo.
echo ==========================================
echo  已全部停止
echo ==========================================
pause
