"""
TextGuard 全局词库 Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class GlobalWordCreate(BaseModel):
    """创建全局词条"""
    word: str = Field(..., max_length=200, description="词条")
    type: str = Field(..., description="类型: sensitive/banned/whitelist/correction")
    replacement: Optional[str] = Field(None, max_length=200, description="替换词（correction类型）")
    category: Optional[str] = Field(None, max_length=50, description="分类标签")
    severity: str = Field(default="error", description="严重程度: error/warning/info")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class GlobalWordUpdate(BaseModel):
    """更新全局词条"""
    word: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = None
    replacement: Optional[str] = Field(None, max_length=200)
    category: Optional[str] = Field(None, max_length=50)
    severity: Optional[str] = None
    remark: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class GlobalWordResponse(BaseModel):
    """全局词条响应"""
    id: int
    word: str
    type: str
    replacement: Optional[str] = None
    category: Optional[str] = None
    severity: str
    remark: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class GlobalWordBatchCreate(BaseModel):
    """批量创建全局词条"""
    entries: List[GlobalWordCreate] = Field(..., description="词条列表")


class GlobalWordStats(BaseModel):
    """全局词库统计"""
    total: int = 0
    sensitive_count: int = 0
    banned_count: int = 0
    whitelist_count: int = 0
    correction_count: int = 0
