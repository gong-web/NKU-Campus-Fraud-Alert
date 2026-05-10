"""审计 SDK——团队 4 人每天调用 N 次的核心 API。

设计目标
--------
"一行调用，无脑接入"。两种使用方式：

1. 显式调用（推荐用于 service 层关键节点）::

    await audit.write(
        operator=user,
        op_type="USER_UPDATE",
        obj_type="user",
        obj_id=str(target.user_id),
        before=before_snapshot,
        after=after_snapshot,
    )

2. 装饰器自动（推荐用于简单 service 方法）::

    @audit_logged(op_type="USER_DISABLE", obj_type="user")
    async def disable_user(self, target_id: int, *, current: UserSnapshot) -> User:
        ...

字段
----
- 强制字段：operator / op_type / object_type / object_id / source_ip / user_agent / operated_at
- 非空校验在 SDK 层做；缺一抛 :class:`AuditWriteFailed`，杜绝写半截日志

异步落库
--------
- 默认 ``audit_async_enabled=true``：扔 Redis Stream，主请求路径 O(1)。
- **强一致场景**（PRD 4.2）必须传 ``sync=True`` 同步落库：
    - 登录 / 登出
    - 权限变更
    - 解密匿名身份（UC-10 备选 A2）
- 同步落库的实现：在调用方所属的 ``uow()`` 事务里直接 INSERT。

失败兜底
--------
- 同步路径：DB 失败 → 写 ``logs/audit_fallback.jsonl``（JSON Lines） + 抛
  :class:`AuditWriteFailed`。
- 异步路径：Stream 失败 → 同样写 fallback 文件 + 不阻塞主请求，但记录一条
  ``logger.error``。

哈希链
------
启用时 ``this_hash = SHA256(prev_hash || serialized_payload)``，
``scripts/verify_audit_chain.py`` 离线校验。
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime
from functools import wraps
from pathlib import Path
from typing import Any, ParamSpec, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import AuditWriteFailed
from app.infra.cache.audit_stream import AuditStream
from app.infra.db.models import AuditLog
from app.infra.db.session import uow
from app.infra.repositories.audit import AuditRepository

logger = get_logger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class AuditService:
    """审计 SDK 主入口。"""

    # 强一致场景必须同步落库的操作类型
    SYNC_OP_TYPES: frozenset[str] = frozenset(
        {
            "LOGIN",
            "LOGIN_FAILED",
            "LOGOUT",
            "ROLE_CHANGE",
            "PERMISSION_GRANT",
            "PERMISSION_REVOKE",
            "DECRYPT_ANONYMOUS",
            "DECRYPT_ANONYMOUS_REQUEST",
            "USER_DISABLE",
            "USER_ROLE_CHANGE",
        }
    )

    def __init__(self) -> None:
        self._settings = get_settings().audit
        self._stream = AuditStream() if self._settings.async_enabled else None
        self._fallback_path = Path(self._settings.fallback_path)
        self._fallback_path.parent.mkdir(parents=True, exist_ok=True)

    # ── 主入口：显式调用 ────────────────────────────────────────
    async def write(
        self,
        *,
        operator: UserSnapshot | None,
        op_type: str,
        obj_type: str,
        obj_id: str | int,
        before: dict[str, Any] | None = None,
        after: dict[str, Any] | None = None,
        sync: bool | None = None,
        session: AsyncSession | None = None,
    ) -> int | None:
        """写一条审计。

        Args:
            operator: 操作人（必填，登录前发生的事件可传 ``None``，但 op_type
                必须是 ``LOGIN_FAILED`` 等系统级）。
            op_type: 见 :data:`SYNC_OP_TYPES` + 模块约定。**大写 + 下划线**。
            obj_type / obj_id: 操作对象。
            before / after: JSON 化的状态快照。
            sync: 强制同步 / 异步；默认按 ``op_type`` 自动判定。
            session: 当 ``sync=True`` 时传入的事务 session（与业务原子提交）。

        Returns:
            同步路径返回 log_id；异步路径返回 None。

        Raises:
            AuditWriteFailed: 同步路径失败（已写 fallback）。
        """
        self._validate(operator=operator, op_type=op_type, obj_type=obj_type, obj_id=obj_id)

        if sync is None:
            sync = op_type in self.SYNC_OP_TYPES

        operated_at = datetime.now(tz=UTC)
        payload = self._build_payload(
            operator=operator,
            op_type=op_type,
            obj_type=obj_type,
            obj_id=str(obj_id),
            before=before,
            after=after,
            operated_at=operated_at,
        )

        try:
            if sync:
                return await self._write_sync(payload, session=session)
            await self._write_async(payload)
            return None
        except Exception as exc:
            self._fallback_write(payload, error=str(exc))
            if sync:
                raise AuditWriteFailed(str(exc)) from exc
            logger.error("audit_async_failed_fallback_written", op_type=op_type, error=str(exc))
            return None

    # ── 校验 ──────────────────────────────────────────────────
    @staticmethod
    def _validate(
        *, operator: UserSnapshot | None, op_type: str, obj_type: str, obj_id: object
    ) -> None:
        if not op_type or not op_type.replace("_", "").isalnum() or not op_type.isupper():
            raise AuditWriteFailed(f"非法 op_type: {op_type!r}（要求大写 + 下划线 + 字母数字）")
        if not obj_type or not obj_type.islower():
            raise AuditWriteFailed(f"非法 obj_type: {obj_type!r}（要求小写）")
        if obj_id is None or str(obj_id) == "":
            raise AuditWriteFailed("obj_id 不能为空")
        # operator 仅在 LOGIN_FAILED / SYSTEM 类操作下允许 None
        if operator is None and op_type not in {"LOGIN_FAILED", "CAS_UNREACHABLE", "SYSTEM"}:
            raise AuditWriteFailed(f"op_type={op_type} 必须提供 operator")

    @staticmethod
    def _build_payload(
        *,
        operator: UserSnapshot | None,
        op_type: str,
        obj_type: str,
        obj_id: str,
        before: dict[str, Any] | None,
        after: dict[str, Any] | None,
        operated_at: datetime,
    ) -> dict[str, Any]:
        return {
            "log_id": next_snowflake_id(),
            "operator_id": operator.user_id if operator else 0,
            "operation_type": op_type,
            "object_type": obj_type,
            "object_id": obj_id,
            "before_state": before,
            "after_state": after,
            "source_ip": operator.source_ip if operator else "",
            "user_agent": operator.user_agent if operator else "",
            "trace_id": _current_trace_id(),
            "operated_at": operated_at.isoformat(),
        }

    # ── 同步路径 ────────────────────────────────────────────────
    async def _write_sync(self, payload: dict[str, Any], *, session: AsyncSession | None) -> int:
        if session is not None:
            return await self._insert_with_session(session, payload)

        async with uow() as new_session:
            return await self._insert_with_session(new_session, payload)

    async def _insert_with_session(self, session: AsyncSession, payload: dict[str, Any]) -> int:
        repo = AuditRepository(session)
        prev_hash: str | None = None
        if self._settings.hash_chain_enabled:
            last = await repo.get_last()
            prev_hash = last.this_hash if last else None
            this_hash = _compute_hash(prev_hash=prev_hash, payload=payload)
        else:
            this_hash = None
        log = AuditLog(
            log_id=payload["log_id"],
            operator_id=payload["operator_id"],
            operation_type=payload["operation_type"],
            object_type=payload["object_type"],
            object_id=payload["object_id"],
            before_state=payload["before_state"],
            after_state=payload["after_state"],
            source_ip=payload["source_ip"] or "",
            user_agent=payload["user_agent"] or None,
            trace_id=payload["trace_id"],
            prev_hash=prev_hash,
            this_hash=this_hash,
            operated_at=datetime.fromisoformat(payload["operated_at"]),
        )
        await repo.add(log)
        return log.log_id

    # ── 异步路径 ────────────────────────────────────────────────
    async def _write_async(self, payload: dict[str, Any]) -> None:
        if self._stream is None:
            # 配置关掉异步：降级到同步
            await self._write_sync(payload, session=None)
            return
        await self._stream.push(payload)

    # ── Fallback ────────────────────────────────────────────────
    def _fallback_write(self, payload: dict[str, Any], *, error: str) -> None:
        """落本地 jsonl，启动时由 worker 补写。"""
        record = {**payload, "_fallback_error": error}
        with suppress(OSError), self._fallback_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")


# ── 哈希链 ──────────────────────────────────────────────────────────
def _compute_hash(*, prev_hash: str | None, payload: dict[str, Any]) -> str:
    """``SHA256(prev_hash || canonical_json(payload))``，hex。"""
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    h = hashlib.sha256()
    if prev_hash:
        h.update(prev_hash.encode("ascii"))
    h.update(serialized.encode("utf-8"))
    return h.hexdigest()


# ── trace_id 辅助 ──────────────────────────────────────────────────
def _current_trace_id() -> str | None:
    """从 contextvars 取当前请求的 trace_id（若中间件已绑定）。"""
    from app.core.logging import _trace_id_var

    return _trace_id_var.get()


# ── 装饰器 ──────────────────────────────────────────────────────────
def audit_logged(
    *,
    op_type: str,
    obj_type: str,
    obj_id_arg: str = "obj_id",
    operator_arg: str = "current",
    sync: bool | None = None,
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """装饰器：自动捕获参数与返回值差分写审计。

    用法::

        class UserService:
            @audit_logged(op_type="USER_DISABLE", obj_type="user")
            async def disable_user(
                self, *, obj_id: int, current: UserSnapshot
            ) -> User:
                ...

    要求被装饰的方法必须是 async，且参数中包含 ``obj_id`` 与 ``current``
    （名字可通过参数自定义）。
    """

    def deco(fn: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            operator = kwargs.get(operator_arg)
            obj_id = kwargs.get(obj_id_arg)
            if not isinstance(operator, UserSnapshot):
                raise AuditWriteFailed(f"@audit_logged 要求 kwargs.{operator_arg} 是 UserSnapshot")
            if obj_id is None:
                raise AuditWriteFailed(f"@audit_logged 要求 kwargs.{obj_id_arg} 非空")
            result = await fn(*args, **kwargs)
            try:
                await get_audit_service().write(
                    operator=operator,
                    op_type=op_type,
                    obj_type=obj_type,
                    obj_id=str(obj_id),
                    after={"result": _safe_jsonify(result)},
                    sync=sync,
                )
            except AuditWriteFailed as exc:
                logger.error("audit_decorator_failed", op_type=op_type, error=str(exc))
                if sync:
                    raise
            return result

        return wrapper

    return deco


def _safe_jsonify(obj: object) -> Any:
    """保守地 JSON 化任意对象（避免序列化异常打断主流程）。"""
    try:
        json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return repr(obj)
    return obj


# ── 全局单例 ────────────────────────────────────────────────────────
_audit: AuditService | None = None


def get_audit_service() -> AuditService:
    global _audit
    if _audit is None:
        _audit = AuditService()
    return _audit
