"""预警业务仓储（UC-03 / UC-07）。

仓储层只负责数据访问；不主动 ``commit``、不抛业务异常，事务边界由
service 层用 ``async with uow():`` 控制。所有方法 keyword-only 参数，
列表方法返回 ``(items, total)`` 元组以便 controller 拼分页响应。
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import desc, func, or_, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.warning_notice import WarningNotice
from app.infra.db.models.warning_target import WarningTarget


class WarningRepository:
    """预警公告仓储。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    # ── 写 ─────────────────────────────────────────────────────────
    async def add(self, notice: WarningNotice) -> WarningNotice:
        self._s.add(notice)
        await self._s.flush()
        return notice

    async def upsert_targets(self, *, warning_id: int, dept_ids: list[int]) -> None:
        """批量插入预警 → 院系映射；已存在的复合主键直接 skip。"""
        if not dept_ids:
            return
        is_sqlite = self._s.bind.dialect.name == "sqlite" if self._s.bind else False
        for dept_id in dict.fromkeys(dept_ids):  # 去重 + 保序
            if is_sqlite:
                stmt = sqlite_insert(WarningTarget).values(
                    warning_id=warning_id, dept_id=dept_id
                )
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["warning_id", "dept_id"]
                )
            else:
                stmt = mysql_insert(WarningTarget).values(
                    warning_id=warning_id, dept_id=dept_id
                )
                stmt = stmt.on_duplicate_key_update(warning_id=stmt.inserted.warning_id)
            await self._s.execute(stmt)
        await self._s.flush()

    # ── 读：单条 ───────────────────────────────────────────────────
    async def get_by_id(self, warning_id: int) -> WarningNotice | None:
        return (
            await self._s.execute(
                select(WarningNotice).where(WarningNotice.warning_id == warning_id)
            )
        ).scalar_one_or_none()

    async def get_target_dept_ids(self, warning_id: int) -> list[int]:
        result = await self._s.execute(
            select(WarningTarget.dept_id)
            .where(WarningTarget.warning_id == warning_id)
            .order_by(WarningTarget.dept_id)
        )
        return [int(r) for r in result.scalars()]

    # ── 读：列表 ───────────────────────────────────────────────────
    async def list_published_for_student(
        self,
        *,
        dept_id: int,
        status: str | None = None,
        level: int | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[WarningNotice], int]:
        """学生可见的预警列表。

        可见规则：``push_scope=FULL_SCHOOL`` OR (``push_scope=DEPARTMENT`` 且
        当前用户的 ``dept_id`` 在 ``warning_targets`` 中)。
        """
        # 用 EXISTS 子查询表达 "本院系命中 warning_targets"
        dept_match_subq = (
            select(WarningTarget.warning_id)
            .where(
                WarningTarget.warning_id == WarningNotice.warning_id,
                WarningTarget.dept_id == dept_id,
            )
            .exists()
        )
        visibility_filter = or_(
            WarningNotice.push_scope == "FULL_SCHOOL",
            dept_match_subq,
        )

        base = select(WarningNotice).where(visibility_filter)
        if status is not None:
            base = base.where(WarningNotice.status == status)
        if level is not None:
            base = base.where(WarningNotice.warning_level == level)
        if keyword:
            kw = f"%{keyword.strip()}%"
            base = base.where(
                or_(WarningNotice.title.like(kw), WarningNotice.content.like(kw))
            )

        total_result = await self._s.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(total_result.scalar_one() or 0)

        items_result = await self._s.execute(
            base.order_by(desc(WarningNotice.published_at), desc(WarningNotice.warning_id))
            .offset(offset)
            .limit(limit)
        )
        items = list(items_result.scalars())
        return items, total

    async def list_admin(
        self,
        *,
        status: str | None = None,
        level: int | None = None,
        keyword: str | None = None,
        publisher_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[WarningNotice], int]:
        """审核管理员视角列表（不做学生可见性过滤）。"""
        base = select(WarningNotice)
        if status is not None:
            base = base.where(WarningNotice.status == status)
        if level is not None:
            base = base.where(WarningNotice.warning_level == level)
        if publisher_id is not None:
            base = base.where(WarningNotice.publisher_id == publisher_id)
        if keyword:
            kw = f"%{keyword.strip()}%"
            base = base.where(
                or_(WarningNotice.title.like(kw), WarningNotice.content.like(kw))
            )

        total_result = await self._s.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = int(total_result.scalar_one() or 0)

        items_result = await self._s.execute(
            base.order_by(desc(WarningNotice.published_at), desc(WarningNotice.warning_id))
            .offset(offset)
            .limit(limit)
        )
        return list(items_result.scalars()), total

    # ── 内部辅助：可在 service 直接拿到当前 utc 时间，避免重复 import ──
    @staticmethod
    def utcnow() -> datetime:
        return datetime.now(tz=UTC)
