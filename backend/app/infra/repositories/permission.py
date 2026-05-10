"""Permission 仓储。"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import Permission


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_code(self, permission_code: str) -> Permission | None:
        stmt = select(Permission).where(Permission.permission_code == permission_code)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list_all(self) -> Sequence[Permission]:
        stmt = select(Permission).order_by(Permission.permission_id)
        return (await self._s.execute(stmt)).scalars().all()
