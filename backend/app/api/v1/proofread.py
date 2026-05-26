"""
TextGuard 文本校对 API
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.core.rate_limit import check_guest_rate_limit
from app.core.config import settings
from app.models.proofread import ProofreadRecord
from app.schemas.proofread import (
    TextProofreadRequest,
    TextProofreadResponse,
    ProofreadIssue,
)
from app.services.proofread import proofread_text
from app.services.audit_log import record_audit_log, AuditTimer

router = APIRouter(prefix="/proofread", tags=["校对"])


@router.post("/text", response_model=TextProofreadResponse)
async def text_proofread(
    request: TextProofreadRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    文本在线校对
    支持游客使用（受限流限制）和登录用户使用
    """
    # 游客限流检查
    if current_user is None:
        await check_guest_rate_limit(http_request)
        # 游客文本长度限制
        if len(request.text) > settings.GUEST_TEXT_MAX_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"游客模式文本长度不能超过{settings.GUEST_TEXT_MAX_LENGTH}字，请登录后使用",
            )

    timer = AuditTimer()
    timer.start()
    audit_extra = {"check_types": request.check_types, "domain": request.domain}

    try:
        # 调用校对服务
        result = await proofread_text(
            text=request.text,
            check_types=request.check_types,
            domain=request.domain,
        )
    except RuntimeError as e:
        import traceback
        logger.error(f"校对服务异常: {e}\n{traceback.format_exc()}")
        record_audit_log(
            http_request, "proofread_text", user=current_user,
            input_text=request.text, extra_params=audit_extra,
            status="failed", error_message=str(e), duration_ms=timer.elapsed_ms(),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="校对服务暂时不可用，请稍后重试",
        )
    except Exception as e:
        import traceback
        logger.error(f"校对过程发生未知错误: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        record_audit_log(
            http_request, "proofread_text", user=current_user,
            input_text=request.text, extra_params=audit_extra,
            status="failed", error_message=str(e), duration_ms=timer.elapsed_ms(),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="校对过程发生错误，请稍后重试",
        )

    # 保存校对记录（已登录用户）
    record_id = None
    if current_user:
        record = ProofreadRecord(
            user_id=current_user.id,
            type="text",
            original_text=request.text,
            check_types=json.dumps(request.check_types or []),
            domain=request.domain,
            result=result,
            total_issues=result["total_issues"],
            token_usage=result["usage"],
        )
        db.add(record)
        await db.flush()
        record_id = record.id

    # 构建响应
    issues = [
        ProofreadIssue(
            original=item.get("original", ""),
            type=item.get("type", "unknown"),
            suggestion=item.get("suggestion", ""),
            explanation=item.get("explanation", ""),
            severity=item.get("severity", "warning"),
            chunk_index=item.get("chunk_index", 0),
        )
        for item in result["issues"]
    ]

    # 记录审计日志（成功）
    output_summary = f"发现{result['total_issues']}个问题"
    record_audit_log(
        http_request, "proofread_text", user=current_user,
        input_text=request.text,
        output_text=output_summary,
        extra_params={**audit_extra, "total_issues": result["total_issues"]},
        token_usage=result.get("usage"),
        duration_ms=timer.elapsed_ms(),
    )

    return TextProofreadResponse(
        issues=issues,
        total_issues=result["total_issues"],
        chunks_count=result["chunks_count"],
        usage=result["usage"],
        domain=result["domain"],
        check_types=result["check_types"],
        record_id=record_id,
    )
