"""匿名映射仓储。

**注意**：此仓储仅用于司法协助查询的解密读路径——其它任何业务路径绝不应
注入本类。运行时业务连接（``app_user``）对 ``anonymous_mappings`` 表无任
何权限，调用本仓储会得到 SQL 拒绝。
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import AnonymousMapping


class AnonymousMappingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_report_id(self, report_id: int) -> AnonymousMapping | None:
        stmt = select(AnonymousMapping).where(AnonymousMapping.report_id == report_id)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def add(self, mapping: AnonymousMapping) -> AnonymousMapping:
        self._s.add(mapping)
        await self._s.flush()
        return mapping
