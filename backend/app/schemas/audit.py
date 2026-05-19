"""审计查询 schemas。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)

    log_id: str
    operator_id: str
    operation_type: str
    object_type: str
    object_id: str
    before_state: dict[str, Any] | None = None
    after_state: dict[str, Any] | None = None
    source_ip: str
    trace_id: str | None = None
    operated_at: datetime


class AuditFilterIn(BaseModel):
    op_type: str | None = Field(default=None, max_length=64)
    operator_id: int | None = None
    object_type: str | None = Field(default=None, max_length=32)
    object_id: str | None = Field(default=None, max_length=64)
    start: datetime | None = None
    end: datetime | None = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=50, ge=1, le=200)
