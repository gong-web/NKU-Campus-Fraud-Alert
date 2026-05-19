"""司法协助查询 schemas。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class JudicialDecryptRequestIn(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    report_id: str = Field(min_length=1, pattern=r"^\d+$", description="目标事件 report_id")
    judicial_doc_no: str = Field(min_length=1, max_length=64, description="协查文书编号（必填）")
    reason: str = Field(min_length=8, max_length=2000, description="申请理由（≥ 8 字）")
    related_case_no: str | None = Field(default=None, max_length=32)


class JudicialDecryptRequestOut(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    decrypt_log_id: str
    expires_at: str
    window_seconds: int


class JudicialDecryptOut(BaseModel):
    model_config = ConfigDict(coerce_numbers_to_str=True)

    report_id: str
    user_id: str
    real_name: str
    cas_account: str
    watermark_text: str
    expires_at: str
