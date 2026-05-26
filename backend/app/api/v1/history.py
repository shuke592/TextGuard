"""
TextGuard 校对历史记录 API
仅登录用户可查看自己的历史
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.proofread import ProofreadRecord
from app.schemas.history import HistoryListResponse, HistoryDetailResponse, HistoryListItem
from app.services.audit_log import record_audit_log

router = APIRouter(prefix="/history", tags=["校对历史"])


@router.get("", response_model=HistoryListResponse)
async def list_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    type: Optional[str] = Query(None, description="记录类型: text/document/polish"),
    domain: Optional[str] = Query(None, description="领域"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的校对历史列表"""
    # 构建查询
    base_query = select(ProofreadRecord).where(ProofreadRecord.user_id == current_user.id)

    if type:
        base_query = base_query.where(ProofreadRecord.type == type)
    if domain:
        base_query = base_query.where(ProofreadRecord.domain == domain)

    # 统计总数
    count_query = select(func.count()).select_from(
        base_query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询
    list_query = base_query.order_by(desc(ProofreadRecord.created_at))
    list_query = list_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(list_query)
    records = result.scalars().all()

    items = [
        HistoryListItem(
            id=r.id,
            type=r.type,
            domain=r.domain,
            total_issues=r.total_issues,
            text_preview=(r.original_text or "")[:100] + ("..." if r.original_text and len(r.original_text) > 100 else ""),
            source_filename=r.source_filename,
            token_usage=r.token_usage,
            created_at=r.created_at,
        )
        for r in records
    ]

    return HistoryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{record_id}", response_model=HistoryDetailResponse)
async def get_history_detail(
    record_id: int,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取校对记录详情"""
    result = await db.execute(
        select(ProofreadRecord).where(
            ProofreadRecord.id == record_id,
            ProofreadRecord.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    # 记录审计日志（查看历史详情）
    record_audit_log(
        http_request, "view_history", user=current_user,
        extra_params={"record_id": record_id, "record_type": record.type},
    )

    return HistoryDetailResponse(
        id=record.id,
        type=record.type,
        domain=record.domain,
        original_text=record.original_text,
        modified_text=record.modified_text,
        check_types=record.check_types,
        result=record.result,
        total_issues=record.total_issues,
        source_filename=record.source_filename,
        token_usage=record.token_usage,
        created_at=record.created_at,
    )


@router.delete("/{record_id}", status_code=204)
async def delete_history(
    record_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除校对记录"""
    result = await db.execute(
        select(ProofreadRecord).where(
            ProofreadRecord.id == record_id,
            ProofreadRecord.user_id == current_user.id,
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="记录不存在")

    await db.delete(record)
