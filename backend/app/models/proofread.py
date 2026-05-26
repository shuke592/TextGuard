"""
TextGuard 校对记录模型
"""
from typing import Optional

from sqlalchemy import String, Integer, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class ProofreadRecord(BaseModel):
    """校对记录表"""
    __tablename__ = "proofread_records"

    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="用户ID(游客为null)"
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="text", comment="记录类型: text/document/polish"
    )
    original_text: Mapped[str] = mapped_column(
        Text, nullable=False, comment="原始文本"
    )
    check_types: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="校对类型列表(JSON)"
    )
    domain: Mapped[str] = mapped_column(
        String(50), nullable=False, default="general", comment="领域"
    )
    result: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="校对结果(JSON)"
    )
    modified_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="修改后的文本"
    )
    total_issues: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="问题总数"
    )
    token_usage: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True, comment="Token用量(JSON)"
    )
    source_filename: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="源文件名(文档校对)"
    )

    def __repr__(self):
        return f"<ProofreadRecord(id={self.id}, type={self.type}, issues={self.total_issues})>"
