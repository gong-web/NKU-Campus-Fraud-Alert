"""审核中段业务服务。"""

from __future__ import annotations

import base64
from collections import defaultdict
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import Select, and_, desc, func, or_, select

from app.core.logging import get_logger
from app.core.security import decrypt_field
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import Conflict, NotFound, PermissionDenied, ValidationError
from app.infra.db.models import (
    AggregateAlertLog,
    AnonymousDecryptLog,
    CaseAnonymousReporter,
    CaseStatusHistory,
    Department,
    EvidenceFile,
    FraudCase,
    FraudType,
    Role,
    User,
)
from app.infra.db.models.user import UserStatus
from app.infra.db.session import uow
from app.schemas.reports import (
    AdminReportDetailOut,
    AdminReportListItemOut,
    AdminReportListQuery,
    AnonymousDecryptOut,
    ContactInfoOut,
    DashboardSummaryOut,
    DashboardTrendPointOut,
    EvidenceAccessOut,
    EvidenceFileOut,
    RecentActionOut,
    ReporterSummaryOut,
    ReviewerSummaryOut,
    StatusHistoryOut,
)
from app.schemas.state import OperationType
from app.services.audit_service import get_audit_service
from app.services.knowledge_service import create_knowledge_draft_from_report
from app.services.notification_service import send_notification
from app.services.state_machine import IllegalStateTransitionError, change_status
from app.services.storage_service import read_evidence_file

logger = get_logger(__name__)


class SensitiveAccessPreconditionFailed(ValidationError):
    code = 30006
    http_status = 412
    default_message = "缺少敏感访问确认"


async def list_admin_reports(
    *,
    current: UserSnapshot,
    query: AdminReportListQuery,
) -> tuple[list[AdminReportListItemOut], int]:
    async with uow() as session:
        scope = await _get_access_scope(session, current)
        filters = _build_admin_filters(query, scope)

        stmt = (
            select(
                FraudCase.case_id,
                FraudCase.case_no,
                FraudCase.fraud_type_id,
                FraudType.type_name,
                FraudCase.title,
                FraudCase.amount,
                FraudCase.status,
                FraudCase.created_at,
                FraudCase.is_anonymous,
                func.count(EvidenceFile.file_id).label("evidence_count"),
            )
            .join(FraudType, FraudType.type_id == FraudCase.fraud_type_id)
            .outerjoin(EvidenceFile, EvidenceFile.case_id == FraudCase.case_id)
            .where(*filters)
            .group_by(
                FraudCase.case_id,
                FraudCase.case_no,
                FraudCase.fraud_type_id,
                FraudType.type_name,
                FraudCase.title,
                FraudCase.amount,
                FraudCase.status,
                FraudCase.created_at,
                FraudCase.is_anonymous,
            )
        )

        count_stmt = select(func.count()).select_from(select(FraudCase.case_id).where(*filters).subquery())
        total = int((await session.execute(count_stmt)).scalar_one())

        if query.sort == "amount_desc":
            stmt = stmt.order_by(desc(FraudCase.amount), desc(FraudCase.created_at))
        else:
            stmt = stmt.order_by(desc(FraudCase.created_at))

        offset = (query.page - 1) * query.size
        rows = (await session.execute(stmt.offset(offset).limit(query.size))).all()

        items = [
            AdminReportListItemOut(
                case_id=row.case_id,
                case_no=row.case_no,
                fraud_type_id=row.fraud_type_id,
                fraud_type_name=row.type_name,
                title=row.title,
                amount=row.amount,
                status=row.status,
                created_at=row.created_at,
                is_anonymous=row.is_anonymous,
                evidence_count=int(row.evidence_count or 0),
            )
            for row in rows
        ]
        return items, total


async def get_admin_report_detail(
    *,
    case_id: int,
    current: UserSnapshot,
) -> AdminReportDetailOut:
    async with uow() as session:
        report = await _get_case_or_404(session, case_id)
        await _ensure_report_access(session, current, report)

        if report.status == "PENDING":
            try:
                await change_status(
                    session,
                    case_id=case_id,
                    operation=OperationType.OPEN_DETAIL,
                    operator=current,
                )
            except IllegalStateTransitionError:
                logger.info("report_detail_race_lost", case_id=case_id, user_id=current.user_id)

        detail = await _assemble_admin_report_detail(session, report.case_id)
        await get_audit_service().write(
            operator=current,
            op_type="REPORT_DETAIL_VIEW",
            obj_type="fraud_case",
            obj_id=str(case_id),
            after={"status": detail.status},
            sync=True,
            session=session,
        )
        return detail


