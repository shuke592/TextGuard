"""
TextGuard 大模型配置模型
支持多个大模型供应商配置，管理员可灵活切换
"""
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class LLMConfig(BaseModel):
    """
    大模型配置表
    支持存储多个大模型供应商的配置，通过 is_active 标记当前使用的模型
    所有兼容 OpenAI Chat Completions API 的模型均可接入
    """
    __tablename__ = "llm_configs"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="配置名称（如 DeepSeek、GPT-4o）"
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="供应商标识: deepseek/openai/litellm/azure/custom"
    )
    api_base: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="API 基础地址"
    )
    api_key: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="API 密钥（加密存储）"
    )
    model: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="模型名称（如 deepseek-chat、gpt-4o）"
    )
    temperature: Mapped[float] = mapped_column(
        Float, default=0.3, nullable=False, comment="默认温度参数"
    )
    max_tokens: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="最大输出 token 数，空则不限"
    )
    timeout: Mapped[int] = mapped_column(
        Integer, default=60, nullable=False, comment="单次请求超时（秒）"
    )
    max_retries: Mapped[int] = mapped_column(
        Integer, default=3, nullable=False, comment="失败重试次数"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True,
        comment="是否为当前使用的模型（全局仅一个为 True）"
    )
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用（停用后不可选为活跃）"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注说明"
    )

    def __repr__(self):
        return f"<LLMConfig(id={self.id}, name={self.name}, provider={self.provider}, active={self.is_active})>"
