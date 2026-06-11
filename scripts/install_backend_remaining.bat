@echo off
echo ==========================================
echo  EduAgent 后端依赖完整性安装
echo ==========================================
echo.

cd /d "d:\agent_project_v2\backend"
call venv\Scripts\activate.bat

echo [1/4] 安装 chromadb (向量数据库)...
pip install chromadb --no-cache-dir

echo.
echo [2/4] 安装 langchain (AI框架)...
pip install langchain --no-cache-dir

echo.
echo [3/4] 安装 langchain-community...
pip install langchain-community --no-cache-dir

echo.
echo [4/4] 安装 langgraph + langchain-huggingface...
pip install langgraph langchain-huggingface --no-cache-dir

echo.
echo ==========================================
echo  验证安装...
echo ==========================================
pip list | findstr /i "chromadb langchain langgraph"

echo.
echo ==========================================
echo  安装完成！
echo ==========================================
pause
