"""诈骗类型接口（UC-01 字典接口）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.domain.user_snapshot import UserSnapshot
from app.schemas.reports import FraudTypeOut
from app.services import report_service

router = APIRouter(prefix="/fraud-types", tags=["fraud-types"])


@router.get("", response_model=list[FraudTypeOut], summary="诈骗类型字典（任何登录用户）")
async def list_fraud_types(
    _current: Annotated[UserSnapshot, Depends(get_current_user)],
) -> list[FraudTypeOut]:
    """返回所有启用中的诈骗类型，供前端下拉框使用。"""
    return await report_service.list_fraud_types()
