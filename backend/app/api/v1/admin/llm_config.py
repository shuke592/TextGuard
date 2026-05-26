"""
TextGuard 大模型配置管理 API（管理后台）
支持多个大模型配置的增删改查、测试连接、切换默认模型
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.llm_config import LLMConfig
from app.schemas.llm_config import (
    LLMConfigCreate, LLMConfigUpdate, LLMConfigResponse,
    LLMTestResult, LLMProviderOption, SUPPORTED_PROVIDERS,
)
from app.services.llm.openai_compat import OpenAICompatProvider

router = APIRouter(prefix="/llm-config", tags=["大模型配置管理"])


def _mask_api_key(api_key: str) -> str:
    """API 密钥脱敏"""
    if not api_key or len(api_key) <= 8:
        return "****"
    return api_key[:4] + "****" + api_key[-4:]


def _to_response(config: LLMConfig) -> LLMConfigResponse:
    """模型实例转响应（含密钥脱敏）"""
    resp = LLMConfigResponse.model_validate(config)
    resp.api_key_masked = _mask_api_key(config.api_key)
    return resp


@router.get("/providers", response_model=list[LLMProviderOption])
async def list_providers(_user=Depends(require_permission("admin:llm:edit"))):
    """获取支持的大模型供应商列表"""
    return [LLMProviderOption(**p) for p in SUPPORTED_PROVIDERS]


@router.get("", response_model=list[LLMConfigResponse])
async def list_llm_configs(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """获取所有大模型配置列表"""
    result = await db.execute(
        select(LLMConfig).order_by(LLMConfig.is_active.desc(), LLMConfig.created_at.asc())
    )
    configs = result.scalars().all()
    return [_to_response(c) for c in configs]


@router.post("", response_model=LLMConfigResponse, status_code=201)
async def create_llm_config(
    data: LLMConfigCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """创建大模型配置"""
    # 检查名称唯一
    exists = await db.execute(select(LLMConfig).where(LLMConfig.name == data.name))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="配置名称已存在")

    config = LLMConfig(
        name=data.name,
        provider=data.provider,
        api_base=data.api_base,
        api_key=data.api_key,
        model=data.model,
        temperature=data.temperature,
        max_tokens=data.max_tokens,
        timeout=data.timeout,
        max_retries=data.max_retries,
        remark=data.remark,
        is_active=False,
        is_enabled=True,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)
    logger.info(f"大模型配置已创建: {data.name} ({data.provider})")
    return _to_response(config)


@router.put("/{config_id}", response_model=LLMConfigResponse)
async def update_llm_config(
    config_id: int,
    data: LLMConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """更新大模型配置"""
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(config, field, val)

    await db.flush()
    await db.refresh(config)
    logger.info(f"大模型配置已更新: {config.name}")
    return _to_response(config)


@router.delete("/{config_id}", status_code=204)
async def delete_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """删除大模型配置"""
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    if config.is_active:
        raise HTTPException(status_code=400, detail="不能删除当前正在使用的配置，请先切换到其他模型")

    await db.delete(config)
    logger.info(f"大模型配置已删除: {config.name}")


@router.post("/{config_id}/activate", response_model=LLMConfigResponse)
async def activate_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """设为当前使用的模型（全局仅一个活跃）"""
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    if not config.is_enabled:
        raise HTTPException(status_code=400, detail="该配置已停用，请先启用")

    # 将所有配置设为非活跃
    await db.execute(update(LLMConfig).values(is_active=False))
    # 将目标配置设为活跃
    config.is_active = True
    await db.flush()
    await db.refresh(config)
    logger.info(f"当前大模型已切换为: {config.name} ({config.provider}/{config.model})")
    return _to_response(config)


@router.post("/{config_id}/test", response_model=LLMTestResult)
async def test_llm_config(
    config_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """测试大模型连接"""
    result = await db.execute(select(LLMConfig).where(LLMConfig.id == config_id))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")

    provider = OpenAICompatProvider(
        api_key=config.api_key,
        api_base=config.api_base,
        model=config.model,
        timeout=min(config.timeout, 30),  # 测试用短超时
        max_retries=1,
        provider_name=config.name,
    )
    try:
        test_result = await provider.test_connection()
        return LLMTestResult(**test_result)
    finally:
        await provider.close()


@router.get("/active", response_model=LLMConfigResponse)
async def get_active_config(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:llm:edit")),
):
    """获取当前活跃的大模型配置"""
    result = await db.execute(select(LLMConfig).where(LLMConfig.is_active == True))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="尚未配置活跃的大模型，请在管理后台配置")
    return _to_response(config)
