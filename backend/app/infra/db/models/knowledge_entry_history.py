"""知识库条目版本历史（PRD 5.20）。

每次条目状态机流转或内容更新均追加一行，保存当时整行 JSON 快照，提供条目
全生命周期回溯能力。

事件溯源语义：同一 ``version`` 上可叠加多条历史（如 v1 上先 CREATE 再
SUBMIT 再 REJECT），因此不对 ``(entry_id, version)`` 加唯一约束，仅在
``(entry_id, version)`` 上加普通索引以加速回溯查询。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class KnowledgeEntryHistoryAction:
    """版本历史动作常量（与 PRD UC-04 / UC-08 状态机配对）。"""

    CREATE = "CREATE"
    SUBMIT = "SUBMIT"
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    UPDATE = "UPDATE"
    OFFLINE = "OFFLINE"

    ALL: frozenset[str] = frozenset({CREATE, SUBMIT, APPROVE, REJECT, UPDATE, OFFLINE})


class KnowledgeEntryHistory(Base):
    """知识库条目版本快照。"""

    __tablename__ = "knowledge_entry_history"
    __table_args__ = (
        Index("idx_kb_history_entry_version", "entry_id", "version"),
        Index("idx_kb_history_entry_modified", "entry_id", "modified_at"),
        {"comment": "知识库条目版本历史 PRD UC-08"},
    )

    history_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="雪花算法生成"
    )
    entry_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_entries.entry_id", ondelete="CASCADE"),
        nullable=False,
        comment="所属条目 ID",
    )
    version: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="对应版本号"
    )
    content_snapshot: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment="变更时整行 JSON 快照"
    )
    modified_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="变更人 user_id",
    )
    action: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="动作 CREATE / SUBMIT / APPROVE / REJECT / UPDATE / OFFLINE",
    )
    modified_at: Mapped[datetime] = mapped_column(
        nullable=False,
        server_default=func.current_timestamp(),
        comment="变更时间",
    )

    def __repr__(self) -> str:
        return (
            f"<KnowledgeEntryHistory entry={self.entry_id} v{self.version} "
            f"{self.action}>"
        )
