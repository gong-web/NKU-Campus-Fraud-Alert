from __future__ import annotations

from datetime import UTC, datetime, timedelta
from io import BytesIO

import pytest
from openpyxl import load_workbook
from pydantic import ValidationError

from app.domain.user_snapshot import UserSnapshot
from app.schemas.quiz import (
    AssignedQuizCreateIn,
    DepartmentCompletionItem,
    QuizCompletionReportOut,
)
from app.services import quiz_service


def _assigned_quiz_body(question_ids: list[int]) -> dict[str, object]:
    return {
        "title": "演示测验",
        "question_ids": question_ids,
        "pass_score": 60,
        "deadline_at": datetime.now(tz=UTC) + timedelta(days=1),
        "scope_type": "ALL",
    }


def test_assigned_quiz_requires_at_least_three_questions() -> None:
    with pytest.raises(ValidationError):
        AssignedQuizCreateIn.model_validate(_assigned_quiz_body([1, 2]))

    body = AssignedQuizCreateIn.model_validate(_assigned_quiz_body([1, 2, 3]))
    assert body.question_ids == [1, 2, 3]


@pytest.mark.asyncio
async def test_completion_report_export_is_valid_xlsx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    report = QuizCompletionReportOut(
        quiz_id="123",
        title="反诈知识测验",
        status="ACTIVE",
        deadline_at=datetime.now(tz=UTC) + timedelta(days=1),
        total_targets=3,
        submitted_count=2,
        completion_rate=2 / 3,
        pass_rate=0.5,
        avg_score=70,
        by_department=[
            DepartmentCompletionItem(
                dept_id=1,
                dept_name="计算机学院",
                total_targets=3,
                submitted_count=2,
                completion_rate=2 / 3,
                pass_count=1,
                pass_rate=0.5,
                avg_score=70,
            )
        ],
    )

    async def fake_report(
        quiz_id: int, *, current: UserSnapshot
    ) -> QuizCompletionReportOut:
        del quiz_id, current
        return report

    monkeypatch.setattr(quiz_service, "get_completion_report", fake_report)
    current = UserSnapshot(
        user_id=1,
        cas_account="reviewer_school001",
        real_name="校级审核员",
        role_id=1,
        role_code="REVIEWER",
        department_id=1,
        session_id="test",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )

    data, filename = await quiz_service.export_completion_report_xlsx(
        123, current=current
    )
    workbook = load_workbook(BytesIO(data), read_only=True)
    sheet = workbook["完成率报告"]

    assert filename == "quiz_report_123_反诈知识测验.xlsx"
    assert sheet["A1"].value == "测验 ID"
    assert sheet["B1"].value == "123"
    assert sheet["B2"].value == "反诈知识测验"
    assert sheet["B12"].value == "计算机学院"
