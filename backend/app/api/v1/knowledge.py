"""学生侧知识库接口（UC-04）。"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.schemas.common import PaginationOut
from app.schemas.knowledge import KnowledgeDetailOut, KnowledgeListItemOut
from app.services import knowledge_entry_service
from app.services import permissions as perm

router = APIRouter(prefix="/knowledge", tags=["knowledge (UC-04)"])


@router.get(
    "",
    response_model=PaginationOut[KnowledgeListItemOut],
    summary="知识库浏览列表（UC-04，强制 PUBLISHED）",
)
async def list_knowledge(
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_READ))],
    keyword: Annotated[str | None, Query(max_length=128, description="标题 / 摘要全文搜索关键字")] = None,
    fraud_type_id: Annotated[int | None, Query(ge=1, description="按诈骗类型筛选")] = None,
    sort: Annotated[str, Query(description="排序 published_at_desc / hot")] = "published_at_desc",
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginationOut[KnowledgeListItemOut]:
    """学生浏览知识库已发布条目；支持关键字 / 类型 / 排序。"""
    del current  # 仅用于鉴权
    items, total = await knowledge_entry_service.list_public(
        keyword=keyword,
        fraud_type_id=fraud_type_id,
        page=page,
        size=size,
        sort=sort,
    )
    return PaginationOut[KnowledgeListItemOut](
        items=items, total=total, page=page, size=size
    )


@router.get(
    "/{entry_id}",
    response_model=KnowledgeDetailOut,
    summary="知识库条目详情 + 同类推荐（UC-04）",
)
async def knowledge_detail(
    entry_id: int,
    current: Annotated[UserSnapshot, Depends(require_permission(perm.KB_READ))],
) -> KnowledgeDetailOut:
    """学生查看条目详情，附带同 ``fraud_type_id`` 的最近 3 条已发布相关条目。"""
    return await knowledge_entry_service.get_public(entry_id, current=current)
