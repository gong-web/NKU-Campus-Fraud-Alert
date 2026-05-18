"""上报草稿表（UC-01）。

30 天后由 tasks/draft_cleanup 定时任务清理。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class ReportDraft(Base, TimestampMixin):
    """上报草稿。所有字段均可选，支持随时保存未完成的上报。"""

    __tablename__ = "report_drafts"
    __table_args__ = (
        Index("idx_draft_student", "student_id"),
        Index("idx_draft_expires", "expires_at"),
        {"comment": "上报草稿表 PRD UC-01"},
    )

    draft_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花算法生成")
    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fraud_type_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("fraud_types.type_id", ondelete="SET NULL"), nullable=True
    )
    incident_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    fraud_method: Mapped[str | None] = mapped_column(String(200), nullable=True)
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    contact_way: Mapped[str | None] = mapped_column(String(200), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False, comment="30 天后由定时任务清理")

    def __repr__(self) -> str:
        return f"<ReportDraft {self.draft_id} by student={self.student_id}>"
