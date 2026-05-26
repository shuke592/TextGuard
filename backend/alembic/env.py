"""
Alembic 迁移环境配置
支持异步 SQLAlchemy 引擎
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Alembic Config 对象
config = context.config

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 导入所有模型以便 Alembic 自动检测
from app.core.database import Base
from app.models.base import BaseModel  # noqa
from app.models.user import User  # noqa
from app.models.role import Role, Permission, RolePermission  # noqa
from app.models.proofread import ProofreadRecord  # noqa
from app.models.dictionary import Dictionary, DictionaryEntry, WhitelistWord  # noqa
from app.models.global_word import GlobalWord  # noqa
from app.models.llm_config import LLMConfig  # noqa
from app.models.audit_log import AuditLog  # noqa
from app.models.uploaded_document import UploadedDocument  # noqa

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """以离线模式运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """以异步模式运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """以在线模式运行迁移"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
