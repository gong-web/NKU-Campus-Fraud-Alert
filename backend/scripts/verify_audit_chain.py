"""审计链校验（PRD 5.5 可选增强）。

按 ``log_id`` 升序遍历 ``audit_logs``，逐条重算 ``this_hash`` 并与库中字段比
对。任何一次篡改都会让该条以及之后所有条的哈希失效。

输出
----
- 全部 OK：``audit_chain_ok`` 行 + exit 0
- 发现破坏：打出"首次失败"行号 + exit 2

用法
----
``python -m scripts.verify_audit_chain``

也可在 PR 演示时给老师/助教看效果——故意 UPDATE 一条日志（绕过权限直接到
DB），再跑这个脚本，可看到红字告警。
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import sys
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import configure_logging, get_logger
from app.infra.db.models import AuditLog
from app.infra.db.session import uow

logger = get_logger(__name__)


def _serialize_payload(log: AuditLog) -> dict[str, Any]:
    return {
        "log_id": log.log_id,
        "operator_id": log.operator_id,
        "operation_type": log.operation_type,
        "object_type": log.object_type,
        "object_id": log.object_id,
        "before_state": log.before_state,
        "after_state": log.after_state,
        "source_ip": log.source_ip or "",
        "user_agent": log.user_agent or "",
        "trace_id": log.trace_id,
        "operated_at": log.operated_at.isoformat() if log.operated_at else None,
    }


def _compute_hash(*, prev_hash: str | None, payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    h = hashlib.sha256()
    if prev_hash:
        h.update(prev_hash.encode("ascii"))
    h.update(serialized.encode("utf-8"))
    return h.hexdigest()


async def verify(session: AsyncSession) -> tuple[bool, int, str]:
    """返回 (是否通过, 校验条数, 出错原因)。"""
    stmt = select(AuditLog).order_by(AuditLog.log_id)
    result = await session.execute(stmt)
    prev_hash: str | None = None
    count = 0
    async for batch in result.partitions(500):
        for log in batch:
            count += 1
            if log.this_hash is None:
                # 老数据没启用哈希链；记录但不视为破坏
                continue
            expected = _compute_hash(prev_hash=prev_hash, payload=_serialize_payload(log))
            if expected != log.this_hash:
                return (
                    False,
                    count,
                    f"log_id={log.log_id} hash mismatch (expect {expected}, got {log.this_hash})",
                )
            if log.prev_hash != prev_hash:
                return (
                    False,
                    count,
                    f"log_id={log.log_id} prev_hash mismatch (expect {prev_hash}, got {log.prev_hash})",
                )
            prev_hash = log.this_hash
    return True, count, ""


async def _main() -> int:
    configure_logging(level="INFO")
    async with uow() as session:
        ok, count, reason = await verify(session)
    if ok:
        logger.info("audit_chain_ok", count=count)
        return 0
    logger.error("audit_chain_broken", count=count, reason=reason)
    return 2


if __name__ == "__main__":
    sys.exit(asyncio.run(_main()))