async def resolve_report(
    *,
    case_id: int,
    current: UserSnapshot,
    desensitized_summary: str,
    identification_points: str,
    prevention_advice: str,
    internal_remark: str | None,
) -> dict[str, int | str]:
    async with uow() as session:
        report = await _get_case_or_404(session, case_id, for_update=True)
        await _ensure_report_access(session, current, report)
        if report.status != "REVIEWING":
            raise Conflict("仅审核中的案件可录入案例库")

        entry_id = await create_knowledge_draft_from_report(
            report_id=report.case_id,
            desensitized_summary=desensitized_summary,
            identification_points=identification_points,
            prevention_advice=prevention_advice,
            fraud_type_id=report.fraud_type_id,
            author_id=current.user_id,
            db_session=session,
        )
        await change_status(
            session,
            case_id=case_id,
            operation=OperationType.RESOLVE,
            operator=current,
            external_feedback="您的上报已处理完毕，感谢您的反馈。",
            internal_remark=internal_remark,
        )
        return {"entry_id": entry_id, "status": "HANDLED"}


async def reject_report(
    *,
    case_id: int,
    current: UserSnapshot,
    reason: str,
    internal_remark: str | None,
) -> dict[str, str]:
    async with uow() as session:
        report = await _get_case_or_404(session, case_id)
        await _ensure_report_access(session, current, report)
        await change_status(
            session,
            case_id=case_id,
            operation=OperationType.REJECT,
            operator=current,
            external_feedback=reason,
            internal_remark=internal_remark,
        )
        return {"status": "REJECTED"}


async def transfer_report(
    *,
    case_id: int,
    current: UserSnapshot,
    transfer_note: str,
    internal_remark: str | None,
) -> dict[str, str]:
    async with uow() as session:
        report = await _get_case_or_404(session, case_id)
        await _ensure_report_access(session, current, report)
        await change_status(
            session,
            case_id=case_id,
            operation=OperationType.TRANSFER_POLICE,
            operator=current,
            external_feedback=transfer_note,
            internal_remark=internal_remark,
        )
        return {"status": "REPORTED"}


async def contact_reporter(
    *,
    case_id: int,
    current: UserSnapshot,
) -> ContactInfoOut:
    async with uow() as session:
        report = await _get_case_or_404(session, case_id)
        await _ensure_report_access(session, current, report)
        if report.is_anonymous:
            raise PermissionDenied("匿名上报者联系方式不可见，如确需联系，请走司法协助流程")
        if report.reporter_id is None:
            raise NotFound("案件缺少上报人信息")

        reporter = await session.get(User, report.reporter_id)
        if reporter is None:
            raise NotFound("上报人不存在")

        await get_audit_service().write(
            operator=current,
            op_type="VIEW_CONTACT_INFO",
            obj_type="fraud_case",
            obj_id=str(case_id),
            after={"reporter_id": reporter.user_id},
            sync=True,
            session=session,
        )
        return ContactInfoOut(phone=reporter.phone_encrypted, email=reporter.email_encrypted)


async def view_evidence(
    *,
    case_id: int,
    file_id: int,
    current: UserSnapshot,
    confirmed: bool,
) -> EvidenceAccessOut:
    if not confirmed:
        raise SensitiveAccessPreconditionFailed("查看证据前必须完成二次确认")

    async with uow() as session:
        report = await _get_case_or_404(session, case_id)
        await _ensure_report_access(session, current, report)

        ev = await session.get(EvidenceFile, file_id)
        if ev is None or ev.case_id != case_id:
            raise NotFound("证据文件不存在")

        content = await read_evidence_file(ev.storage_path)
        await get_audit_service().write(
            operator=current,
            op_type="VIEW_EVIDENCE",
            obj_type="evidence_file",
            obj_id=str(file_id),
            after={"case_id": case_id},
            sync=True,
            session=session,
        )
        return EvidenceAccessOut(
            file_id=ev.file_id,
            original_name=ev.original_name,
            mime_type=ev.mime_type,
            content_base64=base64.b64encode(content).decode("ascii"),
        )


