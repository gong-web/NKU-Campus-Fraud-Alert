"""管理员侧安全测验接口（UC-05 题库管理 + UC-09 指定测验）。

端点
----
- 题库管理：``/api/v1/admin/quiz/questions``（CRUD）
- 指定测验：``/api/v1/admin/quiz/quizzes``（创建 / 列表 / 详情 / 撤回）
- 完成率报告：``/api/v1/admin/quiz/quizzes/{quiz_id}/report``
- 报告导出：``/api/v1/admin/quiz/quizzes/{quiz_id}/report/export``（XLSX）
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.quiz import (
    AssignedQuizCreateIn,
    QuestionAdminOut,
    QuestionCreateIn,
    QuestionUpdateIn,
    QuizCancelIn,
    QuizCompletionReportOut,
    QuizDetailOut,
    QuizListItemOut,
)
from app.services import permissions as perm
from app.services.quiz_service import (
    cancel_quiz,
    create_assigned_quiz,
    create_question,
    delete_question,
    export_completion_report_xlsx,
    get_completion_report,
    get_question,
    get_quiz_admin,
    list_assigned_quizzes_admin,
    list_questions,
    update_question,
)

router = APIRouter(prefix="/admin/quiz", tags=["admin-quiz (UC-05/UC-09)"])


# ── 题库管理 ──────────────────────────────────────────────────────
@router.post(
    "/questions",
    response_model=QuestionAdminOut,
    status_code=201,
    summary="新增题目",
)
async def admin_create_question(
    body: QuestionCreateIn,
    current: Annotated[
        UserSnapshot, Depends(require_permission(perm.QUIZ_BANK_MANAGE))
    ],
) -> QuestionAdminOut:
    return await create_question(body, current=current)


@router.get(
    "/questions",
    response_model=PaginationOut[QuestionAdminOut],
    summary="题库分页",
)
async def admin_list_questions(
    _: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_BANK_MANAGE))],
    keyword: Annotated[str | None, Query(max_length=128)] = None,
    fraud_type_id: Annotated[int | None, Query(ge=1)] = None,
    difficulty: Annotated[int | None, Query(ge=1, le=3)] = None,
    is_active: Annotated[bool | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[QuestionAdminOut]:
    return await list_questions(
        keyword=keyword,
        fraud_type_id=fraud_type_id,
        difficulty=difficulty,
        is_active=is_active,
        page=page,
        size=size,
    )


@router.get(
    "/questions/{question_id}",
    response_model=QuestionAdminOut,
    summary="题目详情",
)
async def admin_get_question(
    question_id: int,
    _: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_BANK_MANAGE))],
) -> QuestionAdminOut:
    return await get_question(question_id)


@router.patch(
    "/questions/{question_id}",
    response_model=QuestionAdminOut,
    summary="编辑题目",
)
async def admin_update_question(
    question_id: int,
    body: QuestionUpdateIn,
    current: Annotated[
        UserSnapshot, Depends(require_permission(perm.QUIZ_BANK_MANAGE))
    ],
) -> QuestionAdminOut:
    return await update_question(question_id, body, current=current)


@router.delete(
    "/questions/{question_id}",
    summary="软删除题目（is_active=0）",
)
async def admin_delete_question(
    question_id: int,
    current: Annotated[
        UserSnapshot, Depends(require_permission(perm.QUIZ_BANK_MANAGE))
    ],
) -> dict[str, str]:
    return await delete_question(question_id, current=current)


# ── 指定测验 ──────────────────────────────────────────────────────
@router.post(
    "/quizzes",
    response_model=QuizDetailOut,
    status_code=201,
    summary="发起指定测验（UC-09）",
)
async def admin_create_assigned_quiz(
    body: AssignedQuizCreateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_ASSIGN))],
) -> QuizDetailOut:
    return await create_assigned_quiz(body, current=current)


@router.get(
    "/quizzes",
    response_model=PaginationOut[QuizListItemOut],
    summary="指定测验列表",
)
async def admin_list_quizzes(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_ASSIGN))],
    status: Annotated[
        str | None, Query(description="ACTIVE / CANCELLED / FINISHED")
    ] = None,
    keyword: Annotated[str | None, Query(max_length=128)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[QuizListItemOut]:
    return await list_assigned_quizzes_admin(
        current=current, status=status, keyword=keyword, page=page, size=size
    )


@router.get(
    "/quizzes/{quiz_id}",
    response_model=QuizDetailOut,
    summary="指定测验详情",
)
async def admin_get_quiz(
    quiz_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_ASSIGN))],
) -> QuizDetailOut:
    return await get_quiz_admin(quiz_id, current=current)


@router.post(
    "/quizzes/{quiz_id}/cancel",
    summary="撤回测验",
)
async def admin_cancel_quiz(
    quiz_id: int,
    body: QuizCancelIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_ASSIGN))],
) -> dict[str, str]:
    return await cancel_quiz(quiz_id, body, current=current)


# ── 完成率报告 ────────────────────────────────────────────────────
@router.get(
    "/quizzes/{quiz_id}/report",
    response_model=QuizCompletionReportOut,
    summary="完成率报告（按院系）",
)
async def admin_quiz_report(
    quiz_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_ASSIGN))],
) -> QuizCompletionReportOut:
    return await get_completion_report(quiz_id, current=current)


@router.get(
    "/quizzes/{quiz_id}/report/export",
    summary="完成率报告导出 Excel",
    response_class=StreamingResponse,
)
async def admin_quiz_report_export(
    quiz_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.QUIZ_ASSIGN))],
) -> StreamingResponse:
    from io import BytesIO
    from urllib.parse import quote

    data, filename = await export_completion_report_xlsx(quiz_id, current=current)
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or f"quiz_report_{quiz_id}.xlsx"
    disposition = (
        f'attachment; filename="{ascii_fallback}"; '
        f"filename*=UTF-8''{quote(filename)}"
    )
    return StreamingResponse(
        BytesIO(data),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": disposition},
    )
