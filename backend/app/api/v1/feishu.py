"""
TextGuard 飞书认证 API
包含飞书扫码登录回调、SSO入口、配置获取等接口
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger
from pydantic import BaseModel, Field

from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, hash_password
from app.models.user import User
from app.services.feishu import feishu_service
from app.services.audit_log import record_audit_log_sync, get_client_ip

router = APIRouter(prefix="/auth/feishu", tags=["飞书认证"])


class FeishuCallbackRequest(BaseModel):
    """飞书授权回调请求"""
    code: str = Field(..., description="飞书临时授权码")


class FeishuCallbackResponse(BaseModel):
    """飞书登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    is_new_user: bool = Field(default=False, description="是否新创建的用户")


class FeishuConfigResponse(BaseModel):
    """飞书扫码配置响应"""
    app_id: str = Field(..., description="飞书应用ID")
    redirect_uri: str = Field(..., description="回调地址")
    enabled: bool = Field(..., description="是否启用飞书登录")


@router.get("/config", response_model=FeishuConfigResponse)
async def get_feishu_config():
    """
    获取飞书扫码登录配置
    前端用这些信息初始化飞书JS SDK扫码组件
    """
    config = feishu_service.get_login_config()
    return FeishuConfigResponse(**config)

@router.post("/callback", response_model=FeishuCallbackResponse)
async def feishu_callback(
    request: FeishuCallbackRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    飞书授权回调
    前端获取到飞书code后调用此接口完成登录
    流程：code → 飞书用户信息 → 匹配/创建本系统用户 → 返回JWT
    """
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")

    # 检查飞书功能是否启用
    if not settings.FEISHU_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="飞书登录功能未启用",
        )

    # Step 1: 用code换取飞书用户信息
    feishu_result = await feishu_service.login_with_code(request.code)
    if not feishu_result.get("success"):
        error_detail = feishu_result.get("error_detail", "未知错误")
        logger.error(f"[飞书登录] 授权失败: {error_detail}")
        record_audit_log_sync(
            "login_failed", client_ip=client_ip, user_agent=user_agent,
            status="failed", error_message=f"飞书授权失败: {error_detail}",
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"飞书授权失败: {error_detail}",
        )

    # 提取飞书用户信息（success=True时，用户信息字段在顶层）
    feishu_user_info = feishu_result
    open_id = feishu_user_info.get("open_id", "")
    union_id = feishu_user_info.get("union_id", "")
    user_id = feishu_user_info.get("user_id", "")
    name = feishu_user_info.get("name", "飞书用户")
    mobile = feishu_user_info.get("mobile", "")
    avatar_url = feishu_user_info.get("avatar_url", "")
    employee_no = feishu_user_info.get("employee_no", "")

    # 手机号去除国际区号前缀（+86）
    if mobile and mobile.startswith("+86"):
        mobile = mobile[3:]

    logger.info(
        f"[飞书登录] 提取到的用户信息: name={name}, mobile={mobile}, "
        f"employee_no='{employee_no}', open_id={open_id}, "
        f"union_id={union_id}, user_id={user_id}, avatar_url={bool(avatar_url)}"
    )

    # Step 2: 匹配已有用户
    user = None
    is_new_user = False

    # 优先用union_id匹配
    if union_id:
        result = await db.execute(
            select(User).where(User.feishu_union_id == union_id)
        )
        user = result.scalar_one_or_none()

    # 其次用open_id匹配
    if not user and open_id:
        result = await db.execute(
            select(User).where(User.feishu_open_id == open_id)
        )
        user = result.scalar_one_or_none()

    # 再次用手机号匹配
    if not user and mobile:
        result = await db.execute(
            select(User).where(User.phone == mobile)
        )
        user = result.scalar_one_or_none()

    # 最后用工号匹配
    if not user and employee_no:
        result = await db.execute(
            select(User).where(User.employee_id == employee_no)
        )
        user = result.scalar_one_or_none()

    # Step 3: 如果未匹配到，自动创建用户
    if not user:
        # 确定employee_id：优先用飞书工号，其次用完整手机号，最后用open_id前8位
        if employee_no:
            new_employee_id = employee_no
            id_source = "飞书工号(employee_no)"
        elif mobile:
            new_employee_id = mobile
            id_source = "手机号(mobile)"
        else:
            new_employee_id = open_id[:8] if open_id else union_id[:8]
            id_source = "open_id/union_id前8位"

        logger.info(
            f"[飞书登录] 新用户工号决策: employee_no='{employee_no}', mobile='{mobile}', "
            f"最终选择={new_employee_id} (来源: {id_source})"
        )

        # 检查employee_id是否已存在（极端情况），加随机后缀
        existing = await db.execute(
            select(User).where(User.employee_id == new_employee_id)
        )
        if existing.scalar_one_or_none():
            import random
            new_employee_id = f"{new_employee_id}_{random.randint(100, 999)}"
            logger.info(f"[飞书登录] 工号已存在，追加随机后缀: {new_employee_id}")

        # 获取默认角色ID（普通用户角色）
        from app.models.role import Role
        role_result = await db.execute(
            select(Role).where(Role.code == "user")
        )
        default_role = role_result.scalar_one_or_none()
        if not default_role:
            # 如果没有user角色，取第一个非admin角色
            role_result = await db.execute(
                select(Role).where(Role.code != "super_admin").limit(1)
            )
            default_role = role_result.scalar_one_or_none()

        if not default_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="系统角色配置异常，请联系管理员",
            )

        # 创建新用户
        user = User(
            employee_id=new_employee_id,
            username=name,
            password_hash=hash_password(settings.DEFAULT_USER_PASSWORD),
            phone=mobile or None,
            avatar=avatar_url or None,
            department=None,
            role_id=default_role.id,
            is_active=True,
            feishu_open_id=open_id or None,
            feishu_union_id=union_id or None,
            feishu_user_id=user_id or None,
            login_method="feishu",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        is_new_user = True
        logger.info(f"[飞书登录] 自动创建用户: employee_id={new_employee_id}, name={name}, id_source={id_source}")
    else:
        # 更新已有用户的飞书信息
        if open_id and not user.feishu_open_id:
            user.feishu_open_id = open_id
        if union_id and not user.feishu_union_id:
            user.feishu_union_id = union_id
        if user_id and not user.feishu_user_id:
            user.feishu_user_id = user_id
        # 更新头像（如果飞书有头像且本系统未设置）
        if avatar_url and not user.avatar:
            user.avatar = avatar_url
        # 更新手机号
        if mobile and not user.phone:
            user.phone = mobile

    # Step 4: 检查用户状态
    if not user.is_active:
        record_audit_log_sync(
            "login_failed", client_ip=client_ip, user_agent=user_agent,
            user=user, status="failed", error_message="账号已被停用（飞书登录）",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被停用，请联系管理员",
        )

    # Step 5: 更新登录信息（数据库字段为TIMESTAMP WITHOUT TIME ZONE，需写入无TZ的UTC时间）
    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.login_method = "feishu"
    db.add(user)
    await db.commit()

    # Step 6: 生成JWT Token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    logger.info(f"[飞书登录] 登录成功: {user.employee_id} ({user.username}), new_user={is_new_user}")

    # 记录审计日志
    record_audit_log_sync(
        "login_success", client_ip=client_ip, user_agent=user_agent, user=user,
    )

    return FeishuCallbackResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        is_new_user=is_new_user,
    )


@router.get("/sso")
async def feishu_sso(
    http_request: Request,
    code: str = None,
    db: AsyncSession = Depends(get_db),
):
    """
    飞书工作台SSO入口
    用户从飞书工作台点击应用时，飞书会带code跳转到此URL
    验证后重定向到前端，前端带token完成登录
    若无code参数（如手机直接访问），则重定向到登录页
    """
    client_ip = get_client_ip(http_request)
    user_agent = http_request.headers.get("User-Agent", "")

    # 前端登录页地址
    frontend_login = settings.FEISHU_REDIRECT_URI

    if not settings.FEISHU_ENABLED:
        return RedirectResponse(url=f"{frontend_login}?error=feishu_disabled")

    # 无code时主动跳转到飞书授权页面（飞书客户端内打开会自动免确认授权）
    if not code:
        import urllib.parse
        feishu_auth_url = (
            f"https://accounts.feishu.cn/open-apis/authen/v1/authorize"
            f"?client_id={settings.FEISHU_APP_ID}"
            f"&redirect_uri={urllib.parse.quote(frontend_login, safe='')}"
            f"&response_type=code"
            f"&state=feishu_sso"
        )
        logger.info(f"[飞书SSO] 无code，重定向到飞书授权页: ip={client_ip}")
        return RedirectResponse(url=feishu_auth_url)

    # 用code换取用户信息
    feishu_result = await feishu_service.login_with_code(code)
    if not feishu_result.get("success"):
        error_detail = feishu_result.get("error_detail", "未知错误")
        logger.warning(f"[飞书SSO] 授权失败: {error_detail}, ip={client_ip}")
        return RedirectResponse(url=f"{frontend_login}?error=feishu_auth_failed")

    # 提取信息
    feishu_user_info = feishu_result
    open_id = feishu_user_info.get("open_id", "")
    union_id = feishu_user_info.get("union_id", "")
    user_id = feishu_user_info.get("user_id", "")
    name = feishu_user_info.get("name", "飞书用户")
    mobile = feishu_user_info.get("mobile", "")
    avatar_url = feishu_user_info.get("avatar_url", "")
    employee_no = feishu_user_info.get("employee_no", "")

    if mobile and mobile.startswith("+86"):
        mobile = mobile[3:]

    logger.info(
        f"[飞书SSO] 提取到的用户信息: name={name}, mobile={mobile}, "
        f"employee_no='{employee_no}', open_id={open_id}, user_id={user_id}"
    )

    # 匹配用户（与callback逻辑相同）
    user = None

    if union_id:
        result = await db.execute(select(User).where(User.feishu_union_id == union_id))
        user = result.scalar_one_or_none()

    if not user and open_id:
        result = await db.execute(select(User).where(User.feishu_open_id == open_id))
        user = result.scalar_one_or_none()

    if not user and mobile:
        result = await db.execute(select(User).where(User.phone == mobile))
        user = result.scalar_one_or_none()

    if not user and employee_no:
        result = await db.execute(select(User).where(User.employee_id == employee_no))
        user = result.scalar_one_or_none()

    # 自动创建用户
    if not user:
        if employee_no:
            new_employee_id = employee_no
            id_source = "飞书工号(employee_no)"
        elif mobile:
            new_employee_id = mobile
            id_source = "手机号(mobile)"
        else:
            new_employee_id = open_id[:8] if open_id else union_id[:8]
            id_source = "open_id/union_id前8位"

        logger.info(
            f"[飞书SSO] 新用户工号决策: employee_no='{employee_no}', mobile='{mobile}', "
            f"最终选择={new_employee_id} (来源: {id_source})"
        )

        existing = await db.execute(select(User).where(User.employee_id == new_employee_id))
        if existing.scalar_one_or_none():
            import random
            new_employee_id = f"{new_employee_id}_{random.randint(100, 999)}"
            logger.info(f"[飞书SSO] 工号已存在，追加随机后缀: {new_employee_id}")

        from app.models.role import Role
        role_result = await db.execute(select(Role).where(Role.code == "user"))
        default_role = role_result.scalar_one_or_none()
        if not default_role:
            role_result = await db.execute(select(Role).where(Role.code != "super_admin").limit(1))
            default_role = role_result.scalar_one_or_none()

        if not default_role:
            return RedirectResponse(url=f"{frontend_login}?error=system_error")

        user = User(
            employee_id=new_employee_id,
            username=name,
            password_hash=hash_password(settings.DEFAULT_USER_PASSWORD),
            phone=mobile or None,
            avatar=avatar_url or None,
            role_id=default_role.id,
            is_active=True,
            feishu_open_id=open_id or None,
            feishu_union_id=union_id or None,
            feishu_user_id=user_id or None,
            login_method="feishu",
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        logger.info(f"[飞书SSO] 自动创建用户: employee_id={new_employee_id}, name={name}, id_source={id_source}")

    if not user.is_active:
        return RedirectResponse(url=f"{frontend_login}?error=account_disabled")

    # 更新飞书信息
    if open_id and not user.feishu_open_id:
        user.feishu_open_id = open_id
    if union_id and not user.feishu_union_id:
        user.feishu_union_id = union_id
    if user_id and not user.feishu_user_id:
        user.feishu_user_id = user_id
    if avatar_url and not user.avatar:
        user.avatar = avatar_url
    if mobile and not user.phone:
        user.phone = mobile

    user.last_login_at = datetime.now(timezone.utc).replace(tzinfo=None)
    user.login_method = "feishu"
    db.add(user)
    await db.commit()

    # 生成Token
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    record_audit_log_sync(
        "login_success", client_ip=client_ip, user_agent=user_agent, user=user,
    )

    # 重定向到前端，通过URL参数传递token
    redirect_url = f"{frontend_login}?feishu_token={access_token}&feishu_refresh={refresh_token}"
    return RedirectResponse(url=redirect_url)
