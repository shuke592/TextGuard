"""
TextGuard 系统配置管理 API（管理后台）
包含：基本设置、飞书配置、安全设置、数据维护
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, cast, Date
from loguru import logger

from app.core.dependencies import require_permission
from app.core.redis import get_redis
from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/system-config", tags=["系统配置管理"])

# Redis 键前缀
BASIC_SETTINGS_KEY = "system:config:basic"
FEISHU_SETTINGS_KEY = "system:config:feishu"
SECURITY_SETTINGS_KEY = "system:config:security"


# ========== 基本设置 ==========
class BasicSettingsConfig(BaseModel):
    """系统基本设置"""
    version: str = "1.0.0"
    debug: bool = False
    allow_register: bool = False
    maintenance_mode: bool = False


@router.get("/basic", response_model=BasicSettingsConfig)
async def get_basic_settings(
    _user=Depends(require_permission("admin:settings:edit")),
):
    """获取系统基本设置"""
    redis = await get_redis()
    data = await redis.hgetall(BASIC_SETTINGS_KEY)
    
    if not data:
        return BasicSettingsConfig()
    
    return BasicSettingsConfig(
        version=data.get(b"version", b"1.0.0").decode(),
        debug=data.get(b"debug", b"0") == b"1",
        allow_register=data.get(b"allow_register", b"0") == b"1",
        maintenance_mode=data.get(b"maintenance_mode", b"0") == b"1",
    )


@router.put("/basic", response_model=BasicSettingsConfig)
async def update_basic_settings(
    config: BasicSettingsConfig,
    _user=Depends(require_permission("admin:settings:edit")),
):
    """更新系统基本设置"""
    redis = await get_redis()
    await redis.hset(
        BASIC_SETTINGS_KEY,
        mapping={
            "version": config.version,
            "debug": "1" if config.debug else "0",
            "allow_register": "1" if config.allow_register else "0",
            "maintenance_mode": "1" if config.maintenance_mode else "0",
        }
    )
    logger.info(f"系统基本设置已更新: {config.model_dump()}")
    return config


# ========== 飞书配置 ==========
class FeishuSettingsConfig(BaseModel):
    """飞书对接配置"""
    enabled: bool = False
    app_id: str = ""
    app_secret: str = ""
    redirect_uri: str = ""


@router.get("/feishu", response_model=FeishuSettingsConfig)
async def get_feishu_settings(
    _user=Depends(require_permission("admin:settings:edit")),
):
    """获取飞书配置"""
    redis = await get_redis()
    data = await redis.hgetall(FEISHU_SETTINGS_KEY)
    
    if not data:
        return FeishuSettingsConfig()
    
    return FeishuSettingsConfig(
        enabled=data.get(b"enabled", b"0") == b"1",
        app_id=data.get(b"app_id", b"").decode(),
        app_secret=data.get(b"app_secret", b"").decode(),
        redirect_uri=data.get(b"redirect_uri", b"").decode(),
    )


@router.put("/feishu", response_model=FeishuSettingsConfig)
async def update_feishu_settings(
    config: FeishuSettingsConfig,
    _user=Depends(require_permission("admin:settings:edit")),
):
    """更新飞书配置"""
    redis = await get_redis()
    await redis.hset(
        FEISHU_SETTINGS_KEY,
        mapping={
            "enabled": "1" if config.enabled else "0",
            "app_id": config.app_id,
            "app_secret": config.app_secret,
            "redirect_uri": config.redirect_uri,
        }
    )
    logger.info(f"飞书配置已更新（app_id={config.app_id}）")
    return config


# ========== 安全设置 ==========
class SecuritySettingsConfig(BaseModel):
    """用户安全设置"""
    default_password: str = "admin123"


@router.get("/security", response_model=SecuritySettingsConfig)
async def get_security_settings(
    _user=Depends(require_permission("admin:settings:edit")),
):
    """获取安全设置"""
    redis = await get_redis()
    data = await redis.hgetall(SECURITY_SETTINGS_KEY)
    
    if not data:
        # 返回配置文件中的默认密码
        return SecuritySettingsConfig(default_password=settings.DEFAULT_USER_PASSWORD)
    
    return SecuritySettingsConfig(
        default_password=data.get(b"default_password", settings.DEFAULT_USER_PASSWORD.encode()).decode(),
    )


@router.put("/security", response_model=SecuritySettingsConfig)
async def update_security_settings(
    config: SecuritySettingsConfig,
    _user=Depends(require_permission("admin:settings:edit")),
):
    """更新安全设置"""
    redis = await get_redis()
    await redis.hset(
        SECURITY_SETTINGS_KEY,
        mapping={"default_password": config.default_password}
    )
    
    # 同时更新 settings 对象（运行时生效）
    settings.DEFAULT_USER_PASSWORD = config.default_password
    
    logger.info("用户安全设置已更新")
    return config


# ========== 数据维护 ==========
class MaintenanceResult(BaseModel):
    """数据维护结果"""
    success: bool
    message: str
    deleted_count: int = 0


@router.post("/maintenance/clean-logs", response_model=MaintenanceResult)
async def clean_logs(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:settings:edit")),
):
    """清理审计日志（默认保留90天）"""
    from app.models.audit_log import AuditLog
    
    cutoff_date = datetime.utcnow().date() - timedelta(days=days)
    result = await db.execute(
        delete(AuditLog).where(cast(AuditLog.created_at, Date) < cutoff_date)
    )
    deleted = result.rowcount or 0
    await db.commit()
    
    logger.info(f"清理审计日志: 删除 {deleted} 条（{days}天前）")
    return MaintenanceResult(
        success=True,
        message=f"已清理 {days} 天前的审计日志",
        deleted_count=deleted,
    )


@router.post("/maintenance/clean-temp", response_model=MaintenanceResult)
async def clean_temp_files(
    _user=Depends(require_permission("admin:settings:edit")),
):
    """清理临时文件"""
    import os
    import shutil
    
    temp_dir = os.path.join(settings.UPLOAD_DIR, "temp")
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
        os.makedirs(temp_dir, exist_ok=True)
        logger.info("临时文件已清理")
        return MaintenanceResult(success=True, message="临时文件已清理")
    
    return MaintenanceResult(success=True, message="无临时文件需要清理")


@router.post("/maintenance/clean-cache", response_model=MaintenanceResult)
async def clean_cache(
    _user=Depends(require_permission("admin:settings:edit")),
):
    """清理 Redis 缓存（保留配置项）"""
    redis = await get_redis()
    
    # 获取所有键
    keys = await redis.keys("*")
    
    # 过滤出非配置项的缓存键
    cache_keys = [
        k for k in keys
        if not k.decode().startswith("system:")
    ]
    
    if cache_keys:
        await redis.delete(*cache_keys)
        logger.info(f"Redis 缓存已清理: {len(cache_keys)} 个键")
        return MaintenanceResult(
            success=True,
            message=f"已清理 {len(cache_keys)} 个缓存项",
            deleted_count=len(cache_keys),
        )
    
    return MaintenanceResult(success=True, message="无缓存需要清理")


@router.post("/maintenance/clean-expired-whitelist", response_model=MaintenanceResult)
async def clean_expired_whitelist(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:settings:edit")),
):
    """清理过期放行词"""
    from app.models.dictionary import WhitelistWord
    
    now = datetime.utcnow()
    result = await db.execute(
        delete(WhitelistWord).where(
            WhitelistWord.expires_at.isnot(None),
            WhitelistWord.expires_at < now
        )
    )
    deleted = result.rowcount or 0
    await db.commit()
    
    logger.info(f"清理过期放行词: 删除 {deleted} 条")
    return MaintenanceResult(
        success=True,
        message=f"已清理 {deleted} 条过期放行词",
        deleted_count=deleted,
    )
