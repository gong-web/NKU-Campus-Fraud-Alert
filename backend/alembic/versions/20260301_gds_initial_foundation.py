"""initial foundation: users / departments / roles / permissions / role_permissions / sessions / audit_logs / notifications / system_configs / anonymous_mappings / anonymous_decrypt_logs.

Revision ID: 0001_initial
Revises:
Create Date: 2026-03-01 00:00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001_initial"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    current_timestamp_default = sa.text("CURRENT_TIMESTAMP")

    # ── 院系 ─────────────────────────────────────────────────────
    op.create_table(
        "departments",
        sa.Column("dept_id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("dept_code", sa.String(16), nullable=False),
        sa.Column("dept_name", sa.String(64), nullable=False),
        sa.Column("parent_dept_id", sa.BigInteger(), nullable=True),
        sa.Column("dept_level", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("dept_code", name="uq_departments_dept_code"),
        sa.ForeignKeyConstraint(
            ["parent_dept_id"],
            ["departments.dept_id"],
            name="fk_departments_parent_dept_id_departments",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="院系表 - PRD 5.3.1 表 5.6",
    )

    # ── 角色 ─────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("role_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("role_code", sa.String(32), nullable=False),
        sa.Column("role_name", sa.String(64), nullable=False),
        sa.Column("role_level", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.UniqueConstraint(
            "role_code", "role_level", name="uq_roles_role_code_role_level"
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="角色表 - PRD 5.3.1 表 5.7",
    )

    # ── 权限 ─────────────────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("permission_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("permission_code", sa.String(64), nullable=False),
        sa.Column("permission_name", sa.String(64), nullable=False),
        sa.Column("resource_type", sa.String(32), nullable=False),
        sa.Column("action_type", sa.String(16), nullable=False),
        sa.Column("description", sa.String(255), nullable=True),
        sa.UniqueConstraint("permission_code", name="uq_permissions_permission_code"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="权限表 - PRD 5.3.1 表 5.8",
    )

    # ── 用户 ─────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("user_id", sa.BigInteger(), primary_key=True),
        sa.Column("cas_account", sa.String(32), nullable=False),
        sa.Column("real_name", sa.String(64), nullable=False),
        sa.Column("department_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("email_encrypted", sa.VARBINARY(255), nullable=True),
        sa.Column("phone_encrypted", sa.VARBINARY(96), nullable=True),
        sa.Column("avatar_url", sa.String(255), nullable=True),
        sa.Column("status", sa.SmallInteger(), nullable=False, server_default="1"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("last_login_ip", sa.String(45), nullable=True),
        sa.UniqueConstraint("cas_account", name="uq_users_cas_account"),
        sa.ForeignKeyConstraint(
            ["department_id"], ["departments.dept_id"],
            name="fk_users_department_id_departments", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.role_id"],
            name="fk_users_role_id_roles", ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="用户表 - PRD 5.3.1 表 5.5",
    )
    op.create_index("idx_user_dept_role", "users", ["department_id", "role_id"])
    op.create_index("idx_user_status", "users", ["status"])

    # ── 角色权限关联 ─────────────────────────────────────────────
    op.create_table(
        "role_permissions",
        sa.Column("role_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.Column(
            "granted_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("granted_by", sa.BigInteger(), nullable=True),
        sa.PrimaryKeyConstraint("role_id", "permission_id", name="pk_role_permissions"),
        sa.ForeignKeyConstraint(
            ["role_id"], ["roles.role_id"],
            name="fk_role_permissions_role_id_roles", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], ["permissions.permission_id"],
            name="fk_role_permissions_permission_id_permissions", ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"], ["users.user_id"],
            name="fk_role_permissions_granted_by_users", ondelete="SET NULL",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="角色权限关联表 - PRD 5.3.1 表 5.9",
    )

    # ── 会话 ─────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("cas_ticket", sa.String(128), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.Column(
            "last_active_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("source_ip", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("is_revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.user_id"],
            name="fk_sessions_user_id_users", ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="会话表 - PRD 5.3.5 表 5.28",
    )
    op.create_index("idx_session_user_id", "sessions", ["user_id"])
    op.create_index("idx_session_expires_at", "sessions", ["expires_at"])

    # ── 审计日志 ─────────────────────────────────────────────────
    # PRD 5.6.3 三层归档（热 3 月 / 温 3 年 / 冷归档）的"按月分区"由后续
    # 迁移引入：MySQL 的 PARTITION BY RANGE 要求分区列在 PK 内，会把 PK
    # 从单列 log_id 变成复合 (log_id, operated_at)，与 ORM 单列 PK 不一致。
    # 对于 5 年累计 ≤ 1000 万行的预期规模，单表 + 索引完全够用；待月度
    # 数据量超过 5M 行再做分区拆分。届时新增一个迁移即可。
    op.create_table(
        "audit_logs",
        sa.Column("log_id", sa.BigInteger(), primary_key=True),
        sa.Column("operator_id", sa.BigInteger(), nullable=False),
        sa.Column("operation_type", sa.String(64), nullable=False),
        sa.Column("object_type", sa.String(32), nullable=False),
        sa.Column("object_id", sa.String(64), nullable=False),
        sa.Column("before_state", sa.JSON(), nullable=True),
        sa.Column("after_state", sa.JSON(), nullable=True),
        sa.Column("source_ip", sa.String(45), nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("trace_id", sa.String(64), nullable=True),
        sa.Column("prev_hash", sa.String(64), nullable=True),
        sa.Column("this_hash", sa.String(64), nullable=True),
        sa.Column(
            "operated_at",
            sa.DateTime(timezone=False),
            nullable=False,
            server_default=current_timestamp_default,
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="审计日志表（不可变） - PRD 5.3.5 表 5.27",
    )
    op.create_index("idx_audit_op_time", "audit_logs", ["operator_id", "operated_at"])
    op.create_index("idx_audit_object", "audit_logs", ["object_type", "object_id", "operated_at"])
    op.create_index("idx_audit_op_type_time", "audit_logs", ["operation_type", "operated_at"])
    op.create_index("idx_audit_trace_id", "audit_logs", ["trace_id"])

    # ── 通知 ─────────────────────────────────────────────────────
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.BigInteger(), primary_key=True),
        sa.Column("recipient_id", sa.BigInteger(), nullable=False),
        sa.Column("type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(128), nullable=False),
        sa.Column("content", sa.String(512), nullable=False),
        sa.Column("related_object_type", sa.String(32), nullable=True),
        sa.Column("related_object_id", sa.BigInteger(), nullable=True),
        sa.Column("is_read", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["recipient_id"], ["users.user_id"],
            name="fk_notifications_recipient_id_users", ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="站内通知表 - PRD 5.3.5 表 5.26",
    )
    op.create_index(
        "idx_notif_user_read_time", "notifications", ["recipient_id", "is_read", "created_at"]
    )
    op.create_index("idx_notif_type", "notifications", ["type"])

    # ── 系统参数 ─────────────────────────────────────────────────
    op.create_table(
        "system_configs",
        sa.Column("config_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("config_key", sa.String(64), nullable=False),
        sa.Column("config_value", sa.Text(), nullable=False),
        sa.Column(
            "value_type", sa.String(16), nullable=False, server_default="STRING"
        ),
        sa.Column("is_sensitive", sa.SmallInteger(), nullable=False, server_default="0"),
        sa.Column("description", sa.String(255), nullable=True),
        sa.Column("updated_by", sa.BigInteger(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.current_timestamp(),
            onupdate=sa.func.current_timestamp(),
        ),
        sa.UniqueConstraint("config_key", name="uq_system_configs_config_key"),
        sa.ForeignKeyConstraint(
            ["updated_by"], ["users.user_id"],
            name="fk_system_configs_updated_by_users", ondelete="SET NULL",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="系统参数表 - PRD 5.3.5 表 5.29",
    )

    # ── 匿名映射 ─────────────────────────────────────────────────
    op.create_table(
        "anonymous_mappings",
        sa.Column("mapping_id", sa.BigInteger(), primary_key=True),
        sa.Column("report_id", sa.BigInteger(), nullable=False),
        sa.Column("encrypted_reporter_id", sa.VARBINARY(128), nullable=False),
        sa.Column("encryption_key_version", sa.String(32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.UniqueConstraint("report_id", name="uq_anonymous_mappings_report_id"),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="匿名映射表（独立 DB 账号访问） - PRD 5.3.2 表 5.14",
    )

    # ── 匿名解密授权日志 ─────────────────────────────────────────
    op.create_table(
        "anonymous_decrypt_logs",
        sa.Column("decrypt_log_id", sa.BigInteger(), primary_key=True),
        sa.Column("report_id", sa.BigInteger(), nullable=False),
        sa.Column("requester_id", sa.BigInteger(), nullable=False),
        sa.Column("approver_id", sa.BigInteger(), nullable=True),
        sa.Column("judicial_doc_no", sa.String(64), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("related_case_no", sa.String(32), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("audit_log_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.current_timestamp()
        ),
        sa.ForeignKeyConstraint(
            ["requester_id"], ["users.user_id"],
            name="fk_anonymous_decrypt_logs_requester_id_users", ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["approver_id"], ["users.user_id"],
            name="fk_anonymous_decrypt_logs_approver_id_users", ondelete="RESTRICT",
        ),
        # 注意：audit_logs 由于复合 PK，无法对其 log_id 单独建外键，故省略 FK；逻辑约束由应用层保证
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="匿名身份解密授权日志（UC-10 备选 A2）",
    )
    op.create_index("idx_anon_decrypt_report", "anonymous_decrypt_logs", ["report_id"])

    # ── DB 层强制审计不可变（PRD 5.4.3） ────────────────────────
    # MySQL trigger creation may require elevated privileges when binary logging is enabled.
    # The app account runs migrations; root applies trigger + least-privilege grants via
    # infra/docker/mysql/post_migration/01_grants.sql after `alembic upgrade head`.


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "mysql":
        op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_no_delete")
        op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_no_update")

    op.drop_index("idx_anon_decrypt_report", table_name="anonymous_decrypt_logs")
    op.drop_table("anonymous_decrypt_logs")

    op.drop_table("anonymous_mappings")

    op.drop_table("system_configs")

    op.drop_index("idx_notif_type", table_name="notifications")
    op.drop_index("idx_notif_user_read_time", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("idx_audit_trace_id", table_name="audit_logs")
    op.drop_index("idx_audit_op_type_time", table_name="audit_logs")
    op.drop_index("idx_audit_object", table_name="audit_logs")
    op.drop_index("idx_audit_op_time", table_name="audit_logs")
    op.drop_table("audit_logs")

    op.drop_index("idx_session_expires_at", table_name="sessions")
    op.drop_index("idx_session_user_id", table_name="sessions")
    op.drop_table("sessions")

    op.drop_table("role_permissions")

    op.drop_index("idx_user_status", table_name="users")
    op.drop_index("idx_user_dept_role", table_name="users")
    op.drop_table("users")

    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("departments")
