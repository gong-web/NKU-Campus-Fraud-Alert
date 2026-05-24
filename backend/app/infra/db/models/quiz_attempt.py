"""答题记录表（PRD UC-05 / UC-09）。

一个学生对一场测验生成一条 ``QuizAttempt``：开测时插入 ``IN_PROGRESS``，
提交答案时改为 ``SUBMITTED`` 并写入分数。RANDOM 测验本身就是一次性的
 quiz_id（开测即新建），ASSIGNED 测验通过 service 层校验同一 ``(quiz_id, student_id)``
 只能有一条记录。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Index, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class QuizAttemptStatus:
    """答题记录状态。"""

    IN_PROGRESS = "IN_PROGRESS"
    SUBMITTED = "SUBMITTED"

    ALL: frozenset[str] = frozenset({IN_PROGRESS, SUBMITTED})


class QuizAttempt(Base):
    """答题记录。"""

    __tablename__ = "quiz_attempts"
    __table_args__ = (
        Index("idx_attempts_quiz_student", "quiz_id", "student_id"),
        Index("idx_attempts_student", "student_id"),
        Index("idx_attempts_status", "status"),
        {"comment": "答题记录表 PRD UC-05/UC-09"},
    )

    attempt_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quiz_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("quizzes.quiz_id", ondelete="RESTRICT"),
        nullable=False,
        comment="测验 ID",
    )
    student_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="答题学生 user_id",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=QuizAttemptStatus.IN_PROGRESS,
        server_default=QuizAttemptStatus.IN_PROGRESS,
        comment="IN_PROGRESS / SUBMITTED",
    )
    score: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="百分制得分（提交后写入）"
    )
    correct_count: Mapped[int | None] = mapped_column(
        SmallInteger, nullable=True, comment="答对题数"
    )
    started_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp(), comment="开始时间"
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="提交时间（仅 SUBMITTED）"
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt {self.attempt_id} quiz={self.quiz_id} score={self.score}>"
