"""司法协助查询（UC-10 备选 A2）—— 全平台最高敏。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Path

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.judicial import (
    JudicialDecryptOut,
    JudicialDecryptRequestIn,
    JudicialDecryptRequestOut,
)
from app.services import permissions as perm
from app.services.judicial_service import JudicialService

router = APIRouter(prefix="/judicial-assist", tags=["judicial (UC-10 A2)"])
_svc = JudicialService()


@router.post(
    "/request-decryption",
    response_model=JudicialDecryptRequestOut,
    summary="发起解密申请（5 分钟窗口）",
)
async def request_decryption(
    body: JudicialDecryptRequestIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.JUDICIAL_REQUEST_DECRYPT))],
) -> JudicialDecryptRequestOut:
    res = await _svc.request_decryption(
        operator=current,
        report_id=body.report_id,
        judicial_doc_no=body.judicial_doc_no,
        reason=body.reason,
        related_case_no=body.related_case_no,
    )
    return JudicialDecryptRequestOut(**res)


@router.get(
    "/{decrypt_log_id}/reveal",
    response_model=JudicialDecryptOut,
    summary="在窗口内解密（一次性）",
)
async def reveal(
    decrypt_log_id: Annotated[int, Path(ge=1)],
    current: Annotated[UserSnapshot, Depends(require_permission(perm.JUDICIAL_REQUEST_DECRYPT))],
) -> JudicialDecryptOut:
    res = await _svc.decrypt(operator=current, decrypt_log_id=decrypt_log_id)
    return JudicialDecryptOut(**res)
