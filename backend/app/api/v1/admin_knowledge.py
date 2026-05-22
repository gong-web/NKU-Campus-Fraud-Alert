"""审核管理员知识库接口（UC-08）。"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.infra.db.models import KnowledgeEntryHistory
from app.infra.db.session import uow
from app.schemas.common import PaginationOut
from app.schemas.knowledge import (
    KnowledgeCreateIn,
    KnowledgeListItemOut,
    KnowledgeOfflineIn,
    KnowledgeOut,
    KnowledgeReviewIn,
    KnowledgeUpdateIn,
)
from app.services import knowledge_entry_service
from app.services import permissions as perm

router = APIRouter(prefix="/admin/knowledge", tags=["admin-knowledge (UC-08)"])


@router.post(
    "",
    response_model=KnowledgeOut,
    status_code=201,
    summary="新建知识库条目（草稿）",
)
async def admin_create_entry(
    body: KnowledgeCreateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_CREATE))],
) -> KnowledgeOut:
    """管理员新建知识库条目，初始为 ``DRAFT`` 状态。"""
    return await knowledge_entry_service.create_entry(body, current=current)


@router.get(
    "",
    response_model=PaginationOut[KnowledgeListItemOut],
    summary="管理员条目列表（按状态/作者筛选）",
)
async def admin_list_entries(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_CREATE))],
    status: Annotated[
        list[str] | None,
        Query(description="状态筛选，可多次传入 DRAFT / PENDING / PUBLISHED / OFFLINE"),
    ] = None,
    keyword: Annotated[str | None, Query(max_length=128, description="标题 / 摘要模糊搜索")] = None,
    fraud_type_id: Annotated[int | None, Query(ge=1, description="按诈骗类型筛选")] = None,
    author_id: Annotated[int | None, Query(ge=1, description="按作者 user_id 筛选")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[KnowledgeListItemOut]:
    """管理员可查看任意状态条目；多状态筛选时重复传 ``status`` 参数。"""
    items, total = await knowledge_entry_service.list_admin(
        current=current,
        statuses=status,
        keyword=keyword,
        fraud_type_id=fraud_type_id,
        author_id=author_id,
        page=page,
        size=size,
    )
    return PaginationOut[KnowledgeListItemOut](
        items=items, total=total, page=page, size=size
    )


@router.get(
    "/{entry_id}",
    response_model=KnowledgeOut,
    summary="管理员条目详情",
)
async def admin_entry_detail(
    entry_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_CREATE))],
) -> KnowledgeOut:
    """管理员查看任意状态的条目详情。"""
    return await knowledge_entry_service.get_admin(entry_id, current=current)


@router.patch(
    "/{entry_id}",
    response_model=KnowledgeOut,
    summary="编辑条目（草稿任意字段；校级可强改 PUBLISHED 并 version+1）",
)
async def admin_update_entry(
    entry_id: int,
    body: KnowledgeUpdateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_CREATE))],
) -> KnowledgeOut:
    """部分字段更新（PATCH 语义）。仅作者可改自己的草稿；校级可强改已发布。"""
    return await knowledge_entry_service.update_entry(entry_id, body, current=current)


@router.post(
    "/{entry_id}/submit",
    response_model=KnowledgeOut,
    summary="提交审核（DRAFT → PENDING）",
)
async def admin_submit_entry(
    entry_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_CREATE))],
) -> KnowledgeOut:
    """作者提交草稿等待审核；同事务通知所有校级 reviewer。"""
    return await knowledge_entry_service.submit_entry(entry_id, current=current)


@router.post(
    "/{entry_id}/review",
    response_model=KnowledgeOut,
    summary="审核（APPROVE/REJECT）",
)
async def admin_review_entry(
    entry_id: int,
    body: KnowledgeReviewIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_REVIEW))],
) -> KnowledgeOut:
    """校级审核：APPROVE → PUBLISHED；REJECT → 回退到 DRAFT 并要求填写 review_note。"""
    return await knowledge_entry_service.review_entry(entry_id, body, current=current)


@router.post(
    "/{entry_id}/offline",
    summary="下线条目（PUBLISHED → OFFLINE）",
)
async def admin_offline_entry(
    entry_id: int,
    body: KnowledgeOfflineIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_OFFLINE))],
) -> dict[str, str | int]:
    """下线已发布条目；学生端不再可见，管理员仍可查看历史。"""
    return await knowledge_entry_service.offline_entry(entry_id, body, current=current)


@router.get(
    "/{entry_id}/history",
    summary="条目历史版本列表（事件溯源）",
)
async def admin_entry_history(
    entry_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_CREATE))],
) -> list[dict[str, Any]]:
    """返回条目所有版本快照，按 ``modified_at`` 升序。"""
    del current  # 仅用于鉴权
    async with uow() as session:
        rows = (
            await session.execute(
                select(KnowledgeEntryHistory)
                .where(KnowledgeEntryHistory.entry_id == entry_id)
                .order_by(KnowledgeEntryHistory.modified_at, KnowledgeEntryHistory.history_id)
            )
        ).scalars().all()
    return [
        {
            "history_id": str(h.history_id),
            "entry_id": str(h.entry_id),
            "version": h.version,
            "action": h.action,
            "modified_by": str(h.modified_by),
            "modified_at": h.modified_at,
            "content_snapshot": h.content_snapshot,
        }
        for h in rows
    ]
