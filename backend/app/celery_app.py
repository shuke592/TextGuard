"""
TextGuard Celery 应用实例
使用 Redis 作为 Broker 和 Result Backend
"""
from celery import Celery
from app.core.config import settings

# 使用独立 Redis DB 避免和缓存冲突 (db=8)
CELERY_BROKER_URL = settings.REDIS_URL.rsplit("/", 1)[0] + "/8"
CELERY_RESULT_BACKEND = settings.REDIS_URL.rsplit("/", 1)[0] + "/9"

celery_app = Celery(
    "textguard",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600 * 24,  # 结果保留24小时
    task_soft_time_limit=300,  # 软超时5分钟
    task_time_limit=360,  # 硬超时6分钟
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)

# 自动发现任务模块
celery_app.autodiscover_tasks(["app.tasks"])
