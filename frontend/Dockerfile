# TextGuard 前端 Dockerfile（多阶段构建 - Nginx + 静态文件 + 反向代理）
# 默认 HTTP 模式，如需 HTTPS 请参考 README.md 中的说明
# ---- 构建阶段 ----
FROM node:18-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --registry=https://registry.npmmirror.com

COPY . .
RUN npm run build

# ---- 运行阶段（Nginx + 静态文件 + 反向代理） ----
FROM nginx:alpine

# 删除默认配置
RUN rm -f /etc/nginx/conf.d/default.conf

# 复制 Nginx 配置（默认 HTTP 模式）
# 如需 HTTPS：将 nginx.production.ssl.conf 替换此行，并确保 ssl/ 目录含证书
COPY nginx.production.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 3022

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost:3022/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
