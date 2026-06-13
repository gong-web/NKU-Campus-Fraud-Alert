"""上报功能 Schemas（UC-01 / UC-02）。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


STRING_ID_CONFIG = ConfigDict(coerce_numbers_to_str=True)
STRING_ID_ATTR_CONFIG = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)


# ── 诈骗类型 ────────────────────────────────────────────────────────
class FraudTypeOut(BaseModel):
    type_id: int
    type_code: str
    type_name: str
    description: str | None = None
    sort_order: int

    model_config = {"from_attributes": True}


# ── 上报表单 ─────────────────────────────────────────────────────────
class ReportCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=200, description="简短标题")
    description: str = Field(min_length=1, max_length=5000, description="事件详细描述")
    fraud_type_id: int = Field(ge=1, description="诈骗类型 ID")
    incident_date: date = Field(description="事发日期")
    amount: Decimal | None = Field(default=None, ge=0, decimal_places=2, description="涉案金额（元）")
    fraud_method: str | None = Field(default=None, max_length=200, description="诈骗手法简述")
    is_anonymous: bool = Field(default=False, description="是否匿名上报")
    contact_way: str | None = Field(default=None, max_length=200, description="联系方式（可选）")


# ── 上报响应 ─────────────────────────────────────────────────────────
class ReportOut(BaseModel):
    case_id: str
    case_no: str
    title: str
    status: str
    fraud_type_id: int
    fraud_type_name: str | None = None
    incident_date: date
    amount: Decimal | None = None
    is_anonymous: bool
    dept_code: str
    created_at: datetime
    updated_at: datetime

    model_config = STRING_ID_ATTR_CONFIG


class StatusHistoryOut(BaseModel):
    history_id: str
    from_status: str | None
    to_status: str
    operator_id: str
    note: str | None
    created_at: datetime

    model_config = STRING_ID_ATTR_CONFIG


class ReportDetailOut(ReportOut):
    description: str
    fraud_method: str | None = None
    contact_way: str | None = None
    review_note: str | None = None
    reviewed_at: datetime | None = None
    history: list[StatusHistoryOut] = Field(default_factory=list)
    evidence_count: int = 0


# ── 证据文件响应 ──────────────────────────────────────────────────────
class EvidenceFileOut(BaseModel):
    file_id: str
    original_name: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

    model_config = STRING_ID_ATTR_CONFIG


class EvidenceAccessOut(BaseModel):
    model_config = STRING_ID_CONFIG

    file_id: str
    original_name: str
    mime_type: str
    content_base64: str


class ReviewerSummaryOut(BaseModel):
    model_config = STRING_ID_CONFIG

    user_id: str
    real_name: str


class ReporterSummaryOut(BaseModel):
    model_config = STRING_ID_CONFIG

    user_id: str
    real_name: str
    cas_account: str
    department_id: int


class AdminReportListItemOut(BaseModel):
    model_config = STRING_ID_CONFIG

    case_id: str
    case_no: str
    fraud_type_id: int
    fraud_type_name: str | None = None
    title: str
    amount: Decimal | None = None
    status: str
    created_at: datetime
    is_anonymous: bool
    evidence_count: int


class AdminReportDetailOut(BaseModel):
    model_config = STRING_ID_CONFIG

    case_id: str
    case_no: str
    title: str
    description: str
    fraud_type_id: int
    fraud_type_name: str | None = None
    incident_date: date
    amount: Decimal | None = None
    fraud_method: str | None = None
    contact_way: str | None = None
    created_at: datetime
    updated_at: datetime
    status: str
    is_anonymous: bool
    dept_code: str
    review_note: str | None = None
    reviewed_at: datetime | None = None
    reviewer: ReviewerSummaryOut | None = None
    reporter: ReporterSummaryOut | None = None
    evidence_list: list[EvidenceFileOut] = Field(default_factory=list)
    history: list[StatusHistoryOut] = Field(default_factory=list)


class AdminReportListQuery(BaseModel):
    statuses: list[str] = Field(default_factory=lambda: ["PENDING", "REVIEWING"])
    fraud_type_id: int | None = Field(default=None, ge=1)
    date_from: date | None = None
    date_to: date | None = None
    amount_min: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    amount_max: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    keyword: str | None = Field(default=None, max_length=200)
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort: str = Field(default="created_at_desc", pattern="^(created_at_desc|amount_desc)$")


class ResolveReportIn(BaseModel):
    desensitized_summary: str = Field(min_length=1, max_length=4000)
    identification_points: str = Field(min_length=1, max_length=4000)
    prevention_advice: str = Field(min_length=1, max_length=4000)
    internal_remark: str | None = Field(default=None, max_length=500)


class RejectReportIn(BaseModel):
    reason: str = Field(min_length=1, max_length=500)
    internal_remark: str | None = Field(default=None, max_length=500)


class TransferReportIn(BaseModel):
    transfer_note: str = Field(min_length=1, max_length=500)
    internal_remark: str | None = Field(default=None, max_length=500)


class ContactInfoOut(BaseModel):
    phone: str | None = None
    email: str | None = None


class AnonymousDecryptIn(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    reason: str = Field(min_length=1, max_length=2000)
    approver_id: str | None = Field(default=None, pattern=r"^\d+$")


class AnonymousDecryptOut(BaseModel):
    model_config = STRING_ID_CONFIG

    case_id: str
    user_id: str
    real_name: str
    cas_account: str
    phone: str | None = None
    email: str | None = None
    expires_at: datetime


class DashboardTrendPointOut(BaseModel):
    date: str
    submitted: int
    handled: int


class RecentActionOut(BaseModel):
    model_config = STRING_ID_CONFIG

    case_id: str
    case_no: str
    to_status: str
    note: str | None = None
    created_at: datetime


class DashboardSummaryOut(BaseModel):
    pending_count: int
    reviewing_count: int
    today_handled: int
    today_rejected: int
    today_reported: int
    trend_7days: list[DashboardTrendPointOut]
    my_recent_actions: list[RecentActionOut]


# ── 草稿 ─────────────────────────────────────────────────────────────
class DraftSaveIn(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=5000)
    fraud_type_id: int | None = Field(default=None, ge=1)
    incident_date: date | None = None
    amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    fraud_method: str | None = Field(default=None, max_length=200)
    is_anonymous: bool = False
    contact_way: str | None = Field(default=None, max_length=200)


class DraftOut(BaseModel):
    # Snowflake IDs exceed JS safe integer range; expose as string to keep precision in the browser.
    model_config = STRING_ID_ATTR_CONFIG

    draft_id: str
    title: str | None
    description: str | None
    fraud_type_id: int | None
    incident_date: date | None
    amount: Decimal | None
    fraud_method: str | None
    is_anonymous: bool
    contact_way: str | None
    created_at: datetime
    updated_at: datetime
    expires_at: datetime
    evidence_count: int = 0
    evidence_list: list[EvidenceFileOut] = Field(default_factory=list)
