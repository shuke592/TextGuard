"""
TextGuard 全局词库管理 API（管理后台）
仅管理员可操作
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.global_word import GlobalWord
from app.schemas.global_word import (
    GlobalWordCreate, GlobalWordUpdate, GlobalWordResponse,
    GlobalWordBatchCreate, GlobalWordStats,
)

router = APIRouter(prefix="/global-dict", tags=["全局词库管理"])


@router.get("/stats", response_model=GlobalWordStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:global_dict:edit")),
):
    """获取全局词库统计"""
    total = (await db.execute(select(func.count(GlobalWord.id)))).scalar() or 0
    sensitive = (await db.execute(
        select(func.count(GlobalWord.id)).where(GlobalWord.type == "sensitive")
    )).scalar() or 0
    banned = (await db.execute(
        select(func.count(GlobalWord.id)).where(GlobalWord.type == "banned")
    )).scalar() or 0
    whitelist = (await db.execute(
        select(func.count(GlobalWord.id)).where(GlobalWord.type == "whitelist")
    )).scalar() or 0
    correction = (await db.execute(
        select(func.count(GlobalWord.id)).where(GlobalWord.type == "correction")
    )).scalar() or 0

    return GlobalWordStats(
        total=total,
        sensitive_count=sensitive,
        banned_count=banned,
        whitelist_count=whitelist,
        correction_count=correction,
    )


@router.get("", response_model=list[GlobalWordResponse])
async def list_global_words(
    type: Optional[str] = Query(None, description="类型过滤: sensitive/banned/whitelist/correction"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:global_dict:edit")),
):
    """获取全局词库列表"""
    query = select(GlobalWord)
    if type:
        query = query.where(GlobalWord.type == type)
    if keyword:
        query = query.where(GlobalWord.word.contains(keyword))
    query = query.order_by(GlobalWord.type, GlobalWord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=GlobalWordResponse, status_code=201)
async def create_global_word(
    data: GlobalWordCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:global_dict:edit")),
):
    """添加全局词条"""
    # 检查重复
    exists = await db.execute(
        select(GlobalWord).where(
            GlobalWord.word == data.word,
            GlobalWord.type == data.type,
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该词条已存在")

    word = GlobalWord(
        word=data.word,
        type=data.type,
        replacement=data.replacement,
        category=data.category,
        severity=data.severity,
        remark=data.remark,
    )
    db.add(word)
    await db.flush()
    await db.refresh(word)
    logger.info(f"全局词条已添加: {data.word} ({data.type})")
    return word


@router.post("/batch", status_code=201)
async def batch_create_global_words(
    data: GlobalWordBatchCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:global_dict:edit")),
):
    """批量添加全局词条"""
    added = 0
    skipped = 0
    for entry in data.entries:
        exists = await db.execute(
            select(GlobalWord).where(
                GlobalWord.word == entry.word,
                GlobalWord.type == entry.type,
            )
        )
        if exists.scalar_one_or_none():
            skipped += 1
            continue
        db.add(GlobalWord(
            word=entry.word,
            type=entry.type,
            replacement=entry.replacement,
            category=entry.category,
            severity=entry.severity,
            remark=entry.remark,
        ))
        added += 1

    await db.flush()
    logger.info(f"批量添加全局词条: 成功={added}, 跳过={skipped}")
    return {"message": f"成功添加 {added} 条，跳过 {skipped} 条重复", "added": added, "skipped": skipped}


@router.put("/{word_id}", response_model=GlobalWordResponse)
async def update_global_word(
    word_id: int,
    data: GlobalWordUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:global_dict:edit")),
):
    """更新全局词条"""
    result = await db.execute(select(GlobalWord).where(GlobalWord.id == word_id))
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="词条不存在")

    for field in ["word", "type", "replacement", "category", "severity", "remark", "is_active"]:
        val = getattr(data, field, None)
        if val is not None:
            setattr(word, field, val)

    await db.flush()
    await db.refresh(word)
    return word


@router.delete("/{word_id}", status_code=204)
async def delete_global_word(
    word_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:global_dict:edit")),
):
    """删除全局词条"""
    result = await db.execute(select(GlobalWord).where(GlobalWord.id == word_id))
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="词条不存在")
    await db.delete(word)
    logger.info(f"全局词条已删除: {word.word} ({word.type})")
