"""测验截止前 24h 提醒定时任务（UC-09）。

每小时跑一次：扫描所有 ``ACTIVE`` 的指定测验，若 ``deadline_at`` 落在
[now, now+24h) 且未发过提醒，给参与范围内未提交的学生各发一条站内通知。
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.logging import get_logger
from app.services.quiz_service import send_quiz_deadline_reminders

logger = get_logger(__name__)

_scheduler: AsyncIOScheduler | None = None


def start_quiz_reminder_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    scheduler = AsyncIOScheduler()
    # 每小时第 5 分钟跑一次，避开整点高峰
    scheduler.add_job(
        send_quiz_deadline_reminders, "cron", minute=5, id="quiz-deadline-reminder"
    )
    scheduler.start()
    _scheduler = scheduler
    logger.info("quiz_reminder_scheduler_started")
    return scheduler


def stop_quiz_reminder_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
