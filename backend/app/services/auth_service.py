"""CAS 登录 / 登出 / 会话续期。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import (
    AccountDisabled,
    CASTicketReplay,
    Unauthenticated,
)
from app.infra.cache.session_store import SessionData, SessionStore
from app.infra.cache.ticket_dedup import TicketDedup
from app.infra.cas.base import AuthProvider, CASUserInfo
from app.infra.db.models import Department, Role, User
from app.infra.db.models.user import UserStatus
from app.infra.db.session import uow
from app.infra.repositories.role import RoleRepository
from app.infra.repositories.user import UserRepository
from app.services.audit_service import get_audit_service

logger = get_logger(__name__)


class AuthService:
    """登录 / 登出 / 续期。"""

    def __init__(self, *, provider: AuthProvider) -> None:
        self._provider = provider
        self._sessions = SessionStore()
        self._dedup = TicketDedup()
        self._audit = get_audit_service()

    # ── 登录 ──────────────────────────────────────────────────
    async def cas_login(
        self,
        *,
        ticket: str,
        service: str,
        source_ip: str,
        user_agent: str,
    ) -> tuple[SessionData, UserSnapshot]:
        """完成 CAS 校验 + 建立 session。"""
        # 1. 票据去重（防重放）
        if not await self._dedup.acquire(ticket):
            logger.warning("cas_ticket_replay", ticket_prefix=ticket[:6], source_ip=source_ip)
            await self._audit.write(
                operator=None,
                op_type="LOGIN_FAILED",
                obj_type="cas_ticket",
                obj_id=ticket[:32],
                after={"reason": "replay", "source_ip": source_ip},
                sync=True,
            )
            raise CASTicketReplay()

        # 2. 调 CAS 校验
        info: CASUserInfo = await self._provider.validate_ticket(ticket, service=service)

        # 3. 查 / 建本地用户
        async with uow() as session:
            users = UserRepository(session)
            roles = RoleRepository(session)
            user = await users.get_by_cas_account(info.cas_account)
            if user is None:
                user = await self._provision_user(session, info, users)
            if user.status == UserStatus.DISABLED.value:
                logger.warning("login_disabled_account", cas_account=info.cas_account)
                await self._audit.write(
                    operator=None,
                    op_type="LOGIN_FAILED",
                    obj_type="user",
                    obj_id=str(user.user_id),
                    after={"reason": "disabled", "source_ip": source_ip},
                    sync=True,
                    session=session,
                )
                raise AccountDisabled()
            if user.status == UserStatus.DEREGISTERED.value:
                raise AccountDisabled("账号已注销")

            # 4. 更新最近登录信息
            user.last_login_at = datetime.now(tz=UTC)
            user.last_login_ip = source_ip

            role = await roles.get_by_id(user.role_id)
            assert role is not None  # FK 约束保证

            # 5. 建立 session
            sd = await self._sessions.create(
                user_id=user.user_id,
                role_id=user.role_id,
                role_code=role.role_code,
                dept_id=user.department_id,
                cas_account=user.cas_account,
                real_name=user.real_name,
                cas_ticket=ticket,
                source_ip=source_ip,
                user_agent=user_agent,
            )
            snap = UserSnapshot(
                user_id=user.user_id,
                cas_account=user.cas_account,
                real_name=user.real_name,
                role_id=user.role_id,
                role_code=role.role_code,
                department_id=user.department_id,
                session_id=sd.session_id,
                source_ip=source_ip,
                user_agent=user_agent,
            )

            # 6. 审计同步落库（强一致）
            await self._audit.write(
                operator=snap,
                op_type="LOGIN",
                obj_type="user",
                obj_id=str(user.user_id),
                after={
                    "session_id": sd.session_id,
                    "provider": self._provider.name,
                    "service": service,
                },
                sync=True,
                session=session,
            )

        logger.info("login_success", user_id=snap.user_id, cas_account=snap.cas_account)
        return sd, snap

    async def _provision_user(
        self, session: AsyncSession, info: CASUserInfo, users: UserRepository
    ) -> User:
        """首登注册：默认 STUDENT 角色 + 默认院系。"""
        from sqlalchemy import select

        # 院系：CAS 给的就用，没给就用 UNKNOWN（迁移种子里建的）
        dept_code = info.department_code or "UNKNOWN"
        dept_stmt = select(Department).where(Department.dept_code == dept_code)
        dept = (await session.execute(dept_stmt)).scalar_one_or_none()
        if dept is None:
            dept_stmt = select(Department).where(Department.dept_code == "UNKNOWN")
            dept = (await session.execute(dept_stmt)).scalar_one_or_none()
        if dept is None:
            raise RuntimeError("UNKNOWN 院系未初始化，请先 `make seed`")

        role_stmt = select(Role).where(Role.role_code == Role.CODE_STUDENT)
        role = (await session.execute(role_stmt)).scalar_one()
        user = User(
            user_id=next_snowflake_id(),
            cas_account=info.cas_account,
            real_name=info.real_name,
            department_id=dept.dept_id,
            role_id=role.role_id,
            status=UserStatus.ACTIVE.value,
        )
        await users.add(user)
        logger.info("user_provisioned", cas_account=info.cas_account, role=role.role_code)
        return user

    # ── 登出 ──────────────────────────────────────────────────
    async def logout(self, snap: UserSnapshot) -> str:
        """主动登出；返回 CAS logout URL。"""
        await self._sessions.revoke(snap.session_id)
        await self._audit.write(
            operator=snap,
            op_type="LOGOUT",
            obj_type="user",
            obj_id=str(snap.user_id),
            sync=True,
        )
        logger.info("logout", user_id=snap.user_id)
        cas_settings = get_settings().cas
        return self._provider.logout_url(service=cas_settings.service_url)

    # ── 续期 ──────────────────────────────────────────────────
    async def touch(self, session_id: str) -> SessionData:
        sd = await self._sessions.touch(session_id)
        if sd is None:
            raise Unauthenticated("会话不存在或已过期")
        return sd

    # ── 会话即将过期（前端轮询用）─────────────────────────────
    async def remaining_seconds(self, session_id: str) -> int:
        sd = await self._sessions.get(session_id)
        if sd is None:
            return 0
        delta = sd.expires_at - datetime.now(tz=UTC)
        return max(0, int(delta.total_seconds()))

    @staticmethod
    def expires_in(seconds: int) -> datetime:
        return datetime.now(tz=UTC) + timedelta(seconds=seconds)
