"""审核状态机引擎。

核心原则：
- 所有状态变更必须通过本模块，避免 controller / service 各写一套流程。
- 状态历史、主表状态、通知、审计必须在同一事务里原子提交。
- 调用方负责提供并持有事务边界；本函数不主动 commit。
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.user_snapshot import UserSnapshot
from app.exceptions import Conflict, NotFound, ValidationError
from app.infra.db.models import CaseStatusHistory, FraudCase
from app.schemas.state import ALLOWED_TRANSITIONS, OperationType, ReportStatus
from app.services.audit_service import get_audit_service
from app.services.notification_service import send_notification


class IllegalStateTransitionError(Conflict):
    """非法状态转换。"""

    code = 30005
    default_message = "非法状态转换"


async def change_status(
    db: AsyncSession,
    *,
    case_id: int,
    operation: OperationType,
    operator: UserSnapshot,
    external_feedback: str | None = None,
    internal_remark: str | None = None,
) -> CaseStatusHistory:
    """原子状态变更。

    调用方必须在 ``uow()`` 或显式 session 事务内调用本函数。
    任何副作用失败都会向上抛异常，由外层统一回滚。
    """

    result = await db.execute(
        select(FraudCase).where(FraudCase.case_id == case_id).with_for_update()
    )
    report = result.scalar_one_or_none()
    if report is None:
        raise NotFound("案件不存在")

    from_status = ReportStatus(report.status)
    key = (from_status, operation)
    if key not in ALLOWED_TRANSITIONS:
        raise IllegalStateTransitionError(
            f"非法转换：{from_status.value} --[{operation.value}]--> ?"
        )

    to_status = ALLOWED_TRANSITIONS[key]
    _validate_business_rules(
        operation=operation,
        external_feedback=external_feedback,
    )

    now = datetime.now(tz=UTC)
    before_snapshot = {
        "status": from_status.value,
        "reviewer_id": report.reviewer_id,
        "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        "review_note": report.review_note,
    }

    transition = CaseStatusHistory(
        history_id=_next_history_id(db, report.case_id, operator.user_id),
        case_id=report.case_id,
        from_status=from_status.value,
        to_status=to_status.value,
        operator_id=operator.user_id,
        note=external_feedback or internal_remark,
    )
    db.add(transition)
    await db.flush()

    report.status = to_status.value
    if operation == OperationType.OPEN_DETAIL:
        report.reviewer_id = operator.user_id
    if operation in {
        OperationType.RESOLVE,
        OperationType.REJECT,
        OperationType.TRANSFER_POLICE,
    }:
        report.reviewed_at = now
        if internal_remark:
            report.review_note = internal_remark

    await db.flush()

    await _maybe_notify_reporter(
        db=db,
        report=report,
        operation=operation,
        external_feedback=external_feedback,
        to_status=to_status.value,
    )

    after_snapshot = {
        "status": report.status,
        "reviewer_id": report.reviewer_id,
        "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        "review_note": report.review_note,
    }
    await get_audit_service().write(
        operator=operator,
        op_type=f"STATE_CHANGE_{operation.value}",
        obj_type="fraud_case",
        obj_id=str(case_id),
        before=before_snapshot,
        after=after_snapshot
        | {
            "external_feedback": external_feedback,
            "internal_remark": internal_remark,
        },
        sync=True,
        session=db,
    )

    return transition


def _validate_business_rules(
    *,
    operation: OperationType,
    external_feedback: str | None,
) -> None:
    if operation == OperationType.REJECT and not (external_feedback or "").strip():
        raise ValidationError("驳回必须填写对外反馈")
    if operation == OperationType.TRANSFER_POLICE and not (external_feedback or "").strip():
        raise ValidationError("转报警必须填写转报说明")


async def _maybe_notify_reporter(
    *,
    db: AsyncSession,
    report: FraudCase,
    operation: OperationType,
    external_feedback: str | None,
    to_status: str,
) -> None:
    if report.reporter_id is None:
        return

    type_map = {
        OperationType.RESOLVE: "REPORT_RESOLVED",
        OperationType.REJECT: "REPORT_REJECTED",
        OperationType.TRANSFER_POLICE: "REPORT_TRANSFERRED",
    }
    notif_type = type_map.get(operation)
    if notif_type is None:
        return

    await send_notification(
        recipient_id=report.reporter_id,
        type=notif_type,
        title=f"您的上报事件 {report.case_no} 状态已更新",
        content=external_feedback or f"当前状态：{to_status}",
        related_object_type="fraud_case",
        related_object_id=report.case_id,
        db_session=db,
    )


def _next_history_id(db: AsyncSession, case_id: int, operator_id: int) -> int:
    """为状态历史生成稳定主键。

    当前项目统一使用雪花 ID，但本模块又希望尽量保持纯函数式依赖最少。
    这里延迟导入，避免循环依赖。
    """

    del db, case_id, operator_id
    from app.core.snowflake import next_snowflake_id

    return next_snowflake_id()
