"""UC-03/04/07/08: warning_notices / warning_targets / knowledge_entries / knowledge_entry_history.

Revision ID: 0004_lht_warnings_kb
Revises: 0003_gzh_review
Create Date: 2026-06-01 00:00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0004_lht_warnings_kb"
down_revision: str | Sequence[str] | None = "0003_gzh_review"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    current_timestamp_default = sa.text("CURRENT_TIMESTAMP")

    # ── 1. 预警公告主表 (PRD 5.16, UC-03 / UC-07) ───────────────────
    op.create_table(
        "warning_notices",
        sa.Column("warning_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column("title", sa.String(128), nullable=False, comment="预警标题"),
        sa.Column("content", sa.Text(), nullable=False, comment="预警正文"),
        sa.Column(
            "warning_level",
            sa.SmallInteger(),
            nullable=False,
            comment="预警等级 1=提示 / 2=警告 / 3=紧急",
        ),
        sa.Column(
            "related_case_no",
            sa.String(32),
            nullable=True,
            comment="关联案件编号（可选）",
        ),
        sa.Column("publisher_id", sa.BigInteger(), nullable=False, comment="发布人 user_id"),
        sa.Column(
            "push_scope",
            sa.String(16),
            nullable=False,
            comment="推送范围 FULL_SCHOOL / DEPARTMENT",
        ),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="ONLINE",
            comment="状态 ONLINE / OFFLINE",
        ),
        sa.Column("appendix", sa.Text(), nullable=True, comment="追加后续说明（UC-07 步骤 8）"),
        sa.Column(
            "published_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
            comment="发布时间",
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=True, comment="过期时间（可选）"),
        sa.Column("offline_at", sa.DateTime(), nullable=True, comment="下线时间"),
        sa.Column("offline_reason", sa.String(255), nullable=True, comment="下线原因"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
            onupdate=current_timestamp_default,
        ),
        sa.ForeignKeyConstraint(
            ["publisher_id"],
            ["users.user_id"],
            name="fk_warning_notices_publisher_id_users",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="预警公告主表 PRD UC-03/UC-07",
    )
    op.create_index(
        "idx_warning_status_published",
        "warning_notices",
        ["status", sa.text("published_at DESC")],
    )
    op.create_index("idx_warning_level", "warning_notices", ["warning_level"])
    op.create_index("idx_warning_publisher", "warning_notices", ["publisher_id"])
    op.create_index("idx_warning_scope", "warning_notices", ["push_scope"])

    # ── 2. 预警推送目标 (PRD 5.17, push_scope=DEPARTMENT 时生效) ────
    op.create_table(
        "warning_targets",
        sa.Column("warning_id", sa.BigInteger(), nullable=False, comment="预警 ID"),
        sa.Column("dept_id", sa.BigInteger(), nullable=False, comment="目标院系 ID"),
        sa.Column(
            "added_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
        ),
        sa.PrimaryKeyConstraint("warning_id", "dept_id", name="pk_warning_targets"),
        sa.ForeignKeyConstraint(
            ["warning_id"],
            ["warning_notices.warning_id"],
            name="fk_warning_targets_warning_id_warning_notices",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["dept_id"],
            ["departments.dept_id"],
            name="fk_warning_targets_dept_id_departments",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="预警推送目标表（按院系） PRD UC-03",
    )
    op.create_index("idx_warning_targets_dept", "warning_targets", ["dept_id"])

    # ── 3. 知识库正式条目 (PRD 5.19, UC-04 / UC-08) ─────────────────
    op.create_table(
        "knowledge_entries",
        sa.Column("entry_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column("title", sa.String(128), nullable=False, comment="条目标题"),
        sa.Column("fraud_type_id", sa.Integer(), nullable=False, comment="所属诈骗类型"),
        sa.Column("desensitized_summary", sa.Text(), nullable=False, comment="脱敏案例摘要"),
        sa.Column("identification_points", sa.Text(), nullable=False, comment="识别要点"),
        sa.Column("prevention_advice", sa.Text(), nullable=False, comment="防范建议"),
        sa.Column("peak_periods", sa.String(255), nullable=True, comment="高发时间段"),
        sa.Column(
            "source_type",
            sa.String(16),
            nullable=False,
            server_default="CASE",
            comment="来源类型 CASE / SCHOOL / NATIONAL",
        ),
        sa.Column("source_reference", sa.String(255), nullable=True, comment="来源引用说明"),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="DRAFT",
            comment="状态 DRAFT / PENDING / PUBLISHED / OFFLINE",
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default="1",
            comment="版本号（每次状态变更后由业务层 +1）",
        ),
        sa.Column("author_id", sa.BigInteger(), nullable=False, comment="作者 user_id"),
        sa.Column("reviewer_id", sa.BigInteger(), nullable=True, comment="审核人 user_id"),
        sa.Column("review_note", sa.String(500), nullable=True, comment="审核备注 / 驳回原因"),
        sa.Column(
            "source_draft_id",
            sa.BigInteger(),
            nullable=True,
            comment="来源草稿 ID（来自 UC-06 转入，可空）",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
            onupdate=current_timestamp_default,
        ),
        sa.Column("published_at", sa.DateTime(), nullable=True, comment="首次发布时间"),
        sa.Column("offlined_at", sa.DateTime(), nullable=True, comment="下线时间"),
        sa.ForeignKeyConstraint(
            ["fraud_type_id"],
            ["fraud_types.type_id"],
            name="fk_knowledge_entries_fraud_type_id_fraud_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.user_id"],
            name="fk_knowledge_entries_author_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.user_id"],
            name="fk_knowledge_entries_reviewer_id_users",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["source_draft_id"],
            ["knowledge_drafts.entry_id"],
            name="fk_knowledge_entries_source_draft_id_knowledge_drafts",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="知识库正式条目表 PRD UC-04/UC-08",
    )
    op.create_index(
        "idx_kb_entries_fraud_type_status",
        "knowledge_entries",
        ["fraud_type_id", "status", sa.text("published_at DESC")],
    )
    op.create_index(
        "idx_kb_entries_status_published",
        "knowledge_entries",
        ["status", sa.text("published_at DESC")],
    )
    op.create_index("idx_kb_entries_author", "knowledge_entries", ["author_id"])

    # MySQL 8 FULLTEXT 索引 + ngram parser，覆盖标题 / 摘要 / 识别要点
    op.execute(
        "CREATE FULLTEXT INDEX ft_kb_entries_search "
        "ON knowledge_entries (title, desensitized_summary, identification_points) "
        "WITH PARSER ngram"
    )

    # ── 4. 知识库条目版本历史 (PRD 5.20) ────────────────────────────
    op.create_table(
        "knowledge_entry_history",
        sa.Column("history_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column("entry_id", sa.BigInteger(), nullable=False, comment="所属条目 ID"),
        sa.Column("version", sa.Integer(), nullable=False, comment="对应版本号"),
        sa.Column(
            "content_snapshot",
            sa.JSON(),
            nullable=False,
            comment="变更时整行 JSON 快照",
        ),
        sa.Column("modified_by", sa.BigInteger(), nullable=False, comment="变更人 user_id"),
        sa.Column(
            "action",
            sa.String(32),
            nullable=False,
            comment="动作 CREATE / SUBMIT / APPROVE / REJECT / UPDATE / OFFLINE",
        ),
        sa.Column(
            "modified_at",
            sa.DateTime(),
            nullable=False,
            server_default=current_timestamp_default,
        ),
        sa.ForeignKeyConstraint(
            ["entry_id"],
            ["knowledge_entries.entry_id"],
            name="fk_knowledge_entry_history_entry_id_knowledge_entries",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["modified_by"],
            ["users.user_id"],
            name="fk_knowledge_entry_history_modified_by_users",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="知识库条目版本历史 PRD UC-08",
    )
    op.create_index(
        "idx_kb_history_entry_version",
        "knowledge_entry_history",
        ["entry_id", "version"],
    )
    op.create_index(
        "idx_kb_history_entry_modified",
        "knowledge_entry_history",
        ["entry_id", sa.text("modified_at DESC")],
    )


def downgrade() -> None:
    # 严格逆序删除；依赖 ``op.drop_table`` 自动级联清理表内的索引、外键、唯
    # 一约束。MySQL InnoDB 不允许单独 ``DROP INDEX`` 掉为外键提供唯一覆盖
    # 的索引（如 ``idx_kb_entries_author``），故不预先 ``drop_index``。
    # FULLTEXT 索引同理随表一起 drop。
    op.drop_table("knowledge_entry_history")
    op.drop_table("knowledge_entries")
    op.drop_table("warning_targets")
    op.drop_table("warning_notices")
