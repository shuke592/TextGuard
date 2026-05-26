"""
TextGuard AI润色相关 Schema
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class PolishRequest(BaseModel):
    """AI润色请求"""
    text: str = Field(..., min_length=10, max_length=5000, description="待润色原文（10-5000字）")
    style: str = Field(
        default="formal",
        description="润色风格: formal/friendly/plain/concise/evidence/strategic/practical/firm/gentle/action"
    )


class PolishVersion(BaseModel):
    """单个润色版本"""
    label: str = Field(..., description="版本标签，如 轻量润色/标准润色/深度润色")
    level: str = Field(..., description="改动级别: light/standard/deep")
    content: str = Field(..., description="润色后正文")


class PolishResponse(BaseModel):
    """AI润色响应"""
    versions: List[PolishVersion] = Field(default_factory=list, description="三个润色版本")
    style: str = Field(default="formal", description="所选风格")
    style_name: str = Field(default="正式规范", description="风格中文名")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token用量")
