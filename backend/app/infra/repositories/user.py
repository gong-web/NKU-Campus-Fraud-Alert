"""User 仓储。"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import User


class UserRepository:
    """用户仓储（仅暴露业务需要的查询，不暴露原始 SQL）。"""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._s.get(User, user_id)

    async def get_by_cas_account(self, cas_account: str) -> User | None:
        stmt = select(User).where(User.cas_account == cas_account)
        result = await self._s.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        *,
        role_id: int | None = None,
        department_id: int | None = None,
        status: int | None = None,
        keyword: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[Sequence[User], int]:
        """分页 + 过滤查询；返回 (items, total)。"""
        base = select(User)
        if role_id is not None:
            base = base.where(User.role_id == role_id)
        if department_id is not None:
            base = base.where(User.department_id == department_id)
        if status is not None:
            base = base.where(User.status == status)
        if keyword:
            kw = f"%{keyword}%"
            base = base.where(or_(User.cas_account.like(kw), User.real_name.like(kw)))

        # 总数
        total_stmt = select(func.count()).select_from(base.subquery())
        total = (await self._s.execute(total_stmt)).scalar_one()

        # 列表
        page_stmt = base.order_by(User.user_id.desc()).offset(offset).limit(limit)
        rows = (await self._s.execute(page_stmt)).scalars().all()

        return rows, int(total)

    async def add(self, user: User) -> User:
        self._s.add(user)
        await self._s.flush()
        return user

    async def update_status(self, user_id: int, status: int) -> bool:
        u = await self.get_by_id(user_id)
        if u is None:
            return False
        u.status = status
        await self._s.flush()
        return True

    async def update_role(self, user_id: int, role_id: int) -> User | None:
        u = await self.get_by_id(user_id)
        if u is None:
            return None
        u.role_id = role_id
        await self._s.flush()
        return u
