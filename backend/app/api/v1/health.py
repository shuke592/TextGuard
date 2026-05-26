"""
TextGuard 健康检查接口
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.database import get_db
from app.core.redis import get_redis

router = APIRouter(tags=["健康检查"])


@router.get("/health")
async def health_check():
    """基础健康检查"""
    return {"status": "ok", "service": "TextGuard API"}


@router.get("/health/db")
async def health_check_db(db: AsyncSession = Depends(get_db)):
    """数据库连接健康检查"""
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        return {"status": "error", "database": str(e)}


@router.get("/health/redis")
async def health_check_redis():
    """Redis 连接健康检查"""
    try:
        redis = get_redis()
        await redis.ping()
        return {"status": "ok", "redis": "connected"}
    except Exception as e:
        return {"status": "error", "redis": str(e)}
