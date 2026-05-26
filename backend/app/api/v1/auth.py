"""
TextGuard 认证 API
包含登录、获取当前用户信息、密码修改等接口
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.core.database import get_db
from app.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.dependencies import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.models.role import Role, RolePermission, Permission
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserInfoResponse,
    PasswordChangeRequest,
    RefreshTokenRequest,
    ProfileUpdateRequest,
    ProfileUpdateResponse,
)
from app.services.audit_log import record_audit_log_sync, get_client_ip

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request, db: AsyncSession = Depends(get_db)):
    """
    用户登录
    使用工号 + 密码进行认证，返回 JWT Token
    """
    # 查询用户
    result = await db.execute(
        select(User).where(User.employee_id == request.employee_id)
    )
    user = result.scalar_one_or_none()

    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")

    if user is None:
        record_audit_log_sync(
            "login_failed", client_ip=client_ip, user_agent=user_agent,
            employee_id_attempt=request.employee_id,
            status="failed", error_message="工号不存在",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="工号或密码错误",
        )

    # 校验密码
    if not verify_password(request.password, user.password_hash):
        record_audit_log_sync(
            "login_failed", client_ip=client_ip, user_agent=user_agent,
            user=user, status="failed", error_message="密码错误",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="工号或密码错误",
        )

    # 检查用户状态
    if not user.is_active:
        record_audit_log_sync(
            "login_failed", client_ip=client_ip, user_agent=user_agent,
            user=user, status="failed", error_message="账号已被禁用",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员",
        )

    # 生成 Token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    logger.info(f"用户登录成功: {user.employee_id} ({user.username})")

    # 记录登录成功审计日志
    record_audit_log_sync(
        "login_success", client_ip=client_ip, user_agent=user_agent, user=user,
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserInfoResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    获取当前登录用户信息
    包含角色名称和权限编码列表
    """
    # 获取角色信息
    role_name = None
    role_code = None
    permissions = []

    if current_user.role_id:
        result = await db.execute(
            select(Role).where(Role.id == current_user.role_id)
        )
        role = result.scalar_one_or_none()
        if role:
            role_name = role.name
            role_code = role.code

            # 超级管理员拥有所有权限
            if role.code == "super_admin":
                perm_result = await db.execute(select(Permission.code))
                permissions = [row[0] for row in perm_result.fetchall()]
            else:
                # 查询角色关联的权限
                perm_result = await db.execute(
                    select(Permission.code)
                    .join(RolePermission, RolePermission.permission_id == Permission.id)
                    .where(RolePermission.role_id == current_user.role_id)
                )
                permissions = [row[0] for row in perm_result.fetchall()]

    return UserInfoResponse(
        id=current_user.id,
        employee_id=current_user.employee_id,
        username=current_user.username,
        phone=current_user.phone,
        gender=current_user.gender,
        avatar=current_user.avatar,
        department=current_user.department,
        role_id=current_user.role_id,
        role_name=role_name,
        role_code=role_code,
        is_active=current_user.is_active,
        permissions=permissions,
    )


@router.put("/password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """修改密码"""
    # 校验旧密码
    if not verify_password(request.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误",
        )

    # 更新密码
    current_user.password_hash = hash_password(request.new_password)
    db.add(current_user)
    await db.flush()

    logger.info(f"用户修改密码: {current_user.employee_id}")
    return {"message": "密码修改成功"}


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """使用 Refresh Token 获取新的 Access Token"""
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.put("/profile", response_model=ProfileUpdateResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    修改个人信息
    支持修改姓名、手机号、性别
    """
    if request.username is not None:
        current_user.username = request.username
    if request.phone is not None:
        current_user.phone = request.phone
    if request.gender is not None:
        current_user.gender = request.gender
    if request.avatar is not None:
        current_user.avatar = request.avatar

    db.add(current_user)
    await db.flush()

    logger.info(f"用户修改个人信息: {current_user.employee_id}")
    return ProfileUpdateResponse(
        id=current_user.id,
        employee_id=current_user.employee_id,
        username=current_user.username,
        phone=current_user.phone,
        gender=current_user.gender,
        avatar=current_user.avatar,
        department=current_user.department,
        message="个人信息修改成功",
    )
