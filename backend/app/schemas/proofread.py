"""
TextGuard 校对相关 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class TextProofreadRequest(BaseModel):
    """文本校对请求"""
    text: str = Field(..., min_length=1, max_length=100000, description="待校对文本")
    check_types: Optional[List[str]] = Field(
        None,
        description="校对类型: typo/grammar/punctuation/style/sensitive/logic"
    )
    domain: str = Field(
        default="general",
        description="领域: general/official/legal/power/new_energy/meter"
    )


class ProofreadIssue(BaseModel):
    """单个校对问题"""
    original: str = Field(..., description="原文片段")
    type: str = Field(..., description="问题类型")
    suggestion: str = Field(..., description="修改建议")
    explanation: str = Field(default="", description="解释")
    severity: str = Field(default="warning", description="严重程度: error/warning/info")
    chunk_index: int = Field(default=0, description="分片序号")


class TextProofreadResponse(BaseModel):
    """文本校对响应"""
    issues: List[ProofreadIssue] = Field(default_factory=list, description="问题列表")
    total_issues: int = Field(default=0, description="问题总数")
    chunks_count: int = Field(default=1, description="分片数")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token用量")
    domain: str = Field(default="general", description="领域")
    check_types: List[str] = Field(default_factory=list, description="校对类型")
    record_id: Optional[int] = Field(None, description="校对记录ID")


class ProofreadRecordResponse(BaseModel):
    """校对历史记录响应"""
    id: int
    type: str
    original_text: str
    domain: str
    total_issues: int
    result: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}
