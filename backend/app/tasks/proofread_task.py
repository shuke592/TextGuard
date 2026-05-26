"""
TextGuard 异步文档校对任务
通过 Celery 在后台执行耗时的大模型调用
"""
import os
import json
import asyncio
from loguru import logger

from app.celery_app import celery_app
from app.core.config import settings


def _run_async(coro):
    """在同步 Celery worker 中运行异步协程"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@celery_app.task(bind=True, name="proofread.async_document")
def async_proofread_document(
    self,
    text: str,
    check_types: list = None,
    domain: str = "general",
    file_id: str = None,
    filename: str = None,
    file_path: str = None,
    file_ext: str = None,
    user_id: int = None,
):
    """
    异步执行文档校对任务
    
    :param text: 提取的文本内容
    :param check_types: 校对类型
    :param domain: 领域
    :param file_id: 文件ID
    :param filename: 原始文件名
    :param file_path: 文件路径
    :param file_ext: 文件扩展名
    :param user_id: 用户ID
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] 开始异步校对: file={filename}, text_len={len(text)}")

    # 更新进度
    self.update_state(state="PROGRESS", meta={"step": "proofread", "progress": 10, "message": "正在调用AI模型校对..."})

    try:
        # 调用校对服务（异步转同步）
        from app.services.proofread import proofread_text
        result = _run_async(proofread_text(text=text, check_types=check_types, domain=domain))
    except Exception as e:
        logger.error(f"[Task {task_id}] 校对失败: {e}")
        self.update_state(state="FAILURE", meta={"error": str(e)})
        raise

    self.update_state(state="PROGRESS", meta={"step": "generate", "progress": 80, "message": "正在生成修订文档..."})

    # 生成修订文档
    corrected_url = None
    try:
        if file_path and file_ext:
            from app.services.document import generate_corrected_docx, generate_corrected_txt
            upload_dir = os.path.dirname(file_path)

            if file_ext == ".docx":
                corrected_filename = f"校对修订_{filename}"
                corrected_path = os.path.join(upload_dir, corrected_filename)
                generate_corrected_docx(file_path, result["issues"], corrected_path)
                corrected_url = f"/uploads/{file_id}/{corrected_filename}"
            elif file_ext == ".txt":
                corrected_filename = f"校对修订_{filename}"
                corrected_path = os.path.join(upload_dir, corrected_filename)
                generate_corrected_txt(text, result["issues"], corrected_path)
                corrected_url = f"/uploads/{file_id}/{corrected_filename}"
    except Exception as e:
        logger.warning(f"[Task {task_id}] 生成修订文档失败: {e}")

    self.update_state(state="PROGRESS", meta={"step": "save", "progress": 95, "message": "正在保存记录..."})

    # 保存校对记录到数据库
    record_id = None
    if user_id:
        try:
            from sqlalchemy import create_engine
            from sqlalchemy.orm import Session
            from app.models.proofread import ProofreadRecord

            sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg", "postgresql+psycopg2")
            sync_engine = create_engine(sync_url)
            with Session(sync_engine) as session:
                record = ProofreadRecord(
                    user_id=user_id,
                    type="document",
                    original_text=text[:10000],
                    check_types=json.dumps(check_types or []),
                    domain=domain,
                    result=result,
                    total_issues=result["total_issues"],
                    token_usage=result["usage"],
                    source_filename=filename,
                )
                session.add(record)
                session.commit()
                record_id = record.id
            sync_engine.dispose()
        except Exception as e:
            logger.warning(f"[Task {task_id}] 保存记录失败: {e}")

    logger.info(f"[Task {task_id}] 异步校对完成: issues={result['total_issues']}")

    return {
        "file_id": file_id,
        "filename": filename,
        "issues": result["issues"],
        "total_issues": result["total_issues"],
        "chunks_count": result["chunks_count"],
        "usage": result["usage"],
        "domain": result["domain"],
        "record_id": record_id,
        "corrected_download_url": corrected_url,
    }
