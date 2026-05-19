"""审核状态机契约。"""

from __future__ import annotations

from enum import Enum

from app.infra.db.models.fraud_case import CaseStatus


class ReportStatus(str, Enum):
    PENDING = CaseStatus.PENDING
    REVIEWING = CaseStatus.REVIEWING
    HANDLED = CaseStatus.HANDLED
    REJECTED = CaseStatus.REJECTED
    REPORTED = CaseStatus.REPORTED


class OperationType(str, Enum):
    OPEN_DETAIL = "OPEN_DETAIL"
    RESOLVE = "RESOLVE"
    REJECT = "REJECT"
    TRANSFER_POLICE = "TRANSFER_POLICE"


ALLOWED_TRANSITIONS: dict[tuple[ReportStatus, OperationType], ReportStatus] = {
    (ReportStatus.PENDING, OperationType.OPEN_DETAIL): ReportStatus.REVIEWING,
    (ReportStatus.REVIEWING, OperationType.RESOLVE): ReportStatus.HANDLED,
    (ReportStatus.REVIEWING, OperationType.REJECT): ReportStatus.REJECTED,
    (ReportStatus.REVIEWING, OperationType.TRANSFER_POLICE): ReportStatus.REPORTED,
}

TERMINAL_STATES: frozenset[ReportStatus] = frozenset(
    {ReportStatus.HANDLED, ReportStatus.REJECTED, ReportStatus.REPORTED}
)
