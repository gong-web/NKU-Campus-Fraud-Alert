"""预警推送目标表（PRD 5.17）。

仅当 :class:`WarningNotice.push_scope` = ``DEPARTMENT`` 时按院系列出。复合主键
``(warning_id, dept_id)`` 保证同一预警对同一院系不重复。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class WarningTarget(Base):
    """预警推送目标（按院系）。"""

    __tablename__ = "warning_targets"
    __table_args__ = (
        Index("idx_warning_targets_dept", "dept_id"),
        {"comment": "预警推送目标表（按院系） PRD UC-03"},
    )

    warning_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("warning_notices.warning_id", ondelete="CASCADE"),
        primary_key=True,
        comment="预警 ID",
    )
    dept_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("departments.dept_id", ondelete="RESTRICT"),
        primary_key=True,
        comment="目标院系 ID",
    )
    added_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        comment="加入推送名单时间",
    )

    def __repr__(self) -> str:
        return f"<WarningTarget warning={self.warning_id} dept={self.dept_id}>"
