"""站内通知仓储。

仓储层只负责数据访问；不主动 ``commit``、不抛业务异常，事务边界由
service 层的 ``async with uow():`` 控制。所有方法 keyword-only 参数，
列表方法返回 ``(items, total)`` 元组以便 controller 拼分页响应。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.notification import Notification


class NotificationRepository:
    """站内通知仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── 写 ─────────────────────────────────────────────────────────
    async def add(self, notification: Notification) -> Notification:
        """插入一条通知并 flush（由 service 的 uow 控制事务提交）。"""
        self._s.add(notification)
        await self._s.flush()
        return notification

    async def mark_read(self, *, notification_id: int, recipient_id: int) -> bool:
        """标记单条通知为已读。

        只操作属于 ``recipient_id`` 的通知（防止横向越权），
        同时仅对 ``is_read == 0`` 的行生效，返回是否确实更新了一行。
        """
        result = await self._s.execute(
            update(Notification)
            .where(
                Notification.notification_id == notification_id,
                Notification.recipient_id == recipient_id,
                Notification.is_read == 0,
            )
            .values(is_read=1, read_at=datetime.now(tz=UTC))
        )
        await self._s.flush()
        return result.rowcount > 0

    async def mark_all_read(self, *, recipient_id: int) -> int:
        """一键已读当前用户所有未读通知，返回实际更新条数。"""
        result = await self._s.execute(
            update(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read == 0,
            )
            .values(is_read=1, read_at=datetime.now(tz=UTC))
        )
        await self._s.flush()
        return result.rowcount

    # ── 读 ─────────────────────────────────────────────────────────
    async def list_by_recipient(
        self,
        *,
        recipient_id: int,
        unread_only: bool = False,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Notification], int]:
        """分页查询某用户的通知列表，按创建时间倒序。

        Args:
            recipient_id: 接收人 user_id。
            unread_only: 若为 True 则仅返回未读通知。
            offset: SQL OFFSET。
            limit: SQL LIMIT。

        Returns:
            (items, total) 元组，total 为过滤后的总条数。
        """
        base = select(Notification).where(
            Notification.recipient_id == recipient_id
        )
        if unread_only:
            base = base.where(Notification.is_read == 0)

        total_result = await self._s.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(total_result.scalar_one() or 0)

        items_result = await self._s.execute(
            base.order_by(
                Notification.created_at.desc(),
                Notification.notification_id.desc(),
            )
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars()), total

    async def count_unread(self, *, recipient_id: int) -> int:
        """查询未读通知数量（前端铃铛红点轮询专用，走索引 idx_notif_user_read_time）。"""
        result = await self._s.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                Notification.recipient_id == recipient_id,
                Notification.is_read == 0,
            )
        )
        return int(result.scalar_one() or 0)
