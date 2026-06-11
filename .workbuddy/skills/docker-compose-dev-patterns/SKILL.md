---
name: docker-compose-dev-patterns
description: >
  Docker Compose 开发与生产环境编排模式——当 CodeBuddy 开始编写 Dockerfile、
  docker-compose.yml、nginx.conf 或服务编排逻辑时触发。
  覆盖：多阶段构建（前端 Node→Nginx / 后端 Python→Gunicorn）、
  8 服务完整编排（含 Redis + Celery Worker）、健康检查与启动依赖、
  卷挂载策略、网络隔离、dev vs prod 配置切换、
  .dockerignore 最佳实践、本项目完整的 docker-compose.yml 参考。
agent_created: true
---

# Docker Compose Development Patterns

## Purpose

本 Skill 提供教学智能体项目的 Docker 环境编排专家级实施模式。
当 CodeBuddy 需要编写 Dockerfile、docker-compose.yml、Nginx 反向代理配置
或开发环境启动脚本时，应使用本 Skill 中的模式和参数。

> **⚠️ 重要说明**：`docs/02_技术架构文档.md` 中的 docker-compose.yml 为基础版本，
> 缺少 Redis 和 Celery Worker 两个关键服务。**本 Skill 提供完整版 8 服务编排，
> 以本 Skill 为准。**

## When to Use

在以下场景中触发本 Skill：
- CodeBuddy 创建 Dockerfile（前端多阶段 / 后端 Python）
- CodeBuddy 编写 docker-compose.yml 或服务编排
- CodeBuddy 配置健康检查（healthcheck）或启动依赖（depends_on）
- CodeBuddy 编写 Nginx 反向代理配置
- CodeBuddy 需要区分 dev/prod 模式
- 首次启动需要完整环境（`docker compose up -d`）

---

## Pattern 1: Multi-Stage Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
# ============================================================
# Stage 1: 构建阶段 — Node 环境编译 Vue 3 + Vite
# ============================================================
FROM node:20-alpine AS builder

WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --only=production 2>/dev/null || npm install

COPY . .
RUN npm run build
# 产物输出到 /app/dist/

# ============================================================
# Stage 2: 运行阶段 — Nginx 托管静态文件
# ============================================================
FROM nginx:alpine

# 复制构建产物到 Nginx 默认目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制自定义 Nginx 配置（SPA 路由支持）
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

**为什么用多阶段构建？**
- Stage 1（~600MB）包含 node_modules + 源码
- Stage 2（~25MB）只含编译后的静态文件 + Nginx
- 最终镜像体积小、攻击面小、启动快

### SPA 路由支持的 Nginx 配置（frontend/nginx.conf）

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip 压缩
    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 256;

    # 静态资源缓存
    location /assets/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA 路由 — 非静态文件全部 fallback 到 index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # 不记录 favicon 404
    location = /favicon.ico {
        log_not_found off;
        access_log off;
    }
}
```

---

## Pattern 2: Backend Dockerfile (Dev + Prod 双模式)

```dockerfile
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
```

**关键决策**：

| 维度 | dev | prod |
|------|-----|------|
| 启动 | uvicorn --reload | gunicorn -w 4 |
| 代码来源 | 卷挂载（实时） | COPY 到镜像内 |
| 进程数 | 1（单进程） | 4 worker |
| 镜像大小 | 较大（含 watchdog） | 较小 |

---

## Pattern 3: Celery Worker Dockerfile

```dockerfile
# backend/Dockerfile.celery
# ============================================================
# Celery Worker — 与 Backend 共用基础层
# ============================================================
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Celery Worker
# -A app.celery_app → Celery 实例位置
# -Q default,rag → 监听两个队列（通用 + RAG 处理）
# -c 2 → 每个 worker 2 个并发（资源有限时用并发而非多 worker）
CMD ["celery", "-A", "app.celery_app", "worker", \
     "-l", "info", "-Q", "default,rag", "-c", "2"]
```

**Celery 队列分配说明**：

| 队列名 | 用途 | 典型任务 | task_routes |
|--------|------|---------|:--:|
| `default` | 通用异步任务 | 报告生成、任务生成 | 默认路由 |
| `rag` | RAG 专用 | 文件解析→分块→向量化 | 显式路由 |

```python
# backend/app/celery_app.py（项目约束）
from celery import Celery

