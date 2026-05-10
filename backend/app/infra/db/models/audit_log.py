"""审计日志表（PRD 5.3.5 表 5.27）。

铁律
----
- 数据库账号 ``app_user`` 仅有 ``INSERT / SELECT`` 权限；``UPDATE / DELETE`` 在
  数据库层就被拒绝（见 ``infra/docker/mysql/init/02_grants.sql``）。
- 通过 :class:`PARTITION BY RANGE` 按月分区（迁移脚本里实现）。
- 链式哈希字段 ``prev_hash`` / ``this_hash``：可由
  ``scripts/verify_audit_chain.py`` 离线校验任何篡改。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class AuditLog(Base):
    """所有敏感操作的不可篡改留痕。"""

    __tablename__ = "audit_logs"
    __table_args__ = (
        # PRD 5.6.2 索引：(operator_id, operated_at) 与 (object_type, object_id, operated_at)
        Index("idx_audit_op_time", "operator_id", "operated_at"),
        Index("idx_audit_object", "object_type", "object_id", "operated_at"),
        Index("idx_audit_op_type_time", "operation_type", "operated_at"),
        Index("idx_audit_trace_id", "trace_id"),
        {"comment": "审计日志表（不可变） - PRD 5.3.5 表 5.27"},
    )

    log_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花 ID")
    operator_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
    )
    operation_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="如 LOGIN / VIEW_EVIDENCE / DECRYPT_ANONYMOUS",
    )
    object_type: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="操作对象类型（user / report / warning ...）"
    )
    object_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="操作对象标识（雪花 ID 或 case_no）"
    )
    before_state: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="变更前状态快照（MySQL 8 原生 JSON）"
    )
    after_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    source_ip: Mapped[str] = mapped_column(String(45), nullable=False)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    trace_id: Mapped[str | None] = mapped_column(
        String(64), nullable=True, comment="请求 trace_id，便于跨日志对照"
    )

    # 链式哈希（PRD 5.5 可选增强）
    prev_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="上一条日志的 this_hash（首条为 NULL）",
    )
    this_hash: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        comment="当前日志的 SHA-256（hex），由 SDK 计算",
    )

    # NOTE: 模型层用 ``current_timestamp()`` 通用形式（SQLite/MySQL 兼容）；
    # MySQL 方言下迁移脚本会把 default 替换为 ``CURRENT_TIMESTAMP(6)`` 取毫秒精度
    operated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp(), comment="操作时间"
    )
