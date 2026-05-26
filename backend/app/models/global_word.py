"""
TextGuard 全局词库模型
包含：全局敏感词/禁词、全局放行词、全局纠错词条
"""
from typing import Optional

from sqlalchemy import String, Integer, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class GlobalWord(BaseModel):
    """
    全局词库条目
    type 类型说明：
      - sensitive: 敏感词（校对时标记为敏感内容）
      - banned: 禁词（校对时标记为禁止使用）
      - whitelist: 全局放行词（校对时忽略该词的误报）
      - correction: 全局纠错词条（错误词 → 正确词）
    """
    __tablename__ = "global_words"

    word: Mapped[str] = mapped_column(
        String(200), nullable=False, index=True, comment="词条"
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True,
        comment="类型: sensitive/banned/whitelist/correction"
    )
    replacement: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True,
        comment="替换词（仅 correction 类型使用）"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="分类标签，如：政治、色情、暴力、广告等"
    )
    severity: Mapped[str] = mapped_column(
        String(10), default="error", nullable=False,
        comment="严重程度: error/warning/info"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )

    def __repr__(self):
        return f"<GlobalWord(id={self.id}, word={self.word}, type={self.type})>"
