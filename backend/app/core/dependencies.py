"""
TextGuard 全局依赖注入
提供数据库Session、Redis客户端、当前用户等通用依赖
"""
from typing import Optional

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import decode_token

# HTTP Bearer Token 提取器
security_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前登录用户（必须登录）
    从 Authorization Header 提取 Bearer Token 并解析用户信息
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token无效或已过期",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token类型无效",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token载荷无效",
        )

    # 延迟导入避免循环依赖
    from app.models.user import User

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前用户（可选，游客也可访问）
    未登录时返回 None
    """
    if credentials is None:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


def require_permission(permission_code: str):
    """
    权限校验依赖注入工厂
    用法：Depends(require_permission("proofread:export"))

    :param permission_code: 权限编码，如 "proofread:export"
    """
    async def _check_permission(
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
    ):
        # 延迟导入避免循环依赖
        from app.models.role import Role, RolePermission, Permission

        # 超级管理员拥有所有权限
        result = await db.execute(
            select(Role).where(Role.id == current_user.role_id)
        )
        role = result.scalar_one_or_none()
        if role and role.code == "super_admin":
            return current_user

        # 查询用户角色关联的权限
        result = await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == current_user.role_id)
        )
        user_permissions = {row[0] for row in result.fetchall()}

        if permission_code not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"无权执行此操作，需要权限：{permission_code}",
            )

        return current_user

    return _check_permission
