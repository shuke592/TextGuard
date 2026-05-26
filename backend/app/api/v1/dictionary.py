"""
TextGuard 自定义词库 API
仅登录用户可使用
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.dictionary import Dictionary, DictionaryEntry
from app.schemas.dictionary import (
    DictionaryCreate, DictionaryUpdate, DictionaryResponse,
    EntryCreate, EntryBatchCreate, EntryResponse,
)

router = APIRouter(prefix="/dictionary", tags=["自定义词库"])


# ========== 词库 CRUD ==========

@router.get("", response_model=list[DictionaryResponse])
async def list_dictionaries(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取当前用户的词库列表"""
    result = await db.execute(
        select(Dictionary)
        .where(Dictionary.user_id == current_user.id)
        .order_by(Dictionary.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=DictionaryResponse, status_code=201)
async def create_dictionary(
    data: DictionaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """创建词库"""
    # 检查同名词库
    exists = await db.execute(
        select(Dictionary).where(
            Dictionary.user_id == current_user.id,
            Dictionary.name == data.name,
        )
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已存在同名词库")

    dictionary = Dictionary(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
    )
    db.add(dictionary)
    await db.flush()
    await db.refresh(dictionary)
    return dictionary


@router.put("/{dict_id}", response_model=DictionaryResponse)
async def update_dictionary(
    dict_id: int,
    data: DictionaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """更新词库"""
    result = await db.execute(
        select(Dictionary).where(
            Dictionary.id == dict_id,
            Dictionary.user_id == current_user.id,
        )
    )
    dictionary = result.scalar_one_or_none()
    if not dictionary:
        raise HTTPException(status_code=404, detail="词库不存在")

    if data.name is not None:
        dictionary.name = data.name
    if data.description is not None:
        dictionary.description = data.description
    if data.is_active is not None:
        dictionary.is_active = data.is_active

    await db.flush()
    await db.refresh(dictionary)
    return dictionary


@router.delete("/{dict_id}", status_code=204)
async def delete_dictionary(
    dict_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除词库（级联删除词条）"""
    result = await db.execute(
        select(Dictionary).where(
            Dictionary.id == dict_id,
            Dictionary.user_id == current_user.id,
        )
    )
    dictionary = result.scalar_one_or_none()
    if not dictionary:
        raise HTTPException(status_code=404, detail="词库不存在")

    await db.delete(dictionary)


# ========== 词条 CRUD ==========

@router.get("/{dict_id}/entries", response_model=list[EntryResponse])
async def list_entries(
    dict_id: int,
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取词库的词条列表"""
    # 验证词库归属
    dict_result = await db.execute(
        select(Dictionary).where(
            Dictionary.id == dict_id,
            Dictionary.user_id == current_user.id,
        )
    )
    if not dict_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="词库不存在")

    query = select(DictionaryEntry).where(DictionaryEntry.dictionary_id == dict_id)
    if keyword:
        query = query.where(
            DictionaryEntry.wrong_word.contains(keyword) |
            DictionaryEntry.correct_word.contains(keyword)
        )
    query = query.order_by(DictionaryEntry.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{dict_id}/entries", response_model=EntryResponse, status_code=201)
async def create_entry(
    dict_id: int,
    data: EntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """添加单条词条"""
    dict_result = await db.execute(
        select(Dictionary).where(
            Dictionary.id == dict_id,
            Dictionary.user_id == current_user.id,
        )
    )
    dictionary = dict_result.scalar_one_or_none()
    if not dictionary:
        raise HTTPException(status_code=404, detail="词库不存在")

    entry = DictionaryEntry(
        dictionary_id=dict_id,
        wrong_word=data.wrong_word,
        correct_word=data.correct_word,
        remark=data.remark,
    )
    db.add(entry)
    dictionary.entry_count += 1
    await db.flush()
    await db.refresh(entry)
    return entry


@router.post("/{dict_id}/entries/batch", status_code=201)
async def batch_create_entries(
    dict_id: int,
    data: EntryBatchCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批量添加词条"""
    dict_result = await db.execute(
        select(Dictionary).where(
            Dictionary.id == dict_id,
            Dictionary.user_id == current_user.id,
        )
    )
    dictionary = dict_result.scalar_one_or_none()
    if not dictionary:
        raise HTTPException(status_code=404, detail="词库不存在")

    entries = [
        DictionaryEntry(
            dictionary_id=dict_id,
            wrong_word=e.wrong_word,
            correct_word=e.correct_word,
            remark=e.remark,
        )
        for e in data.entries
    ]
    db.add_all(entries)
    dictionary.entry_count += len(entries)
    await db.flush()

    return {"message": f"成功添加 {len(entries)} 条词条", "count": len(entries)}


@router.delete("/{dict_id}/entries/{entry_id}", status_code=204)
async def delete_entry(
    dict_id: int,
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除词条"""
    dict_result = await db.execute(
        select(Dictionary).where(
            Dictionary.id == dict_id,
            Dictionary.user_id == current_user.id,
        )
    )
    dictionary = dict_result.scalar_one_or_none()
    if not dictionary:
        raise HTTPException(status_code=404, detail="词库不存在")

    entry_result = await db.execute(
        select(DictionaryEntry).where(
            DictionaryEntry.id == entry_id,
            DictionaryEntry.dictionary_id == dict_id,
        )
    )
    entry = entry_result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="词条不存在")

    await db.delete(entry)
    dictionary.entry_count = max(0, dictionary.entry_count - 1)
