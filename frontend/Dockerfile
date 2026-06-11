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
