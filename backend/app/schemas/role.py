"""
TextGuard 角色与权限相关 Schema
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class PermissionResponse(BaseModel):
    """权限信息响应"""
    id: int
    name: str
    code: str
    type: str
    parent_id: Optional[int] = None
    path: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    description: Optional[str] = None
    children: List["PermissionResponse"] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RoleCreateRequest(BaseModel):
    """创建角色请求"""
    name: str = Field(..., min_length=1, max_length=100, description="角色名称")
    code: str = Field(..., min_length=1, max_length=50, description="角色编码")
    description: Optional[str] = Field(None, description="角色描述")
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")


class RoleUpdateRequest(BaseModel):
    """更新角色请求"""
    name: Optional[str] = Field(None, max_length=100, description="角色名称")
    description: Optional[str] = Field(None, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否启用")
    permission_ids: Optional[List[int]] = Field(None, description="权限ID列表")


class RoleResponse(BaseModel):
    """角色信息响应"""
    id: int
    name: str
    code: str
    description: Optional[str] = None
    is_system: bool
    is_active: bool
    sort_order: int = 0
    permission_ids: List[int] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class RolePermissionAssignRequest(BaseModel):
    """角色权限分配请求"""
    permission_ids: List[int] = Field(..., description="权限ID列表")
