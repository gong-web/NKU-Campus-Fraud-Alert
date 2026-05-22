"""审核管理员预警接口（UC-07）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.warnings import (
    WarningAppendIn,
    WarningCreateIn,
    WarningListItemOut,
    WarningOfflineIn,
    WarningOut,
)
from app.services import permissions as perm
from app.services.warning_service import (
    append_warning,
    get_warning_for_admin,
    list_warnings_for_admin,
    offline_warning,
    publish_warning,
)

router = APIRouter(prefix="/admin/warnings", tags=["admin-warnings (UC-07)"])


@router.post(
    "",
    response_model=WarningOut,
    status_code=201,
    summary="发布预警（UC-07 步骤 4）",
)
async def admin_publish_warning(
    body: WarningCreateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_PUBLISH))],
) -> WarningOut:
    """发布预警公告。紧急级（level=3）业务层会再次校验仅校级管理员可发。"""
    return await publish_warning(body, current=current)


@router.get(
    "",
    response_model=PaginationOut[WarningListItemOut],
    summary="管理员预警列表",
)
async def admin_list_warnings(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_PUBLISH))],
    status: Annotated[str | None, Query(description="状态筛选 ONLINE / OFFLINE，留空表示全部")] = None,
    level: Annotated[int | None, Query(ge=1, le=3, description="预警等级 1/2/3")] = None,
    keyword: Annotated[str | None, Query(max_length=128, description="标题 / 正文模糊搜索关键字")] = None,
    publisher_id: Annotated[int | None, Query(ge=1, description="按发布人筛选")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[WarningListItemOut]:
    """管理员可看到所有预警（含已下线），用于回顾与追加管理。"""
    items, total = await list_warnings_for_admin(
        current=current,
        status=status,
        level=level,
        keyword=keyword,
        publisher_id=publisher_id,
        page=page,
        size=size,
    )
    return PaginationOut[WarningListItemOut](
        items=items, total=total, page=page, size=size
    )


@router.get(
    "/{warning_id}",
    response_model=WarningOut,
    summary="管理员预警详情",
)
async def admin_warning_detail(
    warning_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_PUBLISH))],
) -> WarningOut:
    """管理员侧详情。"""
    return await get_warning_for_admin(warning_id, current=current)


@router.post(
    "/{warning_id}/append",
    response_model=WarningOut,
    summary="追加后续说明（UC-07 步骤 8）",
)
async def admin_append_warning(
    warning_id: int,
    body: WarningAppendIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_APPEND))],
) -> WarningOut:
    """对已上线预警追加后续说明，自动以 ``\\n----\\n`` 拼接历史追加。"""
    return await append_warning(warning_id, body, current=current)


@router.post(
    "/{warning_id}/offline",
    summary="手动下线预警（UC-07 步骤 6）",
)
async def admin_offline_warning(
    warning_id: int,
    body: WarningOfflineIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_OFFLINE))],
) -> dict[str, str]:
    """将预警手动下线；下线后学生端不再可见，管理员仍可查看。"""
    return await offline_warning(warning_id, body, current=current)
