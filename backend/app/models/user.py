"""
TextGuard 用户模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class User(BaseModel):
    """用户表"""
    __tablename__ = "users"

    employee_id: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="工号"
    )
    username: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="姓名"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="手机号"
    )
    gender: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="性别：male/female/unknown"
    )
    avatar: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="头像URL"
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="部门"
    )
    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id"), nullable=False, comment="角色ID"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )
    daily_quota: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, default=None, comment="每日校对配额(null=不限)"
    )
    remark: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="备注"
    )

    # 飞书关联字段
    feishu_open_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="飞书应用内用户ID"
    )
    feishu_union_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, unique=True, index=True, comment="飞书企业内唯一ID"
    )
    feishu_user_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="飞书用户ID"
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, comment="最后登录时间"
    )
    login_method: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, default="password", comment="最近登录方式：password/feishu"
    )

    # 关联关系
    role = relationship("Role", back_populates="users", lazy="selectin")

    def __repr__(self):
        return f"<User(id={self.id}, employee_id={self.employee_id}, username={self.username})>"
