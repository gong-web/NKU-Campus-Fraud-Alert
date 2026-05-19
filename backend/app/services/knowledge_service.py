"""知识库草稿适配服务。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.snowflake import next_snowflake_id
from app.infra.db.models import KnowledgeDraft
from app.infra.db.session import uow


async def create_knowledge_draft_from_report(
    *,
    report_id: int,
    desensitized_summary: str,
    identification_points: str,
    prevention_advice: str,
    fraud_type_id: int,
    author_id: int,
    db_session: AsyncSession | None = None,
) -> int:
    """创建知识库草稿，为后续 UC-08 审核发布留出接口。"""

    async def _create(session: AsyncSession) -> int:
        row = KnowledgeDraft(
            entry_id=next_snowflake_id(),
            report_id=report_id,
            desensitized_summary=desensitized_summary,
            identification_points=identification_points,
            prevention_advice=prevention_advice,
            fraud_type_id=fraud_type_id,
            author_id=author_id,
        )
        session.add(row)
        await session.flush()
        return row.entry_id

    if db_session is not None:
        return await _create(db_session)

    async with uow() as session:
        return await _create(session)
