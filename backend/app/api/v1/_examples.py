"""给团队 4 人照抄的最小可工作接口示例。

下面 3 个示例覆盖 80% 的鉴权场景：
1. ``GET /examples/public-warnings``        —— 任何登录用户可访问
2. ``POST /examples/reviewer-only-action``  —— 角色限定（``Reviewer`` / ``SysAdmin``）
3. ``POST /examples/permission-required``   —— 细粒度权限码限定

复制本文件结构，**只换三件事**：路径、schema、service 调用。
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_permission, require_role
from app.domain.user_snapshot import UserSnapshot
from app.services import permissions as perm
from app.services.audit_service import get_audit_service

router = APIRouter(prefix="/examples", tags=["examples (照抄即可)"])


# ── 例 1：任何登录用户 ───────────────────────────────────────────
class _PublicWarningOut(BaseModel):
    id: int
    title: str
    level: str


@router.get(
    "/public-warnings",
    response_model=list[_PublicWarningOut],
    summary="任何登录用户可访问",
)
async def list_public_warnings(
    current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> list[_PublicWarningOut]:
    """
    Args
    ----
    current
        通过 :func:`get_current_user` 注入的当前用户。
    """
    del current  # 不参与逻辑；只是示意鉴权依赖
    return [
        _PublicWarningOut(id=1, title="刷单返利新变种警示", level="WARNING"),
        _PublicWarningOut(id=2, title="冒充客服退款", level="INFO"),
    ]


# ── 例 2：角色限定 ───────────────────────────────────────────────
class _ReviewActionIn(BaseModel):
    report_id: int = Field(ge=1)
    note: str = Field(min_length=1, max_length=500)


@router.post(
    "/reviewer-only-action",
    summary="仅 Reviewer / SysAdmin 可调用",
)
async def reviewer_only_action(
    body: _ReviewActionIn,
    current: Annotated[UserSnapshot, Depends(require_role("Reviewer", "SysAdmin"))],
) -> dict[str, object]:
    """演示：角色限定 + 审计 SDK 一行接入。"""
    audit = get_audit_service()
    await audit.write(
        operator=current,
        op_type="EXAMPLE_REVIEWER_ACTION",
        obj_type="report",
        obj_id=str(body.report_id),
        after={"note": body.note[:80]},
    )
    return {"ok": True, "by": current.cas_account}


# ── 例 3：细粒度权限码 ───────────────────────────────────────────
@router.post(
    "/permission-required",
    summary="细粒度权限码：require_permission('user:create')",
)
async def permission_required_example(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.USER_CREATE))],
) -> dict[str, object]:
    """
    用 :func:`require_permission` 注入。最常用——业务模块 80% 接口都该这样写。
    """
    return {"ok": True, "by": current.cas_account, "role": current.role_code}
