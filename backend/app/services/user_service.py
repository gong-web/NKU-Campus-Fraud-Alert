"""账号管理（UC-10）。"""

from __future__ import annotations

import csv
from collections.abc import Sequence
from io import StringIO
from typing import Any

from app.core.logging import get_logger
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import Conflict, NotFound, ValidationError
from app.infra.cache.session_store import SessionStore
from app.infra.db.models import Role, User
from app.infra.db.models.user import UserStatus
from app.infra.db.session import uow
from app.infra.repositories.role import RoleRepository
from app.infra.repositories.user import UserRepository
from app.services.audit_service import get_audit_service

logger = get_logger(__name__)


class UserService:
    """账号 CRUD + 角色变更 + CSV 批量导入。"""

    def __init__(self) -> None:
        self._audit = get_audit_service()
        self._sessions = SessionStore()

    # ── 列表 ──────────────────────────────────────────────────
    async def list_users(
        self,
        *,
        operator: UserSnapshot,
        role_id: int | None = None,
        department_id: int | None = None,
        status: int | None = None,
        keyword: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> dict[str, Any]:
        size = min(max(size, 1), 100)
        offset = (page - 1) * size
        async with uow() as session:
            users = UserRepository(session)
            items, total = await users.list(
                role_id=role_id,
                department_id=department_id,
                status=status,
                keyword=keyword,
                offset=offset,
                limit=size,
            )
        # 这里不写 audit（read 操作太频繁；查看具体用户详情才写）
        del operator  # operator 仅用于权限注入，本方法不需要
        return {
            "items": [_user_to_dict(u) for u in items],
            "total": total,
            "page": page,
            "size": size,
        }

    # ── 详情 ──────────────────────────────────────────────────
    async def get_user(self, *, target_id: int, operator: UserSnapshot) -> dict[str, Any]:
        async with uow() as session:
            user = await UserRepository(session).get_by_id(target_id)
            if user is None:
                raise NotFound("用户不存在")
            await self._audit.write(
                operator=operator,
                op_type="USER_READ_DETAIL",
                obj_type="user",
                obj_id=str(target_id),
            )
        return _user_to_dict(user)

    # ── 创建 ──────────────────────────────────────────────────
    async def create_user(
        self,
        *,
        operator: UserSnapshot,
        cas_account: str,
        real_name: str,
        department_id: int,
        role_id: int,
        email: str | None = None,
        phone: str | None = None,
        idempotency_key: str | None = None,  # 由 controller 校验过
    ) -> dict[str, Any]:
        if not cas_account or not real_name:
            raise ValidationError("cas_account 与 real_name 必填")
        del idempotency_key  # 实际幂等性由 controller 中间件保证

        async with uow() as session:
            users = UserRepository(session)
            roles = RoleRepository(session)
            existing = await users.get_by_cas_account(cas_account)
            if existing is not None:
                raise Conflict(f"CAS 账号 {cas_account!r} 已存在")
            role = await roles.get_by_id(role_id)
            if role is None:
                raise ValidationError(f"role_id={role_id} 不存在")

            user = User(
                user_id=next_snowflake_id(),
                cas_account=cas_account,
                real_name=real_name,
                department_id=department_id,
                role_id=role_id,
                email_encrypted=email,  # TypeDecorator 自动加密
                phone_encrypted=phone,
                status=UserStatus.ACTIVE.value,
            )
            await users.add(user)

            await self._audit.write(
                operator=operator,
                op_type="USER_CREATE",
                obj_type="user",
                obj_id=str(user.user_id),
                after=_user_to_dict(user),
                sync=True,
                session=session,
            )
        logger.info("user_created", user_id=user.user_id, by=operator.user_id)
        return _user_to_dict(user)

    # ── 角色变更（强一致 + 立即吊销旧 session） ─────────────────
    async def change_role(
        self, *, target_id: int, new_role_id: int, operator: UserSnapshot
    ) -> dict[str, Any]:
        async with uow() as session:
            users = UserRepository(session)
            roles = RoleRepository(session)
            user = await users.get_by_id(target_id)
            if user is None:
                raise NotFound("用户不存在")
            if user.role_id == new_role_id:
                raise Conflict("目标角色与当前角色一致，无变更")
            new_role = await roles.get_by_id(new_role_id)
            if new_role is None:
                raise ValidationError("new_role_id 不存在")
            before = {"role_id": user.role_id}
            user.role_id = new_role_id
            after = {"role_id": user.role_id, "role_code": new_role.role_code}
            await self._audit.write(
                operator=operator,
                op_type="USER_ROLE_CHANGE",
                obj_type="user",
                obj_id=str(user.user_id),
                before=before,
                after=after,
                sync=True,
                session=session,
            )
        # 角色变更：踢光当事人所有 session（PRD 4.3.2"权限变更立即生效"）
        await self._sessions.revoke_all_for_user(target_id)
        logger.info(
            "user_role_changed",
            user_id=target_id,
            new_role_id=new_role_id,
            by=operator.user_id,
        )
        return {"user_id": target_id, "role_id": new_role_id}

    # ── 停用（软删除） ─────────────────────────────────────────
    async def disable_user(
        self, *, target_id: int, operator: UserSnapshot, reason: str | None = None
    ) -> dict[str, Any]:
        async with uow() as session:
            users = UserRepository(session)
            user = await users.get_by_id(target_id)
            if user is None:
                raise NotFound("用户不存在")
            if user.status == UserStatus.DISABLED.value:
                raise Conflict("用户已是停用状态")
            before = {"status": user.status}
            user.status = UserStatus.DISABLED.value
            after = {"status": user.status, "reason": reason or ""}
            await self._audit.write(
                operator=operator,
                op_type="USER_DISABLE",
                obj_type="user",
                obj_id=str(user.user_id),
                before=before,
                after=after,
                sync=True,
                session=session,
            )
        await self._sessions.revoke_all_for_user(target_id)
        return {"user_id": target_id, "status": UserStatus.DISABLED.value}

    async def enable_user(self, *, target_id: int, operator: UserSnapshot) -> dict[str, Any]:
        async with uow() as session:
            users = UserRepository(session)
            user = await users.get_by_id(target_id)
            if user is None:
                raise NotFound("用户不存在")
            if user.status == UserStatus.ACTIVE.value:
                raise Conflict("用户已是正常状态")
            before = {"status": user.status}
            user.status = UserStatus.ACTIVE.value
            after = {"status": user.status}
            await self._audit.write(
                operator=operator,
                op_type="USER_ENABLE",
                obj_type="user",
                obj_id=str(user.user_id),
                before=before,
                after=after,
                sync=True,
                session=session,
            )
        return {"user_id": target_id, "status": UserStatus.ACTIVE.value}

    # ── CSV 批量导入（新生名单） ───────────────────────────────
    async def import_csv(
        self, *, csv_text: str, operator: UserSnapshot, dry_run: bool = False
    ) -> dict[str, Any]:
        """CSV 列：cas_account,real_name,dept_code,role_code

        - 先解析全部行；任何一行格式不对即返回失败行明细；
        - ``dry_run=True`` 仅校验不入库，便于干跑预览；
        - ``dry_run=False`` 全部成功才事务提交，部分失败则**全部回滚**。
        """
        rows, errors = self._parse_csv(csv_text)
        if errors:
            return {"ok": False, "imported": 0, "errors": errors}
        if dry_run:
            return {"ok": True, "imported": 0, "dry_run": True, "preview_count": len(rows)}

        from sqlalchemy import select

        async with uow() as session:
            users = UserRepository(session)
            from app.infra.db.models import Department

            depts_stmt = select(Department.dept_code, Department.dept_id)
            dept_map: dict[str, int] = {  # noqa: C416 - SQLAlchemy Row typing needs unpacking
                code: dept_id for code, dept_id in (await session.execute(depts_stmt)).all()
            }
            roles_stmt = select(Role.role_code, Role.role_id)
            role_map: dict[str, int] = {  # noqa: C416 - SQLAlchemy Row typing needs unpacking
                code: role_id for code, role_id in (await session.execute(roles_stmt)).all()
            }

            for line_no, row in rows:
                if row["dept_code"] not in dept_map:
                    raise ValidationError(f"第 {line_no} 行：dept_code={row['dept_code']!r} 不存在")
                if row["role_code"] not in role_map:
                    raise ValidationError(f"第 {line_no} 行：role_code={row['role_code']!r} 不存在")
                if await users.get_by_cas_account(row["cas_account"]):
                    raise Conflict(f"第 {line_no} 行：cas_account={row['cas_account']!r} 已存在")
                user = User(
                    user_id=next_snowflake_id(),
                    cas_account=row["cas_account"],
                    real_name=row["real_name"],
                    department_id=dept_map[row["dept_code"]],
                    role_id=role_map[row["role_code"]],
                    status=UserStatus.ACTIVE.value,
                )
                await users.add(user)

            await self._audit.write(
                operator=operator,
                op_type="USER_BATCH_IMPORT",
                obj_type="user_batch",
                obj_id=str(len(rows)),
                after={"count": len(rows)},
                sync=True,
                session=session,
            )
        return {"ok": True, "imported": len(rows)}

    @staticmethod
    def _parse_csv(text: str) -> tuple[list[tuple[int, dict[str, str]]], list[dict[str, Any]]]:
        rows: list[tuple[int, dict[str, str]]] = []
        errors: list[dict[str, Any]] = []
        reader = csv.DictReader(StringIO(text))
        required = {"cas_account", "real_name", "dept_code", "role_code"}
        if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
            return [], [{"line": 1, "error": f"CSV 列必须包含 {sorted(required)}"}]
        for i, raw in enumerate(reader, start=2):  # 行号从 2 开始（含表头）
            data = {k: (raw.get(k) or "").strip() for k in required}
            for key, value in data.items():
                if not value:
                    errors.append({"line": i, "error": f"{key} 不能为空"})
                    break
            else:
                rows.append((i, data))
        return rows, errors


def _user_to_dict(u: User) -> dict[str, Any]:
    return {
        "user_id": u.user_id,
        "cas_account": u.cas_account,
        "real_name": u.real_name,
        "department_id": u.department_id,
        "role_id": u.role_id,
        "status": u.status,
        "created_at": u.created_at.isoformat() if u.created_at else None,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
    }


def stream_users_csv(items: Sequence[User]) -> str:
    """工具方法：用户列表 → CSV（管理页导出用）。"""
    buf = StringIO()
    writer = csv.writer(buf)
    writer.writerow(["user_id", "cas_account", "real_name", "department_id", "role_id", "status"])
    for u in items:
        writer.writerow(
            [u.user_id, u.cas_account, u.real_name, u.department_id, u.role_id, u.status]
        )
    return buf.getvalue()
