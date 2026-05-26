"""
TextGuard 校对历史 Schema
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class HistoryListItem(BaseModel):
    """历史列表项"""
    id: int
    type: str
    domain: str
    total_issues: int
    text_preview: str
    source_filename: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class HistoryListResponse(BaseModel):
    """历史列表响应（分页）"""
    items: List[HistoryListItem]
    total: int
    page: int
    page_size: int


class HistoryDetailResponse(BaseModel):
    """历史详情响应"""
    id: int
    type: str
    domain: str
    original_text: str
    modified_text: Optional[str] = None
    check_types: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    total_issues: int
    source_filename: Optional[str] = None
    token_usage: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