app = Celery(
    "edu_agent",
    broker=settings.REDIS_URL,      # Redis 作为 broker
    backend=settings.REDIS_URL,     # Redis 作为 result backend
)

app.conf.update(
    task_routes={
        "app.tasks.resources.process_resource": {"queue": "rag"},
        "app.tasks.resources.batch_process":   {"queue": "rag"},
    },
    task_serializer="json",
    result_serializer="json",
    task_track_started=True,
    task_acks_late=True,          # 任务完成后才 ack，防止 worker 崩溃丢任务
    worker_prefetch_multiplier=1, # 每次只取 1 个任务，公平分配
)

# 自动发现 tasks/ 目录下的任务
app.autodiscover_tasks(["app.tasks"])
```

---

## Pattern 4: 完整 docker-compose.yml（8 服务）

**这是本 Skill 的核心**——以下是教学智能体项目完整的 8 服务 Docker Compose 编排：

```yaml
# docker-compose.yml
# ============================================================
# 教学智能体 — 完整 8 服务编排（dev 模式）
# ============================================================
version: '3.8'

services:
  # ======================================================
  # 1. Nginx — 统一入口（前端 + API 代理）
  # ======================================================
  nginx:
    image: nginx:alpine
    container_name: edu-nginx
    ports:
      - "${NGINX_PORT:-80}:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 2. Frontend — Vue 3 SPA
  # ======================================================
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: edu-frontend
    # 开发模式：挂载 dist 目录实现热更新
    # 生产模式：移除 volumes，使用镜像内文件
    volumes:
      - ./frontend/dist:/usr/share/nginx/html:ro
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 3. Backend — FastAPI 应用
  # ======================================================
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: dev    # dev 阶段：uvicorn --reload
    container_name: edu-backend
    ports:
      - "${BACKEND_PORT:-8000}:8000"
    env_file:
      - .env
    volumes:
      - ./backend/app:/app/app          # 代码热重载
      - ./data/uploads:/app/uploads     # 上传临时目录
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_started
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 4. Celery Worker — 异步任务处理
  # ======================================================
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.celery
    container_name: edu-celery-worker
    env_file:
      - .env
    volumes:
      - ./backend/app:/app/app          # 代码热重载
      - ./data/uploads:/app/uploads     # 文件处理
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      chromadb:
        condition: service_started
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 5. PostgreSQL — 业务数据库
  # ======================================================
  postgres:
    image: postgres:16-alpine
    container_name: edu-postgres
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-edu_agent}
      POSTGRES_USER: ${POSTGRES_USER:-edu_agent}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-change-me}
      # 性能优化参数
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=C"
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
      - ./backend/app/scripts/init_db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-edu_agent} -d ${POSTGRES_DB:-edu_agent}"]
      interval: 5s
      timeout: 5s
      retries: 5
      start_period: 10s
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 6. Redis — 会话记忆 + Celery Broker + Token 黑名单
  # ======================================================
  redis:
    image: redis:7-alpine
    container_name: edu-redis
    command: >
      redis-server
      --appendonly yes
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
    volumes:
      - ./data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 7. ChromaDB — 向量数据库
  # ======================================================
  chromadb:
    image: chromadb/chroma:0.5.23
    container_name: edu-chromadb
    volumes:
      - ./data/chromadb:/chroma/chroma
    environment:
      - IS_PERSISTENT=TRUE
      - ANONYMIZED_TELEMETRY=FALSE
      - ALLOW_RESET=TRUE
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v2/heartbeat"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 8. MinIO — 对象存储（文件上传）
  # ======================================================
  minio:
    image: minio/minio:latest
    container_name: edu-minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    volumes:
      - ./data/minio:/data
    ports:
      - "${MINIO_PORT:-9000}:9000"
      - "${MINIO_CONSOLE_PORT:-9001}:9001"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - edu-net
    restart: unless-stopped

  # ======================================================
  # 可选：Celery Flower — 任务监控面板（仅开发环境）
  # ======================================================
  # flower:
  #   image: mher/flower:latest
  #   container_name: edu-flower
  #   environment:
  #     - CELERY_BROKER_URL=${REDIS_URL}
  #   ports:
  #     - "5555:5555"
  #   depends_on:
  #     - redis
  #   networks:
  #     - edu-net

