"""院系字典接口（UC-07 / UC-10 通用，按 sort_order 排序）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.api.deps import get_current_user
from app.domain.user_snapshot import UserSnapshot
from app.infra.db.models import Department
from app.infra.db.session import uow

router = APIRouter(prefix="/departments", tags=["departments"])


class DepartmentOut(BaseModel):
    """院系下拉项。"""

    model_config = ConfigDict(from_attributes=True)

    dept_id: int
    dept_code: str
    dept_name: str
    parent_dept_id: int | None = None
    dept_level: int
    sort_order: int


@router.get("", response_model=list[DepartmentOut], summary="院系字典（任何登录用户）")
async def list_departments(
    _current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> list[DepartmentOut]:
    """返回所有院系，按 ``sort_order`` 升序，供前端下拉框使用。"""
    async with uow() as session:
        rows = (
            await session.execute(
                select(Department).order_by(Department.sort_order, Department.dept_id)
            )
        ).scalars().all()
    return [DepartmentOut.model_validate(d) for d in rows]
