<div align="center">

# 🛡️ TextGuard - 智能文档审校平台

**AI 驱动的新一代文档校对与润色平台，支持 AI 润色、文本校对、文档上传校对，在线预览、问题高亮、一键/逐条修改，修改后导出。**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB.svg)](https://www.python.org/)
[![Vue 3](https://img.shields.io/badge/Vue-3.x-4FC08D.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

*让每一份文档都经得起推敲 —— 智能校对 · AI润色 · 多模型驱动 · 开箱即用*

</div>

---

## ✨ 为什么选择 TextGuard？

当前市面上的文档校对工具大多依赖商业闭源方案，费用高昂且不可定制。**TextGuard** 是一个完全开源、可私有化部署的智能文档审校平台，让企业和个人都能拥有媲美商业级产品的文档校对能力。

- **🚀 开箱即用** — Docker 一键部署，5 分钟即可上线
- **🤖 多模型支持** — 内置 8 种 AI 供应商适配（DeepSeek、OpenAI、Kimi、通义千问等），管理后台动态切换
- **📝 全格式覆盖** — 支持 DOCX / PDF / TXT 上传校对，保留原始排版
- **🎨 AI 智能润色** — 10 种风格一键润色，三段式对比输出
- **🔍 精准问题定位** — 校对结果高亮标注，支持逐条审阅、一键采纳或忽略
- **📚 专业词库系统** — 全局词库 + 个性化词库 + 放行词，覆盖 6 大专业领域
- **🏢 企业级管理** — 完善的 RBAC 权限体系、审计日志、用户配额管理
- **📱 全端适配** — PC 与移动端完整适配，随时随地审校文档

---

## 🎯 核心功能

### 📋 文本校对
> 在线输入文本即可智能校对，支持分片处理超长文本，校对结果高亮展示，逐条修改并导出

### 📄 文档上传校对
> 上传 DOCX / PDF / TXT 文件，AI 自动解析并校对，在线预览保留排版，修改后导出新文档

### 🎨 AI 智能润色
> 提供 10 种润色风格（正式/口语/学术/新闻稿等），三段式输出（润色结果 + 修改对比 + 优化说明）

### 📚 词库管理
> - **全局词库**：预置 107 条常见易错词，6 大专业领域词库
> - **个性化词库**：用户自定义校对规则
> - **放行词管理**：对特定词语设置免校对白名单

### 🤖 多大模型管理
> 支持 8 种 AI 供应商：DeepSeek / OpenAI / Kimi / 通义千问 / 智谱GLM / 百度文心 / 讯飞星火 / Ollama 本地模型
> 管理后台可视化配置，动态切换，无需重启

### 🔐 企业级管理后台
> 用户管理 / 角色权限(RBAC) / 大模型配置 / 词库管理 / 审计日志 / 平台设置 / 品牌定制

### 🔗 飞书对接（可选）
> 飞书扫码登录 / SSO 单点登录 / 自动创建用户 — 默认关闭，按需配置

---

## 🛠️ 技术栈

| 层级 | 技术方案 |
|:----:|----------|
| **前端** | Vue 3 + TypeScript + Vite + Element Plus + Pinia |
| **编辑器** | Tiptap 富文本 + docx-preview + pdf.js |
| **后端** | Python 3.10+ / FastAPI / SQLAlchemy 2.0 |
| **数据库** | PostgreSQL + Redis |
| **异步任务** | Celery Worker |
| **认证** | JWT + RBAC 权限模型 |
| **部署** | Docker Compose (3 容器架构) |

---

## 🚀 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### 本地开发

```bash
# 1. 克隆项目
git clone https://github.com/shuke592/TextGuard.git
cd TextGuard

# 2. 配置后端环境
cd backend
cp .env.example .env          # 复制并修改配置（数据库/Redis/API Key）
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 初始化数据库
alembic upgrade head
python init_database.py    # 创建测试数据（管理员账号、角色权限等）

# 4. 配置前端
cd ../frontend
npm install --registry=https://registry.npmmirror.com

# 5. 一键启动（Windows）
cd ..
start_dev.bat
```

### Windows 快捷启动

```bash
# 首次安装依赖
安装依赖.bat

# 日常开发（自动清理端口 + 启动前后端）
start_dev.bat
```

| 服务 | 地址 |
|------|------|
| 前端 | http://localhost:3022 |
| 后端 API 文档 | http://localhost:3020/docs |
| 默认账号 | admin / admin123 |

---

## 🐳 Docker 部署

```bash
# 1. 修改生产配置
cp backend/.env.example backend/.env.production
# 编辑 .env.production 填入实际的数据库、Redis、大模型 API Key 等

# 2. 构建镜像（Windows）
build_images.bat

# 3. 上传到服务器后部署
bash deploy.sh
```

### 启用 HTTPS（可选）

1. 将 SSL 证书放到 `frontend/ssl/` 目录
2. 将 `frontend/nginx.production.ssl.conf` 重命名为 `nginx.production.conf`
3. 修改证书路径后重新构建前端镜像

> 详细部署文档请参考 [部署操作指南](部署操作指南.md)

---

## 📁 项目结构

```
TextGuard/
├── backend/                # 后端（FastAPI）
│   ├── app/
│   │   ├── api/           # API 路由
│   │   ├── core/          # 核心配置、安全、数据库
│   │   ├── models/        # 数据模型
│   │   └── services/      # 业务逻辑层
│   ├── alembic/           # 数据库迁移
│   ├── .env.example       # 配置模板
│   └── requirements.txt
├── frontend/              # 前端（Vue 3）
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── stores/        # Pinia 状态管理
│   │   ├── api/           # API 接口
│   │   └── utils/         # 工具函数
│   ├── nginx.production.conf      # Nginx 配置（HTTP）
│   ├── nginx.production.ssl.conf  # Nginx 配置（HTTPS）
│   └── Dockerfile
├── docker-compose.yml     # 容器编排
├── deploy.sh              # 服务器部署脚本
├── start_dev.bat          # Windows 一键启动
└── README.md
```

---

## 📖 文档索引

| 文档 | 说明 |
|------|------|
| [数据库初始化说明](数据库初始化说明.md) | 数据库安装、配置、初始化、常见问题 |
| [系统功能设计文档](系统功能设计文档.md) | 技术架构、数据模型、API 设计、开发规范 |
| [系统运维操作手册](系统运维操作手册.md) | 本地开发、生产部署、日常运维、故障排查 |
| [功能说明文档](智能文档审校平台功能说明.md) | 产品功能描述、用户端 / 管理后台功能清单 |
| [部署操作指南](部署操作指南.md) | Docker 部署、日常更新、回滚操作 |
| [用户使用手册](用户使用手册.md) | 面向终端用户的操作指南 |

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的修改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交 Pull Request

> 详细贡献指南请参考 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 开源协议，你可以自由使用、修改和分发。

---

## ⭐ Star History

如果这个项目对你有帮助，请点一个 ⭐ Star 支持一下！

---

<div align="center">

**TextGuard** — 让 AI 守护每一个文字

Made with ❤️ by TextGuard Contributors

</div>
