"""预警公告服务层（UC-03 / UC-07）。

模块级 ``async`` 函数，事务由 ``async with uow():`` 统一管理。
审计走 ``audit.write(sync=True, session=session)`` 与业务原子提交；
通知走 ``send_notification(... db_session=session)``。
异常一律抛 :mod:`app.exceptions` 自定义类，不抛 ``HTTPException``。

紧急级（``warning_level=3``）业务规则：只允许 **校级** 审核管理员
（``Role.role_level == 2``）发布——从 DB 取登录用户的角色二次校验。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import (
    PermissionDenied,
    WarningInvalidParam,
    WarningNotFound,
    WarningOfflineConflict,
)
from app.infra.db.models import Role, User, WarningNotice
from app.infra.db.models.user import UserStatus
from app.infra.db.models.warning_notice import WarningStatus
from app.infra.db.session import uow
from app.infra.repositories.warning import WarningRepository
from app.schemas.warnings import (
    WarningAppendIn,
    WarningCreateIn,
    WarningListItemOut,
    WarningOfflineIn,
    WarningOut,
)
from app.services.audit_service import get_audit_service
from app.services.notification_service import send_notification

logger = get_logger(__name__)


# ── 对外业务函数 ────────────────────────────────────────────────────


async def publish_warning(
    body: WarningCreateIn,
    *,
    current: UserSnapshot,
) -> WarningOut:
    """发布一条预警（UC-03 步骤 4-6）。"""
    # 入参再次双重校验（即使 schema 已校验，仍兜底防绕过）
    if body.push_scope == "DEPARTMENT" and not body.target_dept_ids:
        raise WarningInvalidParam("按院系推送必须提供 target_dept_ids")

    async with uow() as session:
        # 紧急级仅校级 reviewer 可发
        if body.warning_level == 3:
            await _ensure_school_reviewer(session, current=current)

        repo = WarningRepository(session)
        warning_id = next_snowflake_id()
        now = datetime.now(tz=UTC)
        notice = WarningNotice(
            warning_id=warning_id,
            title=body.title,
            content=body.content,
            warning_level=body.warning_level,
            related_case_no=body.related_case_no,
            publisher_id=current.user_id,
            push_scope=body.push_scope,
            status=WarningStatus.ONLINE,
            published_at=now,
            expires_at=body.expires_at,
        )
        await repo.add(notice)

        target_dept_ids: list[int] = []
        if body.push_scope == "DEPARTMENT":
            target_dept_ids = list(dict.fromkeys(body.target_dept_ids or []))
            await repo.upsert_targets(warning_id=warning_id, dept_ids=target_dept_ids)

        # 推送目标（学生 + ACTIVE）
        recipients = await _resolve_recipients(
            session,
            push_scope=body.push_scope,
            target_dept_ids=target_dept_ids,
        )
        for stu in recipients:
            await send_notification(
                recipient_id=stu.user_id,
                type="WARNING_PUBLISHED",
                title=f"[预警] {body.title}",
                content=body.content[:200],
                related_object_type="warning_notice",
                related_object_id=warning_id,
                db_session=session,
            )

        # 紧急级额外发邮件（基础设施未就绪时仅落日志）
        if body.warning_level == 3:
            await _send_email_for_urgent(
                title=body.title,
                content=body.content,
                recipient_count=len(recipients),
            )

        await get_audit_service().write(
            operator=current,
            op_type="WARNING_PUBLISH",
            obj_type="warning_notice",
            obj_id=str(warning_id),
            after={
                "title": body.title,
                "level": body.warning_level,
                "scope": body.push_scope,
                "target_count": len(target_dept_ids),
                "recipient_count": len(recipients),
            },
            sync=True,
            session=session,
        )

        out = await _build_warning_out(
            session,
            notice=notice,
            current=current,
        )
    logger.info(
        "warning_published",
        warning_id=warning_id,
        level=body.warning_level,
        scope=body.push_scope,
        recipient_count=len(recipients),
        publisher_id=current.user_id,
    )
    return out


async def append_warning(
    warning_id: int,
    body: WarningAppendIn,
    *,
    current: UserSnapshot,
) -> WarningOut:
    """追加后续说明（UC-07 步骤 8）。"""
    async with uow() as session:
        repo = WarningRepository(session)
        notice = await repo.get_by_id(warning_id)
        if notice is None:
            raise WarningNotFound()
        if notice.status != WarningStatus.ONLINE:
            raise WarningOfflineConflict("已下线的预警不可再追加")

        new_appendix = body.appendix.strip()
        notice.appendix = (
            new_appendix
            if not notice.appendix
            else f"{notice.appendix}\n----\n{new_appendix}"
        )
        await session.flush()

        await get_audit_service().write(
            operator=current,
            op_type="WARNING_APPEND",
            obj_type="warning_notice",
            obj_id=str(warning_id),
            after={"appendix_len": len(new_appendix)},
            sync=True,
            session=session,
        )

        out = await _build_warning_out(
            session,
            notice=notice,
            current=current,
        )
    logger.info("warning_appended", warning_id=warning_id, operator_id=current.user_id)
    return out


async def offline_warning(
    warning_id: int,
    body: WarningOfflineIn,
    *,
    current: UserSnapshot,
) -> dict[str, str]:
    """手动下线预警（UC-07 步骤 6）。"""
    async with uow() as session:
        repo = WarningRepository(session)
        notice = await repo.get_by_id(warning_id)
        if notice is None:
            raise WarningNotFound()
        if notice.status != WarningStatus.ONLINE:
            raise WarningOfflineConflict("预警已处于 OFFLINE 状态")

        reason = body.reason.strip()
        notice.status = WarningStatus.OFFLINE
        notice.offline_at = datetime.now(tz=UTC)
        notice.offline_reason = reason
        await session.flush()

        await get_audit_service().write(
            operator=current,
            op_type="WARNING_OFFLINE",
            obj_type="warning_notice",
            obj_id=str(warning_id),
            after={"reason": reason[:120]},
            sync=True,
            session=session,
        )
    logger.info(
        "warning_offlined",
        warning_id=warning_id,
        operator_id=current.user_id,
        reason=reason[:60],
    )
    return {"warning_id": str(warning_id), "status": WarningStatus.OFFLINE}


async def list_warnings_for_student(
    *,
    current: UserSnapshot,
    status: str | None = None,
    level: int | None = None,
    keyword: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[WarningListItemOut], int]:
    """学生侧预警列表（L1，无审计）。"""
    offset = (page - 1) * size
    async with uow() as session:
        repo = WarningRepository(session)
        items, total = await repo.list_published_for_student(
            dept_id=current.department_id,
            status=status,
            level=level,
            keyword=keyword,
            offset=offset,
            limit=size,
        )
        publisher_names = await _resolve_publisher_names(
            session, ids={n.publisher_id for n in items}
        )
        results = [
            WarningListItemOut(
                warning_id=str(n.warning_id),
                title=n.title,
                warning_level=n.warning_level,
                status=n.status,
                push_scope=n.push_scope,
                publisher_name=publisher_names.get(n.publisher_id),
                published_at=n.published_at,
            )
            for n in items
        ]
    return results, total


async def get_warning_for_student(
    warning_id: int,
    *,
    current: UserSnapshot,
) -> WarningOut:
    """学生端查看单条预警（L1，无审计）。

    不可见时一律返回 NotFound，不暴露存在性。
    """
    async with uow() as session:
        repo = WarningRepository(session)
        notice = await repo.get_by_id(warning_id)
        if notice is None:
            raise WarningNotFound()

        # 可见性：FULL_SCHOOL 或 当前用户所在 dept 在 targets
        if notice.push_scope == "DEPARTMENT":
            target_ids = await repo.get_target_dept_ids(warning_id)
            if current.department_id not in set(target_ids):
                raise WarningNotFound()

        out = await _build_warning_out(
            session,
            notice=notice,
            current=current,
        )
    return out


async def list_warnings_for_admin(
    *,
    current: UserSnapshot,
    status: str | None = None,
    level: int | None = None,
    keyword: str | None = None,
    publisher_id: int | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[WarningListItemOut], int]:
    """审核管理员侧预警列表。

    ``current`` 当前未做范围过滤；保留参数为了后续接入按角色 scope 限流。
    """
    _ = current  # 占位以保留接口签名（后续按 scope 限流时改用）
    offset = (page - 1) * size
    async with uow() as session:
        repo = WarningRepository(session)
        items, total = await repo.list_admin(
            status=status,
            level=level,
            keyword=keyword,
            publisher_id=publisher_id,
            offset=offset,
            limit=size,
        )
        publisher_names = await _resolve_publisher_names(
            session, ids={n.publisher_id for n in items}
        )
        results = [
            WarningListItemOut(
                warning_id=str(n.warning_id),
                title=n.title,
                warning_level=n.warning_level,
                status=n.status,
                push_scope=n.push_scope,
                publisher_name=publisher_names.get(n.publisher_id),
                published_at=n.published_at,
            )
            for n in items
        ]
    return results, total


async def get_warning_for_admin(
    warning_id: int,
    *,
    current: UserSnapshot,
) -> WarningOut:
    """审核管理员查看预警详情。"""
    async with uow() as session:
        repo = WarningRepository(session)
        notice = await repo.get_by_id(warning_id)
        if notice is None:
            raise WarningNotFound()
        out = await _build_warning_out(
            session,
            notice=notice,
            current=current,
        )
    return out


# ── 内部工具 ────────────────────────────────────────────────────────


async def _ensure_school_reviewer(
    session: AsyncSession, *, current: UserSnapshot
) -> None:
    """紧急预警仅校级（``Role.role_level == 2``）reviewer 可发布。"""
    role = await session.get(Role, current.role_id)
    if role is None:
        raise PermissionDenied("角色信息缺失")
    if not (role.role_code == "REVIEWER" and role.role_level == 2):
        raise PermissionDenied("紧急预警仅校级管理员可发")


async def _resolve_recipients(
    session: AsyncSession,
    *,
    push_scope: str,
    target_dept_ids: list[int],
) -> list[User]:
    """根据推送范围解析收件人（仅在线的学生）。"""
    stmt = (
        select(User)
        .join(Role, Role.role_id == User.role_id)
        .where(
            Role.role_code == "STUDENT",
            User.status == UserStatus.ACTIVE.value,
        )
    )
    if push_scope == "DEPARTMENT":
        if not target_dept_ids:
            return []
        stmt = stmt.where(User.department_id.in_(target_dept_ids))
    rows = (await session.execute(stmt)).scalars().all()
    return list(rows)


async def _resolve_publisher_names(
    session: AsyncSession, *, ids: set[int]
) -> dict[int, str]:
    if not ids:
        return {}
    rows = (
        await session.execute(
            select(User.user_id, User.real_name).where(User.user_id.in_(ids))
        )
    ).all()
    return {int(r.user_id): r.real_name for r in rows}


async def _build_warning_out(
    session: AsyncSession,
    *,
    notice: WarningNotice,
    current: UserSnapshot,
) -> WarningOut:
    """把 ORM ``WarningNotice`` 装配成 ``WarningOut``。"""
    _ = current  # 保留入参以便后续按角色裁剪字段
    repo = WarningRepository(session)
    publisher_names = await _resolve_publisher_names(
        session, ids={notice.publisher_id}
    )
    target_dept_ids: list[int] = []
    if notice.push_scope == "DEPARTMENT":
        target_dept_ids = await repo.get_target_dept_ids(notice.warning_id)

    return WarningOut(
        warning_id=str(notice.warning_id),
        title=notice.title,
        content=notice.content,
        warning_level=notice.warning_level,
        push_scope=notice.push_scope,
        publisher_id=str(notice.publisher_id),
        publisher_name=publisher_names.get(notice.publisher_id),
        target_dept_ids=target_dept_ids,
        status=notice.status,
        appendix=notice.appendix,
        related_case_no=notice.related_case_no,
        published_at=notice.published_at,
        expires_at=notice.expires_at,
        offline_at=notice.offline_at,
        offline_reason=notice.offline_reason,
    )


async def _send_email_for_urgent(
    *, title: str, content: str, recipient_count: int
) -> None:
    """紧急预警邮件发送占位。

    真实邮件通道（SMTP / SendGrid 等）由基础设施组后续补；当前仅
    打 INFO 日志，便于运行期可观测。
    """
    logger.info(
        "email_skipped_in_dev",
        title=title[:60],
        content_len=len(content),
        recipient_count=recipient_count,
    )
