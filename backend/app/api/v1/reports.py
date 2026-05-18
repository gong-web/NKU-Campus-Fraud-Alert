"""上报接口（UC-01 / UC-02）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.api.deps import get_current_user, require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.reports import EvidenceFileOut, ReportCreateIn, ReportDetailOut, ReportOut
from app.services import permissions as perm
from app.services import report_service
from app.services.report_service import BusinessError

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post(
    "",
    response_model=ReportOut,
    status_code=201,
    summary="提交上报（UC-01）",
)
async def create_report(
    body: ReportCreateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> ReportOut:
    """学生提交诈骗事件上报。支持实名 / 匿名。"""
    return await report_service.create_report(body, current=current)


@router.post(
    "/{case_id}/evidence",
    response_model=EvidenceFileOut,
    status_code=201,
    summary="上传证据图片（UC-01）",
)
async def upload_evidence(
    case_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
    file: UploadFile = File(..., description="图片文件（JPEG / PNG / GIF / PDF，≤5 MB）"),
) -> EvidenceFileOut:
    """上传一张证据图片。最多 10 张，每张 ≤5 MB。文件服务端 AES-256-GCM 加密后落盘。"""
    return await report_service.upload_evidence(case_id, file, current=current)


@router.get(
    "/my",
    response_model=PaginationOut[ReportOut],
    summary="我的上报列表（UC-02）",
)
async def my_reports(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_READ_OWN))],
    status: str | None = Query(default=None, description="按状态筛选（PENDING/REVIEWING/HANDLED/REJECTED/REPORTED）"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> PaginationOut[ReportOut]:
    """返回当前学生自己提交的所有上报记录（分页）。"""
    items, total = await report_service.list_my_reports(
        current=current, status=status, page=page, size=size
    )
    return PaginationOut(items=items, total=total, page=page, size=size)


@router.get(
    "/{case_id}",
    response_model=ReportDetailOut,
    summary="上报详情 + 处理时间线（UC-02）",
)
async def report_detail(
    case_id: int,
    current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> ReportDetailOut:
    """获取单条上报的完整详情与状态变更历史。

    学生只能查看自己的案件；审核员可查看所有案件。
    """
    return await report_service.get_report_detail(case_id, current=current)
