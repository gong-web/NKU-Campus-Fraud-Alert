"""知识库草稿表。

为 UC-06 的“录入案例库”动作提供最小但可用的落地存储，后续知识库模块可直接复用。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class KnowledgeDraft(Base):
    """从审核通过案件生成的知识库草稿。"""

    __tablename__ = "knowledge_drafts"
    __table_args__ = (
        Index("idx_knowledge_drafts_status_created", "status", "created_at"),
        Index("idx_knowledge_drafts_report_id", "report_id"),
        {"comment": "知识库草稿表 UC-06/UC-08 适配"},
    )

    entry_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fraud_cases.case_id", ondelete="RESTRICT"),
        nullable=False,
    )
    fraud_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fraud_types.type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default="DRAFT",
        server_default="DRAFT",
        comment="草稿状态",
    )
    desensitized_summary: Mapped[str] = mapped_column(Text, nullable=False)
    identification_points: Mapped[str] = mapped_column(Text, nullable=False)
    prevention_advice: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
    )
