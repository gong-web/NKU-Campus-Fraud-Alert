"""审计日志查询接口（UC-10 备选 A1）。"""

from __future__ import annotations

import csv
from datetime import datetime
from io import StringIO
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.api.deps import require_permission
from app.api.response_headers import content_disposition
from app.domain.user_snapshot import UserSnapshot
from app.infra.db.session import uow
from app.infra.repositories.audit import AuditRepository
from app.schemas.audit import AuditLogOut
from app.schemas.common import PaginationOut
from app.services import permissions as perm
from app.services.audit_service import get_audit_service

router = APIRouter(prefix="/audit-logs", tags=["audit (UC-10 备选 A1)"])


@router.get(
    "",
    response_model=PaginationOut[AuditLogOut],
    summary="审计日志列表（仅 SysAdmin）",
)
async def list_audit_logs(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.AUDIT_READ))],
    op_type: Annotated[str | None, Query(max_length=64)] = None,
    operator_id: Annotated[int | None, Query()] = None,
    object_type: Annotated[str | None, Query(max_length=32)] = None,
    object_id: Annotated[str | None, Query(max_length=64)] = None,
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=200)] = 50,
) -> PaginationOut[AuditLogOut]:
    del current
    async with uow() as session:
        repo = AuditRepository(session)
        items, total = await repo.list(
            op_type=op_type,
            operator_id=operator_id,
            object_type=object_type,
            object_id=object_id,
            start=start,
            end=end,
            offset=(page - 1) * size,
            limit=size,
        )
    return PaginationOut[AuditLogOut](
        items=[AuditLogOut.model_validate(x) for x in items],
        total=total,
        page=page,
        size=size,
    )


@router.get(
    "/by-object",
    response_model=list[AuditLogOut],
    summary="跨用户全链路追溯：根据 object_type + object_id 拉所有相关日志",
)
async def list_by_object(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.AUDIT_READ))],
    object_type: Annotated[str, Query(min_length=1, max_length=32)],
    object_id: Annotated[str, Query(min_length=1, max_length=64)],
) -> list[AuditLogOut]:
    del current
    async with uow() as session:
        repo = AuditRepository(session)
        items = await repo.list_by_object(object_type=object_type, object_id=object_id)
    return [AuditLogOut.model_validate(x) for x in items]


@router.get(
    "/export",
    summary="CSV 导出（导出动作本身也写审计）",
)
async def export_audit_logs(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.AUDIT_EXPORT))],
    op_type: Annotated[str | None, Query(max_length=64)] = None,
    operator_id: Annotated[int | None, Query()] = None,
    object_type: Annotated[str | None, Query(max_length=32)] = None,
    object_id: Annotated[str | None, Query(max_length=64)] = None,
    start: Annotated[datetime | None, Query()] = None,
    end: Annotated[datetime | None, Query()] = None,
) -> StreamingResponse:
    async with uow() as session:
        repo = AuditRepository(session)
        rows = await repo.export_csv_rows(
            op_type=op_type,
            operator_id=operator_id,
            object_type=object_type,
            object_id=object_id,
            start=start,
            end=end,
        )
    buf = StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=[
            "log_id",
            "operator_id",
            "operation_type",
            "object_type",
            "object_id",
            "source_ip",
            "trace_id",
            "operated_at",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    audit = get_audit_service()
    await audit.write(
        operator=current,
        op_type="AUDIT_EXPORT",
        obj_type="audit",
        obj_id=f"export:{len(rows)}",
        after={
            "row_count": len(rows),
            "filters": {
                "op_type": op_type,
                "operator_id": operator_id,
                "object_type": object_type,
                "object_id": object_id,
            },
        },
        sync=True,
    )
    payload = buf.getvalue().encode("utf-8-sig")
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": content_disposition(
                "audit_logs.csv",
                disposition="attachment",
                fallback_filename="audit_logs.csv",
            ),
            "Cache-Control": "no-store",
        },
    )
