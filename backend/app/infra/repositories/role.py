"""Role / RolePermission 仓储。"""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models import Permission, Role, RolePermission


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, role_id: int) -> Role | None:
        return await self._s.get(Role, role_id)

    async def get_by_code(self, role_code: str) -> Role | None:
        stmt = select(Role).where(Role.role_code == role_code)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def list_all(self) -> Sequence[Role]:
        stmt = select(Role).order_by(Role.role_id)
        return (await self._s.execute(stmt)).scalars().all()

    async def list_permissions(self, role_id: int) -> set[str]:
        """该角色拥有的所有 permission_code。"""
        stmt = (
            select(Permission.permission_code)
            .join(RolePermission, RolePermission.permission_id == Permission.permission_id)
            .where(RolePermission.role_id == role_id)
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return set(rows)

    async def list_role_permissions_full(self) -> dict[int, set[str]]:
        """启动期 / 失效后用：把整张 role_permission 拉成 ``role_id → {code}``。"""
        stmt = select(RolePermission.role_id, Permission.permission_code).join(
            Permission, Permission.permission_id == RolePermission.permission_id
        )
        rows = (await self._s.execute(stmt)).all()
        out: dict[int, set[str]] = {}
        for role_id, code in rows:
            out.setdefault(role_id, set()).add(code)
        return out

    async def grant(self, role_id: int, permission_id: int, granted_by: int | None = None) -> None:
        rp = RolePermission(role_id=role_id, permission_id=permission_id, granted_by=granted_by)
        self._s.add(rp)
        await self._s.flush()

    async def revoke(self, role_id: int, permission_id: int) -> bool:
        rp = await self._s.get(RolePermission, {"role_id": role_id, "permission_id": permission_id})
        if rp is None:
            return False
        await self._s.delete(rp)
        await self._s.flush()
        return True
