"""
TextGuard 词库与放行词 Schema
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


# ========== 词库 ==========
class DictionaryCreate(BaseModel):
    """创建词库"""
    name: str = Field(..., max_length=100, description="词库名称")
    description: Optional[str] = Field(None, max_length=500, description="词库描述")


class DictionaryUpdate(BaseModel):
    """更新词库"""
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class DictionaryResponse(BaseModel):
    """词库响应"""
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    entry_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ========== 词条 ==========
class EntryCreate(BaseModel):
    """创建词条"""
    wrong_word: str = Field(..., max_length=200, description="错误词")
    correct_word: str = Field(..., max_length=200, description="正确词")
    remark: Optional[str] = Field(None, max_length=500, description="备注")


class EntryBatchCreate(BaseModel):
    """批量创建词条"""
    entries: List[EntryCreate] = Field(..., description="词条列表")


class EntryResponse(BaseModel):
    """词条响应"""
    id: int
    dictionary_id: int
    wrong_word: str
    correct_word: str
    remark: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ========== 放行词 ==========
class WhitelistCreate(BaseModel):
    """创建放行词"""
    word: str = Field(..., max_length=200, description="放行词")
    type: str = Field(default="permanent", description="类型: permanent/temporary")
    remark: Optional[str] = Field(None, max_length=500, description="备注")
    expire_at: Optional[datetime] = Field(None, description="过期时间(临时放行)")


class WhitelistUpdate(BaseModel):
    """更新放行词"""
    word: Optional[str] = Field(None, max_length=200)
    type: Optional[str] = None
    remark: Optional[str] = Field(None, max_length=500)
    expire_at: Optional[datetime] = None


class WhitelistResponse(BaseModel):
    """放行词响应"""
    id: int
    word: str
    type: str
    remark: Optional[str] = None
    expire_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
