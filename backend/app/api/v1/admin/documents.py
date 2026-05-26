"""
TextGuard 后台管理 - 文档管理 API
提供上传文档的列表查询、下载、删除功能
"""
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.uploaded_document import UploadedDocument

router = APIRouter(prefix="/documents", tags=["后台-文档管理"])


@router.get("")
async def list_documents(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词(文件名/上传者)"),
    file_ext: Optional[str] = Query(None, description="文件类型筛选"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:documents:view")),
):
    """获取上传文档列表（分页）"""
    query = select(UploadedDocument).where(UploadedDocument.status != "deleted")

    # 条件筛选
    if keyword:
        query = query.where(
            (UploadedDocument.filename.ilike(f"%{keyword}%")) |
            (UploadedDocument.username.ilike(f"%{keyword}%"))
        )
    if file_ext:
        query = query.where(UploadedDocument.file_ext == file_ext)

    # 总数查询
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页查询
    query = query.order_by(desc(UploadedDocument.created_at))
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    docs = result.scalars().all()

    items = []
    for doc in docs:
        items.append({
            "id": doc.id,
            "file_id": doc.file_id,
            "filename": doc.filename,
            "file_ext": doc.file_ext,
            "file_size": doc.file_size,
            "text_length": doc.text_length,
            "username": doc.username or "游客",
            "status": doc.status,
            "download_url": f"/uploads/{doc.file_id}/{doc.filename}",
            "created_at": doc.created_at.strftime("%Y-%m-%d %H:%M:%S") if doc.created_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{file_id}/download")
async def download_document(
    file_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:documents:view")),
):
    """下载指定文档"""
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.file_id == file_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="文件已从服务器删除")

    return FileResponse(
        path=doc.file_path,
        filename=doc.filename,
        media_type="application/octet-stream",
    )


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:documents:delete")),
):
    """删除文档记录（软删除，标记为 deleted）"""
    result = await db.execute(
        select(UploadedDocument).where(UploadedDocument.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    doc.status = "deleted"
    await db.commit()
    logger.info(f"文档已删除: id={doc_id}, filename={doc.filename}")

    return {"message": "删除成功"}
