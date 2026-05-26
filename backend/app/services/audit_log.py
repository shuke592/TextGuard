"""
TextGuard 审计日志写入服务
提供异步写入方法，不阻塞用户请求
"""
import re
import time
import asyncio
from typing import Optional

from fastapi import Request
from loguru import logger

from app.core.database import async_session_factory
from app.models.audit_log import AuditLog


def get_client_ip(request: Request) -> str:
    """
    从请求中提取客户端真实 IP
    优先级：X-Forwarded-For > X-Real-IP > request.client.host
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    if request.client:
        return request.client.host

    return "unknown"


def detect_device_type(user_agent: str) -> str:
    """
    从 User-Agent 字符串中判断设备类型
    返回: desktop / mobile / tablet
    """
    if not user_agent:
        return "unknown"

    ua_lower = user_agent.lower()

    # 平板优先判断（iPad / Android Tablet）
    if re.search(r"ipad|tablet|playbook|silk", ua_lower):
        return "tablet"

    # 手机判断
    if re.search(
        r"mobile|iphone|ipod|android.*mobile|windows phone|blackberry|opera mini|opera mobi",
        ua_lower,
    ):
        return "mobile"

    return "desktop"


async def _write_audit_log(log_data: dict):
    """
    内部方法：实际写入审计日志到数据库
    使用独立的数据库 session，不受外部事务影响
    """
    try:
        async with async_session_factory() as session:
            audit_log = AuditLog(**log_data)
            session.add(audit_log)
            await session.commit()
    except Exception as e:
        logger.error(f"审计日志写入失败: {e}")


def record_audit_log(
    request: Request,
    action_type: str,
    *,
    user=None,
    input_text: Optional[str] = None,
    output_text: Optional[str] = None,
    extra_params: Optional[dict] = None,
    file_id: Optional[str] = None,
    file_name: Optional[str] = None,
    file_path: Optional[str] = None,
    file_size: Optional[int] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    duration_ms: Optional[int] = None,
    token_usage: Optional[dict] = None,
):
    """
    记录审计日志（异步后台任务，不阻塞当前请求）

    :param request: FastAPI Request 对象
    :param action_type: 操作类型
    :param user: 当前用户对象（游客为 None）
    :param input_text: 用户输入文本
    :param output_text: AI 输出文本
    :param extra_params: 额外参数（风格、领域、校对类型等）
    :param file_id: 文档文件 ID
    :param file_name: 文档文件名
    :param file_path: 文档服务器路径
    :param file_size: 文档文件大小
    :param status: 操作状态
    :param error_message: 错误信息
    :param duration_ms: 操作耗时
    :param token_usage: Token 消耗
    """
    user_agent = request.headers.get("User-Agent", "")

    log_data = {
        "action_type": action_type,
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "employee_id": user.employee_id if user else None,
        "is_guest": user is None,
        "client_ip": get_client_ip(request),
        "user_agent": user_agent[:500] if user_agent else None,
        "device_type": detect_device_type(user_agent),
        "input_text": input_text,
        "input_length": len(input_text) if input_text else 0,
        "output_text": output_text,
        "output_length": len(output_text) if output_text else 0,
        "extra_params": extra_params,
        "file_id": file_id,
        "file_name": file_name,
        "file_path": file_path,
        "file_size": file_size,
        "status": status,
        "error_message": error_message,
        "duration_ms": duration_ms,
        "token_usage": token_usage,
    }

    # 异步写入，不阻塞当前请求
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_write_audit_log(log_data))
        else:
            loop.run_until_complete(_write_audit_log(log_data))
    except RuntimeError:
        # 无事件循环时的降级处理
        logger.warning("审计日志异步写入降级为同步日志记录")
        logger.info(f"[AUDIT] {action_type} | user={log_data.get('username')} | ip={log_data.get('client_ip')}")


def record_audit_log_sync(
    action_type: str,
    *,
    client_ip: str = "unknown",
    user_agent: str = "",
    user=None,
    employee_id_attempt: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    extra_params: Optional[dict] = None,
):
    """
    记录审计日志（无 Request 对象的场景，如登录失败只有工号）
    """
    log_data = {
        "action_type": action_type,
        "user_id": user.id if user else None,
        "username": user.username if user else None,
        "employee_id": (user.employee_id if user else None) or employee_id_attempt,
        "is_guest": user is None and employee_id_attempt is None,
        "client_ip": client_ip,
        "user_agent": user_agent[:500] if user_agent else None,
        "device_type": detect_device_type(user_agent),
        "input_text": None,
        "input_length": 0,
        "output_text": None,
        "output_length": 0,
        "extra_params": extra_params,
        "file_id": None,
        "file_name": None,
        "file_path": None,
        "file_size": None,
        "status": status,
        "error_message": error_message,
        "duration_ms": None,
        "token_usage": None,
    }

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(_write_audit_log(log_data))
        else:
            loop.run_until_complete(_write_audit_log(log_data))
    except RuntimeError:
        logger.info(f"[AUDIT] {action_type} | emp={employee_id_attempt} | ip={client_ip}")


class AuditTimer:
    """
    审计计时器上下文管理器
    用法:
        timer = AuditTimer()
        timer.start()
        ... 执行操作 ...
        duration = timer.elapsed_ms()
    """
    def __init__(self):
        self._start = None

    def start(self):
        self._start = time.perf_counter()

    def elapsed_ms(self) -> int:
        if self._start is None:
            return 0
        return int((time.perf_counter() - self._start) * 1000)
