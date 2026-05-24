"""学生侧安全测验接口（UC-05 / UC-09）。

端点
----
- ``POST /api/v1/quiz/random/start`` 开始随机练习
- ``GET  /api/v1/quiz/assigned`` 列出本人可参与的指定测验
- ``POST /api/v1/quiz/assigned/{quiz_id}/start`` 开始指定测验
- ``POST /api/v1/quiz/attempts/{attempt_id}/submit`` 提交答卷
- ``GET  /api/v1/quiz/wrong-questions`` 错题汇总
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.quiz import (
    QuizHistoryItemOut,
    QuizListItemOut,
    StartQuizOut,
    SubmitQuizIn,
    SubmitQuizOut,
    WrongQuestionOut,
)
from app.services import permissions as perm
from app.services.quiz_service import (
    list_assigned_quizzes_for_student,
    list_quiz_history_for_student,
    list_wrong_questions_for_student,
    start_assigned_quiz,
    start_random_quiz,
    submit_quiz,
)

router = APIRouter(prefix="/quiz", tags=["quiz-student (UC-05/UC-09)"])


@router.post(
    "/random/start",
    response_model=StartQuizOut,
    status_code=201,
    summary="学生开始随机练习（UC-05）",
)
async def student_start_random(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_TAKE))],
) -> StartQuizOut:
    """从题库随机抽 10 道启用题目，新建一次答题。"""
    return await start_random_quiz(current=current)


@router.get(
    "/assigned",
    response_model=list[QuizListItemOut],
    summary="学生侧：本人可参与的指定测验列表",
)
async def student_list_assigned(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_TAKE))],
    status: Annotated[
        str | None, Query(description="ACTIVE / CANCELLED / FINISHED；留空全部")
    ] = None,
) -> list[QuizListItemOut]:
    return await list_assigned_quizzes_for_student(current=current, status=status)


@router.post(
    "/assigned/{quiz_id}/start",
    response_model=StartQuizOut,
    summary="学生开始指定测验",
)
async def student_start_assigned(
    quiz_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_TAKE))],
) -> StartQuizOut:
    """幂等：已开始未提交的复用同一 attempt；已提交则 409。"""
    return await start_assigned_quiz(quiz_id, current=current)


@router.post(
    "/attempts/{attempt_id}/submit",
    response_model=SubmitQuizOut,
    summary="学生提交答卷",
)
async def student_submit(
    attempt_id: int,
    body: SubmitQuizIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_TAKE))],
) -> SubmitQuizOut:
    """提交后返回每题正确答案 / 解析 / 关联知识库条目用于跳转学习。"""
    return await submit_quiz(attempt_id, body, current=current)


@router.get(
    "/wrong-questions",
    response_model=list[WrongQuestionOut],
    summary="学生错题汇总",
)
async def student_wrong_questions(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_TAKE))],
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> list[WrongQuestionOut]:
    return await list_wrong_questions_for_student(current=current, limit=limit)


@router.get(
    "/history",
    response_model=PaginationOut[QuizHistoryItemOut],
    summary="学生测验历史（个人中心）",
)
async def student_quiz_history(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_TAKE))],
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[QuizHistoryItemOut]:
    """按提交时间倒序返回本人所有已提交的测验记录（含随机练习与指定测验）。"""
    return await list_quiz_history_for_student(current=current, page=page, size=size)
