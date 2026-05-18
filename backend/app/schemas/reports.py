"""上报功能 Schemas（UC-01 / UC-02）。"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


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
    title: str = Field(min_length=2, max_length=200, description="简短标题")
    description: str = Field(min_length=10, max_length=5000, description="事件详细描述（建议 200 字以上）")
    fraud_type_id: int = Field(ge=1, description="诈骗类型 ID")
    incident_date: date = Field(description="事发日期")
    amount: Decimal | None = Field(default=None, ge=0, decimal_places=2, description="涉案金额（元）")
    fraud_method: str | None = Field(default=None, max_length=200, description="诈骗手法简述")
    is_anonymous: bool = Field(default=False, description="是否匿名上报")
    contact_way: str | None = Field(default=None, max_length=200, description="联系方式（可选）")


# ── 上报响应 ─────────────────────────────────────────────────────────
class ReportOut(BaseModel):
    case_id: int
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

    model_config = {"from_attributes": True}


class StatusHistoryOut(BaseModel):
    history_id: int
    from_status: str | None
    to_status: str
    operator_id: int
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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
    file_id: int
    original_name: str
    file_size: int
    mime_type: str
    uploaded_at: datetime

    model_config = {"from_attributes": True}


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
    draft_id: int
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

    model_config = {"from_attributes": True}
