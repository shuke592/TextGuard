"""
TextGuard 上传文档记录模型
记录用户上传的所有文档，供后台管理查询和下载
"""
from typing import Optional

from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class UploadedDocument(BaseModel):
    """上传文档记录表"""
    __tablename__ = "uploaded_documents"

    file_id: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True, comment="文件唯一标识(UUID)"
    )
    filename: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="原始文件名"
    )
    file_ext: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="文件扩展名(含点)"
    )
    file_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="文件大小(字节)"
    )
    file_path: Mapped[str] = mapped_column(
        String(1000), nullable=False, comment="文件在服务器上的存储路径"
    )
    text_length: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="提取的文本字数"
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True, comment="上传者用户ID(游客为null)"
    )
    username: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="上传者姓名(冗余存储便于查询)"
    )
    extracted_text: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="提取的文本内容(持久化存储，避免内存缓存丢失)"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="uploaded", comment="状态: uploaded/proofread/deleted"
    )

    def __repr__(self):
        return f"<UploadedDocument(id={self.id}, filename={self.filename}, file_id={self.file_id})>"
