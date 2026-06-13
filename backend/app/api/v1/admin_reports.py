"""管理员审核接口（UC-06）。"""

from __future__ import annotations

import base64
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response

from app.api.deps import require_permission, require_role
from app.api.response_headers import content_disposition
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.reports import (
    AdminReportDetailOut,
    AdminReportListItemOut,
    AdminReportListQuery,
    AnonymousDecryptIn,
    AnonymousDecryptOut,
    ContactInfoOut,
    DashboardSummaryOut,
    RejectReportIn,
    ResolveReportIn,
    TransferReportIn,
)
from app.services import permissions as perm
from app.services.review_service import (
    contact_reporter,
    decrypt_anonymous_reporter,
    get_admin_report_detail,
    get_dashboard_summary,
    list_admin_reports,
    reject_report,
    resolve_report,
    transfer_report,
    view_evidence,
)

router = APIRouter(prefix="/admin", tags=["admin-review"])


@router.get("/reports", response_model=PaginationOut[AdminReportListItemOut], summary="审核事件列表")
async def admin_reports(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_READ_ALL))],
    status: list[str] | None = Query(default=None),
    fraud_type_id: int | None = Query(default=None, ge=1),
    date_from: str | None = Query(default=None),
    date_to: str | None = Query(default=None),
    amount_min: float | None = Query(default=None, ge=0),
    amount_max: float | None = Query(default=None, ge=0),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="created_at_desc"),
) -> PaginationOut[AdminReportListItemOut]:
    query = AdminReportListQuery(
        statuses=status or ["PENDING", "REVIEWING"],
        fraud_type_id=fraud_type_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        keyword=keyword,
        page=page,
        size=size,
        sort=sort,
    )
    items, total = await list_admin_reports(current=current, query=query)
    return PaginationOut(items=items, total=total, page=page, size=size)


@router.get("/reports/{case_id}", response_model=AdminReportDetailOut, summary="审核事件详情")
async def admin_report_detail(
    case_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_READ_ALL))],
) -> AdminReportDetailOut:
    return await get_admin_report_detail(case_id=case_id, current=current)


@router.post("/reports/{case_id}/resolve", summary="录入案例库并处理完成")
async def admin_resolve_report(
    case_id: int,
    body: ResolveReportIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_REVIEW))],
) -> dict[str, int | str]:
    return await resolve_report(case_id=case_id, current=current, **body.model_dump())


@router.post("/reports/{case_id}/reject", summary="驳回案件")
async def admin_reject_report(
    case_id: int,
    body: RejectReportIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_REVIEW))],
) -> dict[str, str]:
    return await reject_report(case_id=case_id, current=current, **body.model_dump())


@router.post("/reports/{case_id}/transfer", summary="转报警")
async def admin_transfer_report(
    case_id: int,
    body: TransferReportIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_REVIEW))],
) -> dict[str, str]:
    return await transfer_report(case_id=case_id, current=current, **body.model_dump())


@router.post(
    "/reports/{case_id}/contact-request",
    response_model=ContactInfoOut,
    summary="查看联系方式",
)
async def admin_contact_request(
    case_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_REVIEW))],
) -> ContactInfoOut:
    return await contact_reporter(case_id=case_id, current=current)


@router.get("/reports/{case_id}/evidence/{file_id}", summary="查看证据文件")
async def admin_evidence_content(
    case_id: int,
    file_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_VIEW_EVIDENCE))],
    x_confirm_sensitive_access: str | None = Header(default=None),
) -> Response:
    access = await view_evidence(
        case_id=case_id,
        file_id=file_id,
        current=current,
        confirmed=x_confirm_sensitive_access == "yes",
    )
    return Response(
        content=base64.b64decode(access.content_base64),
        media_type=access.mime_type,
        headers={
            "Content-Disposition": content_disposition(
                access.original_name,
                fallback_filename="evidence",
            )
        },
    )


@router.post(
    "/reports/{case_id}/decrypt-anonymous",
    response_model=AnonymousDecryptOut,
    summary="解密匿名上报者身份",
)
async def admin_decrypt_anonymous(
    case_id: int,
    body: AnonymousDecryptIn,
    current: Annotated[UserSnapshot, Depends(require_role("SYS_ADMIN"))],
) -> AnonymousDecryptOut:
    payload = body.model_dump()
    if payload.get("approver_id") is not None:
        payload["approver_id"] = int(payload["approver_id"])
    return await decrypt_anonymous_reporter(case_id=case_id, current=current, **payload)


@router.get(
    "/dashboard/summary",
    response_model=DashboardSummaryOut,
    summary="审核工作台摘要",
)
async def admin_dashboard_summary(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_READ_ALL))],
) -> DashboardSummaryOut:
    return await get_dashboard_summary(current=current)
