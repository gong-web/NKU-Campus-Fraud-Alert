from __future__ import annotations

from datetime import UTC, date, datetime

import pytest
from sqlalchemy import select

from app.domain.user_snapshot import UserSnapshot
from app.infra.db.models import AuditLog, CaseStatusHistory, FraudCase, FraudType, Notification, Role, User
from app.infra.db.models.department import Department
from app.schemas.state import OperationType
from app.services.state_machine import IllegalStateTransitionError, change_status

pytestmark = pytest.mark.unit


@pytest.fixture
async def state_fixture(db_session):
    dept = Department(dept_code="CS", dept_name="计算机学院", dept_level=1, sort_order=1)
    db_session.add(dept)
    await db_session.flush()

    student_role = Role(role_code="STUDENT", role_name="学生", role_level=1)
    reviewer_role = Role(role_code="REVIEWER", role_name="审核员", role_level=2)
    db_session.add_all([student_role, reviewer_role])
    await db_session.flush()

    reporter = User(
        user_id=1001,
        cas_account="student_state",
        real_name="学生甲",
        department_id=dept.dept_id,
        role_id=student_role.role_id,
        email_encrypted="student@example.com",
        phone_encrypted="13800000000",
    )
    reviewer = User(
        user_id=2001,
        cas_account="reviewer_state",
        real_name="审核员甲",
        department_id=dept.dept_id,
        role_id=reviewer_role.role_id,
    )
    fraud_type = FraudType(
        type_code="TEST",
        type_name="测试类型",
        description="测试",
        is_active=True,
        sort_order=1,
    )
    db_session.add_all([reporter, reviewer, fraud_type])
    await db_session.flush()

    case = FraudCase(
        case_id=3001,
        case_no="2026-CS-003001",
        title="测试案件",
        description="测试案件描述文本足够长",
        fraud_type_id=fraud_type.type_id,
        incident_date=date(2026, 5, 1),
        reporter_id=reporter.user_id,
        is_anonymous=False,
        dept_code="CS",
        status="PENDING",
    )
    db_session.add(case)
    await db_session.commit()

    snapshot = UserSnapshot(
        user_id=reviewer.user_id,
        cas_account=reviewer.cas_account,
        real_name=reviewer.real_name,
        role_id=reviewer.role_id,
        role_code="REVIEWER",
        department_id=dept.dept_id,
        session_id="test-session",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    return {"case": case, "snapshot": snapshot, "reporter": reporter, "fraud_type": fraud_type, "dept": dept}


@pytest.mark.asyncio
async def test_change_status_open_detail_success(db_session, state_fixture):
    case = state_fixture["case"]
    snapshot = state_fixture["snapshot"]

    await change_status(
        db_session,
        case_id=case.case_id,
        operation=OperationType.OPEN_DETAIL,
        operator=snapshot,
    )
    await db_session.commit()

    db_case = await db_session.get(FraudCase, case.case_id)
    assert db_case is not None
    assert db_case.status == "REVIEWING"
    assert db_case.reviewer_id == snapshot.user_id

    histories = (
        await db_session.execute(
            select(CaseStatusHistory).where(CaseStatusHistory.case_id == case.case_id)
        )
    ).scalars().all()
    assert len(histories) == 1

    notifications = (await db_session.execute(select(Notification))).scalars().all()
    assert notifications == []

    audits = (await db_session.execute(select(AuditLog))).scalars().all()
    assert len(audits) == 1
    assert audits[0].operation_type == "STATE_CHANGE_OPEN_DETAIL"


@pytest.mark.asyncio
async def test_change_status_rollback_on_notification_failure(db_session, state_fixture, monkeypatch):
    case = state_fixture["case"]
    snapshot = state_fixture["snapshot"]

    async def boom(**kwargs):
        del kwargs
        raise RuntimeError("notification down")

    monkeypatch.setattr("app.services.state_machine.send_notification", boom)

    await change_status(
        db_session,
        case_id=case.case_id,
        operation=OperationType.OPEN_DETAIL,
        operator=snapshot,
    )
    await db_session.commit()

    with pytest.raises(RuntimeError):
        await change_status(
            db_session,
            case_id=case.case_id,
            operation=OperationType.REJECT,
            operator=snapshot,
            external_feedback="驳回原因满足长度要求，用于验证事务回滚。",
        )
        await db_session.commit()

    await db_session.rollback()
    await db_session.refresh(case)
    assert case.status == "REVIEWING"

    histories = (
        await db_session.execute(
            select(CaseStatusHistory).where(CaseStatusHistory.case_id == case.case_id)
        )
    ).scalars().all()
    assert len(histories) == 1

    notifications = (await db_session.execute(select(Notification))).scalars().all()
    assert len(notifications) == 0

    audits = (await db_session.execute(select(AuditLog))).scalars().all()
    assert len(audits) == 1


@pytest.mark.asyncio
async def test_change_status_illegal_transition(db_session, state_fixture):
    case = state_fixture["case"]
    snapshot = state_fixture["snapshot"]

    case.status = "HANDLED"
    await db_session.commit()

    with pytest.raises(IllegalStateTransitionError):
        await change_status(
            db_session,
            case_id=case.case_id,
            operation=OperationType.OPEN_DETAIL,
            operator=snapshot,
        )


@pytest.mark.asyncio
async def test_anonymous_report_does_not_notify(db_session, state_fixture):
    snapshot = state_fixture["snapshot"]
    fraud_type = state_fixture["fraud_type"]

    anon_case = FraudCase(
        case_id=3002,
        case_no="2026-CS-003002",
        title="匿名案件",
        description="匿名案件描述文本足够长",
        fraud_type_id=fraud_type.type_id,
        incident_date=date(2026, 5, 2),
        reporter_id=None,
        is_anonymous=True,
        dept_code="CS",
        status="PENDING",
    )
    db_session.add(anon_case)
    await db_session.commit()

    await change_status(
        db_session,
        case_id=anon_case.case_id,
        operation=OperationType.OPEN_DETAIL,
        operator=snapshot,
    )
    await db_session.commit()

    notifications = (await db_session.execute(select(Notification))).scalars().all()
    assert notifications == []
