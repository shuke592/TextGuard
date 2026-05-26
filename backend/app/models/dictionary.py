"""
TextGuard 自定义词库与放行词模型
"""
from typing import Optional
from datetime import datetime

from sqlalchemy import String, Integer, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Dictionary(BaseModel):
    """用户自定义词库"""
    __tablename__ = "dictionaries"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="词库名称"
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="词库描述"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )
    entry_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="词条数量"
    )

    def __repr__(self):
        return f"<Dictionary(id={self.id}, name={self.name})>"


class DictionaryEntry(BaseModel):
    """词库词条"""
    __tablename__ = "dictionary_entries"

    dictionary_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dictionaries.id", ondelete="CASCADE"), nullable=False, comment="所属词库ID"
    )
    wrong_word: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="错误词"
    )
    correct_word: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="正确词"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )

    def __repr__(self):
        return f"<DictionaryEntry(id={self.id}, {self.wrong_word} -> {self.correct_word})>"


class WhitelistWord(BaseModel):
    """放行词（白名单）"""
    __tablename__ = "whitelist_words"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="所属用户ID"
    )
    word: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="放行词"
    )
    type: Mapped[str] = mapped_column(
        String(20), default="permanent", nullable=False, comment="类型: permanent/temporary"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="备注"
    )
    expire_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="过期时间(临时放行词)"
    )

    def __repr__(self):
        return f"<WhitelistWord(id={self.id}, word={self.word})>"
