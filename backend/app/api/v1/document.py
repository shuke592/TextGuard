"""
TextGuard 文档校对 API
支持上传 .doc / .docx / .pdf / .txt 文件进行校对
"""
import os
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.config import settings
from app.core.dependencies import get_current_user_optional
from app.core.rate_limit import check_guest_rate_limit
from app.models.proofread import ProofreadRecord
from app.models.uploaded_document import UploadedDocument
from app.schemas.document import (
    DocumentUploadResponse,
    DocumentProofreadRequest,
    DocumentProofreadResponse,
)
from app.services.document import extract_text_from_file, extract_html_from_file, generate_corrected_docx, generate_corrected_txt
from app.services.proofread import proofread_text
from app.services.audit_log import record_audit_log, AuditTimer

from app.tasks.proofread_task import async_proofread_document

router = APIRouter(prefix="/document", tags=["文档校对"])

# 允许的文件扩展名
ALLOWED_EXTENSIONS = {".doc", ".docx", ".pdf", ".txt"}

# 临时存储上传文件的文本内容（生产环境应使用 Redis 或数据库）
_uploaded_files_cache: dict = {}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    http_request: Request = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    上传文档并提取文本
    返回文件 ID 和文本预览，供后续校对使用
    """
    # 校验文件名
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    # 获取扩展名
    _, file_ext = os.path.splitext(file.filename)
    file_ext = file_ext.lower()

    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式: {file_ext}，仅支持 .doc / .docx / .pdf / .txt",
        )

    # 读取文件内容
    content = await file.read()
    file_size = len(content)

    # 校验文件大小
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file_size > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"文件大小超过限制（{file_size // 1024 // 1024}MB，最大{settings.MAX_UPLOAD_SIZE_MB}MB）",
        )

    # 生成文件 ID 并保存到磁盘
    file_id = str(uuid.uuid4())
    upload_dir = os.path.join(settings.UPLOAD_DIR, file_id)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(content)

    # 提取文本
    try:
        extracted_text = extract_text_from_file(file_path, file_ext)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文本提取失败: {e}")
        raise HTTPException(status_code=500, detail="文件文本提取失败，请检查文件是否损坏")

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="文件中未提取到有效文本内容")

    # 缓存提取的文本和文件信息
    _uploaded_files_cache[file_id] = {
        "filename": file.filename,
        "file_path": file_path,
        "file_ext": file_ext,
        "file_size": file_size,
        "text": extracted_text,
        "user_id": current_user.id if current_user else None,
    }

    text_preview = extracted_text[:200] + ("..." if len(extracted_text) > 200 else "")

    # 提取格式化 HTML（保留排版和字体样式）
    extracted_html = ""
    try:
        extracted_html = extract_html_from_file(file_path, file_ext, extracted_text)
    except Exception as e:
        logger.warning(f"HTML格式提取失败，将降级使用纯文本: {e}")

    logger.info(f"文档上传成功: {file.filename}, 文本长度={len(extracted_text)}")

    # 写入数据库记录
    try:
        doc_record = UploadedDocument(
            file_id=file_id,
            filename=file.filename,
            file_ext=file_ext,
            file_size=file_size,
            file_path=file_path,
            text_length=len(extracted_text),
            extracted_text=extracted_text,
            user_id=current_user.id if current_user else None,
            username=current_user.username if current_user else None,
            status="uploaded",
        )
        db.add(doc_record)
        await db.commit()
    except Exception as e:
        logger.warning(f"保存文档上传记录失败（不影响上传功能）: {e}")

    # 记录审计日志（文档上传）
    if http_request:
        record_audit_log(
            http_request, "proofread_doc", user=current_user,
            input_text=text_preview,
            extra_params={"action": "upload", "text_length": len(extracted_text)},
            file_id=file_id,
            file_name=file.filename,
            file_path=file_path,
            file_size=file_size,
        )

    return DocumentUploadResponse(
        file_id=file_id,
        filename=file.filename,
        file_size=file_size,
        file_ext=file_ext,
        text_length=len(extracted_text),
        text_preview=text_preview,
        extracted_text=extracted_text,
        extracted_html=extracted_html,
    )


@router.post("/proofread", response_model=DocumentProofreadResponse)
async def document_proofread(
    request: DocumentProofreadRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    对已上传的文档执行校对
    需要先调用 /upload 获取 file_id
    """
    # 优先从内存缓存获取，缓存未命中则从数据库查找
    file_info = _uploaded_files_cache.get(request.file_id)
    if file_info is None:
        # 从数据库查找上传记录
        from sqlalchemy import select
        result = await db.execute(
            select(UploadedDocument).where(
                UploadedDocument.file_id == request.file_id,
                UploadedDocument.status != "deleted",
            )
        )
        doc_record = result.scalar_one_or_none()
        if doc_record is None:
            raise HTTPException(status_code=404, detail="文件不存在或已过期，请重新上传")

        # 从数据库记录还原 file_info
        extracted_text = doc_record.extracted_text
        if not extracted_text:
            # extracted_text 为空，尝试从磁盘重新提取
            if os.path.exists(doc_record.file_path):
                try:
                    extracted_text = extract_text_from_file(doc_record.file_path, doc_record.file_ext)
                except Exception as e:
                    logger.error(f"重新提取文本失败: {e}")
                    raise HTTPException(status_code=500, detail="文本提取失败，请重新上传")
            else:
                raise HTTPException(status_code=404, detail="文件已删除，请重新上传")

        file_info = {
            "filename": doc_record.filename,
            "file_path": doc_record.file_path,
            "file_ext": doc_record.file_ext,
            "file_size": doc_record.file_size,
            "text": extracted_text,
            "user_id": doc_record.user_id,
        }
        # 回填内存缓存，加速后续请求
        _uploaded_files_cache[request.file_id] = file_info
        logger.info(f"从数据库恢复文件信息: {doc_record.filename} (file_id={request.file_id})")

    # 游客限流
    if current_user is None:
        await check_guest_rate_limit(http_request)

    text = file_info["text"]
    filename = file_info["filename"]

    # 调用校对服务
    try:
        result = await proofread_text(
            text=text,
            check_types=request.check_types,
            domain=request.domain,
        )
    except RuntimeError as e:
        import traceback
        logger.error(f"文档校对服务异常: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="校对服务暂时不可用，请稍后重试",
        )
    except Exception as e:
        import traceback
        logger.error(f"文档校对未知错误: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="校对过程发生错误")

    # 生成修订文档
    corrected_url = None
    try:
        file_ext = file_info["file_ext"]
        file_path = file_info["file_path"]
        upload_dir = os.path.dirname(file_path)

        if file_ext == ".docx":
            corrected_filename = f"校对修订_{filename}"
            corrected_path = os.path.join(upload_dir, corrected_filename)
            generate_corrected_docx(file_path, result["issues"], corrected_path)
            corrected_url = f"/uploads/{request.file_id}/{corrected_filename}"

        elif file_ext == ".txt":
            corrected_filename = f"校对修订_{filename}"
            corrected_path = os.path.join(upload_dir, corrected_filename)
            generate_corrected_txt(text, result["issues"], corrected_path)
            corrected_url = f"/uploads/{request.file_id}/{corrected_filename}"

    except Exception as e:
        logger.warning(f"生成修订文档失败（不影响校对结果）: {e}")

    # 保存校对记录
    record_id = None
    if current_user:
        record = ProofreadRecord(
            user_id=current_user.id,
            type="document",
            original_text=text[:10000],
            check_types=json.dumps(request.check_types or []),
            domain=request.domain,
            result=result,
            total_issues=result["total_issues"],
            token_usage=result["usage"],
            source_filename=filename,
        )
        db.add(record)
        await db.flush()
        record_id = record.id

    logger.info(f"文档校对完成: {filename}, 问题数={result['total_issues']}")

    # 记录审计日志（文档校对）
    record_audit_log(
        http_request, "proofread_doc", user=current_user,
        input_text=text[:500],
        output_text=f"发现{result['total_issues']}个问题",
        extra_params={
            "action": "proofread",
            "check_types": request.check_types,
            "domain": request.domain,
            "total_issues": result["total_issues"],
        },
        file_id=request.file_id,
        file_name=filename,
        file_path=file_info.get("file_path"),
        file_size=file_info.get("file_size"),
        token_usage=result.get("usage"),
    )

    return DocumentProofreadResponse(
        file_id=request.file_id,
        filename=filename,
        issues=result["issues"],
        total_issues=result["total_issues"],
        chunks_count=result["chunks_count"],
        usage=result["usage"],
        domain=result["domain"],
        record_id=record_id,
        corrected_download_url=corrected_url,
    )


@router.post("/proofread/async")
async def document_proofread_async(
    request: DocumentProofreadRequest,
    http_request: Request,
    current_user=Depends(get_current_user_optional),
):
    """
    异步文档校对 - 提交 Celery 任务
    返回 task_id，前端轮询 /tasks/{task_id} 获取进度和结果
    """
    file_info = _uploaded_files_cache.get(request.file_id)
    if file_info is None:
        # 从数据库查找上传记录
        from sqlalchemy import select
        from app.core.database import get_db as _get_db
        async for db in _get_db():
            result = await db.execute(
                select(UploadedDocument).where(
                    UploadedDocument.file_id == request.file_id,
                    UploadedDocument.status != "deleted",
                )
            )
            doc_record = result.scalar_one_or_none()
            if doc_record is None:
                raise HTTPException(status_code=404, detail="文件不存在或已过期，请重新上传")

            extracted_text = doc_record.extracted_text
            if not extracted_text:
                if os.path.exists(doc_record.file_path):
                    try:
                        extracted_text = extract_text_from_file(doc_record.file_path, doc_record.file_ext)
                    except Exception as e:
                        logger.error(f"重新提取文本失败: {e}")
                        raise HTTPException(status_code=500, detail="文本提取失败，请重新上传")
                else:
                    raise HTTPException(status_code=404, detail="文件已从服务器删除，请重新上传")

            file_info = {
                "filename": doc_record.filename,
                "file_path": doc_record.file_path,
                "file_ext": doc_record.file_ext,
                "file_size": doc_record.file_size,
                "text": extracted_text,
                "user_id": doc_record.user_id,
            }
            _uploaded_files_cache[request.file_id] = file_info
            break

    # 游客限流
    if current_user is None:
        await check_guest_rate_limit(http_request)

    # 提交异步任务
    task = async_proofread_document.delay(
        text=file_info["text"],
        check_types=request.check_types,
        domain=request.domain,
        file_id=request.file_id,
        filename=file_info["filename"],
        file_path=file_info["file_path"],
        file_ext=file_info["file_ext"],
        user_id=current_user.id if current_user else None,
    )

    logger.info(f"异步校对任务已提交: task_id={task.id}, file={file_info['filename']}")

    return {
        "task_id": task.id,
        "message": "校对任务已提交，请通过 task_id 查询进度",
    }
