"""
TextGuard 管理后台 - 审计日志查询接口
管理员可查询所有用户（含游客）的操作审计日志
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit", tags=["管理后台-审计日志"])


@router.get("/logs")
async def list_audit_logs(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页条数"),
    action_type: Optional[str] = Query(None, description="操作类型"),
    user_type: Optional[str] = Query(None, description="用户类型: guest/registered"),
    keyword: Optional[str] = Query(None, description="关键词（用户名/工号/内容）"),
    ip: Optional[str] = Query(None, description="IP地址"),
    status: Optional[str] = Query(None, description="操作状态: success/failed"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:access")),
):
    """
    查询审计日志列表（分页 + 多条件筛选）
    """
    base_query = select(AuditLog)

    # 操作类型筛选
    if action_type:
        base_query = base_query.where(AuditLog.action_type == action_type)

    # 用户类型筛选
    if user_type == "guest":
        base_query = base_query.where(AuditLog.is_guest == True)
    elif user_type == "registered":
        base_query = base_query.where(AuditLog.is_guest == False)

    # IP 筛选
    if ip:
        base_query = base_query.where(AuditLog.client_ip.like(f"{ip}%"))

    # 操作状态
    if status:
        base_query = base_query.where(AuditLog.status == status)

    # 时间范围
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            base_query = base_query.where(AuditLog.created_at >= start_dt)
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            base_query = base_query.where(AuditLog.created_at <= end_dt)
        except ValueError:
            pass

    # 关键词搜索（用户名/工号/输入输出内容）
    if keyword:
        kw = f"%{keyword}%"
        base_query = base_query.where(
            or_(
                AuditLog.username.ilike(kw),
                AuditLog.employee_id.ilike(kw),
                AuditLog.input_text.ilike(kw),
                AuditLog.output_text.ilike(kw),
            )
        )

    # 统计总数
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询
    list_query = base_query.order_by(desc(AuditLog.created_at))
    list_query = list_query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(list_query)
    logs = result.scalars().all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "action_type": log.action_type,
            "user_id": log.user_id,
            "username": log.username,
            "employee_id": log.employee_id,
            "is_guest": log.is_guest,
            "client_ip": log.client_ip,
            "device_type": log.device_type,
            "input_preview": (log.input_text or "")[:80] + ("..." if log.input_text and len(log.input_text) > 80 else ""),
            "output_preview": (log.output_text or "")[:80] + ("..." if log.output_text and len(log.output_text) > 80 else ""),
            "file_name": log.file_name,
            "status": log.status,
            "duration_ms": log.duration_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/logs/{log_id}")
async def get_audit_log_detail(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:access")),
):
    """
    查看审计日志详情
    """
    result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
    log = result.scalar_one_or_none()

    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="日志记录不存在")

    return {
        "id": log.id,
        "action_type": log.action_type,
        "user_id": log.user_id,
        "username": log.username,
        "employee_id": log.employee_id,
        "is_guest": log.is_guest,
        "client_ip": log.client_ip,
        "user_agent": log.user_agent,
        "device_type": log.device_type,
        "input_text": log.input_text,
        "input_length": log.input_length,
        "output_text": log.output_text,
        "output_length": log.output_length,
        "extra_params": log.extra_params,
        "file_id": log.file_id,
        "file_name": log.file_name,
        "file_path": log.file_path,
        "file_size": log.file_size,
        "status": log.status,
        "error_message": log.error_message,
        "duration_ms": log.duration_ms,
        "token_usage": log.token_usage,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/stats")
async def get_audit_stats(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:access")),
):
    """
    获取审计日志统计概览
    """
    from datetime import date, timedelta
    today = date.today()

    # 今日操作总数
    today_count_result = await db.execute(
        select(func.count()).select_from(AuditLog)
        .where(func.date(AuditLog.created_at) == today)
    )
    today_count = today_count_result.scalar() or 0

    # 今日游客操作数
    guest_count_result = await db.execute(
        select(func.count()).select_from(AuditLog)
        .where(func.date(AuditLog.created_at) == today, AuditLog.is_guest == True)
    )
    guest_count = guest_count_result.scalar() or 0

    # 总操作数
    total_result = await db.execute(select(func.count()).select_from(AuditLog))
    total_count = total_result.scalar() or 0

    # 今日各操作类型分布
    type_dist_result = await db.execute(
        select(AuditLog.action_type, func.count().label("count"))
        .where(func.date(AuditLog.created_at) == today)
        .group_by(AuditLog.action_type)
    )
    type_distribution = {row[0]: row[1] for row in type_dist_result.fetchall()}

    # 今日失败操作数
    failed_count_result = await db.execute(
        select(func.count()).select_from(AuditLog)
        .where(func.date(AuditLog.created_at) == today, AuditLog.status == "failed")
    )
    failed_count = failed_count_result.scalar() or 0

    return {
        "today_count": today_count,
        "today_guest_count": guest_count,
        "today_failed_count": failed_count,
        "total_count": total_count,
        "type_distribution": type_distribution,
    }
