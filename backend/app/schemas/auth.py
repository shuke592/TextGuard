"""
TextGuard 认证相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求"""
    employee_id: str = Field(..., description="工号")
    password: str = Field(..., description="密码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class UserInfoResponse(BaseModel):
    """当前用户信息响应"""
    id: int
    employee_id: str
    username: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None
    department: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    role_code: Optional[str] = None
    is_active: bool
    permissions: List[str] = Field(default_factory=list, description="权限编码列表")

    model_config = {"from_attributes": True}


class PasswordChangeRequest(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(..., description="刷新令牌")


class ProfileUpdateRequest(BaseModel):
    """个人信息修改请求"""
    username: Optional[str] = Field(None, min_length=1, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    gender: Optional[str] = Field(None, description="性别：male/female/unknown")
    avatar: Optional[str] = Field(None, max_length=500, description="头像URL")


class ProfileUpdateResponse(BaseModel):
    """个人信息修改响应"""
    id: int
    employee_id: str
    username: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None
    department: Optional[str] = None
    message: str = "修改成功"

    model_config = {"from_attributes": True}
