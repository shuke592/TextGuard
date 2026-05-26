"""
TextGuard 异步任务状态查询 API
"""
from fastapi import APIRouter, Depends, HTTPException
from celery.result import AsyncResult
from loguru import logger

from app.celery_app import celery_app
from app.core.dependencies import get_current_user_optional

router = APIRouter(prefix="/tasks", tags=["异步任务"])


@router.get("/{task_id}")
async def get_task_status(
    task_id: str,
    current_user=Depends(get_current_user_optional),
):
    """
    查询异步任务状态
    返回任务当前状态、进度和结果
    """
    result = AsyncResult(task_id, app=celery_app)

    response = {
        "task_id": task_id,
        "status": result.state,
    }

    if result.state == "PENDING":
        response["progress"] = 0
        response["message"] = "任务排队中..."
    elif result.state == "PROGRESS":
        meta = result.info or {}
        response["progress"] = meta.get("progress", 0)
        response["message"] = meta.get("message", "处理中...")
        response["step"] = meta.get("step", "")
    elif result.state == "SUCCESS":
        response["progress"] = 100
        response["message"] = "校对完成"
        response["result"] = result.result
    elif result.state == "FAILURE":
        response["progress"] = 0
        response["message"] = f"任务失败: {str(result.info)}"
        response["error"] = str(result.info)
    else:
        response["progress"] = 5
        response["message"] = f"状态: {result.state}"

    return response