# ============================================================
# 网络定义
# ============================================================
networks:
  edu-net:
    driver: bridge
    name: edu-agent-network

# ============================================================
# 卷定义（数据持久化）
# ============================================================
volumes:
  postgres-data:
    driver: local
  redis-data:
    driver: local
  chromadb-data:
    driver: local
  minio-data:
    driver: local
```

---

## Pattern 5: Nginx 反向代理总配置（环境级 nginx.conf）

```nginx
# nginx.conf（项目根目录 — 环境级反向代理）
# ============================================================
# 作用：统一入口，将 / 路由到前端，/api/ 代理到后端
# ============================================================

# 上游服务器定义
upstream frontend_upstream {
    server frontend:80;
}

upstream backend_upstream {
    server backend:8000;
}

server {
    listen 80;
    server_name _;
    client_max_body_size 50M;   # 匹配 .env 中的 MAX_UPLOAD_SIZE_MB

    # ====================================================
    # 前端 SPA — 直接代理到 frontend 容器
    # ====================================================
    location / {
        proxy_pass http://frontend_upstream;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SPA fallback 在 frontend 容器的 nginx.conf 中处理
    }

    # ====================================================
    # 后端 API — 代理到 FastAPI
    # ====================================================
    location /api/ {
        proxy_pass http://backend_upstream/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式支持（禁用缓冲）
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;  # 5 分钟超时（匹配 SSE keepalive）

        # WebSocket 支持（预留）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # ====================================================
    # API 文档 — 直通 FastAPI
    # ====================================================
    location /docs {
        proxy_pass http://backend_upstream/docs;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://backend_upstream/openapi.json;
        proxy_set_header Host $host;
    }

    # ====================================================
    # MinIO 文件访问 — 直通对象存储（开发环境）
    # 生产环境改为 CDN 直连
    # ====================================================
    location /files/ {
        proxy_pass http://minio:9000/;
        proxy_set_header Host $host;
    }
}
```

---

## Pattern 6: Health Check 启动依赖策略

**本项目 8 服务的健康检查与启动依赖关系**：

```
                    nginx
                  /       \
            frontend     backend ←────────────┐
                           │                    │
              ┌────────────┼────────────┐       │
              ▼            ▼            ▼       │
          postgres      redis       chromadb   minio
         (healthy)    (healthy)    (started)  (started)
              │            │
              └──────┬─────┘
                     ▼
              celery-worker
```

| 服务 | 健康检查方式 | depends_on 级别 | 原因 |
|------|------------|:--:|------|
| postgres | `pg_isready` | `service_healthy` | 数据完整性不可降级 |
| redis | `redis-cli ping` | `service_healthy` | 会话记忆 + Celery broker |
| chromadb | `curl /heartbeat` | `service_started` | 可降级（Level 2/3） |
| minio | `curl /health/live` | 无 | 非必需（仅上传时用） |
| backend | — | postgres(healthy) + redis(healthy) + chromadb(started) | |
| celery-worker | — | postgres(healthy) + redis(healthy) + chromadb(started) | |
| frontend | `wget localhost` | 无 | 纯静态，无依赖 |
| nginx | — | frontend + backend | |

**depends_on 级别说明**：

| 级别 | 含义 | 适用场景 |
|------|------|---------|
| `service_started` | 容器启动即可（不等待健康检查通过） | 非关键服务、可降级服务 |
| `service_healthy` | 必须健康检查通过才启动 | 核心依赖、无替代方案 |

---

## Pattern 7: .env.example 环境变量完整配置

```bash
# .env.example — 教学智能体项目完整环境变量
# 复制为 .env 后修改

# ========== 项目 ==========
APP_NAME=edu-agent
APP_ENV=development        # development | production
DEBUG=true

# ========== 服务端口（可自定义避免冲突） ==========
NGINX_PORT=80
BACKEND_PORT=8000
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# ========== 数据库 ==========
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=edu_agent
POSTGRES_USER=edu_agent
POSTGRES_PASSWORD=change-me
DATABASE_URL=postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# ========== Redis ==========
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# ========== Celery ==========
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=${REDIS_URL}

# ========== ChromaDB ==========
CHROMA_HOST=chromadb
CHROMA_PORT=8000

# ========== 对象存储 (MinIO) ==========
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=edu-agent-files
MINIO_SECURE=false

# ========== LLM 配置 ==========
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-4o-mini
LLM_API_KEY=sk-your-api-key-here
LLM_TEMPERATURE=0.3
LLM_MAX_TOKENS=2048

# ========== Embedding 模型 ==========
EMBEDDING_MODEL=BAAI/bge-m3       # 本地 BGE-M3（中文最佳）
EMBEDDING_DEVICE=cpu               # Docker 容器内用 CPU；本地开发可改为 cuda

# ========== JWT ==========
JWT_SECRET_KEY=change-me-jwt-secret-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# ========== 文件上传 ==========
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx,pptx,md,txt,xlsx

# ========== CORS ==========
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost

# ========== 安全 ==========
# 输入护栏开关
GUARDRAIL_INPUT_ENABLED=true
# 输出护栏开关
GUARDRAIL_OUTPUT_ENABLED=true
```

---

## Pattern 8: .dockerignore 最佳实践

```dockerignore
# .dockerignore（项目根目录 + frontend/backend 各自一份）

# ========== 通用 ==========
.git
.gitignore
.gitattributes
*.md
LICENSE

# ========== Docker ==========
Dockerfile*
docker-compose*.yml
.dockerignore

# ========== IDE ==========
.vscode/
.idea/
*.swp
*.swo
*~

# ========== 前端专用 ==========
# frontend/.dockerignore
node_modules/
dist/
.cache/
*.log

# ========== 后端专用 ==========
# backend/.dockerignore
__pycache__/
*.pyc
*.pyo
.env
.env.*
.venv/
venv/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
data/
uploads/
chroma_db/
```

---

## Pattern 9: Dev vs Prod 启动脚本

### 开发环境

```bash
#!/bin/bash
# scripts/dev-start.sh

set -e

echo "🚀 Starting development environment..."

# 1. 复制 .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "  📝 .env created from .env.example — edit with your API keys"
fi

# 2. 启动服务（dev 模式：热重载 + 调试）
docker compose up -d

# 3. 等待数据库就绪
echo "  ⏳ Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U edu_agent > /dev/null 2>&1; do
    sleep 2
done

# 4. 运行数据库迁移
docker compose exec -T backend alembic upgrade head
echo "  ✅ Database migrated"

# 5. 初始化种子数据（可选）
# docker compose exec -T backend python app/scripts/seed.py

echo ""
echo "✅ Development environment ready!"
echo "   Frontend:  http://localhost"
echo "   API Docs:  http://localhost:8000/docs"
echo "   MinIO:     http://localhost:9001"
echo "   Redis:     redis-cli -h localhost -p 6379"
```

### 生产环境

```bash
#!/bin/bash
# scripts/prod-start.sh

set -e

echo "🏭 Starting production environment..."

# 生产模式使用 prod target
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

echo ""
echo "✅ Production environment ready!"
```

```yaml
# docker-compose.prod.yml（生产覆盖文件）
version: '3.8'

services:
  frontend:
    build:
      target: default    # 覆盖 dev target
    # 生产不用卷挂载，使用镜像内构建产物
    volumes: []

  backend:
    build:
      target: prod       # gunicorn 多进程
    volumes:
      - ./data/uploads:/app/uploads   # 只挂载上传目录
    # /app/app 不挂载，使用镜像内代码

  celery-worker:
    restart: always      # 生产用 always 而非 unless-stopped

  postgres:
    volumes:
      - postgres-data:/var/lib/postgresql/data   # 命名卷（性能更好）

  redis:
    volumes:
      - redis-data:/data
    command: >
      redis-server
      --appendonly yes
      --maxmemory 512mb            # 生产加大内存
      --maxmemory-policy allkeys-lru

volumes:
  postgres-data:
  redis-data:
```

---

## Anti-Patterns (What NOT to Do)

### ❌ Anti-Pattern 1：忘记多阶段构建，镜像超大

```dockerfile
# 错误：Node 环境直接当运行环境
FROM node:20-alpine
COPY . .
RUN npm install && npm run build
CMD ["npm", "run", "preview"]
# 问题：镜像 >1GB，包含 node_modules + src，攻击面大
```

✅ **正确**：用 Pattern 1 的多阶段构建，运行阶段只有 Nginx + 静态文件（~25MB）。

---

### ❌ Anti-Pattern 2：depends_on 不设 condition，数据库没就绪就开始连

```yaml
# 错误：只等容器启动，不等数据库就绪
backend:
  depends_on:
    - postgres     # 没有 condition: service_healthy
```

✅ **正确**：
```yaml
backend:
  depends_on:
    postgres:
      condition: service_healthy
```

**后果**：数据库容器启动了但 PostgreSQL 进程还没准备好，后端连不上报错重启。

---

### ❌ Anti-Pattern 3：用 `localhost` 连接容器间服务

```python
# 错误：容器内用 localhost
DATABASE_URL = "postgresql://...@localhost:5432/edu_agent"
# 容器内的 localhost 是本容器自己，不是宿主机，也不是其他容器
```

✅ **正确**：用服务名（Docker DNS 自动解析）：
```python
POSTGRES_HOST=postgres   # ← 服务名，Docker 内部 DNS 解析
```

---

### ❌ Anti-Pattern 4：Nginx 不关 SSE 缓冲

```nginx
# 错误：默认缓冲开启，SSE 流式会被缓冲成一块
location /api/ {
    proxy_pass http://backend:8000;
    # 没有 proxy_buffering off;
}
```

✅ **正确**：SSE 路径必须关闭缓冲（Pattern 5 的 `/api/` location）。

---

### ❌ Anti-Pattern 5：Celery Worker 和 Backend 共用一个容器

```yaml
# 错误：在 backend 容器内同时跑 FastAPI 和 Celery
CMD ["sh", "-c", "uvicorn app.main:app & celery -A app worker"]
# 问题：一个进程崩溃可能带崩另一个；无法独立扩容
```

✅ **正确**：Backend 和 Celery Worker 是两个独立容器（Pattern 3 + Pattern 4）。

---

### ❌ Anti-Pattern 6：生产环境用卷挂载覆盖镜像内代码

```yaml
# 错误：生产环境仍然挂载代码卷
backend:
  volumes:
    - ./backend/app:/app/app   # 生产环境不应该挂载
```

✅ **正确**：开发挂载（热重载）、生产不挂载（镜像内固定版本）。用 `docker-compose.prod.yml` 覆盖（Pattern 9）。

---

### ❌ Anti-Pattern 7：忘记 .dockerignore，把 node_modules 打进镜像

没有 `.dockerignore` 的后果：
- `COPY . .` 会把整个 `node_modules/` 打进构建上下文
- 构建时间翻倍、镜像体积膨胀

✅ **正确**：每个服务目录下创建 `.dockerignore`（Pattern 8）。

---

## Project-Specific Constraints

### 1. 服务间通信全部走 `edu-net` 网络

所有服务加入 `edu-net` bridge 网络，通过服务名互访：

| 调用方 | 被调用方 | 地址（容器内） |
|--------|---------|--------------|
| backend → postgres | postgres:5432 | 环境变量 POSTGRES_HOST |
| backend → redis | redis:6379 | 环境变量 REDIS_HOST |
| backend → chromadb | chromadb:8000 | 环境变量 CHROMA_HOST |
| celery-worker → redis | redis:6379 | CELERY_BROKER_URL |
| celery-worker → postgres | postgres:5432 | DATABASE_URL |
| nginx → backend | backend:8000 | upstream |
| nginx → frontend | frontend:80 | upstream |

### 2. 数据卷全部绑定到 `./data/` 目录

```
data/
├── postgres/     ← PostgreSQL 数据（容器内 /var/lib/postgresql/data）
├── redis/        ← Redis AOF 持久化（容器内 /data）
├── chromadb/     ← ChromaDB 向量数据（容器内 /chroma/chroma）
├── minio/        ← MinIO 对象数据（容器内 /data）
└── uploads/      ← 文件上传临时目录（容器内 /app/uploads）
```

**为什么用 bind mount 而非 named volume？**
- 开发环境：bind mount 可以直接在宿主机查看/备份数据
- 生产环境：用 named volume（性能更好），Pattern 9 的 `docker-compose.prod.yml` 覆盖

### 3. Redis 的三个职责

| 职责 | 说明 | 隔离方式 |
|------|------|---------|
| 对话记忆 | 24h TTL（05 文档 §5.3） | Redis DB 0，前缀 `memory:` |
| Celery Broker | 任务队列 | 默认队列 + `rag` 队列 |
| Token 黑名单 | JWT 退出登录 | 前缀 `blacklist:` |

三个职责共用同一 Redis 实例（开发环境），隔离通过 DB 编号或 key 前缀。

### 4. ChromaDB 版本锁定

使用 `chromadb/chroma:0.5.23`（非 `latest`）——ChromaDB 版本升级频繁且 API 变化大，锁定版本避免代码不兼容。

### 5. 启动顺序严格约束

```
第 1 批（并行）: postgres, redis, chromadb, minio
       ↓
第 2 批（并行）: backend, celery-worker, frontend
       ↓
第 3 批: nginx
```

`depends_on` + `healthcheck` 共同保证：nginx 启动时前端和后端都已就绪。

### 6. 首次启动初始化流程

```bash
# Step 1: 启动全部服务
docker compose up -d

# Step 2: 等待 PostgreSQL 健康检查通过（自动，约 15-30s）
# Step 3: 运行数据库迁移（创建表 + 枚举 + 索引）
docker compose exec backend alembic upgrade head

# Step 4: 初始化 MinIO bucket
docker compose exec backend python app/scripts/init_minio.py

# Step 5: 验证
# - curl http://localhost/api/health → {"status": "ok"}
# - curl http://localhost:8000/docs → Swagger UI
# - curl http://localhost:9001 → MinIO Console
```

---

## Quick Reference

| 要做的事 | 看哪个 Pattern | 产出文件 |
|---------|:---:|---------|
| 创建前端 Dockerfile | Pattern 1 | `frontend/Dockerfile` + `frontend/nginx.conf` |
| 创建后端 Dockerfile | Pattern 2 | `backend/Dockerfile` |
| 创建 Celery Worker Dockerfile | Pattern 3 | `backend/Dockerfile.celery` |
| 完整服务编排 | Pattern 4 | `docker-compose.yml` |
| Nginx 反向代理 | Pattern 5 | `nginx.conf`（根目录） |
| 健康检查配置 | Pattern 6 | `docker-compose.yml` 中的 healthcheck 段 |
| 环境变量配置 | Pattern 7 | `.env.example` |
| 忽略文件 | Pattern 8 | 各部 `.dockerignore` |
| dev/prod 切换 | Pattern 9 | `docker-compose.prod.yml` + `scripts/` |
| 首次启动 | 项目约束 §6 | 命令行 |

---

## Cross-Document Compatibility

| 本 Skill 内容 | 对应文档 | 对齐点 |
|-------------|---------|--------|
| 8 服务编排 | `02 §2.2`（6 服务） → 本 Skill 补 Redis + Celery | ✅ 服务名一致，版本号对齐 |
| .env.example | `02 §5` | ✅ 新增 REDIS_URL / CELERY_BROKER_URL / EMBEDDING_MODEL 等 |
| Redis 对话记忆 | `05 §5.3` | ✅ key 格式 `memory:{user_id}:{course_id}` |
| Celery 异步任务 | `04 §1.4（约定）` + `03 §3.3（资源处理）` | ✅ task_routes 队列分配 |
| Nginx SSE 缓冲关闭 | `04 §5.2（SSE 端点）` | ✅ `/api/` location 设置 proxy_buffering off |
| 向量数据库版本 | `02 §1（ChromaDB）` | ✅ 版本锁定 0.5.23 |
| Postgres init SQL | `03 §4（DDL）` | ✅ init_db.sql 挂载到 /docker-entrypoint-initdb.d/ |

---

*本 Skill 由 **Senior Developer（高级开发工程师）** 编写，提供教学智能体项目 8 服务 Docker Compose 完整编排方案。*
