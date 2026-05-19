"""站内通知服务。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.snowflake import next_snowflake_id
from app.infra.db.models import Notification
from app.infra.db.session import uow


async def send_notification(
    *,
    recipient_id: int,
    type: str,
    title: str,
    content: str,
    related_object_type: str | None = None,
    related_object_id: int | None = None,
    db_session: AsyncSession | None = None,
) -> int:
    """在事务内或独立事务中创建一条站内通知。"""

    async def _create(session: AsyncSession) -> int:
        row = Notification(
            notification_id=next_snowflake_id(),
            recipient_id=recipient_id,
            type=type,
            title=title,
            content=content,
            related_object_type=related_object_type,
            related_object_id=related_object_id,
        )
        session.add(row)
        await session.flush()
        return row.notification_id

    if db_session is not None:
        return await _create(db_session)

    async with uow() as session:
        return await _create(session)
