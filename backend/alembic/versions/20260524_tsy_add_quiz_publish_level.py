"""Add quizzes.publish_level to distinguish SCHOOL vs DEPT publisher.

Revision ID: 0007_tsy_quiz_publish_level
Revises: 0006_tsy_quiz
Create Date: 2026-05-24 00:00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_tsy_quiz_publish_level"
down_revision: str | Sequence[str] | None = "0006_tsy_quiz"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "quizzes",
        sa.Column(
            "publish_level",
            sa.SmallInteger(),
            nullable=False,
            server_default="2",
            comment="发布级别 1=院级/学院 2=校级",
        ),
    )
    op.create_index("idx_quizzes_publish_level", "quizzes", ["publish_level"])

    # Backfill: creator is dept-level reviewer (role_level=1) => DEPT(1), else SCHOOL(2)
    op.execute(
        """
        UPDATE quizzes q
        JOIN users u ON u.user_id = q.created_by
        JOIN roles r ON r.role_id = u.role_id
        SET q.publish_level = CASE
            WHEN r.role_code = 'REVIEWER' AND r.role_level = 1 THEN 1
            ELSE 2
        END
        WHERE q.quiz_type = 'ASSIGNED'
        """
    )

    op.alter_column("quizzes", "publish_level", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_quizzes_publish_level", table_name="quizzes")
    op.drop_column("quizzes", "publish_level")
