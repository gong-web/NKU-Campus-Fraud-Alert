"""审计日志仓储。

铁律
----
- 只暴露 :meth:`add`、:meth:`get`、:meth:`list`、:meth:`get_last`。
- **不暴露** ``update`` / ``delete``。即使有人在仓储外用 raw SQL 试图修改，
  数据库 ``app_user`` 账号也没有 UPDATE / DELETE 权限。
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, log: AuditLog) -> AuditLog:
        self._s.add(log)
        await self._s.flush()
        return log

    async def get(self, log_id: int) -> AuditLog | None:
        return await self._s.get(AuditLog, log_id)

    async def get_last(self) -> AuditLog | None:
        """获取最近一条审计日志（用于哈希链 prev_hash）。"""
        stmt = select(AuditLog).order_by(desc(AuditLog.log_id)).limit(1)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        *,
        operator_id: int | None = None,
        op_type: str | None = None,
        object_type: str | None = None,
        object_id: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[Sequence[AuditLog], int]:
        from sqlalchemy import func as sql_func

        stmt = select(AuditLog)
        if operator_id is not None:
            stmt = stmt.where(AuditLog.operator_id == operator_id)
        if op_type is not None:
            stmt = stmt.where(AuditLog.operation_type == op_type)
        if object_type is not None:
            stmt = stmt.where(AuditLog.object_type == object_type)
        if object_id is not None:
            stmt = stmt.where(AuditLog.object_id == object_id)
        if start is not None:
            stmt = stmt.where(AuditLog.operated_at >= start)
        if end is not None:
            stmt = stmt.where(AuditLog.operated_at < end)

        total_stmt = select(sql_func.count()).select_from(stmt.subquery())
        total = (await self._s.execute(total_stmt)).scalar_one()

        page_stmt = (
            stmt.order_by(desc(AuditLog.operated_at), desc(AuditLog.log_id))
            .offset(offset)
            .limit(limit)
        )
        rows = (await self._s.execute(page_stmt)).scalars().all()
        return rows, int(total)

    async def list_by_object(
        self, *, object_type: str, object_id: str, limit: int = 200
    ) -> Sequence[AuditLog]:
        """根据 object 全链路追溯（PRD 4.3）。"""
        stmt = (
            select(AuditLog)
            .where(AuditLog.object_type == object_type)
            .where(AuditLog.object_id == object_id)
            .order_by(AuditLog.operated_at)
            .limit(limit)
        )
        return (await self._s.execute(stmt)).scalars().all()

    async def iter_chain(self, *, batch_size: int = 1000) -> Sequence[AuditLog]:
        """按 log_id 顺序拉全表（``verify_audit_chain.py`` 离线校验用）。

        注意：可能是大表，调用方应自行分批。
        """
        stmt = select(AuditLog).order_by(AuditLog.log_id).limit(batch_size)
        return (await self._s.execute(stmt)).scalars().all()

    async def export_csv_rows(self, **filters: Any) -> Sequence[dict[str, Any]]:
        """导出（CSV 格式由 service 层组装）。"""
        items, _ = await self.list(limit=10_000, **filters)
        return [
            {
                "log_id": x.log_id,
                "operator_id": x.operator_id,
                "operation_type": x.operation_type,
                "object_type": x.object_type,
                "object_id": x.object_id,
                "source_ip": x.source_ip,
                "trace_id": x.trace_id,
                "operated_at": x.operated_at.isoformat(),
            }
            for x in items
        ]
