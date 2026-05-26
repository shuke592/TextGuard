"""
TextGuard 操作审计日志模型
记录所有用户（含游客）的核心操作：AI润色、文本校对、文档校对、登录/登出等
"""
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """操作审计日志表"""
    __tablename__ = "audit_logs"

    # ---- 操作类型 ----
    action_type: Mapped[str] = mapped_column(
        String(30), nullable=False, comment="操作类型: polish/proofread_text/proofread_doc/view_history/login_success/login_failed/logout"
    )

    # ---- 用户信息 ----
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="用户ID（游客为NULL）"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="用户名快照"
    )
    employee_id: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="工号快照"
    )
    is_guest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="是否游客"
    )

    # ---- 客户端信息 ----
    client_ip: Mapped[str] = mapped_column(
        String(45), nullable=False, default="", comment="客户端IP（支持IPv6）"
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="浏览器User-Agent"
    )
    device_type: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="设备类型: desktop/mobile/tablet"
    )

    # ---- 输入/输出内容 ----
    input_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="用户输入文本"
    )
    input_length: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="输入文本字符数"
    )
    output_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AI输出结果"
    )
    output_length: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="输出文本字符数"
    )

    # ---- 额外参数 ----
    extra_params: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="额外参数（润色风格、校对类型、领域等）"
    )

    # ---- 文件信息（文档校对） ----
    file_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="文档校对关联的文件ID"
    )
    file_name: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="源文件名"
    )
    file_path: Mapped[Optional[str]] = mapped_column(
        String(1000), nullable=True, comment="服务器文件存储路径"
    )
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="文件大小（字节）"
    )

    # ---- 操作结果 ----
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="success", comment="操作状态: success/failed/processing"
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="失败时的错误信息"
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="操作耗时（毫秒）"
    )
    token_usage: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="AI Token消耗量"
    )

    # ---- 索引 ----
    __table_args__ = (
        Index("ix_audit_action_type", "action_type"),
        Index("ix_audit_user_id", "user_id"),
        Index("ix_audit_client_ip", "client_ip"),
        Index("ix_audit_created_at", "created_at"),
        Index("ix_audit_status", "status"),
        Index("ix_audit_is_guest", "is_guest"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action_type}, user={self.username}, ip={self.client_ip})>"
