"""
TextGuard 放行词（白名单）API
仅登录用户可使用
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.dictionary import WhitelistWord
from app.schemas.dictionary import WhitelistCreate, WhitelistUpdate, WhitelistResponse

router = APIRouter(prefix="/whitelist", tags=["放行词"])


@router.get("", response_model=list[WhitelistResponse])
async def list_whitelist(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的放行词列表"""
    query = select(WhitelistWord).where(WhitelistWord.user_id == current_user.id)
    if keyword:
        query = query.where(WhitelistWord.word.contains(keyword))
    query = query.order_by(WhitelistWord.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=WhitelistResponse, status_code=201)
async def create_whitelist_word(
    data: WhitelistCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """添加放行词"""
    # 检查是否已存在
    exists = await db.execute(
        select(WhitelistWord).where(
            WhitelistWord.user_id == current_user.id,
            WhitelistWord.word == data.word,
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该放行词已存在")

    word = WhitelistWord(
        user_id=current_user.id,
        word=data.word,
        type=data.type,
        remark=data.remark,
        expire_at=data.expire_at,
    )
    db.add(word)
    await db.flush()
    await db.refresh(word)
    return word


@router.put("/{word_id}", response_model=WhitelistResponse)
async def update_whitelist_word(
    word_id: int,
    data: WhitelistUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新放行词"""
    result = await db.execute(
        select(WhitelistWord).where(
            WhitelistWord.id == word_id,
            WhitelistWord.user_id == current_user.id,
        )
    )
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="放行词不存在")

    if data.word is not None:
        word.word = data.word
    if data.type is not None:
        word.type = data.type
    if data.remark is not None:
        word.remark = data.remark
    if data.expire_at is not None:
        word.expire_at = data.expire_at

    await db.flush()
    await db.refresh(word)
    return word


@router.delete("/{word_id}", status_code=204)
async def delete_whitelist_word(
    word_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除放行词"""
    result = await db.execute(
        select(WhitelistWord).where(
            WhitelistWord.id == word_id,
            WhitelistWord.user_id == current_user.id,
        )
    )
    word = result.scalar_one_or_none()
    if not word:
        raise HTTPException(status_code=404, detail="放行词不存在")

    await db.delete(word)


@router.post("/batch", status_code=201)
async def batch_create_whitelist(
    words: list[WhitelistCreate],
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批量添加放行词"""
    added = 0
    for item in words:
        exists = await db.execute(
            select(WhitelistWord).where(
                WhitelistWord.user_id == current_user.id,
                WhitelistWord.word == item.word,
            )
        )
        if exists.scalar_one_or_none():
            continue
        db.add(WhitelistWord(
            user_id=current_user.id,
            word=item.word,
            type=item.type,
            remark=item.remark,
            expire_at=item.expire_at,
        ))
        added += 1

    await db.flush()
    return {"message": f"成功添加 {added} 个放行词", "count": added}
