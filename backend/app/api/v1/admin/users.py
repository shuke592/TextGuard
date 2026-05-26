"""
TextGuard 用户管理 API（管理后台）
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import require_permission
from app.core.security import hash_password
from app.models.user import User
from app.models.role import Role
from app.schemas.user import (
    UserCreateRequest,
    UserUpdateRequest,
    UserResponse,
)

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("")
async def list_users(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    keyword: Optional[str] = Query(None, description="搜索关键词(工号/姓名)"),
    role_id: Optional[int] = Query(None, description="角色ID筛选"),
    is_active: Optional[bool] = Query(None, description="状态筛选"),
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:users:view")),
):
    """获取用户列表（分页）"""
    query = select(User)

    # 条件筛选
    if keyword:
        query = query.where(
            (User.employee_id.ilike(f"%{keyword}%")) |
            (User.username.ilike(f"%{keyword}%"))
        )
    if role_id is not None:
        query = query.where(User.role_id == role_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)

    # 总数查询
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 分页查询（显式预加载 role 关系）
    query = query.options(selectinload(User.role))
    query = query.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    # 构建响应
    items = []
    for user in users:
        role_name = None
        if user.role:
            role_name = user.role.name
        items.append(UserResponse(
            id=user.id,
            employee_id=user.employee_id,
            username=user.username,
            phone=user.phone,
            gender=user.gender,
            avatar=user.avatar,
            department=user.department,
            role_id=user.role_id,
            role_name=role_name,
            is_active=user.is_active,
            daily_quota=user.daily_quota,
            remark=user.remark,
            created_at=user.created_at.isoformat() if user.created_at else None,
        ))

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    request: UserCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:users:create")),
):
    """创建用户"""
    # 检查工号是否重复
    existing = await db.execute(
        select(User).where(User.employee_id == request.employee_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"工号 '{request.employee_id}' 已存在",
        )

    # 验证角色是否存在
    role_result = await db.execute(select(Role).where(Role.id == request.role_id))
    role = role_result.scalar_one_or_none()
    if role is None:
        raise HTTPException(status_code=400, detail="指定的角色不存在")

    # 创建用户
    user = User(
        employee_id=request.employee_id,
        username=request.username,
        password_hash=hash_password(request.password),
        phone=request.phone,
        gender=request.gender,
        department=request.department,
        role_id=request.role_id,
        daily_quota=request.daily_quota,
        remark=request.remark,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    logger.info(f"创建用户: {user.employee_id} ({user.username})")

    return UserResponse(
        id=user.id,
        employee_id=user.employee_id,
        username=user.username,
        phone=user.phone,
        gender=user.gender,
        avatar=user.avatar,
        department=user.department,
        role_id=user.role_id,
        role_name=role.name,
        is_active=user.is_active,
        daily_quota=user.daily_quota,
        remark=user.remark,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UserUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:users:edit")),
):
    """更新用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()

    role_name = user.role.name if user.role else None

    logger.info(f"更新用户: {user.employee_id}")

    return UserResponse(
        id=user.id,
        employee_id=user.employee_id,
        username=user.username,
        phone=user.phone,
        gender=user.gender,
        avatar=user.avatar,
        department=user.department,
        role_id=user.role_id,
        role_name=role_name,
        is_active=user.is_active,
        daily_quota=user.daily_quota,
        remark=user.remark,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:users:delete")),
):
    """
    删除用户
    同时清理所有关联数据，确保不留下脏数据：
      - 审计日志、校对记录：user_id 置 NULL（保留历史日志）
      - 用户词库及词条、放行词：直接删除
    """
    import traceback
    from sqlalchemy import update as sql_update, delete as sql_delete
    from sqlalchemy.exc import IntegrityError, SQLAlchemyError
    from app.models.audit_log import AuditLog
    from app.models.proofread import ProofreadRecord
    from app.models.dictionary import Dictionary, DictionaryEntry, WhitelistWord
    from app.models.uploaded_document import UploadedDocument

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许删除超级管理员
    if user.role and user.role.code == "super_admin":
        raise HTTPException(status_code=403, detail="不能删除超级管理员账号")

    # 不允许删除自己
    if _user and getattr(_user, "id", None) == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录的账号")

    employee_id = user.employee_id

    try:
        # ---- 清理关联数据（顺序：先清外键，再删主体） ----
        # 1. 审计日志：user_id 置 NULL（保留日志记录）
        await db.execute(
            sql_update(AuditLog).where(AuditLog.user_id == user_id).values(user_id=None)
        )
        # 2. 校对记录：user_id 置 NULL（保留历史记录，便于统计）
        await db.execute(
            sql_update(ProofreadRecord).where(ProofreadRecord.user_id == user_id).values(user_id=None)
        )
        # 3. 用户词库：先删词条再删词库（dictionaries.user_id 为 NOT NULL，必须删除）
        dict_ids_result = await db.execute(
            select(Dictionary.id).where(Dictionary.user_id == user_id)
        )
        dict_ids = [row[0] for row in dict_ids_result.fetchall()]
        if dict_ids:
            await db.execute(
                sql_delete(DictionaryEntry).where(DictionaryEntry.dictionary_id.in_(dict_ids))
            )
            await db.execute(
                sql_delete(Dictionary).where(Dictionary.user_id == user_id)
            )
        # 4. 放行词：直接删除（whitelist_words.user_id 为 NOT NULL，必须删除）
        await db.execute(
            sql_delete(WhitelistWord).where(WhitelistWord.user_id == user_id)
        )
        # 5. 上传文档记录：user_id 置 NULL（保留文档记录）
        await db.execute(
            sql_update(UploadedDocument).where(UploadedDocument.user_id == user_id).values(user_id=None)
        )

        # 先 flush 关联清理结果，后续用原生 SQL 删除用户避免触发 ORM 关系自动加载
        await db.flush()

        # ---- 删除用户（用原生 DELETE，绕过 ORM 关系加载，避免意外副作用） ----
        await db.execute(sql_delete(User).where(User.id == user_id))
        await db.flush()

        logger.info(f"删除用户成功: id={user_id}, employee_id={employee_id}，已清理关联数据")
        return {"message": "删除成功"}

    except IntegrityError as e:
        await db.rollback()
        logger.error(f"删除用户失败(外键约束): id={user_id}, error={e.orig}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败：该用户存在未清理的关联数据 ({e.orig})",
        )
    except SQLAlchemyError as e:
        await db.rollback()
        logger.error(f"删除用户失败(数据库错误): id={user_id}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"数据库错误：{str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除用户失败(未知错误): id={user_id}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:users:edit")),
):
    """
    重置用户密码
    将用户密码重置为系统全局默认密码（管理员在系统设置中配置）
    """
    from app.core.config import settings

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 重置为系统默认密码
    user.password_hash = hash_password(settings.DEFAULT_USER_PASSWORD)
    db.add(user)
    await db.flush()

    logger.info(f"管理员重置用户密码: {user.employee_id}")
    return {"message": f"密码已重置为默认密码"}


@router.put("/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("admin:users:edit")),
):
    """
    停用/启用用户
    用于处理员工离职等场景，停用后用户无法登录
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 不允许停用超级管理员
    if user.role and user.role.code == "super_admin":
        raise HTTPException(status_code=403, detail="不能停用超级管理员账号")

    # 切换状态
    user.is_active = not user.is_active
    db.add(user)
    await db.flush()

    status_text = "启用" if user.is_active else "停用"
    logger.info(f"管理员{status_text}用户: {user.employee_id}")
    return {"message": f"用户已{status_text}", "is_active": user.is_active}
