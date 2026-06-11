#!/usr/bin/env bash
# ============================================================
# EduAgent 本地开发启动脚本（Linux / macOS）
# 用法: bash scripts/dev-start.sh
# ============================================================
set -e

# 获取脚本所在目录的上级（项目根目录）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

echo "=========================================="
echo " EduAgent 本地开发启动脚本"
echo "=========================================="
echo ""

# ========== 0. 前置检查 ==========
echo "[0/5] 检查前置条件..."

if ! command -v docker &> /dev/null; then
    echo "[错误] Docker 未安装，请先安装 Docker Desktop"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo "[错误] Docker Compose v2 未安装"
    exit 1
fi

if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "[错误] Python 3.11+ 未安装"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "[错误] Node.js 20+ 未安装"
    exit 1
fi

echo "[OK] 前置条件满足"

# ========== 1. 启动基础设施 ==========
echo ""
echo "[1/5] 启动 Docker 基础设施服务..."
docker compose up -d postgres redis chromadb minio 2>&1
if [ $? -ne 0 ]; then
    echo "[错误] Docker Desktop 可能未启动，请先启动 Docker Desktop"
    exit 1
fi
echo "[OK] 基础设施已启动"

# ========== 2. 设置本地环境变量 ==========
echo ""
echo "[2/5] 设置本地开发环境变量..."
export POSTGRES_HOST=localhost
export REDIS_HOST=localhost
export CHROMA_HOST=localhost
export MINIO_ENDPOINT=localhost:9000
echo "[OK] 环境变量已设置（覆盖 Docker 主机名）"

# ========== 3. 检查/创建 Python 虚拟环境 ==========
echo ""
echo "[3/5] 检查 Python 虚拟环境..."

PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

cd "$PROJECT_ROOT/backend"

if [ ! -d "venv" ]; then
    echo "  创建虚拟环境..."
    $PYTHON_CMD -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if ! python -c "import fastapi" 2>/dev/null; then
    echo "  安装 Python 依赖..."
    pip install -r requirements.txt -q
fi

echo "[OK] Python 虚拟环境就绪"

# ========== 4. 启动后端 ==========
echo ""
echo "[4/5] 启动后端服务..."
alembic upgrade head 2>&1

# 后台启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "[OK] 后端已在 http://localhost:8000 启动 (PID: $BACKEND_PID)"

# ========== 5. 启动前端 ==========
echo ""
echo "[5/5] 启动前端服务..."

cd "$PROJECT_ROOT/frontend"

if [ ! -d "node_modules" ]; then
    echo "  安装前端依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!
echo "[OK] 前端已在 http://localhost:5173 启动 (PID: $FRONTEND_PID)"

# ========== 完成 ==========
echo ""
echo "=========================================="
echo " 启动完成！"
echo ""
echo " 前端:     http://localhost:5173"
echo " 后端:     http://localhost:8000"
echo " API文档:  http://localhost:8000/docs"
echo ""
echo " 按 Ctrl+C 停止所有服务"
echo "=========================================="

# 捕获 Ctrl+C，清理后台进程
cleanup() {
    echo ""
    echo "正在停止服务..."
    kill $BACKEND_PID 2>/dev/null || true
    kill $FRONTEND_PID 2>/dev/null || true
    echo "服务已停止"
    exit 0
}

trap cleanup SIGINT SIGTERM

# 等待后台进程
wait
