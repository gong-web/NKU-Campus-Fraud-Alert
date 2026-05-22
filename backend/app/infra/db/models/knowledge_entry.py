"""知识库正式条目表（PRD 5.19，UC-04 / UC-08）。

与 :class:`KnowledgeDraft` 区分：草稿用于 UC-06 审核通过案件直接转入；本表
是正式条目，承载 DRAFT → PENDING → PUBLISHED → OFFLINE 状态机。状态机校
验、版本号自增由 :class:`KnowledgeService` 负责，模型层只描述持久化结构。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class KnowledgeEntryStatus:
    """知识库条目状态常量（PRD UC-04 / UC-08 状态机）。"""

    DRAFT = "DRAFT"          # 草稿
    PENDING = "PENDING"      # 待审核
    PUBLISHED = "PUBLISHED"  # 已发布
    OFFLINE = "OFFLINE"      # 已下线

    ALL: frozenset[str] = frozenset({DRAFT, PENDING, PUBLISHED, OFFLINE})

    # 合法流转映射：key → 可流转到的目标集合
    TRANSITIONS: dict[str | None, frozenset[str]] = {
        None: frozenset({DRAFT}),
        DRAFT: frozenset({PENDING, OFFLINE}),
        PENDING: frozenset({PUBLISHED, DRAFT, OFFLINE}),
        PUBLISHED: frozenset({OFFLINE}),
        OFFLINE: frozenset({DRAFT}),
    }


class KnowledgeEntrySourceType:
    """条目来源类型常量。"""

    CASE = "CASE"          # 来自校内案件
    SCHOOL = "SCHOOL"      # 校方公告
    NATIONAL = "NATIONAL"  # 国家反诈中心

    ALL: frozenset[str] = frozenset({CASE, SCHOOL, NATIONAL})


class KnowledgeEntry(Base, TimestampMixin):
    """知识库正式条目。"""

    __tablename__ = "knowledge_entries"
    __table_args__ = (
        Index(
            "idx_kb_entries_fraud_type_status",
            "fraud_type_id",
            "status",
            "published_at",
        ),
        Index("idx_kb_entries_status_published", "status", "published_at"),
        Index("idx_kb_entries_author", "author_id"),
        {"comment": "知识库正式条目表 PRD UC-04/UC-08"},
    )

    entry_id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, comment="雪花算法生成"
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, comment="条目标题")
    fraud_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fraud_types.type_id", ondelete="RESTRICT"),
        nullable=False,
        comment="所属诈骗类型",
    )
    desensitized_summary: Mapped[str] = mapped_column(
        Text, nullable=False, comment="脱敏案例摘要"
    )
    identification_points: Mapped[str] = mapped_column(
        Text, nullable=False, comment="识别要点"
    )
    prevention_advice: Mapped[str] = mapped_column(
        Text, nullable=False, comment="防范建议"
    )
    peak_periods: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="高发时间段"
    )
    source_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=KnowledgeEntrySourceType.CASE,
        server_default=KnowledgeEntrySourceType.CASE,
        comment="来源类型 CASE / SCHOOL / NATIONAL",
    )
    source_reference: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="来源引用说明"
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=KnowledgeEntryStatus.DRAFT,
        server_default=KnowledgeEntryStatus.DRAFT,
        comment="状态 DRAFT / PENDING / PUBLISHED / OFFLINE",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        comment="版本号（每次状态变更后由业务层 +1）",
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="作者 user_id",
    )
    reviewer_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=True,
        comment="审核人 user_id",
    )
    review_note: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="审核备注 / 驳回原因"
    )
    source_draft_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_drafts.entry_id", ondelete="RESTRICT"),
        nullable=True,
        comment="来源草稿 ID（来自 UC-06 转入，可空）",
    )
    published_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="首次发布时间"
    )
    offlined_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="下线时间"
    )

    def __repr__(self) -> str:
        return f"<KnowledgeEntry {self.entry_id} v{self.version} [{self.status}]>"
