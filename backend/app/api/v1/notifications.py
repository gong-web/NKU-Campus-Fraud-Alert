"""站内通知接口（公共组件，全平台共用）。

通知是一个被全员调用的横切组件：审核 / 预警 / 知识库 / 测验 等任何模块
都可以通过 ``send_notification(...)`` 推送到学生 / 管理员。本路由提供：

- ``GET  /api/v1/notifications/my``              当前用户的通知列表（分页）
- ``GET  /api/v1/notifications/my/unread-count`` 未读数（铃铛红点轮询专用）
- ``PATCH /api/v1/notifications/{id}/read``      标记单条已读
- ``PATCH /api/v1/notifications/my/read-all``    一键全部已读

所有接口要求登录但不挑角色（任何人都有"自己的"通知收件箱）。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query

from app.api.deps import get_current_user
from app.domain.user_snapshot import UserSnapshot
from app.infra.db.session import uow
from app.infra.repositories.notification import NotificationRepository
from app.schemas.common import PaginationOut
from app.schemas.notifications import (
    MarkAllReadOut,
    MarkReadOut,
    NotificationOut,
    UnreadCountOut,
)

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get(
    "/my",
    response_model=PaginationOut[NotificationOut],
    summary="当前用户通知列表（分页）",
)
async def list_my_notifications(
    current: Annotated[UserSnapshot, Depends(get_current_user)],
    unread_only: Annotated[
        bool, Query(description="仅返回未读，默认 false")
    ] = False,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[NotificationOut]:
    """返回当前用户的通知列表，按 ``created_at DESC`` 排序。"""
    offset = (page - 1) * size
    async with uow() as session:
        repo = NotificationRepository(session)
        items, total = await repo.list_by_recipient(
            recipient_id=current.user_id,
            unread_only=unread_only,
            offset=offset,
            limit=size,
        )
        out_items = [
            NotificationOut(
                notification_id=str(n.notification_id),
                type=n.type,
                title=n.title,
                content=n.content,
                related_object_type=n.related_object_type,
                related_object_id=(
                    str(n.related_object_id)
                    if n.related_object_id is not None
                    else None
                ),
                is_read=bool(n.is_read),
                created_at=n.created_at,
                read_at=n.read_at,
            )
            for n in items
        ]
    return PaginationOut[NotificationOut](
        items=out_items, total=total, page=page, size=size
    )


@router.get(
    "/my/unread-count",
    response_model=UnreadCountOut,
    summary="当前用户未读通知数量（铃铛红点轮询专用）",
)
async def my_unread_count(
    current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> UnreadCountOut:
    async with uow() as session:
        repo = NotificationRepository(session)
        count = await repo.count_unread(recipient_id=current.user_id)
    return UnreadCountOut(count=count)


@router.patch(
    "/{notification_id}/read",
    response_model=MarkReadOut,
    summary="标记单条通知为已读",
)
async def mark_notification_read(
    current: Annotated[UserSnapshot, Depends(get_current_user)],
    notification_id: Annotated[int, Path(ge=1)],
) -> MarkReadOut:
    """标记一条属于自己的通知为已读。

    跨用户横向越权由仓储层用 ``recipient_id`` 联合过滤防御；不存在或不属于
    当前用户的 ID 都返回 ``success=false``，不暴露存在性。
    """
    async with uow() as session:
        repo = NotificationRepository(session)
        ok = await repo.mark_read(
            notification_id=notification_id,
            recipient_id=current.user_id,
        )
    return MarkReadOut(success=ok)


@router.patch(
    "/my/read-all",
    response_model=MarkAllReadOut,
    summary="一键全部已读",
)
async def mark_all_my_read(
    current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> MarkAllReadOut:
    async with uow() as session:
        repo = NotificationRepository(session)
        marked = await repo.mark_all_read(recipient_id=current.user_id)
    return MarkAllReadOut(marked=marked)
