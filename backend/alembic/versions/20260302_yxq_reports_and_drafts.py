"""UC-01/02/06: fraud_types / report_drafts / fraud_cases / evidence_files / case_status_histories / case_anonymous_reporters.

Revision ID: 0002_yxq_reports
Revises: 0001_initial
Create Date: 2026-03-02 00:00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_yxq_reports"
down_revision: str | Sequence[str] | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    current_timestamp_default = sa.text("CURRENT_TIMESTAMP")

    # ── 1. 诈骗类型字典 ────────────────────────────────────────────
    op.create_table(
        "fraud_types",
        sa.Column("type_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("type_code", sa.String(32), nullable=False),
        sa.Column("type_name", sa.String(64), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.UniqueConstraint("type_code", name="uq_fraud_types_type_code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="诈骗类型字典表 PRD UC-01",
    )
    op.create_index("ix_fraud_types_type_code", "fraud_types", ["type_code"])

    # 预置 8 类诈骗类型
    op.bulk_insert(
        sa.table(
            "fraud_types",
            sa.column("type_code", sa.String),
            sa.column("type_name", sa.String),
            sa.column("sort_order", sa.Integer),
        ),
        [
            {"type_code": "BRUSH_REWARD", "type_name": "刷单返利类", "sort_order": 1},
            {"type_code": "FAKE_POLICE", "type_name": "冒充公检法类", "sort_order": 2},
            {"type_code": "FAKE_JOB", "type_name": "虚假兼职招聘类", "sort_order": 3},
            {"type_code": "DATING_FRAUD", "type_name": "恋爱交友诈骗类", "sort_order": 4},
            {"type_code": "FAKE_REFUND", "type_name": "冒充客服退款类", "sort_order": 5},
            {"type_code": "FAKE_LOAN", "type_name": "虚假网络贷款类", "sort_order": 6},
            {"type_code": "GAME_TRADE", "type_name": "游戏账号交易诈骗类", "sort_order": 7},
            {"type_code": "OTHER", "type_name": "其他类型", "sort_order": 8},
        ],
    )

    # ── 2. 上报草稿（先于 fraud_cases，因为 evidence_files 依赖二者） ──
    op.create_table(
        "report_drafts",
        sa.Column("draft_id", sa.BigInteger(), primary_key=True),
        sa.Column("student_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("fraud_type_id", sa.Integer(), nullable=True),
        sa.Column("incident_date", sa.Date(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("fraud_method", sa.String(200), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("contact_way", sa.String(200), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default,
                  onupdate=current_timestamp_default),
        sa.ForeignKeyConstraint(["student_id"], ["users.user_id"], ondelete="CASCADE",
                                name="fk_report_drafts_student_id_users"),
        sa.ForeignKeyConstraint(["fraud_type_id"], ["fraud_types.type_id"], ondelete="SET NULL",
                                name="fk_report_drafts_fraud_type_id_fraud_types"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="上报草稿表 PRD UC-01",
    )
    op.create_index("ix_report_drafts_student_id", "report_drafts", ["student_id"])
    op.create_index("ix_report_drafts_expires_at", "report_drafts", ["expires_at"])

    # ── 3. 诈骗事件主表 ────────────────────────────────────────────
    op.create_table(
        "fraud_cases",
        sa.Column("case_id", sa.BigInteger(), primary_key=True),
        sa.Column("case_no", sa.String(32), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("fraud_type_id", sa.Integer(), nullable=False),
        sa.Column("incident_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("fraud_method", sa.String(200), nullable=True),
        sa.Column("status", sa.String(16), nullable=False, server_default="PENDING"),
        sa.Column("reporter_id", sa.BigInteger(), nullable=True),
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("contact_way", sa.String(200), nullable=True),
        sa.Column("reviewer_id", sa.BigInteger(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("review_note", sa.String(500), nullable=True),
        sa.Column("dept_code", sa.String(8), nullable=False, server_default="UNKNOWN"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default,
                  onupdate=current_timestamp_default),
        sa.UniqueConstraint("case_no", name="uq_fraud_cases_case_no"),
        sa.ForeignKeyConstraint(["fraud_type_id"], ["fraud_types.type_id"], ondelete="RESTRICT",
                                name="fk_fraud_cases_fraud_type_id_fraud_types"),
        sa.ForeignKeyConstraint(["reporter_id"], ["users.user_id"], ondelete="RESTRICT",
                                name="fk_fraud_cases_reporter_id_users"),
        sa.ForeignKeyConstraint(["reviewer_id"], ["users.user_id"], ondelete="RESTRICT",
                                name="fk_fraud_cases_reviewer_id_users"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="诈骗事件主表 PRD UC-01/06",
    )
    op.create_index("ix_fraud_cases_case_no", "fraud_cases", ["case_no"])
    op.create_index("ix_fraud_cases_reporter_status", "fraud_cases", ["reporter_id", "status"])
    op.create_index("ix_fraud_cases_status_created", "fraud_cases", ["status", "created_at"])
    op.create_index("ix_fraud_cases_fraud_type_id", "fraud_cases", ["fraud_type_id"])
    op.create_index("ix_fraud_cases_dept_code", "fraud_cases", ["dept_code"])

    # ── 4. 证据文件 ───────────────────────────────────────────────
    op.create_table(
        "evidence_files",
        sa.Column("file_id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.BigInteger(), nullable=True),
        sa.Column("draft_id", sa.BigInteger(), nullable=True),
        sa.Column("original_name", sa.String(255), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("encryption_key_version", sa.String(8), nullable=False, server_default="v1"),
        sa.Column("uploaded_by", sa.BigInteger(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.ForeignKeyConstraint(["case_id"], ["fraud_cases.case_id"], ondelete="CASCADE",
                                name="fk_evidence_files_case_id_fraud_cases"),
        sa.ForeignKeyConstraint(["draft_id"], ["report_drafts.draft_id"], ondelete="CASCADE",
                                name="fk_evidence_files_draft_id_report_drafts"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.user_id"], ondelete="RESTRICT",
                                name="fk_evidence_files_uploaded_by_users"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="证据文件表 PRD UC-01",
    )
    op.create_index("ix_evidence_files_case_id", "evidence_files", ["case_id"])
    op.create_index("ix_evidence_files_draft_id", "evidence_files", ["draft_id"])

    # ── 5. 案件状态变更历史 ───────────────────────────────────────
    op.create_table(
        "case_status_histories",
        sa.Column("history_id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("from_status", sa.String(16), nullable=True),
        sa.Column("to_status", sa.String(16), nullable=False),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.ForeignKeyConstraint(["case_id"], ["fraud_cases.case_id"], ondelete="CASCADE",
                                name="fk_case_status_histories_case_id_fraud_cases"),
        sa.ForeignKeyConstraint(["operator_id"], ["users.user_id"], ondelete="RESTRICT",
                                name="fk_case_status_histories_operator_id_users"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="案件状态变更历史表 PRD UC-06",
    )
    op.create_index("ix_case_status_histories_case_id", "case_status_histories", ["case_id"])

    # ── 6. 案件匿名上报者映射 ─────────────────────────────────────
    op.create_table(
        "case_anonymous_reporters",
        sa.Column("mapping_id", sa.BigInteger(), primary_key=True),
        sa.Column("case_id", sa.BigInteger(), nullable=False),
        sa.Column("reporter_user_id_enc", sa.LargeBinary(128), nullable=False),
        sa.Column("encryption_key_version", sa.String(8), nullable=False, server_default="v1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=current_timestamp_default),
        sa.UniqueConstraint("case_id", name="uq_case_anonymous_reporters_case_id"),
        sa.ForeignKeyConstraint(["case_id"], ["fraud_cases.case_id"], ondelete="CASCADE",
                                name="fk_case_anonymous_reporters_case_id_fraud_cases"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        comment="案件匿名上报者映射表 PRD UC-01/UC-10",
    )
    op.create_index("ix_case_anonymous_reporters_case_id", "case_anonymous_reporters", ["case_id"])


def downgrade() -> None:
    op.drop_table("case_anonymous_reporters")
    op.drop_table("case_status_histories")
    op.drop_table("evidence_files")
    op.drop_table("fraud_cases")
    op.drop_table("report_drafts")
    op.drop_table("fraud_types")
