"""测验-题目关联表（PRD UC-05 / UC-09）。

复合主键 ``(quiz_id, question_id)``，``sort_order`` 决定答题页题目顺序。
RANDOM 创建时插入 N 条；ASSIGNED 发布时按选定顺序插入。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, PrimaryKeyConstraint, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class QuizQuestion(Base):
    """测验与题目的多对多关联。"""

    __tablename__ = "quiz_questions"
    __table_args__ = (
        PrimaryKeyConstraint("quiz_id", "question_id", name="pk_quiz_questions"),
        Index("idx_quiz_questions_quiz", "quiz_id"),
        {"comment": "测验题目关联表 PRD UC-05/UC-09"},
    )

    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quizzes.quiz_id", ondelete="CASCADE"),
        nullable=False,
        comment="所属测验 ID",
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("question_bank.question_id", ondelete="RESTRICT"),
        nullable=False,
        comment="题目 ID",
    )
    sort_order: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, comment="展示顺序，从 1 起"
    )
