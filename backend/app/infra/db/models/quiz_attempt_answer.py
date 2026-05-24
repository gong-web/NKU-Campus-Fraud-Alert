"""答题明细表（PRD UC-05 / UC-09）。

每条记录 = 某次 attempt 的某道题的回答快照。提交时由 service 层批量写入：

- 答错时用 ``chosen_answer`` + 题目 ``knowledge_entry_id`` 推送学习
- 报告页统计每题正确率 / 全班正确率
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class QuizAttemptAnswer(Base):
    """答题明细。"""

    __tablename__ = "quiz_attempt_answers"
    __table_args__ = (
        Index("idx_answers_attempt", "attempt_id"),
        Index("idx_answers_question", "question_id"),
        {"comment": "答题明细表 PRD UC-05/UC-09"},
    )

    answer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    attempt_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quiz_attempts.attempt_id", ondelete="CASCADE"),
        nullable=False,
        comment="所属答题记录 ID",
    )
    question_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("question_bank.question_id", ondelete="RESTRICT"),
        nullable=False,
        comment="题目 ID",
    )
    chosen_answer: Mapped[str | None] = mapped_column(
        String(1), nullable=True, comment="学生选择 A/B/C/D（未作答为 null）"
    )
    is_correct: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="是否答对 0/1"
    )
