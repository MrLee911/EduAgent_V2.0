# backend/Dockerfile
# ============================================================
# 多阶段构建：开发（热重载）与生产（Gunicorn）共用基础层
# ============================================================
FROM python:3.11-slim AS base

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 复制依赖文件并安装（利用 Docker 层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ============================================================
# Dev Stage: Uvicorn 热重载（挂载代码卷）
# ============================================================
FROM base AS dev

# 安装开发工具
RUN pip install --no-cache-dir watchdog

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ============================================================
# Prod Stage: Gunicorn + Uvicorn workers（多进程）
# ============================================================
FROM base AS prod

COPY . .

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", "app.main:app"]
