"""聚合告警触发日志（UC-06 扩展亮点）。"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class AggregateAlertLog(Base):
    """记录每次聚合告警触发结果，用于冷却控制与演示追溯。"""

    __tablename__ = "aggregate_alert_logs"
    __table_args__ = (
        Index("idx_aggregate_alert_type_time", "fraud_type_id", "alerted_at"),
        {"comment": "聚合告警触发日志表 UC-06 扩展"},
    )

    alert_log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    fraud_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fraud_types.type_id", ondelete="RESTRICT"),
        nullable=False,
    )
    report_count: Mapped[int] = mapped_column(Integer, nullable=False)
    notified_admin_count: Mapped[int] = mapped_column(Integer, nullable=False)
    alerted_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
