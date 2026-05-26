"""
TextGuard 角色权限管理 API（管理后台）
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from loguru import logger

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.models.role import Role, Permission, RolePermission
from app.schemas.role import (
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleResponse,
    RolePermissionAssignRequest,
    PermissionResponse,
)

router = APIRouter(prefix="/roles", tags=["角色权限管理"])


@router.get("", response_model=List[RoleResponse])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:roles:view")),
):
    """获取所有角色列表"""
    result = await db.execute(select(Role).order_by(Role.sort_order))
    roles = result.scalars().all()

    response = []
    for role in roles:
        # 获取角色关联的权限ID
        perm_result = await db.execute(
            select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
        )
        permission_ids = [row[0] for row in perm_result.fetchall()]

        response.append(RoleResponse(
            id=role.id,
            name=role.name,
            code=role.code,
            description=role.description,
            is_system=role.is_system,
            is_active=role.is_active,
            sort_order=role.sort_order,
            permission_ids=permission_ids,
        ))

    return response


@router.post("", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    request: RoleCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:roles:create")),
):
    """创建自定义角色"""
    # 检查编码是否重复
    existing = await db.execute(select(Role).where(Role.code == request.code))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"角色编码 '{request.code}' 已存在",
        )

    # 创建角色
    role = Role(
        name=request.name,
        code=request.code,
        description=request.description,
        is_system=False,
        is_active=True,
    )
    db.add(role)
    await db.flush()

    # 分配权限
    for perm_id in request.permission_ids:
        db.add(RolePermission(role_id=role.id, permission_id=perm_id))
    await db.flush()

    logger.info(f"创建角色: {role.code} ({role.name})")

    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        sort_order=role.sort_order,
        permission_ids=request.permission_ids,
    )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:roles:edit")),
):
    """更新角色信息"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system and role.code == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="超级管理员角色不可编辑",
        )

    # 更新字段
    if request.name is not None:
        role.name = request.name
    if request.description is not None:
        role.description = request.description
    if request.is_active is not None:
        role.is_active = request.is_active

    # 更新权限
    if request.permission_ids is not None:
        # 删除旧权限
        await db.execute(
            delete(RolePermission).where(RolePermission.role_id == role.id)
        )
        # 添加新权限
        for perm_id in request.permission_ids:
            db.add(RolePermission(role_id=role.id, permission_id=perm_id))

    await db.flush()

    # 返回更新后的权限ID列表
    perm_result = await db.execute(
        select(RolePermission.permission_id).where(RolePermission.role_id == role.id)
    )
    permission_ids = [row[0] for row in perm_result.fetchall()]

    logger.info(f"更新角色: {role.code}")

    return RoleResponse(
        id=role.id,
        name=role.name,
        code=role.code,
        description=role.description,
        is_system=role.is_system,
        is_active=role.is_active,
        sort_order=role.sort_order,
        permission_ids=permission_ids,
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:roles:delete")),
):
    """删除角色"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()

    if role is None:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="系统内置角色不可删除",
        )

    await db.delete(role)
    await db.flush()

    logger.info(f"删除角色: {role.code}")
    return {"message": "删除成功"}


@router.get("/permissions/tree", response_model=List[PermissionResponse])
async def get_permission_tree(
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:roles:view")),
):
    """获取权限树（树形结构）- 一次加载全部权限，Python 端构建树"""
    result = await db.execute(
        select(Permission).order_by(Permission.sort_order)
    )
    all_permissions = result.scalars().all()

    # 构建 id -> PermissionResponse 映射
    perm_map: dict[int, PermissionResponse] = {}
    for p in all_permissions:
        perm_map[p.id] = PermissionResponse(
            id=p.id, name=p.name, code=p.code, type=p.type,
            parent_id=p.parent_id, path=p.path, icon=p.icon,
            sort_order=p.sort_order, description=p.description,
            children=[],
        )

    # 组装树
    roots: list[PermissionResponse] = []
    for p in all_permissions:
        node = perm_map[p.id]
        if p.parent_id and p.parent_id in perm_map:
            perm_map[p.parent_id].children.append(node)
        else:
            roots.append(node)

    return roots
