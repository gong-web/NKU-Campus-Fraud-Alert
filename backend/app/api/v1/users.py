"""账号管理（UC-10）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Path, Query

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.users import UserBatchImportIn, UserCreateIn, UserOut, UserUpdateIn
from app.services import permissions as perm
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users (UC-10)"])
_svc = UserService()


@router.get(
    "",
    response_model=PaginationOut[UserOut],
    summary="账号列表（管理员）",
)
async def list_users(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.USER_READ))],
    role_id: Annotated[int | None, Query(description="按角色过滤")] = None,
    department_id: Annotated[int | None, Query(description="按院系过滤")] = None,
    status: Annotated[int | None, Query(description="按状态过滤")] = None,
    keyword: Annotated[str | None, Query(max_length=64)] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[UserOut]:
    res = await _svc.list_users(
        operator=current,
        role_id=role_id,
        department_id=department_id,
        status=status,
        keyword=keyword,
        page=page,
        size=size,
    )
    return PaginationOut[UserOut](
        items=[UserOut(**x) for x in res["items"]],
        total=res["total"],
        page=res["page"],
        size=res["size"],
    )


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="账号详情",
)
async def get_user(
    user_id: Annotated[int, Path(ge=1)],
    current: Annotated[UserSnapshot, Depends(require_permission(perm.USER_READ))],
) -> UserOut:
    data = await _svc.get_user(target_id=user_id, operator=current)
    return UserOut(**data)


@router.post(
    "",
    response_model=UserOut,
    status_code=201,
    summary="创建账号",
)
async def create_user(
    body: UserCreateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.USER_CREATE))],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=64)] = None,
) -> UserOut:
    data = await _svc.create_user(
        operator=current,
        cas_account=body.cas_account,
        real_name=body.real_name,
        department_id=body.department_id,
        role_id=body.role_id,
        email=str(body.email) if body.email else None,
        phone=body.phone,
        idempotency_key=idempotency_key,
    )
    return UserOut(**data)


@router.patch(
    "/{user_id}",
    summary="部分更新（角色 / 状态）",
)
async def patch_user(
    user_id: Annotated[int, Path(ge=1)],
    body: UserUpdateIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.USER_UPDATE))],
) -> dict[str, object]:
    if body.role_id is not None:
        await _svc.change_role(target_id=user_id, new_role_id=body.role_id, operator=current)
    if body.status is not None:
        if body.status == 1:
            await _svc.enable_user(target_id=user_id, operator=current)
        elif body.status == 2:
            await _svc.disable_user(target_id=user_id, operator=current, reason=body.reason)
    return {"ok": True}


@router.post(
    "/import",
    summary="CSV 批量导入（新生名单）",
)
async def import_users(
    body: UserBatchImportIn,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.USER_BATCH_IMPORT))],
) -> dict[str, object]:
    return await _svc.import_csv(csv_text=body.csv_text, operator=current, dry_run=body.dry_run)
