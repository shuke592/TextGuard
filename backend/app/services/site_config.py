"""
TextGuard 站点配置服务
使用 Redis 存储站点级配置（平台名称、副标题、图标等）
"""
from typing import Dict, Any, Optional
from loguru import logger

from app.core.redis import get_redis

# Redis key 前缀
SITE_CONFIG_PREFIX = "site:config:"

# 默认配置
DEFAULT_SITE_CONFIG: Dict[str, str] = {
    "platform_name": "TextGuard",
    "platform_subtitle": "智能文档审校平台",
    "favicon_url": "/vite.svg",
}


async def get_site_config() -> Dict[str, str]:
    """
    获取全部站点配置
    优先从 Redis 读取，未设置的使用默认值
    """
    redis = get_redis()
    config = dict(DEFAULT_SITE_CONFIG)

    try:
        for key in DEFAULT_SITE_CONFIG:
            val = await redis.get(f"{SITE_CONFIG_PREFIX}{key}")
            if val is not None:
                config[key] = val
    except Exception as e:
        logger.warning(f"[站点配置] Redis 读取失败，使用默认值: {e}")

    return config


async def get_site_config_value(key: str) -> Optional[str]:
    """获取单个配置项"""
    redis = get_redis()
    try:
        val = await redis.get(f"{SITE_CONFIG_PREFIX}{key}")
        return val if val is not None else DEFAULT_SITE_CONFIG.get(key)
    except Exception as e:
        logger.warning(f"[站点配置] Redis 读取 {key} 失败: {e}")
        return DEFAULT_SITE_CONFIG.get(key)


async def update_site_config(updates: Dict[str, str]) -> Dict[str, str]:
    """
    批量更新站点配置
    :param updates: 要更新的配置键值对
    :return: 更新后的完整配置
    """
    redis = get_redis()
    allowed_keys = set(DEFAULT_SITE_CONFIG.keys())

    try:
        for key, value in updates.items():
            if key in allowed_keys:
                await redis.set(f"{SITE_CONFIG_PREFIX}{key}", value)
                logger.info(f"[站点配置] 已更新 {key} = {value}")
    except Exception as e:
        logger.error(f"[站点配置] Redis 写入失败: {e}")
        raise

    return await get_site_config()
