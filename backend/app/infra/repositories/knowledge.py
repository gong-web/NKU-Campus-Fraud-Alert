"""知识库正式条目仓储（UC-04 / UC-08）。

仓储层只负责数据访问；不主动 ``commit``、不抛业务异常，事务边界由
service 层用 ``async with uow():`` 控制。所有方法 keyword-only 参数，
列表方法返回 ``(items, total)`` 元组以便 controller 拼分页响应。

关键词搜索使用 MySQL 8 ``MATCH ... AGAINST(... IN NATURAL LANGUAGE MODE)``
（迁移已建 FULLTEXT + ngram parser），通过绑定参数避免拼字符串注入。
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import desc, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.knowledge_entry import KnowledgeEntry
from app.infra.db.models.knowledge_entry_history import KnowledgeEntryHistory


class KnowledgeRepository:
    """知识库正式条目仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── 写 ─────────────────────────────────────────────────────────
    async def add_entry(self, entry: KnowledgeEntry) -> KnowledgeEntry:
        self._s.add(entry)
        await self._s.flush()
        return entry

    async def add_history(self, history: KnowledgeEntryHistory) -> KnowledgeEntryHistory:
        self._s.add(history)
        await self._s.flush()
        return history

    async def update(self, entry: KnowledgeEntry, **changes: Any) -> None:
        """对已加载的条目应用字段变更并自增 ``version``。

        Service 层负责传入合法字段集；本方法不做白名单限制——但 ``version``
        / ``entry_id`` 始终由本方法自管理，禁止从外部覆盖。
        """
        changes.pop("version", None)
        changes.pop("entry_id", None)
        for field, value in changes.items():
            if hasattr(entry, field):
                setattr(entry, field, value)
        entry.version = (entry.version or 0) + 1
        await self._s.flush()

    # ── 读：单条 ───────────────────────────────────────────────────
    async def get_by_id(self, entry_id: int) -> KnowledgeEntry | None:
        return (
            await self._s.execute(
                select(KnowledgeEntry).where(KnowledgeEntry.entry_id == entry_id)
            )
        ).scalar_one_or_none()

    # ── 读：列表 ───────────────────────────────────────────────────
    async def list_public(
        self,
        *,
        keyword: str | None = None,
        fraud_type_id: int | None = None,
        sort: str = "published_at_desc",
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[KnowledgeEntry], int]:
        """学生 / 公开端的列表（仅 ``status=PUBLISHED``）。

        - ``keyword`` 走 ``MATCH(title, desensitized_summary, identification_points)
          AGAINST(:kw IN NATURAL LANGUAGE MODE)``，绑定参数防注入。
        - ``sort=hot`` 暂按 ``version`` 倒序占位（无浏览量字段时的近似指标），
          后续可换成累计浏览量。
        """
        base = select(KnowledgeEntry).where(
            KnowledgeEntry.status == "PUBLISHED"
        )
        if fraud_type_id is not None:
            base = base.where(KnowledgeEntry.fraud_type_id == fraud_type_id)

        kw = (keyword or "").strip()
        if kw:
            is_sqlite = (
                self._s.bind.dialect.name == "sqlite" if self._s.bind else False
            )
            if is_sqlite:
                # SQLite 没有 FULLTEXT；测试环境退化到 LIKE 模糊搜索
                like_kw = f"%{kw}%"
                base = base.where(
                    or_(
                        KnowledgeEntry.title.like(like_kw),
                        KnowledgeEntry.desensitized_summary.like(like_kw),
                        KnowledgeEntry.identification_points.like(like_kw),
                    )
                )
            else:
                match_expr = text(
                    "MATCH (knowledge_entries.title, "
                    "knowledge_entries.desensitized_summary, "
                    "knowledge_entries.identification_points) "
                    "AGAINST (:kw IN NATURAL LANGUAGE MODE)"
                ).bindparams(kw=kw)
                base = base.where(match_expr)

        total_result = await self._s.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(total_result.scalar_one() or 0)

        if sort == "hot":
            order_clause = (desc(KnowledgeEntry.version), desc(KnowledgeEntry.published_at))
        else:
            order_clause = (
                desc(KnowledgeEntry.published_at),
                desc(KnowledgeEntry.entry_id),
            )

        items_result = await self._s.execute(
            base.order_by(*order_clause).offset(offset).limit(limit)
        )
        return list(items_result.scalars()), total

    async def list_admin(
        self,
        *,
        statuses: list[str] | None = None,
        fraud_type_id: int | None = None,
        keyword: str | None = None,
        author_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[KnowledgeEntry], int]:
        """管理端列表（不限状态，可按状态集过滤）。"""
        base = select(KnowledgeEntry)
        if statuses:
            base = base.where(KnowledgeEntry.status.in_(statuses))
        if fraud_type_id is not None:
            base = base.where(KnowledgeEntry.fraud_type_id == fraud_type_id)
        if author_id is not None:
            base = base.where(KnowledgeEntry.author_id == author_id)
        if keyword:
            kw = f"%{keyword.strip()}%"
            base = base.where(
                or_(
                    KnowledgeEntry.title.like(kw),
                    KnowledgeEntry.desensitized_summary.like(kw),
                )
            )

        total_result = await self._s.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(total_result.scalar_one() or 0)

        items_result = await self._s.execute(
            base.order_by(desc(KnowledgeEntry.updated_at), desc(KnowledgeEntry.entry_id))
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars()), total

    async def list_related(
        self,
        *,
        fraud_type_id: int,
        exclude_entry_id: int,
        limit: int = 3,
    ) -> list[KnowledgeEntry]:
        """同 fraud_type_id 最近 ``limit`` 条已发布条目（不含本身）。"""
        result = await self._s.execute(
            select(KnowledgeEntry)
            .where(
                KnowledgeEntry.fraud_type_id == fraud_type_id,
                KnowledgeEntry.entry_id != exclude_entry_id,
                KnowledgeEntry.status == "PUBLISHED",
            )
            .order_by(desc(KnowledgeEntry.published_at), desc(KnowledgeEntry.entry_id))
            .limit(limit)
        )
        return list(result.scalars())
