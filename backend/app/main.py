"""
TextGuard 智能文档审校平台 - FastAPI 应用入口
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from loguru import logger

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.redis import init_redis, close_redis
from app.api.router import api_router

# 导入所有模型确保表元数据注册（勿删除）
import app.models.user  # noqa
import app.models.role  # noqa
import app.models.proofread  # noqa
import app.models.dictionary  # noqa
import app.models.global_word  # noqa
import app.models.llm_config  # noqa
import app.models.audit_log  # noqa


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭时执行"""
    # ---- 启动阶段 ----
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")

    # 初始化数据库
    await init_db()
    logger.info("✅ 数据库连接初始化完成")

    # 初始化 Redis
    await init_redis()
    logger.info("✅ Redis 连接初始化完成")

    # 确保上传目录存在
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.info(f"✅ 上传目录已就绪: {settings.UPLOAD_DIR}")

    logger.info(f"🎉 {settings.APP_NAME} 启动成功！")

    yield

    # ---- 关闭阶段 ----
    logger.info(f"🛑 {settings.APP_NAME} 正在关闭...")
    await close_db()
    await close_redis()
    logger.info(f"👋 {settings.APP_NAME} 已安全关闭")


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="智能文档审校平台 API",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # ---- 中间件配置 ----
    # CORS 跨域
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ---- 路由注册 ----
    app.include_router(api_router, prefix=settings.API_PREFIX)

    # ---- 静态文件（上传文件访问） ----
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    app.mount(
        "/uploads",
        StaticFiles(directory=settings.UPLOAD_DIR),
        name="uploads",
    )

    return app


# 创建应用实例
app = create_app()
