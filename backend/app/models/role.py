"""
TextGuard 角色与权限模型
RBAC: Role-Based Access Control
支持菜单级（menu）和按钮级（button）权限控制
"""
from typing import Optional, List

from sqlalchemy import String, Integer, Boolean, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class Role(BaseModel):
    """角色表"""
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="角色名称"
    )
    code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True, comment="角色编码"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="角色描述"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否系统内置角色（不可删除）"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="是否启用"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序号"
    )

    # 关联关系
    users = relationship("User", back_populates="role", lazy="selectin")
    role_permissions = relationship(
        "RolePermission", back_populates="role", lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Role(id={self.id}, code={self.code}, name={self.name})>"


class Permission(BaseModel):
    """权限表"""
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="权限名称"
    )
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True, comment="权限编码"
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="权限类型：menu(菜单)/button(按钮)"
    )
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("permissions.id"), nullable=True, comment="父级权限ID"
    )
    path: Mapped[Optional[str]] = mapped_column(
        String(200), nullable=True, comment="前端路由路径（菜单类型适用）"
    )
    icon: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="菜单图标"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序号"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="权限描述"
    )

    # 自引用关联（树形结构）
    children = relationship(
        "Permission",
        back_populates="parent",
        lazy="selectin",
    )
    parent = relationship(
        "Permission",
        back_populates="children",
        remote_side="Permission.id",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Permission(id={self.id}, code={self.code}, type={self.type})>"


class RolePermission(BaseModel):
    """角色-权限关联表"""
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False, comment="角色ID"
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False, comment="权限ID"
    )

    # 关联关系
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", lazy="selectin")

    def __repr__(self):
        return f"<RolePermission(role_id={self.role_id}, permission_id={self.permission_id})>"
