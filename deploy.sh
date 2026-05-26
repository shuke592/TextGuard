#!/bin/bash
set -e

echo "=============================="
echo " TextGuard 生产环境部署脚本"
echo " 使用本地预构建镜像，无需服务器构建"
echo "=============================="
echo ""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查项目目录
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ 请在 /opt/TextGuard 目录执行此脚本${NC}"
    echo -e "${YELLOW}   确保已上传: docker-compose.yml, deploy.sh, backend/.env.production${NC}"
    exit 1
fi

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Docker 就绪${NC}"

# 自动创建所需目录
mkdir -p /opt/TextGuard/backend
mkdir -p /opt/TextGuard/docker-images
mkdir -p /opt/UploadFile/textGuardUpload

# 检查配置文件
if [ ! -f "backend/.env.production" ]; then
    echo -e "${RED}❌ 缺少 backend/.env.production${NC}"
    echo ""
    echo -e "${YELLOW}   请将此文件上传到: /opt/TextGuard/backend/.env.production${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 配置文件就绪${NC}"
echo -e "${GREEN}✅ 目录结构就绪${NC}"

# ---- 加载预构建镜像 ----
echo ""
BACKEND_TAR="docker-images/textguard-backend.tar"
FRONTEND_TAR="docker-images/textguard-frontend.tar"

NEED_LOAD=false

if [ -f "$BACKEND_TAR" ]; then
    echo "📦 检测到后端镜像文件，正在加载..."
    docker load -i "$BACKEND_TAR"
    echo -e "${GREEN}✅ 后端镜像加载完成${NC}"
    NEED_LOAD=true
fi

if [ -f "$FRONTEND_TAR" ]; then
    echo "📦 检测到前端镜像文件，正在加载..."
    docker load -i "$FRONTEND_TAR"
    echo -e "${GREEN}✅ 前端镜像加载完成${NC}"
    NEED_LOAD=true
fi

if [ "$NEED_LOAD" = false ]; then
    # 没有 tar 文件，检查镜像是否已存在
    if ! docker image inspect textguard-backend:latest &>/dev/null; then
        echo -e "${RED}❌ 未找到后端镜像，请先上传 docker-images/textguard-backend.tar${NC}"
        exit 1
    fi
    if ! docker image inspect textguard-frontend:latest &>/dev/null; then
        echo -e "${RED}❌ 未找到前端镜像，请先上传 docker-images/textguard-frontend.tar${NC}"
        exit 1
    fi
    echo -e "${YELLOW}ℹ️  使用已有镜像（未检测到新的 .tar 文件）${NC}"
fi

# 显示镜像信息
echo ""
echo "📋 当前镜像："
docker images --format "  {{.Repository}}:{{.Tag}}  {{.Size}}  {{.CreatedSince}}" | grep textguard || true
echo ""

# 停止旧容器
echo "🛑 停止旧容器..."
docker compose down 2>/dev/null || true
docker rm -f textguard-nginx textguard-postgres textguard-redis 2>/dev/null || true

# 启动（不加 --build，直接使用已加载的镜像）
echo ""
echo "� 启动服务..."
docker compose up -d

# 等待
echo ""
echo "⏳ 等待服务就绪..."
sleep 15

# 状态
echo ""
docker compose ps
echo ""

# 清理已加载的 tar 文件（节省磁盘空间）
if [ -f "$BACKEND_TAR" ] || [ -f "$FRONTEND_TAR" ]; then
    echo ""
    read -p "是否删除已加载的 .tar 镜像文件以释放磁盘空间？[y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -f "$BACKEND_TAR" "$FRONTEND_TAR"
        echo -e "${GREEN}✅ .tar 文件已清理${NC}"
    fi
fi

SERVER_IP=$(hostname -I | awk '{print $1}')
echo ""
echo "=============================="
echo -e "${GREEN}✅ 部署完成！${NC}"
echo ""
echo "  访问地址: http://${SERVER_IP}:3022"
echo "  (如已配置 HTTPS，请使用 https://your-domain:3022)"
echo ""
echo "  查看日志: docker compose logs -f"
echo "  重启:     docker compose restart"
echo "  停止:     docker compose down"
echo "=============================="
