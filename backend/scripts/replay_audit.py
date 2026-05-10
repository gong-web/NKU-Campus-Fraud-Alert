"""重放某个对象的全生命周期审计（PRD 4.3）。

用法
----
``python -m scripts.replay_audit --type report --id 2026-CS-000123``

输出按 ``operated_at`` 顺序的所有相关 audit log，便于现场调试 / 出问题溯源。
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from app.core.logging import configure_logging, get_logger
from app.infra.db.session import uow
from app.infra.repositories.audit import AuditRepository

logger = get_logger(__name__)


async def _replay(*, object_type: str, object_id: str) -> None:
    async with uow() as session:
        repo = AuditRepository(session)
        items = await repo.list_by_object(object_type=object_type, object_id=object_id)
    if not items:
        print(f"[empty] no audit logs for {object_type}:{object_id}")
        return
    print(f"=== Audit timeline for {object_type}:{object_id} ({len(items)} entries) ===")
    for log in items:
        print(
            f"{log.operated_at.isoformat()} | "
            f"op={log.operation_type:<28} | "
            f"by={log.operator_id} | "
            f"trace={log.trace_id or '-'}"
        )


def _main() -> int:
    parser = argparse.ArgumentParser(description="按 object 重放审计日志")
    parser.add_argument("--type", required=True, dest="object_type")
    parser.add_argument("--id", required=True, dest="object_id")
    args = parser.parse_args()

    configure_logging(level="INFO")
    asyncio.run(_replay(object_type=args.object_type, object_id=args.object_id))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
