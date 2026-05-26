"""
TextGuard 游客限流中间件
基于 IP + Redis 的每日计数器实现
"""
from fastapi import Request, HTTPException, status
from loguru import logger

from app.core.config import settings
from app.core.redis import get_redis


async def check_guest_rate_limit(request: Request):
    """
    游客限流检查
    对未携带 Token 的请求进行 IP 维度的每日限流
    每日限制次数由 settings.GUEST_DAILY_LIMIT 控制
    """
    # 检查是否携带 Token（已登录用户不限流）
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and len(auth_header) > 10:
        return  # 已登录用户跳过限流

    # 获取客户端 IP
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    # Redis 计数器 key
    redis_key = f"textguard:guest_limit:{client_ip}"

    try:
        redis = get_redis()
        current_count = await redis.get(redis_key)

        if current_count is not None and int(current_count) >= settings.GUEST_DAILY_LIMIT:
            logger.warning(f"游客限流触发: IP={client_ip}, count={current_count}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"游客每日最多使用 {settings.GUEST_DAILY_LIMIT} 次，请登录后继续使用",
            )

        # 计数器自增
        pipe = redis.pipeline()
        pipe.incr(redis_key)
        # 设置24小时过期（首次设置）
        if current_count is None:
            pipe.expire(redis_key, 86400)
        await pipe.execute()

    except HTTPException:
        raise
    except Exception as e:
        # Redis 异常不阻塞请求，仅记录日志
        logger.error(f"游客限流 Redis 异常: {e}")
