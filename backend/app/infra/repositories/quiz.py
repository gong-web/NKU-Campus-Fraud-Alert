"""安全测验仓储（UC-05 / UC-09）。

仓储层只负责数据访问；不主动 ``commit``、不抛业务异常，事务边界由
service 层用 ``async with uow():`` 控制。所有方法 keyword-only 参数。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import and_, delete, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.question_bank import QuestionBank
from app.infra.db.models.quiz import Quiz, QuizStatus
from app.infra.db.models.quiz_attempt import QuizAttempt, QuizAttemptStatus
from app.infra.db.models.quiz_attempt_answer import QuizAttemptAnswer
from app.infra.db.models.quiz_question import QuizQuestion


class QuizRepository:
    """测验 / 题库 / 答题记录的统一仓储入口。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── 题库 ──────────────────────────────────────────────────────
    async def add_question(self, q: QuestionBank) -> QuestionBank:
        self._s.add(q)
        await self._s.flush()
        return q

    async def get_question(self, question_id: int) -> QuestionBank | None:
        return (
            await self._s.execute(
                select(QuestionBank).where(QuestionBank.question_id == question_id)
            )
        ).scalar_one_or_none()

    async def get_questions_by_ids(
        self, question_ids: list[int]
    ) -> list[QuestionBank]:
        if not question_ids:
            return []
        rows = await self._s.execute(
            select(QuestionBank).where(QuestionBank.question_id.in_(question_ids))
        )
        return list(rows.scalars())

    async def list_questions(
        self,
        *,
        keyword: str | None = None,
        fraud_type_id: int | None = None,
        difficulty: int | None = None,
        is_active: bool | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[QuestionBank], int]:
        base = select(QuestionBank)
        conds = []
        if keyword:
            kw = f"%{keyword.strip()}%"
            conds.append(
                or_(QuestionBank.content.like(kw), QuestionBank.explanation.like(kw))
            )
        if fraud_type_id is not None:
            conds.append(QuestionBank.fraud_type_id == fraud_type_id)
        if difficulty is not None:
            conds.append(QuestionBank.difficulty == difficulty)
        if is_active is not None:
            conds.append(QuestionBank.is_active == (1 if is_active else 0))
        if conds:
            base = base.where(and_(*conds))

        total = int(
            (
                await self._s.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
            or 0
        )
        rows = await self._s.execute(
            base.order_by(desc(QuestionBank.created_at), desc(QuestionBank.question_id))
            .offset(offset)
            .limit(limit)
        )
        return list(rows.scalars()), total

    async def sample_active_questions(self, *, n: int) -> list[QuestionBank]:
        """随机取 N 道启用题目（用于 RANDOM 模式）。

        使用 ``ORDER BY RAND()`` 对 5K 内题量足够，更大题库可改为子查询取 ID。
        """
        rows = await self._s.execute(
            select(QuestionBank)
            .where(QuestionBank.is_active == 1)
            .order_by(func.rand())
            .limit(n)
        )
        return list(rows.scalars())

    async def count_active_questions(self) -> int:
        return int(
            (
                await self._s.execute(
                    select(func.count()).where(QuestionBank.is_active == 1)
                )
            ).scalar_one()
            or 0
        )

    # ── 测验 ──────────────────────────────────────────────────────
    async def add_quiz(self, quiz: Quiz) -> Quiz:
        self._s.add(quiz)
        await self._s.flush()
        return quiz

    async def get_quiz(self, quiz_id: int) -> Quiz | None:
        return (
            await self._s.execute(select(Quiz).where(Quiz.quiz_id == quiz_id))
        ).scalar_one_or_none()

    async def list_assigned_quizzes(
        self,
        *,
        status: str | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Quiz], int]:
        """管理员视角列出所有 ASSIGNED 测验。"""
        base = select(Quiz).where(Quiz.quiz_type == "ASSIGNED")
        if status is not None:
            base = base.where(Quiz.status == status)
        if keyword:
            base = base.where(Quiz.title.like(f"%{keyword.strip()}%"))
        total = int(
            (
                await self._s.execute(select(func.count()).select_from(base.subquery()))
            ).scalar_one()
            or 0
        )
        rows = await self._s.execute(
            base.order_by(desc(Quiz.created_at), desc(Quiz.quiz_id))
            .offset(offset)
            .limit(limit)
        )
        return list(rows.scalars()), total

    async def list_assigned_quizzes_for_student(
        self, *, dept_id: int, user_id: int, status: str | None = None
    ) -> list[Quiz]:
        """学生视角：本人可参与的所有 ASSIGNED 测验。

        命中规则（target_scope JSON）：
          type=ALL  ⇒ 全部
          type=DEPT ⇒ dept_id 在 dept_ids 中
          type=USERS ⇒ user_id 在 user_ids 中

        SQLAlchemy + MySQL JSON_CONTAINS 跨方言不友好，直接 Python 侧过滤。
        """
        stmt = select(Quiz).where(Quiz.quiz_type == "ASSIGNED")
        if status is not None:
            stmt = stmt.where(Quiz.status == status)
        rows = (await self._s.execute(stmt.order_by(desc(Quiz.created_at)))).scalars()
        out: list[Quiz] = []
        for q in rows:
            scope = q.target_scope or {}
            stype = scope.get("type")
            if stype == "ALL":
                out.append(q)
            elif stype == "DEPT":
                if dept_id in set(scope.get("dept_ids") or []):
                    out.append(q)
            elif stype == "USERS":
                if user_id in set(scope.get("user_ids") or []):
                    out.append(q)
        return out

    # ── 测验题目关联 ─────────────────────────────────────────────
    async def add_quiz_questions(
        self, *, quiz_id: int, ordered_question_ids: list[int]
    ) -> None:
        for idx, qid in enumerate(ordered_question_ids, start=1):
            self._s.add(QuizQuestion(quiz_id=quiz_id, question_id=qid, sort_order=idx))
        await self._s.flush()

    async def list_quiz_questions(self, quiz_id: int) -> list[QuizQuestion]:
        rows = await self._s.execute(
            select(QuizQuestion)
            .where(QuizQuestion.quiz_id == quiz_id)
            .order_by(QuizQuestion.sort_order)
        )
        return list(rows.scalars())

    # ── 答题记录 ─────────────────────────────────────────────────
    async def add_attempt(self, attempt: QuizAttempt) -> QuizAttempt:
        self._s.add(attempt)
        await self._s.flush()
        return attempt

    async def get_attempt(self, attempt_id: int) -> QuizAttempt | None:
        return (
            await self._s.execute(
                select(QuizAttempt).where(QuizAttempt.attempt_id == attempt_id)
            )
        ).scalar_one_or_none()

    async def get_attempt_by_quiz_user(
        self, *, quiz_id: int, user_id: int
    ) -> QuizAttempt | None:
        return (
            await self._s.execute(
                select(QuizAttempt).where(
                    QuizAttempt.quiz_id == quiz_id,
                    QuizAttempt.student_id == user_id,
                )
            )
        ).scalar_one_or_none()

    async def list_submitted_attempts_of_quiz_for_students(
        self, *, quiz_id: int, student_ids: list[int]
    ) -> list[QuizAttempt]:
        if not student_ids:
            return []
        rows = await self._s.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.status == QuizAttemptStatus.SUBMITTED,
                QuizAttempt.student_id.in_(student_ids),
            )
        )
        return list(rows.scalars())

    async def list_submitted_attempts_of_quiz(
        self, quiz_id: int
    ) -> list[QuizAttempt]:
        rows = await self._s.execute(
            select(QuizAttempt).where(
                QuizAttempt.quiz_id == quiz_id,
                QuizAttempt.status == QuizAttemptStatus.SUBMITTED,
            )
        )
        return list(rows.scalars())

    async def list_submitted_attempts_for_student(
        self, *, user_id: int, limit: int = 50, offset: int = 0
    ) -> tuple[list[tuple[QuizAttempt, Quiz]], int]:
        """学生测验历史：返回 (attempt, quiz) 对 + 总数，按提交时间倒序。"""
        base = (
            select(QuizAttempt, Quiz)
            .join(Quiz, Quiz.quiz_id == QuizAttempt.quiz_id)
            .where(
                QuizAttempt.student_id == user_id,
                QuizAttempt.status == QuizAttemptStatus.SUBMITTED,
            )
        )
        total = int(
            (
                await self._s.execute(
                    select(func.count()).select_from(
                        select(QuizAttempt.attempt_id)
                        .where(
                            QuizAttempt.student_id == user_id,
                            QuizAttempt.status == QuizAttemptStatus.SUBMITTED,
                        )
                        .subquery()
                    )
                )
            ).scalar_one()
            or 0
        )
        rows = await self._s.execute(
            base.order_by(desc(QuizAttempt.submitted_at), desc(QuizAttempt.attempt_id))
            .offset(offset)
            .limit(limit)
        )
        return [(a, q) for a, q in rows.all()], total

    # ── 答题明细 ─────────────────────────────────────────────────
    async def add_answers(self, answers: list[QuizAttemptAnswer]) -> None:
        if not answers:
            return
        self._s.add_all(answers)
        await self._s.flush()

    async def list_answers_of_attempt(
        self, attempt_id: int
    ) -> list[QuizAttemptAnswer]:
        rows = await self._s.execute(
            select(QuizAttemptAnswer).where(QuizAttemptAnswer.attempt_id == attempt_id)
        )
        return list(rows.scalars())

    async def list_wrong_answers_for_student(
        self, *, user_id: int, limit: int = 100
    ) -> list[tuple[QuizAttemptAnswer, QuizAttempt]]:
        """学生错题汇总：按提交时间倒序返回最近的 ``limit`` 条错题。"""
        rows = await self._s.execute(
            select(QuizAttemptAnswer, QuizAttempt)
            .join(QuizAttempt, QuizAttempt.attempt_id == QuizAttemptAnswer.attempt_id)
            .where(
                QuizAttempt.student_id == user_id,
                QuizAttempt.status == QuizAttemptStatus.SUBMITTED,
                QuizAttemptAnswer.is_correct == 0,
            )
            .order_by(desc(QuizAttempt.submitted_at), desc(QuizAttemptAnswer.answer_id))
            .limit(limit)
        )
        return [(a, t) for a, t in rows.all()]

    # ── 截止任务 ─────────────────────────────────────────────────
    async def list_quizzes_near_deadline(
        self, *, window_start: datetime, window_end: datetime
    ) -> list[Quiz]:
        """返回 ``window_start <= deadline_at < window_end`` 且未发提醒的 ACTIVE 测验。"""
        rows = await self._s.execute(
            select(Quiz).where(
                Quiz.quiz_type == "ASSIGNED",
                Quiz.status == QuizStatus.ACTIVE,
                Quiz.reminder_sent == 0,
                Quiz.deadline_at >= window_start,
                Quiz.deadline_at < window_end,
            )
        )
        return list(rows.scalars())

    async def list_expired_active_quizzes(self) -> list[Quiz]:
        """返回截止时间已过但仍 ACTIVE 的指定测验（用于自动 FINISH）。"""
        now = datetime.now(tz=UTC)
        rows = await self._s.execute(
            select(Quiz).where(
                Quiz.quiz_type == "ASSIGNED",
                Quiz.status == QuizStatus.ACTIVE,
                Quiz.deadline_at.is_not(None),
                Quiz.deadline_at < now,
            )
        )
        return list(rows.scalars())

    # ── 杂项 ─────────────────────────────────────────────────────
    async def delete_quiz_cascade(self, quiz_id: int) -> None:
        """测试 / 仅 DRAFT 删除使用，正式撤回请走 service 的状态变更。"""
        await self._s.execute(delete(Quiz).where(Quiz.quiz_id == quiz_id))
        await self._s.flush()

    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(tz=UTC)

    @staticmethod
    def scope_summary(target_scope: dict[str, Any] | None) -> str:
        if not target_scope:
            return ""
        stype = target_scope.get("type")
        if stype == "ALL":
            return "全校"
        if stype == "DEPT":
            n = len(target_scope.get("dept_ids") or [])
            return f"{n} 个院系"
        if stype == "USERS":
            n = len(target_scope.get("user_ids") or [])
            return f"{n} 名学生"
        return stype or ""
