"""案件状态变更历史表（UC-06 状态机的事件溯源）。

由 UC-06 状态机（郭子涵）在每次 change_status() 事务中写入。
Person 2 在此创建表结构，Person 3 负责写入逻辑。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class CaseStatusHistory(Base):
    """案件每次状态流转的不可变记录。"""

    __tablename__ = "case_status_histories"
    __table_args__ = (
        Index("idx_case_status_hist_case", "case_id"),
        {"comment": "案件状态变更历史表 PRD UC-06"},
    )

    history_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花算法生成")
    case_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fraud_cases.case_id", ondelete="CASCADE"), nullable=False
    )
    from_status: Mapped[str | None] = mapped_column(
        String(16), nullable=True, comment="变更前状态（首次创建为 NULL）"
    )
    to_status: Mapped[str] = mapped_column(String(16), nullable=False, comment="变更后状态")
    operator_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True, comment="变更说明")
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<CaseStatusHistory case={self.case_id} {self.from_status}->{self.to_status}>"
