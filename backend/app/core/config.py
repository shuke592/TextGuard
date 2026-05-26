"""
TextGuard 全局配置管理
使用 Pydantic Settings 从 .env 文件和环境变量中加载配置
"""
import json
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """应用全局配置"""

    # ---- 应用基础配置 ----
    APP_NAME: str = "TextGuard"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "please-change-this-secret-key-in-production"
    API_PREFIX: str = "/api/v1"

    # ---- JWT 配置 ----
    JWT_SECRET_KEY: str = "please-change-this-jwt-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7天
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30天免登录

    # ---- PostgreSQL 数据库配置 ----
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "textguard"
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "your-db-password"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:your-db-password@localhost:5432/textguard"

    # ---- Redis 配置 ----
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str = ""
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0

    @property
    def REDIS_URL(self) -> str:
        """构建Redis连接URL"""
        if self.REDIS_USERNAME:
            return f"redis://{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ---- 大模型配置 - DeepSeek ----
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # ---- 文件存储配置 ----
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE_MB: int = 20

    # ---- 游客限流配置 ----
    GUEST_DAILY_LIMIT: int = 20
    GUEST_TEXT_MAX_LENGTH: int = 10000

    # ---- 飞书对接配置 ----
    FEISHU_APP_ID: str = ""
    FEISHU_APP_SECRET: str = ""
    FEISHU_REDIRECT_URI: str = ""
    FEISHU_ENABLED: bool = False

    # ---- 用户默认密码 ----
    DEFAULT_USER_PASSWORD: str = "admin123"

    # ---- CORS 配置 ----
    CORS_ORIGINS: List[str] = [
        "http://localhost:3022",
        "http://localhost:3000",
        "http://127.0.0.1:3022",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """支持从环境变量中解析JSON字符串"""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# 全局配置单例
settings = Settings()
