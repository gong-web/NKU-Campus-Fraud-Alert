"""单元：预警状态机直接调用（不上 HTTP client）。

直接构造 ``WarningNotice`` 后写库，再调用 service 函数验证：
- 已 OFFLINE 的预警 append → 抛 :class:`WarningOfflineConflict`
- 已 OFFLINE 的预警再 offline → 抛 :class:`WarningOfflineConflict`
- 不存在的 warning_id append/offline → 抛 :class:`WarningNotFound`
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.domain.user_snapshot import UserSnapshot
from app.exceptions import WarningNotFound, WarningOfflineConflict
from app.infra.db.models import Department, Role, User, WarningNotice
from app.infra.db.models.user import UserStatus
from app.infra.db.models.warning_notice import WarningStatus
from app.infra.db.session import uow
from app.schemas.warnings import WarningAppendIn, WarningOfflineIn
from app.services.warning_service import append_warning, offline_warning

pytestmark = pytest.mark.unit


@pytest.fixture
async def warning_state_fixture(db_session):
    """seed 一个 ONLINE 与一个 OFFLINE 预警 + 一个校级 reviewer。"""
    dept = Department(
        dept_code="CS", dept_name="计算机学院", dept_level=1, sort_order=1
    )
    db_session.add(dept)
    await db_session.flush()

    school_role = Role(role_code="REVIEWER", role_name="校级审核员", role_level=2)
    db_session.add(school_role)
    await db_session.flush()

    reviewer = User(
        user_id=7001,
        cas_account="reviewer_state_school",
        real_name="校级审核员",
        department_id=dept.dept_id,
        role_id=school_role.role_id,
        status=UserStatus.ACTIVE.value,
    )
    db_session.add(reviewer)
    await db_session.flush()

    now = datetime.now(tz=UTC)
    online_w = WarningNotice(
        warning_id=70001,
        title="ONLINE 预警",
        content="测试用 ONLINE 预警正文足够十字以上。",
        warning_level=1,
        publisher_id=reviewer.user_id,
        push_scope="FULL_SCHOOL",
        status=WarningStatus.ONLINE,
        published_at=now,
    )
    offline_w = WarningNotice(
        warning_id=70002,
        title="OFFLINE 预警",
        content="测试用 OFFLINE 预警正文足够十字以上。",
        warning_level=1,
        publisher_id=reviewer.user_id,
        push_scope="FULL_SCHOOL",
        status=WarningStatus.OFFLINE,
        published_at=now,
        offline_at=now,
        offline_reason="原案件已澄清",
    )
    db_session.add_all([online_w, offline_w])
    await db_session.commit()

    snapshot = UserSnapshot(
        user_id=reviewer.user_id,
        cas_account=reviewer.cas_account,
        real_name=reviewer.real_name,
        role_id=school_role.role_id,
        role_code="REVIEWER",
        department_id=dept.dept_id,
        session_id="unit-test-session",
        source_ip="127.0.0.1",
        user_agent="pytest",
    )
    return {
        "snapshot": snapshot,
        "online_id": online_w.warning_id,
        "offline_id": offline_w.warning_id,
    }


@pytest.mark.asyncio
async def test_append_on_offline_raises_conflict(warning_state_fixture) -> None:
    """append 在 OFFLINE 时抛 WarningOfflineConflict。"""
    snap = warning_state_fixture["snapshot"]
    offline_id = warning_state_fixture["offline_id"]

    with pytest.raises(WarningOfflineConflict):
        await append_warning(
            offline_id,
            WarningAppendIn(appendix="尝试在已下线预警追加内容应失败"),
            current=snap,
        )


@pytest.mark.asyncio
async def test_offline_on_already_offline_raises_conflict(
    warning_state_fixture,
) -> None:
    """已 OFFLINE 的预警再次 offline 抛 WarningOfflineConflict。"""
    snap = warning_state_fixture["snapshot"]
    offline_id = warning_state_fixture["offline_id"]

    with pytest.raises(WarningOfflineConflict):
        await offline_warning(
            offline_id,
            WarningOfflineIn(reason="重复下线应失败"),
            current=snap,
        )


@pytest.mark.asyncio
async def test_append_missing_warning_raises_not_found(
    warning_state_fixture,
) -> None:
    """不存在的 warning_id 调 append → WarningNotFound。"""
    snap = warning_state_fixture["snapshot"]
    with pytest.raises(WarningNotFound):
        await append_warning(
            999999,
            WarningAppendIn(appendix="不存在的预警追加应抛 NotFound"),
            current=snap,
        )


@pytest.mark.asyncio
async def test_offline_missing_warning_raises_not_found(
    warning_state_fixture,
) -> None:
    """不存在的 warning_id 调 offline → WarningNotFound。"""
    snap = warning_state_fixture["snapshot"]
    with pytest.raises(WarningNotFound):
        await offline_warning(
            999999,
            WarningOfflineIn(reason="不存在的预警下线应抛 NotFound"),
            current=snap,
        )


@pytest.mark.asyncio
async def test_append_on_online_concats_separator(
    warning_state_fixture,
) -> None:
    """ONLINE 预警追加正常工作；连续两次追加应以 ``\\n----\\n`` 拼接。"""
    snap = warning_state_fixture["snapshot"]
    online_id = warning_state_fixture["online_id"]

    out1 = await append_warning(
        online_id,
        WarningAppendIn(appendix="第一次追加：嫌疑人已被控制"),
        current=snap,
    )
    assert out1.appendix is not None
    assert "第一次追加" in out1.appendix

    out2 = await append_warning(
        online_id,
        WarningAppendIn(appendix="第二次追加：案件正式立案"),
        current=snap,
    )
    assert out2.appendix is not None
    assert "第一次追加" in out2.appendix
    assert "第二次追加" in out2.appendix
    assert "\n----\n" in out2.appendix

    # 验证库里也确实持久化了
    async with uow() as session:
        ref = await session.get(WarningNotice, online_id)
        assert ref is not None
        assert ref.appendix is not None
        assert "第二次追加" in ref.appendix
