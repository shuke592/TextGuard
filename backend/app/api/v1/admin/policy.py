"""
TextGuard 策略管理 API（管理后台）
配置游客和登录用户的使用策略
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.core.dependencies import require_permission
from app.core.redis import get_redis

router = APIRouter(prefix="/policy", tags=["策略管理"])

# Redis 键前缀
GUEST_POLICY_KEY = "system:policy:guest"
USER_POLICY_KEY = "system:policy:user"


class GuestPolicyConfig(BaseModel):
    """游客策略配置"""
    daily_limit: int = 20
    max_text_length: int = 5000
    allow_upload: bool = True


class UserPolicyConfig(BaseModel):
    """登录用户策略配置"""
    daily_limit: int = 200
    max_text_length: int = 50000
    allow_upload: bool = True
    allow_export: bool = True
    allow_dictionary: bool = True


@router.get("/guest", response_model=GuestPolicyConfig)
async def get_guest_policy(
    _user=Depends(require_permission("admin:policy:edit")),
):
    """获取游客策略配置"""
    redis = await get_redis()
    data = await redis.hgetall(GUEST_POLICY_KEY)
    
    if not data:
        # 返回默认值
        return GuestPolicyConfig()
    
    return GuestPolicyConfig(
        daily_limit=int(data.get(b"daily_limit", 20)),
        max_text_length=int(data.get(b"max_text_length", 5000)),
        allow_upload=data.get(b"allow_upload", b"1") == b"1",
    )


@router.put("/guest", response_model=GuestPolicyConfig)
async def update_guest_policy(
    config: GuestPolicyConfig,
    _user=Depends(require_permission("admin:policy:edit")),
):
    """更新游客策略配置"""
    redis = await get_redis()
    await redis.hset(
        GUEST_POLICY_KEY,
        mapping={
            "daily_limit": config.daily_limit,
            "max_text_length": config.max_text_length,
            "allow_upload": "1" if config.allow_upload else "0",
        }
    )
    logger.info(f"游客策略已更新: {config.model_dump()}")
    return config


@router.get("/user", response_model=UserPolicyConfig)
async def get_user_policy(
    _user=Depends(require_permission("admin:policy:edit")),
):
    """获取登录用户策略配置"""
    redis = await get_redis()
    data = await redis.hgetall(USER_POLICY_KEY)
    
    if not data:
        return UserPolicyConfig()
    
    return UserPolicyConfig(
        daily_limit=int(data.get(b"daily_limit", 200)),
        max_text_length=int(data.get(b"max_text_length", 50000)),
        allow_upload=data.get(b"allow_upload", b"1") == b"1",
        allow_export=data.get(b"allow_export", b"1") == b"1",
        allow_dictionary=data.get(b"allow_dictionary", b"1") == b"1",
    )


@router.put("/user", response_model=UserPolicyConfig)
async def update_user_policy(
    config: UserPolicyConfig,
    _user=Depends(require_permission("admin:policy:edit")),
):
    """更新登录用户策略配置"""
    redis = await get_redis()
    await redis.hset(
        USER_POLICY_KEY,
        mapping={
            "daily_limit": config.daily_limit,
            "max_text_length": config.max_text_length,
            "allow_upload": "1" if config.allow_upload else "0",
            "allow_export": "1" if config.allow_export else "0",
            "allow_dictionary": "1" if config.allow_dictionary else "0",
        }
    )
    logger.info(f"用户策略已更新: {config.model_dump()}")
    return config
