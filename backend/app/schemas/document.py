"""
TextGuard 文档校对相关 Schema
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    file_id: str = Field(..., description="文件唯一标识")
    filename: str = Field(..., description="原始文件名")
    file_size: int = Field(..., description="文件大小(字节)")
    file_ext: str = Field(..., description="文件扩展名")
    text_length: int = Field(..., description="提取的文本字数")
    text_preview: str = Field(default="", description="文本预览(前200字)")
    extracted_text: str = Field(default="", description="提取的完整文本")
    extracted_html: str = Field(default="", description="格式化HTML（保留原始排版样式）")


class DocumentProofreadRequest(BaseModel):
    """文档校对请求"""
    file_id: str = Field(..., description="文件唯一标识")
    check_types: Optional[List[str]] = Field(
        None,
        description="校对类型"
    )
    domain: str = Field(default="general", description="领域")


class DocumentProofreadResponse(BaseModel):
    """文档校对响应"""
    file_id: str
    filename: str
    issues: List[Dict[str, Any]] = Field(default_factory=list)
    total_issues: int = 0
    chunks_count: int = 1
    usage: Dict[str, int] = Field(default_factory=dict)
    domain: str = "general"
    record_id: Optional[int] = None
    corrected_download_url: Optional[str] = None
