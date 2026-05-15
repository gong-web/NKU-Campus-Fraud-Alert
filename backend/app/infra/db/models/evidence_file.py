"""证据文件元数据表（UC-01）。

实际文件内容落盘前必须 AES-256-GCM 加密（见 storage_service）。
此表只存元数据 + 加密文件路径；不存明文内容。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class EvidenceFile(Base):
    """加密证据文件元数据。实际加密内容存于本地磁盘。"""

    __tablename__ = "evidence_files"
    __table_args__ = (
        Index("idx_evidence_case", "case_id"),
        Index("idx_evidence_draft", "draft_id"),
        {"comment": "证据文件表 PRD UC-01"},
    )

    file_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花算法生成")
    case_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("fraud_cases.case_id", ondelete="CASCADE"), nullable=True
    )
    draft_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("report_drafts.draft_id", ondelete="CASCADE"), nullable=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False, comment="原始文件字节数")
    mime_type: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_path: Mapped[str] = mapped_column(
        String(512), nullable=False, comment="加密后文件的本地存储路径（相对于 EVIDENCE_UPLOAD_DIR）"
    )
    file_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="原始内容 SHA-256 hex"
    )
    encryption_key_version: Mapped[str] = mapped_column(
        String(8), nullable=False, default="v1", comment="KMS 密钥版本"
    )
    uploaded_by: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    uploaded_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<EvidenceFile {self.file_id} {self.original_name}>"
