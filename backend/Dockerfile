# TextGuard 后端 Dockerfile
FROM python:3.11-slim

LABEL maintainer="TextGuard Team"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl antiword && \
    rm -rf /var/lib/apt/lists/*

# 注入可靠DNS（覆盖容器默认DNS，彻底解决构建/运行时DNS解析超时）
COPY resolv.conf /etc/resolv.conf

# Python 依赖（先复制依赖文件，利用镜像层缓存）
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/ && \
    pip install --no-cache-dir -r requirements.txt \
        -i https://mirrors.aliyun.com/pypi/simple/ \
        --timeout 60

# 复制项目代码
COPY . .

# 暴露端口
EXPOSE 3020

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:3020/api/v1/health || exit 1

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3020", "--workers", "2"]
