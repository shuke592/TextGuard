"""
TextGuard AI润色 API
"""
import json
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import get_current_user_optional
from app.core.rate_limit import check_guest_rate_limit
from app.core.config import settings
from app.schemas.polish import PolishRequest, PolishResponse, PolishVersion
from app.services.polish import polish_text, POLISH_STYLES
from app.services.audit_log import record_audit_log, AuditTimer
from app.models.proofread import ProofreadRecord

router = APIRouter(prefix="/polish", tags=["AI润色"])


@router.get("/styles")
async def get_polish_styles():
    """
    获取所有可用的润色风格列表
    """
    styles = []
    for key, val in POLISH_STYLES.items():
        styles.append({
            "key": key,
            "name": val["name"],
            "description": val["description"],
        })
    return {"styles": styles}


@router.post("/text", response_model=PolishResponse)
async def text_polish(
    request: PolishRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user_optional),
):
    """
    AI文本润色
    用户选择润色风格 → 输入原文 → AI输出3段不同变体
    支持游客使用（受限流限制）和登录用户使用
    """
    # 游客限流检查
    if current_user is None:
        await check_guest_rate_limit(http_request)

    # 校验风格参数
    if request.style not in POLISH_STYLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"不支持的润色风格: {request.style}，可选: {', '.join(POLISH_STYLES.keys())}",
        )

    timer = AuditTimer()
    timer.start()

    try:
        result = await polish_text(
            text=request.text,
            style=request.style,
        )
    except RuntimeError as e:
        import traceback
        logger.error(f"润色服务异常: {e}\n{traceback.format_exc()}")
        record_audit_log(
            http_request, "polish", user=current_user,
            input_text=request.text,
            extra_params={"style": request.style},
            status="failed", error_message=str(e),
            duration_ms=timer.elapsed_ms(),
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="润色服务暂时不可用，请稍后重试",
        )
    except Exception as e:
        import traceback
        logger.error(f"润色过程发生未知错误: {type(e).__name__}: {e}\n{traceback.format_exc()}")
        record_audit_log(
            http_request, "polish", user=current_user,
            input_text=request.text,
            extra_params={"style": request.style},
            status="failed", error_message=str(e),
            duration_ms=timer.elapsed_ms(),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="润色过程发生错误，请稍后重试",
        )

    # 构建响应
    versions = [
        PolishVersion(
            label=v["label"],
            level=v["level"],
            content=v["content"],
        )
        for v in result["versions"]
    ]

    # 保存润色记录（已登录用户）
    if current_user:
        modified_text = "\n\n---\n\n".join(
            f"【{v['label']}】\n{v['content']}" for v in result["versions"]
        )
        record = ProofreadRecord(
            user_id=current_user.id,
            type="polish",
            original_text=request.text,
            check_types=json.dumps([request.style]),
            domain=request.style,
            result={"versions": result["versions"], "style": result["style"], "style_name": result["style_name"]},
            modified_text=modified_text,
            total_issues=0,
            token_usage=result.get("usage"),
        )
        db.add(record)
        await db.flush()

    # 记录审计日志（成功）
    output_summary = "\n---\n".join(
        f"【{v['label']}】{v['content'][:200]}" for v in result["versions"]
    )
    style_info = POLISH_STYLES.get(request.style, {})
    record_audit_log(
        http_request, "polish", user=current_user,
        input_text=request.text,
        output_text=output_summary,
        extra_params={"style": request.style, "style_name": style_info.get("name", "")},
        token_usage=result.get("usage"),
        duration_ms=timer.elapsed_ms(),
    )

    return PolishResponse(
        versions=versions,
        style=result["style"],
        style_name=result["style_name"],
        usage=result["usage"],
    )
