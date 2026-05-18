"""草稿清理定时任务（UC-01）。

每天清理 30 天前的草稿（expires_at < now）及其关联证据文件。
通过 asyncio 后台任务在应用启动时注册，每 24 小时运行一次。
"""

from __future__ import annotations

import asyncio

from app.core.logging import get_logger
from app.infra.db.session import uow
from app.infra.repositories.report import DraftRepository, EvidenceRepository
from app.services.storage_service import delete_evidence_file

logger = get_logger(__name__)

_INTERVAL_SECONDS = 24 * 60 * 60  # 24 小时


async def _run_cleanup() -> None:
    """执行一次清理。"""
    try:
        async with uow() as session:
            evidence_repo = EvidenceRepository(session)
            draft_repo = DraftRepository(session)

            # 先查所有过期草稿
            from datetime import UTC, datetime

            from sqlalchemy import select

            from app.infra.db.models.report_draft import ReportDraft

            now = datetime.now(tz=UTC)
            result = await session.execute(
                select(ReportDraft).where(ReportDraft.expires_at < now)
            )
            expired_drafts = list(result.scalars())

            total_files = 0
            for draft in expired_drafts:
                files = await evidence_repo.list_by_draft(draft.draft_id)
                for ev in files:
                    await delete_evidence_file(ev.storage_path)
                    await evidence_repo.delete(ev)
                    total_files += 1
                await draft_repo.delete(draft)

            if expired_drafts:
                logger.info(
                    "draft_cleanup_done",
                    deleted_drafts=len(expired_drafts),
                    deleted_files=total_files,
                )
    except Exception as exc:
        logger.error("draft_cleanup_failed", error=str(exc))


async def run_draft_cleanup_loop() -> None:
    """无限循环：每 24 小时执行一次清理。在应用 lifespan 中作为后台任务启动。"""
    logger.info("draft_cleanup_task_started", interval_hours=_INTERVAL_SECONDS // 3600)
    while True:
        await asyncio.sleep(_INTERVAL_SECONDS)
        await _run_cleanup()
