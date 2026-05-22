"""Revoke kb:review / kb:offline from dept-level REVIEWER (role_level=1).

Revision ID: 0005_lht_split_reviewer
Revises: 0004_lht_warnings_kb
Create Date: 2026-06-05 00:00:00

Background
----------
Seed 矩阵原本把 ``kb:review`` / ``kb:offline`` 灌给 ``role_code='REVIEWER'`` 的所有行，
而院系级（``role_level=1``）实际无权审核知识库（service 层 ``role_level==2`` 校验）。
这造成前端 ``hasPermission('kb:review')`` 返回 true → 误显示「审核」按钮，点击才被
拦下。本迁移把院系级 reviewer 多余的两条 ``role_permissions`` 行删除，使前后端一致。

幂等：``DELETE`` 即使行已不存在也是空操作。
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005_lht_split_reviewer"
down_revision: str | Sequence[str] | None = "0004_lht_warnings_kb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_DEPT_REVIEWER_PERMS = ("kb:review", "kb:offline")


def upgrade() -> None:
    op.execute(
        """
        DELETE rp FROM role_permissions rp
        JOIN roles r ON r.role_id = rp.role_id
        JOIN permissions p ON p.permission_id = rp.permission_id
        WHERE r.role_code = 'REVIEWER'
          AND r.role_level = 1
          AND p.permission_code IN ('kb:review', 'kb:offline')
        """
    )


def downgrade() -> None:
    # 还原：把 kb:review / kb:offline 重新赋给院系级 REVIEWER。
    # INSERT IGNORE 确保即便 PK/UNIQUE 冲突也不报错。
    op.execute(
        """
        INSERT IGNORE INTO role_permissions (role_id, permission_id)
        SELECT r.role_id, p.permission_id
        FROM roles r
        JOIN permissions p ON p.permission_code IN ('kb:review', 'kb:offline')
        WHERE r.role_code = 'REVIEWER' AND r.role_level = 1
        """
    )