async def decrypt_anonymous_reporter(
    *,
    case_id: int,
    current: UserSnapshot,
    reason: str,
    approver_id: int | None,
) -> AnonymousDecryptOut:
    if not current.is_sysadmin:
        raise PermissionDenied("仅系统管理员可解密匿名身份")

    async with uow() as session:
        report = await _get_case_or_404(session, case_id)
        if not report.is_anonymous:
            raise ValidationError("该案件不是匿名上报")

        mapping_stmt = select(CaseAnonymousReporter).where(CaseAnonymousReporter.case_id == case_id)
        mapping = (await session.execute(mapping_stmt)).scalar_one_or_none()
        if mapping is None:
            raise NotFound("匿名映射不存在")

        try:
            reporter_id = int(decrypt_field(mapping.reporter_user_id_enc).decode("utf-8"))
        except ValueError as exc:
            raise ValidationError("匿名映射数据损坏") from exc

        reporter = await session.get(User, reporter_id)
        if reporter is None:
            raise NotFound("匿名上报者不存在")

        now = datetime.now(tz=UTC)
        expires_at = now + timedelta(minutes=5)
        audit_log_id = await get_audit_service().write(
            operator=current,
            op_type="DECRYPT_ANONYMOUS",
            obj_type="fraud_case",
            obj_id=str(case_id),
            after={"reason": reason, "reporter_id": reporter_id},
            sync=True,
            session=session,
        )
        assert audit_log_id is not None

        session.add(
            AnonymousDecryptLog(
                decrypt_log_id=next_snowflake_id(),
                report_id=case_id,
                requester_id=current.user_id,
                approver_id=approver_id,
                judicial_doc_no=f"ADMIN-{case_id}",
                reason=reason,
                related_case_no=report.case_no,
                expires_at=expires_at,
                audit_log_id=audit_log_id,
            )
        )

        admins = await _list_sys_admins(session)
        for admin in admins:
            await send_notification(
                recipient_id=admin.user_id,
                type="ANONYMOUS_DECRYPT_ALERT",
                title="敏感操作告警：匿名身份解密",
                content=f"{current.real_name} 解密了案件 {report.case_no} 的匿名身份，原因：{reason}",
                related_object_type="fraud_case",
                related_object_id=case_id,
                db_session=session,
            )

        return AnonymousDecryptOut(
            case_id=case_id,
            user_id=reporter.user_id,
            real_name=reporter.real_name,
            cas_account=reporter.cas_account,
            phone=reporter.phone_encrypted,
            email=reporter.email_encrypted,
            expires_at=expires_at,
        )


