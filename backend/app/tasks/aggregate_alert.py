"""聚合告警定时任务。"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger
from app.services.review_service import run_aggregate_alert_check

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_aggregate_alert_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_aggregate_alert_check, "cron", minute=0, id="aggregate-alert")
    scheduler.start()
    _scheduler = scheduler
    logger.info("aggregate_alert_scheduler_started")
    return scheduler


def stop_aggregate_alert_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
