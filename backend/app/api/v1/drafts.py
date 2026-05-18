"""上报草稿接口（UC-01）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.reports import DraftOut, DraftSaveIn, EvidenceFileOut
from app.services import permissions as perm
from app.services import report_service

router = APIRouter(prefix="/drafts", tags=["drafts"])


@router.post(
    "",
    response_model=DraftOut,
    status_code=201,
    summary="保存新草稿",
)
async def create_draft(
    body: DraftSaveIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> DraftOut:
    """创建一条上报草稿。所有字段均可选，草稿 30 天后自动清理。"""
    return await report_service.create_draft(body, current=current)


@router.get(
    "",
    response_model=list[DraftOut],
    summary="草稿箱列表",
)
async def list_drafts(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> list[DraftOut]:
    """返回当前学生的所有草稿。"""
    return await report_service.list_drafts(current=current)


@router.get(
    "/{draft_id}",
    response_model=DraftOut,
    summary="获取草稿详情",
)
async def get_draft(
    draft_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> DraftOut:
    return await report_service.get_draft(draft_id, current=current)


@router.put(
    "/{draft_id}",
    response_model=DraftOut,
    summary="更新草稿",
)
async def update_draft(
    draft_id: int,
    body: DraftSaveIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> DraftOut:
    """更新草稿内容，同时刷新 30 天过期时间。"""
    return await report_service.update_draft(draft_id, body, current=current)


@router.delete(
    "/{draft_id}",
    status_code=204,
    summary="删除草稿",
)
async def delete_draft(
    draft_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> None:
    """删除草稿及其关联证据文件。"""
    await report_service.delete_draft(draft_id, current=current)


@router.post(
    "/{draft_id}/evidence",
    response_model=EvidenceFileOut,
    status_code=201,
    summary="为草稿上传证据",
)
async def upload_draft_evidence(
    draft_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
    file: UploadFile = File(...),
) -> EvidenceFileOut:
    return await report_service.upload_draft_evidence(draft_id, file, current=current)


@router.delete(
    "/{draft_id}/evidence/{file_id}",
    status_code=204,
    summary="删除草稿的某张证据",
)
async def delete_draft_evidence(
    draft_id: int,
    file_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.REPORT_CREATE))],
) -> None:
    await report_service.delete_draft_evidence(draft_id, file_id, current=current)
