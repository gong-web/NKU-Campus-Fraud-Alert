"""诈骗事件主表（UC-01 / UC-06）。

匿名上报时 reporter_id 置 NULL；真实身份存入 case_anonymous_reporters 表。
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class CaseStatus:
    """案件状态常量（PRD UC-06 状态机）。"""

    PENDING = "PENDING"      # 待审核
    REVIEWING = "REVIEWING"  # 审核中
    HANDLED = "HANDLED"      # 已处理
    REJECTED = "REJECTED"    # 已驳回
    REPORTED = "REPORTED"    # 已转报警

    ALL: frozenset[str] = frozenset({PENDING, REVIEWING, HANDLED, REJECTED, REPORTED})

    # 合法流转映射：key → 可流转到的目标集合（由 UC-06 状态机校验）
    TRANSITIONS: dict[str | None, frozenset[str]] = {
        None: frozenset({PENDING}),
        PENDING: frozenset({REVIEWING}),
        REVIEWING: frozenset({HANDLED, REJECTED, REPORTED}),
        HANDLED: frozenset(),
        REJECTED: frozenset(),
        REPORTED: frozenset(),
    }


class FraudCase(Base, TimestampMixin):
    """诈骗事件主表。"""

    __tablename__ = "fraud_cases"
    __table_args__ = (
        Index("idx_case_reporter_status", "reporter_id", "status"),
        Index("idx_case_status_created", "status", "created_at"),
        Index("idx_case_fraud_type", "fraud_type_id"),
        Index("idx_case_dept_code", "dept_code"),
        {"comment": "诈骗事件主表 PRD UC-01/06"},
    )

    case_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花算法生成")
    case_no: Mapped[str] = mapped_column(
        String(32), unique=True, nullable=False, index=True, comment="案件编号 YYYY-DEPT-NNNNNN"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    fraud_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fraud_types.type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    incident_date: Mapped[date] = mapped_column(Date, nullable=False, comment="事发日期")
    amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True, comment="涉案金额（元）"
    )
    fraud_method: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="诈骗手法简述"
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=CaseStatus.PENDING,
        server_default=CaseStatus.PENDING,
        comment="案件状态",
    )
    reporter_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=True,
        comment="上报人（匿名时为 NULL）",
    )
    is_anonymous: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    contact_way: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="上报人联系方式（可选）"
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    review_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    dept_code: Mapped[str] = mapped_column(
        String(8),
        nullable=False,
        default="UNKNOWN",
        server_default="UNKNOWN",
        comment="上报时上报人所在院系代码（冗余字段，用于案件编号与聚合统计）",
    )

    def __repr__(self) -> str:
        return f"<FraudCase {self.case_no} [{self.status}]>"
