"""知识库条目业务服务（UC-04 / UC-08）。

风格与 ``review_service.py`` / ``report_service.py`` 一致：模块级 ``async``
函数、事务由 ``async with uow():`` 统一管理；审计走
``audit.write(sync=True, session=session)`` 与业务原子提交；通知走
``send_notification(... db_session=session)``。异常一律抛
:mod:`app.exceptions` 自定义类，不抛 ``HTTPException``。

状态机
------
::

    DRAFT --submit--> PENDING --approve--> PUBLISHED --offline--> OFFLINE
                                  |--reject--> DRAFT
    PUBLISHED --update(校级)--> PUBLISHED  (version+=1, 不变状态)

每一次状态变更或正文更新都会同事务追加一条
:class:`KnowledgeEntryHistory`（``content_snapshot=entry.to_dict()``）。
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import (
    KnowledgeIllegalTransition,
    KnowledgeNotFound,
    PermissionDenied,
    ValidationError,
)
from app.infra.db.models import (
    FraudType,
    KnowledgeDraft,
    KnowledgeEntry,
    KnowledgeEntryHistory,
    Role,
    User,
)
from app.infra.db.models.knowledge_entry import KnowledgeEntryStatus
from app.infra.db.models.knowledge_entry_history import KnowledgeEntryHistoryAction
from app.infra.db.models.user import UserStatus
from app.infra.db.session import uow
from app.infra.repositories.knowledge import KnowledgeRepository
from app.schemas.knowledge import (
    KnowledgeCreateIn,
    KnowledgeDetailOut,
    KnowledgeListItemOut,
    KnowledgeOfflineIn,
    KnowledgeOut,
    KnowledgeReviewIn,
    KnowledgeUpdateIn,
)
from app.services.audit_service import get_audit_service
from app.services.notification_service import send_notification

logger = get_logger(__name__)


# ── 对外业务函数 ────────────────────────────────────────────────────


async def create_entry(
    body: KnowledgeCreateIn,
    *,
    current: UserSnapshot,
) -> KnowledgeOut:
    """新建知识库条目。

    - 院系 reviewer（``role_level=1``）创建：``DRAFT`` 状态，需提交校级审核。
    - 校级 reviewer（``role_level=2``）创建：直接 ``PUBLISHED``，自动跳过审核
      （PRD UC-08 — 校方拥有最终发布权，毋须再走自审流程）。
    """
    async with uow() as session:
        await _ensure_fraud_type_exists(session, body.fraud_type_id)

        is_school = await _is_school_reviewer(session, current)
        now = datetime.now(tz=UTC)

        repo = KnowledgeRepository(session)
        entry = KnowledgeEntry(
            entry_id=next_snowflake_id(),
            title=body.title,
            fraud_type_id=body.fraud_type_id,
            desensitized_summary=body.desensitized_summary,
            identification_points=body.identification_points,
            prevention_advice=body.prevention_advice,
            peak_periods=body.peak_periods,
            source_type=body.source_type,
            source_reference=body.source_reference,
            status=KnowledgeEntryStatus.PUBLISHED if is_school else KnowledgeEntryStatus.DRAFT,
            version=1,
            author_id=current.user_id,
            reviewer_id=current.user_id if is_school else None,
            review_note=None,
            source_draft_id=None,
            published_at=now if is_school else None,
        )
        await repo.add_entry(entry)

        await _append_history(
            session,
            entry=entry,
            action=KnowledgeEntryHistoryAction.CREATE,
            modified_by=current.user_id,
        )
        if is_school:
            # 校级直发：补一条 APPROVE 历史，使审计链与「DRAFT→PENDING→PUBLISHED」等价
            await _append_history(
                session,
                entry=entry,
                action=KnowledgeEntryHistoryAction.APPROVE,
                modified_by=current.user_id,
            )

        await get_audit_service().write(
            operator=current,
            op_type="KB_PUBLISH_DIRECT" if is_school else "KB_DRAFT_CREATE",
            obj_type="knowledge_entry",
            obj_id=str(entry.entry_id),
            after={"title": entry.title, "status": entry.status, "version": entry.version},
            sync=True,
            session=session,
        )

        out = await _build_entry_out(session, entry)
    logger.info(
        "kb_entry_created",
        entry_id=entry.entry_id,
        author_id=current.user_id,
        fraud_type_id=entry.fraud_type_id,
    )
    return out


async def submit_entry(entry_id: int, *, current: UserSnapshot) -> KnowledgeOut:
    """提交审核：DRAFT → PENDING。"""
    async with uow() as session:
        repo = KnowledgeRepository(session)
        entry = await _get_entry_or_404(repo, entry_id)

        # 校级 reviewer 可代为提交（运营场景），其它角色只能提交自己的
        is_school_reviewer = await _is_school_reviewer(session, current)
        if not is_school_reviewer and entry.author_id != current.user_id:
            raise PermissionDenied("仅作者本人或校级审核员可提交审核")

        _ensure_can_transition(entry.status, KnowledgeEntryStatus.PENDING)

        entry.status = KnowledgeEntryStatus.PENDING
        await session.flush()

        # 通知所有校级 reviewer
        reviewers = await _list_school_reviewers(session)
        for reviewer in reviewers:
            await send_notification(
                recipient_id=reviewer.user_id,
                type="KB_PENDING_REVIEW",
                title=f"[知识库] 待审核：{entry.title}",
                content=(entry.desensitized_summary or "")[:200],
                related_object_type="knowledge_entry",
                related_object_id=entry.entry_id,
                db_session=session,
            )

        await _append_history(
            session,
            entry=entry,
            action=KnowledgeEntryHistoryAction.SUBMIT,
            modified_by=current.user_id,
        )

        await get_audit_service().write(
            operator=current,
            op_type="KB_SUBMIT",
            obj_type="knowledge_entry",
            obj_id=str(entry.entry_id),
            after={"status": entry.status, "reviewer_count": len(reviewers)},
            sync=True,
            session=session,
        )

        out = await _build_entry_out(session, entry)
    logger.info(
        "kb_entry_submitted",
        entry_id=entry.entry_id,
        operator_id=current.user_id,
        notified_reviewers=len(reviewers),
    )
    return out


async def review_entry(
    entry_id: int,
    body: KnowledgeReviewIn,
    *,
    current: UserSnapshot,
) -> KnowledgeOut:
    """校级审核：PENDING → PUBLISHED 或回退到 DRAFT。"""
    async with uow() as session:
        repo = KnowledgeRepository(session)
        entry = await _get_entry_or_404(repo, entry_id)

        # 业务校验：必须校级（role_level==2）reviewer
        await _ensure_school_reviewer_or_raise(session, current)

        # 防止自审：作者本人不得审核自己提交的条目（PRD UC-08 — 利益冲突）
        if entry.author_id == current.user_id:
            raise PermissionDenied("不可审核自己提交的条目")

        if entry.status != KnowledgeEntryStatus.PENDING:
            raise KnowledgeIllegalTransition("仅 PENDING 状态条目可审核")

        review_note = (body.review_note or "").strip() or None
        if body.action == "APPROVE":
            target_status = KnowledgeEntryStatus.PUBLISHED
            history_action = KnowledgeEntryHistoryAction.APPROVE
            audit_op = "KB_APPROVE"
            notify_type = "KB_APPROVED"
            notify_title = f"[知识库] 已发布：{entry.title}"
        else:
            target_status = KnowledgeEntryStatus.DRAFT
            history_action = KnowledgeEntryHistoryAction.REJECT
            audit_op = "KB_REJECT"
            notify_type = "KB_REJECTED"
            notify_title = f"[知识库] 已驳回：{entry.title}"
            if not review_note:
                # 二次兜底：schema 已校验，但若被绕过仍要拦截
                raise ValidationError("REJECT 时必须填写 review_note")

        _ensure_can_transition(entry.status, target_status)

        entry.status = target_status
        entry.reviewer_id = current.user_id
        entry.review_note = review_note
        if target_status == KnowledgeEntryStatus.PUBLISHED:
            entry.published_at = datetime.now(tz=UTC)
        await session.flush()

        await send_notification(
            recipient_id=entry.author_id,
            type=notify_type,
            title=notify_title,
            content=(review_note or "")[:200] if body.action == "REJECT" else "您的知识库条目已通过审核并发布。",
            related_object_type="knowledge_entry",
            related_object_id=entry.entry_id,
            db_session=session,
        )

        await _append_history(
            session,
            entry=entry,
            action=history_action,
            modified_by=current.user_id,
        )

        await get_audit_service().write(
            operator=current,
            op_type=audit_op,
            obj_type="knowledge_entry",
            obj_id=str(entry.entry_id),
            after={"status": entry.status, "review_note": (review_note or "")[:120]},
            sync=True,
            session=session,
        )

        out = await _build_entry_out(session, entry)
    logger.info(
        "kb_entry_reviewed",
        entry_id=entry.entry_id,
        action=body.action,
        reviewer_id=current.user_id,
    )
    return out


async def update_entry(
    entry_id: int,
    body: KnowledgeUpdateIn,
    *,
    current: UserSnapshot,
) -> KnowledgeOut:
    """编辑条目（PATCH 语义）。

    - 作者可编辑自己的 ``DRAFT``。
    - 校级 reviewer 可强制编辑 ``PUBLISHED``（``version+=1``，状态不变）。
    """
    payload = body.model_dump(exclude_unset=True)
    if not payload:
        raise ValidationError("请求体不能为空")

    if "fraud_type_id" in payload and payload["fraud_type_id"] is not None:
        async with uow() as preflight:
            await _ensure_fraud_type_exists(preflight, int(payload["fraud_type_id"]))

    async with uow() as session:
        repo = KnowledgeRepository(session)
        entry = await _get_entry_or_404(repo, entry_id)

        is_school_reviewer = await _is_school_reviewer(session, current)
        is_author = entry.author_id == current.user_id

        bump_version = False
        if entry.status == KnowledgeEntryStatus.DRAFT:
            if not is_author and not is_school_reviewer:
                raise PermissionDenied("仅作者或校级审核员可编辑草稿")
        elif entry.status == KnowledgeEntryStatus.PUBLISHED:
            if not is_school_reviewer:
                raise PermissionDenied("仅校级审核员可编辑已发布条目")
            bump_version = True
        else:
            raise KnowledgeIllegalTransition(
                f"当前状态 {entry.status} 不允许编辑"
            )

        # 应用部分字段更新
        for field, value in payload.items():
            if value is None and field in {
                "title",
                "fraud_type_id",
                "desensitized_summary",
                "identification_points",
                "prevention_advice",
                "source_type",
            }:
                # 必填字段不允许清空
                continue
            setattr(entry, field, value)

        if bump_version:
            entry.version = (entry.version or 0) + 1
        await session.flush()

        await _append_history(
            session,
            entry=entry,
            action=KnowledgeEntryHistoryAction.UPDATE,
            modified_by=current.user_id,
        )

        await get_audit_service().write(
            operator=current,
            op_type="KB_UPDATE",
            obj_type="knowledge_entry",
            obj_id=str(entry.entry_id),
            after={
                "status": entry.status,
                "version": entry.version,
                "changed_fields": sorted(payload.keys()),
            },
            sync=True,
            session=session,
        )

        out = await _build_entry_out(session, entry)
    logger.info(
        "kb_entry_updated",
        entry_id=entry.entry_id,
        operator_id=current.user_id,
        version=entry.version,
        bump=bump_version,
    )
    return out


async def offline_entry(
    entry_id: int,
    body: KnowledgeOfflineIn,
    *,
    current: UserSnapshot,
) -> dict[str, str | int]:
    """下线条目：PUBLISHED → OFFLINE。"""
    async with uow() as session:
        repo = KnowledgeRepository(session)
        entry = await _get_entry_or_404(repo, entry_id)

        _ensure_can_transition(entry.status, KnowledgeEntryStatus.OFFLINE)
        if entry.status != KnowledgeEntryStatus.PUBLISHED:
            raise KnowledgeIllegalTransition("仅已发布条目可下线")

        reason = body.reason.strip()
        entry.status = KnowledgeEntryStatus.OFFLINE
        entry.offlined_at = datetime.now(tz=UTC)
        entry.review_note = reason
        await session.flush()

        await _append_history(
            session,
            entry=entry,
            action=KnowledgeEntryHistoryAction.OFFLINE,
            modified_by=current.user_id,
        )

        await get_audit_service().write(
            operator=current,
            op_type="KB_OFFLINE",
            obj_type="knowledge_entry",
            obj_id=str(entry.entry_id),
            after={"status": entry.status, "reason": reason[:120]},
            sync=True,
            session=session,
        )

    logger.info(
        "kb_entry_offlined",
        entry_id=entry_id,
        operator_id=current.user_id,
        reason=reason[:60],
    )
    return {"entry_id": str(entry_id), "status": KnowledgeEntryStatus.OFFLINE}


async def list_public(
    *,
    keyword: str | None = None,
    fraud_type_id: int | None = None,
    page: int = 1,
    size: int = 20,
    sort: str = "published_at_desc",
) -> tuple[list[KnowledgeListItemOut], int]:
    """学生 / 公开端列表（强制 ``status=PUBLISHED``）。"""
    offset = (page - 1) * size
    async with uow() as session:
        repo = KnowledgeRepository(session)
        items, total = await repo.list_public(
            keyword=keyword,
            fraud_type_id=fraud_type_id,
            sort=sort,
            offset=offset,
            limit=size,
        )
        results = await _to_list_items(session, items)
    return results, total


async def get_public(
    entry_id: int,
    *,
    current: UserSnapshot,  # 当前未做个性化推荐，保留参数避免改 router
) -> KnowledgeDetailOut:
    """学生侧详情（含同类推荐 3 条）。"""
    _ = current
    async with uow() as session:
        repo = KnowledgeRepository(session)
        entry = await repo.get_by_id(entry_id)
        if entry is None or entry.status != KnowledgeEntryStatus.PUBLISHED:
            raise KnowledgeNotFound()

        related_entries = await repo.list_related(
            fraud_type_id=entry.fraud_type_id,
            exclude_entry_id=entry.entry_id,
            limit=3,
        )
        related_items = await _to_list_items(session, related_entries)

        base_out = await _build_entry_out(session, entry)
    return KnowledgeDetailOut(
        **base_out.model_dump(),
        related=related_items,
    )


async def list_admin(
    *,
    current: UserSnapshot,  # 占位以便后续按作者范围限流
    statuses: list[str] | None = None,
    keyword: str | None = None,
    fraud_type_id: int | None = None,
    author_id: int | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[KnowledgeListItemOut], int]:
    """管理员条目列表（不限状态）。"""
    _ = current
    offset = (page - 1) * size

    # 校验状态码合法
    if statuses:
        invalid = [s for s in statuses if s not in KnowledgeEntryStatus.ALL]
        if invalid:
            raise ValidationError(f"非法状态值: {invalid}")

    async with uow() as session:
        repo = KnowledgeRepository(session)
        items, total = await repo.list_admin(
            statuses=statuses,
            fraud_type_id=fraud_type_id,
            keyword=keyword,
            author_id=author_id,
            offset=offset,
            limit=size,
        )
        results = await _to_list_items(session, items)
    return results, total


async def get_admin(entry_id: int, *, current: UserSnapshot) -> KnowledgeOut:
    """管理员详情（任意状态可见）。"""
    _ = current
    async with uow() as session:
        repo = KnowledgeRepository(session)
        entry = await _get_entry_or_404(repo, entry_id)
        out = await _build_entry_out(session, entry)
    return out


async def promote_from_draft(
    draft_id: int,
    *,
    current: UserSnapshot,
) -> KnowledgeOut:
    """把 UC-06 留下的 ``KnowledgeDraft`` 转入正式条目表（状态 ``DRAFT``）。"""
    async with uow() as session:
        draft = await session.get(KnowledgeDraft, draft_id)
        if draft is None:
            raise KnowledgeNotFound("草稿不存在")

        await _ensure_fraud_type_exists(session, draft.fraud_type_id)

        repo = KnowledgeRepository(session)
        entry = KnowledgeEntry(
            entry_id=next_snowflake_id(),
            title=f"[草稿] 案件 {draft.report_id} 转入条目",
            fraud_type_id=draft.fraud_type_id,
            desensitized_summary=draft.desensitized_summary,
            identification_points=draft.identification_points,
            prevention_advice=draft.prevention_advice,
            peak_periods=None,
            source_type="CASE",
            source_reference=f"case_id={draft.report_id}",
            status=KnowledgeEntryStatus.DRAFT,
            version=1,
            author_id=current.user_id,
            reviewer_id=None,
            review_note=None,
            source_draft_id=draft.entry_id,
        )
        await repo.add_entry(entry)

        await _append_history(
            session,
            entry=entry,
            action=KnowledgeEntryHistoryAction.CREATE,
            modified_by=current.user_id,
        )

        await get_audit_service().write(
            operator=current,
            op_type="KB_PROMOTE_FROM_DRAFT",
            obj_type="knowledge_entry",
            obj_id=str(entry.entry_id),
            after={"draft_id": draft.entry_id, "report_id": draft.report_id},
            sync=True,
            session=session,
        )

        out = await _build_entry_out(session, entry)
    logger.info(
        "kb_entry_promoted_from_draft",
        entry_id=entry.entry_id,
        draft_id=draft_id,
        operator_id=current.user_id,
    )
    return out


# ── 内部工具 ────────────────────────────────────────────────────────


def _ensure_can_transition(from_status: str | None, to_status: str) -> None:
    """状态机校验。"""
    allowed = KnowledgeEntryStatus.TRANSITIONS.get(from_status, frozenset())
    if to_status not in allowed:
        raise KnowledgeIllegalTransition(
            f"不允许的状态转换：{from_status} → {to_status}"
        )


async def _get_entry_or_404(
    repo: KnowledgeRepository, entry_id: int
) -> KnowledgeEntry:
    entry = await repo.get_by_id(entry_id)
    if entry is None:
        raise KnowledgeNotFound()
    return entry


async def _ensure_fraud_type_exists(
    session: AsyncSession, fraud_type_id: int
) -> None:
    fraud_type = await session.get(FraudType, fraud_type_id)
    if fraud_type is None or not getattr(fraud_type, "is_active", True):
        raise ValidationError(f"诈骗类型 {fraud_type_id} 不存在或已停用")


async def _is_school_reviewer(
    session: AsyncSession, current: UserSnapshot
) -> bool:
    role = await session.get(Role, current.role_id)
    if role is None:
        return False
    return role.role_code == "REVIEWER" and role.role_level == 2


async def _ensure_school_reviewer_or_raise(
    session: AsyncSession, current: UserSnapshot
) -> None:
    if not await _is_school_reviewer(session, current):
        raise PermissionDenied("仅校级审核员（role_level=2）可执行此操作")


async def _list_school_reviewers(session: AsyncSession) -> list[User]:
    rows = (
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
    return list(rows)


async def _append_history(
    session: AsyncSession,
    *,
    entry: KnowledgeEntry,
    action: str,
    modified_by: int,
) -> KnowledgeEntryHistory:
    """追加一条版本快照。``content_snapshot`` 用 ``entry.to_dict()``。"""
    snapshot: dict[str, Any] = entry.to_dict()
    # JSON 列：把 datetime 等类型序列化成字符串，避免 MySQL JSON 落库失败
    snapshot = json.loads(json.dumps(snapshot, default=_json_default))

    history = KnowledgeEntryHistory(
        history_id=next_snowflake_id(),
        entry_id=entry.entry_id,
        version=entry.version,
        content_snapshot=snapshot,
        modified_by=modified_by,
        action=action,
    )
    session.add(history)
    await session.flush()
    return history


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


async def _build_entry_out(
    session: AsyncSession, entry: KnowledgeEntry
) -> KnowledgeOut:
    """把 ORM ``KnowledgeEntry`` 装配成 ``KnowledgeOut``（带 author / reviewer / type 名称）。"""
    fraud_type = await session.get(FraudType, entry.fraud_type_id)
    author = await session.get(User, entry.author_id) if entry.author_id else None
    reviewer = await session.get(User, entry.reviewer_id) if entry.reviewer_id else None

    return KnowledgeOut(
        entry_id=str(entry.entry_id),
        title=entry.title,
        fraud_type_id=entry.fraud_type_id,
        fraud_type_name=fraud_type.type_name if fraud_type else None,
        desensitized_summary=entry.desensitized_summary,
        identification_points=entry.identification_points,
        prevention_advice=entry.prevention_advice,
        peak_periods=entry.peak_periods,
        source_type=entry.source_type,
        source_reference=entry.source_reference,
        status=entry.status,
        version=entry.version,
        author_id=str(entry.author_id),
        author_name=author.real_name if author else None,
        reviewer_id=str(entry.reviewer_id) if entry.reviewer_id else None,
        reviewer_name=reviewer.real_name if reviewer else None,
        review_note=entry.review_note,
        created_at=entry.created_at,
        updated_at=entry.updated_at,
        published_at=entry.published_at,
        offlined_at=entry.offlined_at,
    )


async def _to_list_items(
    session: AsyncSession, items: list[KnowledgeEntry]
) -> list[KnowledgeListItemOut]:
    """批量装配 ``KnowledgeListItemOut``，预取作者名 / 类型名以减少 N+1。"""
    if not items:
        return []
    author_ids = {e.author_id for e in items if e.author_id}
    type_ids = {e.fraud_type_id for e in items if e.fraud_type_id}

    author_map: dict[int, str] = {}
    if author_ids:
        rows = (
            await session.execute(
                select(User.user_id, User.real_name).where(
                    User.user_id.in_(list(author_ids))
                )
            )
        ).all()
        author_map = {int(r.user_id): r.real_name for r in rows}

    type_map: dict[int, str] = {}
    if type_ids:
        rows = (
            await session.execute(
                select(FraudType.type_id, FraudType.type_name).where(
                    FraudType.type_id.in_(list(type_ids))
                )
            )
        ).all()
        type_map = {int(r.type_id): r.type_name for r in rows}

    return [
        KnowledgeListItemOut(
            entry_id=str(e.entry_id),
            title=e.title,
            fraud_type_id=e.fraud_type_id,
            fraud_type_name=type_map.get(e.fraud_type_id),
            desensitized_summary=e.desensitized_summary,
            status=e.status,
            version=e.version,
            author_id=str(e.author_id),
            author_name=author_map.get(e.author_id),
            published_at=e.published_at,
            updated_at=e.updated_at,
        )
        for e in items
    ]
