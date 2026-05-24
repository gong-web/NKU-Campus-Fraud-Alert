"""UC-05 / UC-09: question_bank / quizzes / quiz_questions / quiz_attempts / quiz_attempt_answers.

Revision ID: 0006_tsy_quiz
Create Date: 2026-06-10 00:00:00

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0006_tsy_quiz"
down_revision: str | Sequence[str] | None = "0005_lht_split_reviewer"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    ts = sa.text("CURRENT_TIMESTAMP")

    # ── 1. 题库表 ────────────────────────────────────────────────────
    op.create_table(
        "question_bank",
        sa.Column("question_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column("content", sa.Text(), nullable=False, comment="题干"),
        sa.Column("option_a", sa.String(512), nullable=False, comment="选项 A"),
        sa.Column("option_b", sa.String(512), nullable=False, comment="选项 B"),
        sa.Column("option_c", sa.String(512), nullable=False, comment="选项 C"),
        sa.Column("option_d", sa.String(512), nullable=False, comment="选项 D"),
        sa.Column(
            "correct_answer",
            sa.String(1),
            nullable=False,
            comment="正确答案 A/B/C/D",
        ),
        sa.Column("explanation", sa.Text(), nullable=True, comment="解析说明"),
        sa.Column(
            "fraud_type_id",
            sa.Integer(),
            nullable=True,
            comment="所属诈骗类型（可选，用于推送知识库）",
        ),
        sa.Column(
            "knowledge_entry_id",
            sa.BigInteger(),
            nullable=True,
            comment="关联知识库条目 ID（答错时跳转学习）",
        ),
        sa.Column(
            "difficulty",
            sa.SmallInteger(),
            nullable=False,
            server_default="1",
            comment="难度 1=简单 / 2=中等 / 3=困难",
        ),
        sa.Column(
            "is_active",
            sa.SmallInteger(),
            nullable=False,
            server_default="1",
            comment="1=启用 / 0=禁用",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=False, comment="创建人 user_id"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=ts),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=ts, onupdate=ts),
        sa.ForeignKeyConstraint(
            ["fraud_type_id"],
            ["fraud_types.type_id"],
            name="fk_question_bank_fraud_type_id_fraud_types",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["knowledge_entry_id"],
            ["knowledge_entries.entry_id"],
            name="fk_question_bank_knowledge_entry_id_knowledge_entries",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
            name="fk_question_bank_created_by_users",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="题库表 PRD UC-05/UC-09",
    )
    op.create_index("idx_qbank_fraud_type", "question_bank", ["fraud_type_id"])
    op.create_index("idx_qbank_is_active", "question_bank", ["is_active"])
    op.create_index("idx_qbank_difficulty", "question_bank", ["difficulty"])

    # ── 2. 测验表 ────────────────────────────────────────────────────
    op.create_table(
        "quizzes",
        sa.Column("quiz_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column(
            "quiz_type",
            sa.String(16),
            nullable=False,
            comment="RANDOM=随机练习 / ASSIGNED=指定测验",
        ),
        sa.Column("title", sa.String(128), nullable=False, comment="测验标题"),
        sa.Column(
            "question_count",
            sa.SmallInteger(),
            nullable=False,
            server_default="10",
            comment="题目数量，默认 10",
        ),
        sa.Column(
            "pass_score",
            sa.SmallInteger(),
            nullable=False,
            server_default="60",
            comment="及格分数线（满分 100）",
        ),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="ACTIVE",
            comment="ACTIVE=进行中 / CANCELLED=已撤回 / FINISHED=已结束",
        ),
        sa.Column("created_by", sa.BigInteger(), nullable=False, comment="发起人 user_id"),
        sa.Column("deadline_at", sa.DateTime(), nullable=True, comment="截止时间（指定测验）"),
        sa.Column(
            "target_scope",
            sa.JSON(),
            nullable=True,
            comment='目标范围 JSON: {"type": "ALL"} 或 {"type": "DEPT", "dept_ids": [1,2]}',
        ),
        sa.Column("reminder_sent", sa.SmallInteger(), nullable=False, server_default="0",
                  comment="是否已发提醒 0/1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=ts),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=ts, onupdate=ts),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.user_id"],
            name="fk_quizzes_created_by_users",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="测验表 PRD UC-05/UC-09",
    )
    op.create_index("idx_quizzes_type_status", "quizzes", ["quiz_type", "status"])
    op.create_index("idx_quizzes_deadline", "quizzes", ["deadline_at"])
    op.create_index("idx_quizzes_created_by", "quizzes", ["created_by"])

    # ── 3. 测验题目关联表 ────────────────────────────────────────────
    op.create_table(
        "quiz_questions",
        sa.Column("quiz_id", sa.BigInteger(), nullable=False, comment="测验 ID"),
        sa.Column("question_id", sa.BigInteger(), nullable=False, comment="题目 ID"),
        sa.Column("sort_order", sa.SmallInteger(), nullable=False, comment="题目顺序（从 1 起）"),
        sa.PrimaryKeyConstraint("quiz_id", "question_id", name="pk_quiz_questions"),
        sa.ForeignKeyConstraint(
            ["quiz_id"],
            ["quizzes.quiz_id"],
            name="fk_quiz_questions_quiz_id_quizzes",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["question_bank.question_id"],
            name="fk_quiz_questions_question_id_question_bank",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="测验题目关联表 PRD UC-05/UC-09",
    )
    op.create_index("idx_quiz_questions_quiz", "quiz_questions", ["quiz_id"])

    # ── 4. 答题记录表 ────────────────────────────────────────────────
    op.create_table(
        "quiz_attempts",
        sa.Column("attempt_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column("quiz_id", sa.BigInteger(), nullable=False, comment="测验 ID"),
        sa.Column("student_id", sa.BigInteger(), nullable=False, comment="学生 user_id"),
        sa.Column(
            "status",
            sa.String(16),
            nullable=False,
            server_default="IN_PROGRESS",
            comment="IN_PROGRESS=进行中 / SUBMITTED=已提交",
        ),
        sa.Column("score", sa.SmallInteger(), nullable=True, comment="得分（提交后计算）"),
        sa.Column("correct_count", sa.SmallInteger(), nullable=True, comment="答对题数"),
        sa.Column("started_at", sa.DateTime(), nullable=False, server_default=ts, comment="开始时间"),
        sa.Column("submitted_at", sa.DateTime(), nullable=True, comment="提交时间"),
        sa.ForeignKeyConstraint(
            ["quiz_id"],
            ["quizzes.quiz_id"],
            name="fk_quiz_attempts_quiz_id_quizzes",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["student_id"],
            ["users.user_id"],
            name="fk_quiz_attempts_student_id_users",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="答题记录表 PRD UC-05/UC-09",
    )
    op.create_index("idx_attempts_quiz_student", "quiz_attempts", ["quiz_id", "student_id"])
    op.create_index("idx_attempts_student", "quiz_attempts", ["student_id"])
    op.create_index("idx_attempts_status", "quiz_attempts", ["status"])

    # ── 5. 答题明细表 ────────────────────────────────────────────────
    op.create_table(
        "quiz_attempt_answers",
        sa.Column("answer_id", sa.BigInteger(), primary_key=True, comment="雪花算法生成"),
        sa.Column("attempt_id", sa.BigInteger(), nullable=False, comment="答题记录 ID"),
        sa.Column("question_id", sa.BigInteger(), nullable=False, comment="题目 ID"),
        sa.Column("chosen_answer", sa.String(1), nullable=True, comment="学生选择的答案 A/B/C/D"),
        sa.Column("is_correct", sa.SmallInteger(), nullable=True, comment="是否正确 0/1"),
        sa.ForeignKeyConstraint(
            ["attempt_id"],
            ["quiz_attempts.attempt_id"],
            name="fk_quiz_attempt_answers_attempt_id_quiz_attempts",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["question_id"],
            ["question_bank.question_id"],
            name="fk_quiz_attempt_answers_question_id_question_bank",
            ondelete="RESTRICT",
        ),
        mysql_engine="InnoDB",
        mysql_charset="utf8mb4",
        mysql_collate="utf8mb4_0900_ai_ci",
        comment="答题明细表 PRD UC-05/UC-09",
    )
    op.create_index("idx_answers_attempt", "quiz_attempt_answers", ["attempt_id"])
    op.create_index("idx_answers_question", "quiz_attempt_answers", ["question_id"])


def downgrade() -> None:
    op.drop_index("idx_answers_question", table_name="quiz_attempt_answers")
    op.drop_index("idx_answers_attempt", table_name="quiz_attempt_answers")
    op.drop_table("quiz_attempt_answers")

    op.drop_index("idx_attempts_status", table_name="quiz_attempts")
    op.drop_index("idx_attempts_student", table_name="quiz_attempts")
    op.drop_index("idx_attempts_quiz_student", table_name="quiz_attempts")
    op.drop_table("quiz_attempts")

    op.drop_index("idx_quiz_questions_quiz", table_name="quiz_questions")
    op.drop_table("quiz_questions")

    op.drop_index("idx_quizzes_created_by", table_name="quizzes")
    op.drop_index("idx_quizzes_deadline", table_name="quizzes")
    op.drop_index("idx_quizzes_type_status", table_name="quizzes")
    op.drop_table("quizzes")

    op.drop_index("idx_qbank_difficulty", table_name="question_bank")
    op.drop_index("idx_qbank_is_active", table_name="question_bank")
    op.drop_index("idx_qbank_fraud_type", table_name="question_bank")
    op.drop_table("question_bank")
