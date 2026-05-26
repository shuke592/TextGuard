"""
TextGuard 大模型配置 Schema
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# 支持的供应商列表
SUPPORTED_PROVIDERS = [
    {"code": "deepseek", "name": "DeepSeek", "default_base": "https://api.deepseek.com", "default_model": "deepseek-chat"},
    {"code": "openai", "name": "OpenAI (ChatGPT)", "default_base": "https://api.openai.com", "default_model": "gpt-4o-mini"},
    {"code": "litellm", "name": "LiteLLM", "default_base": "http://localhost:4000", "default_model": "gpt-3.5-turbo"},
    {"code": "azure", "name": "Azure OpenAI", "default_base": "https://your-resource.openai.azure.com", "default_model": "gpt-4o"},
    {"code": "qwen", "name": "通义千问", "default_base": "https://dashscope.aliyuncs.com/compatible-mode", "default_model": "qwen-plus"},
    {"code": "zhipu", "name": "智谱 AI", "default_base": "https://open.bigmodel.cn/api/paas", "default_model": "glm-4-flash"},
    {"code": "moonshot", "name": "月之暗面 (Kimi)", "default_base": "https://api.moonshot.cn", "default_model": "moonshot-v1-8k"},
    {"code": "custom", "name": "自定义 (OpenAI 兼容)", "default_base": "", "default_model": ""},
]


class LLMConfigCreate(BaseModel):
    """创建大模型配置"""
    name: str = Field(..., max_length=100, description="配置名称")
    provider: str = Field(..., max_length=50, description="供应商标识")
    api_base: str = Field(..., max_length=500, description="API 基础地址")
    api_key: str = Field(..., max_length=500, description="API 密钥")
    model: str = Field(..., max_length=100, description="模型名称")
    temperature: float = Field(default=0.3, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(None, ge=1, description="最大输出 token 数")
    timeout: int = Field(default=180, ge=10, le=600, description="超时（秒）")
    max_retries: int = Field(default=2, ge=0, le=10, description="重试次数")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class LLMConfigUpdate(BaseModel):
    """更新大模型配置"""
    name: Optional[str] = Field(None, max_length=100)
    provider: Optional[str] = Field(None, max_length=50)
    api_base: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = Field(None, max_length=500)
    model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0, le=2)
    max_tokens: Optional[int] = Field(None, ge=1)
    timeout: Optional[int] = Field(None, ge=10, le=600)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    is_enabled: Optional[bool] = None
    remark: Optional[str] = Field(None, max_length=500)


class LLMConfigResponse(BaseModel):
    """大模型配置响应"""
    id: int
    name: str
    provider: str
    api_base: str
    api_key: str = ""           # 明文密钥（供编辑回填、运维查看）
    api_key_masked: str = ""    # 脱敏密钥（卡片展示用）
    model: str
    temperature: float
    max_tokens: Optional[int] = None
    timeout: int
    max_retries: int
    is_active: bool
    is_enabled: bool
    remark: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class LLMTestResult(BaseModel):
    """连接测试结果"""
    success: bool
    model: str = ""
    message: str = ""
    usage: dict = {}


class LLMProviderOption(BaseModel):
    """供应商选项（前端下拉用）"""
    code: str
    name: str
    default_base: str
    default_model: str