async def get_dashboard_summary(*, current: UserSnapshot) -> DashboardSummaryOut:
    async with uow() as session:
        scope = await _get_access_scope(session, current)
        filters = _scope_filters(scope)

        today_start = datetime.now(tz=UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        pending_count = await _scalar_count(
            session, select(func.count()).select_from(FraudCase).where(*filters, FraudCase.status == "PENDING")
        )
        reviewing_count = await _scalar_count(
            session,
            select(func.count()).select_from(FraudCase).where(*filters, FraudCase.status == "REVIEWING"),
        )

        today_handled = await _status_history_count(session, current, "HANDLED", today_start)
        today_rejected = await _status_history_count(session, current, "REJECTED", today_start)
        today_reported = await _status_history_count(session, current, "REPORTED", today_start)

        trend_rows = (
            await session.execute(
                select(
                    func.date(FraudCase.created_at).label("day"),
                    func.count().label("submitted"),
                )
                .where(
                    *filters,
                    FraudCase.created_at >= today_start - timedelta(days=6),
                )
                .group_by(func.date(FraudCase.created_at))
            )
        ).all()
        submitted_map = {str(row.day): int(row.submitted) for row in trend_rows}

        handled_rows = (
            await session.execute(
                select(
                    func.date(CaseStatusHistory.created_at).label("day"),
                    func.count().label("handled"),
                )
                .join(FraudCase, FraudCase.case_id == CaseStatusHistory.case_id)
                .where(
                    *_scope_filters(scope),
                    CaseStatusHistory.to_status == "HANDLED",
                    CaseStatusHistory.created_at >= today_start - timedelta(days=6),
                )
                .group_by(func.date(CaseStatusHistory.created_at))
            )
        ).all()
        handled_map = {str(row.day): int(row.handled) for row in handled_rows}

        trend = []
        for days_ago in range(6, -1, -1):
            day = (today_start - timedelta(days=days_ago)).date().isoformat()
            trend.append(
                DashboardTrendPointOut(
                    date=day,
                    submitted=submitted_map.get(day, 0),
                    handled=handled_map.get(day, 0),
                )
            )

        recent_rows = (
            await session.execute(
                select(CaseStatusHistory, FraudCase.case_no)
                .join(FraudCase, FraudCase.case_id == CaseStatusHistory.case_id)
                .where(CaseStatusHistory.operator_id == current.user_id)
                .order_by(desc(CaseStatusHistory.created_at))
                .limit(5)
            )
        ).all()
        recent = [
            RecentActionOut(
                case_id=row.CaseStatusHistory.case_id,
                case_no=row.case_no,
                to_status=row.CaseStatusHistory.to_status,
                note=row.CaseStatusHistory.note,
                created_at=row.CaseStatusHistory.created_at,
            )
            for row in recent_rows
        ]

        return DashboardSummaryOut(
            pending_count=pending_count,
            reviewing_count=reviewing_count,
            today_handled=today_handled,
            today_rejected=today_rejected,
            today_reported=today_reported,
            trend_7days=trend,
            my_recent_actions=recent,
        )


async def count_recent_reports_by_type(*, hours: int) -> dict[int, int]:
    cutoff = datetime.now(tz=UTC) - timedelta(hours=hours)
    async with uow() as session:
        rows = (
            await session.execute(
                select(FraudCase.fraud_type_id, func.count().label("cnt"))
                .where(FraudCase.created_at >= cutoff)
                .group_by(FraudCase.fraud_type_id)
            )
        ).all()
        return {int(row.fraud_type_id): int(row.cnt) for row in rows}


async def get_report_by_case_no(*, case_no: str) -> FraudCase | None:
    async with uow() as session:
        return (await session.execute(select(FraudCase).where(FraudCase.case_no == case_no))).scalar_one_or_none()


async def run_aggregate_alert_check() -> int:
    now = datetime.now(tz=UTC)
    cutoff = now - timedelta(hours=24)
    cooldown_cutoff = now - timedelta(hours=12)

    async with uow() as session:
        rows = (
            await session.execute(
                select(FraudCase.fraud_type_id, func.count().label("cnt"))
                .where(FraudCase.created_at >= cutoff)
                .group_by(FraudCase.fraud_type_id)
                .having(func.count() > 3)
            )
        ).all()
        if not rows:
            return 0

        school_reviewers = await _list_school_reviewers(session)
        triggered = 0
        for row in rows:
            recent_alert = (
                await session.execute(
                    select(AggregateAlertLog)
                    .where(AggregateAlertLog.fraud_type_id == row.fraud_type_id)
                    .where(AggregateAlertLog.alerted_at >= cooldown_cutoff)
                )
            ).scalar_one_or_none()
            if recent_alert is not None:
                continue

            fraud_type = await session.get(FraudType, row.fraud_type_id)
            type_name = fraud_type.type_name if fraud_type else f"类型 {row.fraud_type_id}"
            for reviewer in school_reviewers:
                await send_notification(
                    recipient_id=reviewer.user_id,
                    type="AGGREGATE_ALERT",
                    title=f"聚合告警：{type_name} 上报激增",
                    content=f"过去 24 小时内已收到 {int(row.cnt)} 条同类上报，建议尽快发布预警。",
                    related_object_type="fraud_type",
                    related_object_id=int(row.fraud_type_id),
                    db_session=session,
                )
            await get_audit_service().write(
                operator=_system_operator(),
                op_type="AGGREGATE_ALERT_TRIGGERED",
                obj_type="fraud_type",
                obj_id=str(row.fraud_type_id),
                after={"count": int(row.cnt)},
                sync=True,
                session=session,
            )
            session.add(
                AggregateAlertLog(
                    alert_log_id=next_snowflake_id(),
                    fraud_type_id=int(row.fraud_type_id),
                    report_count=int(row.cnt),
                    notified_admin_count=len(school_reviewers),
                    alerted_at=now,
                )
            )
            triggered += 1
        return triggered


async def _assemble_admin_report_detail(session, case_id: int) -> AdminReportDetailOut:
    report = await _get_case_or_404(session, case_id)
    fraud_type = await session.get(FraudType, report.fraud_type_id)
    reviewer = await session.get(User, report.reviewer_id) if report.reviewer_id else None
    reporter = await session.get(User, report.reporter_id) if report.reporter_id else None
    evidence_rows = (
        await session.execute(
            select(EvidenceFile).where(EvidenceFile.case_id == case_id).order_by(EvidenceFile.uploaded_at)
        )
    ).scalars().all()
    history_rows = (
        await session.execute(
            select(CaseStatusHistory)
            .where(CaseStatusHistory.case_id == case_id)
            .order_by(CaseStatusHistory.created_at)
        )
    ).scalars().all()

    return AdminReportDetailOut(
        case_id=report.case_id,
        case_no=report.case_no,
        title=report.title,
        description=report.description,
        fraud_type_id=report.fraud_type_id,
        fraud_type_name=fraud_type.type_name if fraud_type else None,
        incident_date=report.incident_date,
        amount=report.amount,
        fraud_method=report.fraud_method,
        contact_way=report.contact_way,
        created_at=report.created_at,
        updated_at=report.updated_at,
        status=report.status,
        is_anonymous=report.is_anonymous,
        dept_code=report.dept_code,
        review_note=report.review_note,
        reviewed_at=report.reviewed_at,
        reviewer=ReviewerSummaryOut(user_id=reviewer.user_id, real_name=reviewer.real_name)
        if reviewer
        else None,
        reporter=None
        if report.is_anonymous or reporter is None
        else ReporterSummaryOut(
            user_id=reporter.user_id,
            real_name=reporter.real_name,
            cas_account=reporter.cas_account,
            department_id=reporter.department_id,
        ),
        evidence_list=[EvidenceFileOut.model_validate(ev) for ev in evidence_rows],
        history=[StatusHistoryOut.model_validate(row) for row in history_rows],
    )


def _build_admin_filters(query: AdminReportListQuery, scope: dict[str, Any]) -> list[Any]:
    filters = _scope_filters(scope)
    if query.statuses:
        filters.append(FraudCase.status.in_(query.statuses))
    if query.fraud_type_id is not None:
        filters.append(FraudCase.fraud_type_id == query.fraud_type_id)
    if query.date_from is not None:
        filters.append(FraudCase.incident_date >= query.date_from)
    if query.date_to is not None:
        filters.append(FraudCase.incident_date <= query.date_to)
    if query.amount_min is not None:
        filters.append(FraudCase.amount >= query.amount_min)
    if query.amount_max is not None:
        filters.append(FraudCase.amount <= query.amount_max)
    if query.keyword:
        filters.append(FraudCase.title.ilike(f"%{query.keyword.strip()}%"))
    return filters


async def _get_access_scope(session, current: UserSnapshot) -> dict[str, Any]:
    role = await session.get(Role, current.role_id)
    if role is None:
        raise PermissionDenied("角色不存在")
    department = await session.get(Department, current.department_id)
    dept_code = department.dept_code if department else None
    return {"role_code": role.role_code, "role_level": role.role_level, "dept_code": dept_code}


def _scope_filters(scope: dict[str, Any]) -> list[Any]:
    if scope["role_code"] == "REVIEWER" and scope["role_level"] == 1 and scope["dept_code"]:
        return [FraudCase.dept_code == scope["dept_code"]]
    return []


async def _ensure_report_access(session, current: UserSnapshot, report: FraudCase) -> None:
    scope = await _get_access_scope(session, current)
    if scope["role_code"] == "REVIEWER" and scope["role_level"] == 1 and scope["dept_code"]:
        if report.dept_code != scope["dept_code"]:
            raise PermissionDenied("院系级审核员只能查看本院系案件")


async def _get_case_or_404(session, case_id: int, *, for_update: bool = False) -> FraudCase:
    stmt: Select[Any] = select(FraudCase).where(FraudCase.case_id == case_id)
    if for_update:
        stmt = stmt.with_for_update()
    report = (await session.execute(stmt)).scalar_one_or_none()
    if report is None:
        raise NotFound("案件不存在")
    return report


async def _status_history_count(session, current: UserSnapshot, status: str, since: datetime) -> int:
    scope = await _get_access_scope(session, current)
    stmt = (
        select(func.count())
        .select_from(CaseStatusHistory)
        .join(FraudCase, FraudCase.case_id == CaseStatusHistory.case_id)
        .where(*_scope_filters(scope), CaseStatusHistory.to_status == status, CaseStatusHistory.created_at >= since)
    )
    return await _scalar_count(session, stmt)


async def _scalar_count(session, stmt) -> int:
    return int((await session.execute(stmt)).scalar_one() or 0)


async def _list_sys_admins(session) -> list[User]:
    return (
        await session.execute(
            select(User)
            .join(Role, Role.role_id == User.role_id)
            .where(Role.role_code == "SYS_ADMIN", User.status == UserStatus.ACTIVE.value)
        )
    ).scalars().all()


async def _list_school_reviewers(session) -> list[User]:
    return (
        await session.execute(
            select(User)
            .join(Role, Role.role_id == User.role_id)
            .where(
                Role.role_code == "REVIEWER",
                Role.role_level == 2,
                User.status == UserStatus.ACTIVE.value,
            )
        )
    ).scalars().all()


def _system_operator() -> UserSnapshot:
    return UserSnapshot(
        user_id=0,
        cas_account="system",
        real_name="系统任务",
        role_id=0,
        role_code="SYS_ADMIN",
        department_id=0,
        session_id="scheduler",
        source_ip="127.0.0.1",
        user_agent="scheduler",
    )
