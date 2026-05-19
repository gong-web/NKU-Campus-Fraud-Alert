from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

import pytest
from sqlalchemy import select

from app.infra.db.models import AggregateAlertLog, FraudCase, FraudType, Notification, Role, User
from app.infra.db.models.department import Department
from app.infra.db.models.user import UserStatus
from app.services.review_service import run_aggregate_alert_check

pytestmark = pytest.mark.unit


@pytest.fixture
async def alert_seed(db_session):
    dept = Department(dept_code="SCHOOL", dept_name="学校", dept_level=1, sort_order=1)
    db_session.add(dept)
    await db_session.flush()

    reviewer_school = Role(role_code="REVIEWER", role_name="校级审核员", role_level=2)
    reviewer_dept = Role(role_code="REVIEWER", role_name="院级审核员", role_level=1)
    db_session.add_all([reviewer_school, reviewer_dept])
    await db_session.flush()

    school_admin_1 = User(
        user_id=4101,
        cas_account="reviewer_school_1",
        real_name="校审一",
        department_id=dept.dept_id,
        role_id=reviewer_school.role_id,
        status=UserStatus.ACTIVE.value,
    )
    school_admin_2 = User(
        user_id=4102,
        cas_account="reviewer_school_2",
        real_name="校审二",
        department_id=dept.dept_id,
        role_id=reviewer_school.role_id,
        status=UserStatus.ACTIVE.value,
    )
    dept_admin = User(
        user_id=4103,
        cas_account="reviewer_dept_1",
        real_name="院审一",
        department_id=dept.dept_id,
        role_id=reviewer_dept.role_id,
        status=UserStatus.ACTIVE.value,
    )
    fraud_type = FraudType(
        type_code="ALERT",
        type_name="聚合测试",
        description="聚合测试类型",
        is_active=True,
        sort_order=1,
    )
    db_session.add_all([school_admin_1, school_admin_2, dept_admin, fraud_type])
    await db_session.flush()

    now = datetime.now(tz=UTC)
    for offset in range(4):
        db_session.add(
            FraudCase(
                case_id=5000 + offset,
                case_no=f"2026-SCHOOL-00{offset:03d}",
                title=f"聚合案件{offset}",
                description="用于聚合告警的测试案件描述",
                fraud_type_id=fraud_type.type_id,
                incident_date=date(2026, 5, 1),
                dept_code="SCHOOL",
                status="PENDING",
                is_anonymous=False,
                created_at=now - timedelta(hours=2),
                updated_at=now - timedelta(hours=2),
            )
        )
    await db_session.commit()
    return {"fraud_type": fraud_type}


@pytest.mark.asyncio
async def test_aggregate_alert_trigger_and_cooldown(db_session, alert_seed):
    del alert_seed

    triggered = await run_aggregate_alert_check()
    assert triggered == 1

    notifications = (await db_session.execute(select(Notification))).scalars().all()
    assert len(notifications) == 2

    logs = (await db_session.execute(select(AggregateAlertLog))).scalars().all()
    assert len(logs) == 1

    triggered_again = await run_aggregate_alert_check()
    assert triggered_again == 0

    notifications_again = (await db_session.execute(select(Notification))).scalars().all()
    assert len(notifications_again) == 2
