"""UC-06: knowledge_drafts + aggregate_alert_logs.

Revision ID: 0003_gzh_review
Revises: 0002_yxq_reports
Create Date: 2026-05-18 00:00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0003_gzh_review"
down_revision: str | Sequence[str] | None = "0002_yxq_reports"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    current_timestamp_default = sa.text("CURRENT_TIMESTAMP")

    op.create_table(
        "knowledge_drafts",
        sa.Column("entry_id", sa.BigInteger(), primary_key=True),
        sa.Column("report_id", sa.BigInteger(), nullable=False),
        sa.Column("fraud_type_id", sa.Integer(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="DRAFT"),
        sa.Column("desensitized_summary", sa.Text(), nullable=False),
        sa.Column("identification_points", sa.Text(), nullable=False),
        sa.Column("prevention_advice", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.ForeignKeyConstraint(
            ["report_id"],
            ["fraud_cases.case_id"],
            name="fk_knowledge_drafts_report_id_fraud_cases",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["fraud_type_id"],
            ["fraud_types.type_id"],
            name="fk_knowledge_drafts_fraud_type_id_fraud_types",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["author_id"],
            ["users.user_id"],
            name="fk_knowledge_drafts_author_id_users",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="知识库草稿表 UC-06/UC-08 适配",
    )
    op.create_index(
        "idx_knowledge_drafts_status_created",
        "knowledge_drafts",
        ["status", "created_at"],
    )
    op.create_index("idx_knowledge_drafts_report_id", "knowledge_drafts", ["report_id"])

    op.create_table(
        "aggregate_alert_logs",
        sa.Column("alert_log_id", sa.BigInteger(), primary_key=True),
        sa.Column("fraud_type_id", sa.Integer(), nullable=False),
        sa.Column("report_count", sa.Integer(), nullable=False),
        sa.Column("notified_admin_count", sa.Integer(), nullable=False),
        sa.Column("alerted_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.ForeignKeyConstraint(
            ["fraud_type_id"],
            ["fraud_types.type_id"],
            name="fk_aggregate_alert_logs_fraud_type_id_fraud_types",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="聚合告警触发日志表 UC-06 扩展",
    )
    op.create_index(
        "idx_aggregate_alert_type_time",
        "aggregate_alert_logs",
        ["fraud_type_id", "alerted_at"],
    )
    op.create_index("ix_aggregate_alert_logs_alerted_at", "aggregate_alert_logs", ["alerted_at"])


def downgrade() -> None:
    op.drop_index("ix_aggregate_alert_logs_alerted_at", table_name="aggregate_alert_logs")
    op.drop_index("idx_aggregate_alert_type_time", table_name="aggregate_alert_logs")
    op.drop_table("aggregate_alert_logs")

    op.drop_index("idx_knowledge_drafts_report_id", table_name="knowledge_drafts")
    op.drop_index("idx_knowledge_drafts_status_created", table_name="knowledge_drafts")
    op.drop_table("knowledge_drafts")
