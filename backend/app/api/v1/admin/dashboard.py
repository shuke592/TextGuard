"""
TextGuard 管理后台仪表盘 API
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date, text
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.proofread import ProofreadRecord
from app.models.uploaded_document import UploadedDocument
from app.models.user import User

router = APIRouter(prefix="/dashboard", tags=["仪表盘"])


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:access")),
):
    """获取仪表盘统计数据"""
    today = datetime.utcnow().date()

    # 今日校对次数
    today_count_result = await db.execute(
        select(func.count()).select_from(ProofreadRecord)
        .where(cast(ProofreadRecord.created_at, Date) == today)
    )
    today_proofread_count = today_count_result.scalar() or 0

    # 总校对次数
    total_count_result = await db.execute(
        select(func.count()).select_from(ProofreadRecord)
    )
    total_proofread_count = total_count_result.scalar() or 0

    # 总用户数
    total_users_result = await db.execute(
        select(func.count()).select_from(User)
    )
    total_users = total_users_result.scalar() or 0

    # 今日活跃用户（有校对记录的独立用户数）
    active_today_result = await db.execute(
        select(func.count(func.distinct(ProofreadRecord.user_id)))
        .where(cast(ProofreadRecord.created_at, Date) == today)
        .where(ProofreadRecord.user_id.isnot(None))
    )
    active_users_today = active_today_result.scalar() or 0

    # 总 token 用量（从 JSON 字段 token_usage->>'total_tokens' 聚合）
    total_token_usage = 0
    try:
        token_result = await db.execute(
            text("SELECT COALESCE(SUM((token_usage->>'total_tokens')::int), 0) FROM proofread_records WHERE token_usage IS NOT NULL")
        )
        total_token_usage = token_result.scalar() or 0
    except Exception as e:
        logger.warning(f"统计 token 用量失败: {e}")

    # 今日上传文档数
    today_doc_result = await db.execute(
        select(func.count()).select_from(UploadedDocument)
        .where(cast(UploadedDocument.created_at, Date) == today)
        .where(UploadedDocument.status != "deleted")
    )
    today_document_count = today_doc_result.scalar() or 0

    # 总上传文档数
    total_doc_result = await db.execute(
        select(func.count()).select_from(UploadedDocument)
        .where(UploadedDocument.status != "deleted")
    )
    total_document_count = total_doc_result.scalar() or 0

    return {
        "today_proofread_count": today_proofread_count,
        "total_proofread_count": total_proofread_count,
        "total_users": total_users,
        "active_users_today": active_users_today,
        "total_token_usage": total_token_usage,
        "today_document_count": today_document_count,
        "total_document_count": total_document_count,
    }
