"""
TextGuard 用户相关 Schema
"""
from typing import Optional
from pydantic import BaseModel, Field


class UserCreateRequest(BaseModel):
    """创建用户请求（管理员使用）"""
    employee_id: str = Field(..., min_length=1, max_length=50, description="工号")
    username: str = Field(..., min_length=1, max_length=100, description="姓名")
    password: str = Field(..., min_length=6, description="初始密码")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    gender: Optional[str] = Field(None, description="性别：male/female/unknown")
    department: Optional[str] = Field(None, max_length=200, description="部门")
    role_id: int = Field(..., description="角色ID")
    daily_quota: Optional[int] = Field(None, description="每日校对配额")
    remark: Optional[str] = Field(None, description="备注")


class UserUpdateRequest(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, max_length=100, description="姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    gender: Optional[str] = Field(None, description="性别")
    department: Optional[str] = Field(None, max_length=200, description="部门")
    role_id: Optional[int] = Field(None, description="角色ID")
    is_active: Optional[bool] = Field(None, description="是否启用")
    daily_quota: Optional[int] = Field(None, description="每日校对配额")
    remark: Optional[str] = Field(None, description="备注")


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    employee_id: str
    username: str
    phone: Optional[str] = None
    gender: Optional[str] = None
    avatar: Optional[str] = None
    department: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None
    is_active: bool
    daily_quota: Optional[int] = None
    remark: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}
