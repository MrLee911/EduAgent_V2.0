@echo off
echo ========================================
echo 安装 EduAgent 后端 Python 依赖
echo ========================================
cd /d "d:\agent_project_v2\backend"
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo ========================================
echo 安装完成！
echo ========================================
pause
