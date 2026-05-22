"""学生侧预警接口（UC-03）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.warnings import WarningListItemOut, WarningOut
from app.services import permissions as perm
from app.services.warning_service import (
    get_warning_for_student,
    list_warnings_for_student,
)

router = APIRouter(prefix="/warnings", tags=["warnings (UC-03)"])


@router.get(
    "",
    response_model=PaginationOut[WarningListItemOut],
    summary="学生预警列表（UC-03）",
)
async def list_warnings(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_READ))],
    status: Annotated[str | None, Query(description="状态筛选 ONLINE / OFFLINE，留空表示全部")] = None,
    level: Annotated[int | None, Query(ge=1, le=3, description="预警等级 1=提示 / 2=警告 / 3=紧急")] = None,
    keyword: Annotated[str | None, Query(max_length=128, description="标题 / 正文模糊搜索关键字")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[WarningListItemOut]:
    """学生查看自己可见的预警公告列表（FULL_SCHOOL 或本院系命中）。"""
    items, total = await list_warnings_for_student(
        current=current,
        status=status,
        level=level,
        keyword=keyword,
        page=page,
        size=size,
    )
    return PaginationOut[WarningListItemOut](
        items=items, total=total, page=page, size=size
    )


@router.get(
    "/{warning_id}",
    response_model=WarningOut,
    summary="学生预警详情（UC-03，自动标记已读）",
)
async def warning_detail(
    warning_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.WARNING_READ))],
) -> WarningOut:
    """学生端查看预警详情，同事务幂等记录已读状态。"""
    return await get_warning_for_student(warning_id, current=current)
