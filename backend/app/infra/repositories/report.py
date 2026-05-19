"""上报业务仓储（UC-01 / UC-02）。"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db.models.case_anonymous_reporter import CaseAnonymousReporter
from app.infra.db.models.case_status_history import CaseStatusHistory
from app.infra.db.models.department import Department
from app.infra.db.models.evidence_file import EvidenceFile
from app.infra.db.models.fraud_case import FraudCase
from app.infra.db.models.fraud_type import FraudType
from app.infra.db.models.report_draft import ReportDraft


class FraudTypeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_active(self) -> list[FraudType]:
        result = await self._s.execute(
            select(FraudType)
            .where(FraudType.is_active == True)  # noqa: E712
            .order_by(FraudType.sort_order, FraudType.type_id)
        )
        return list(result.scalars())

    async def get_by_id(self, type_id: int) -> FraudType | None:
        return (
            await self._s.execute(select(FraudType).where(FraudType.type_id == type_id))
        ).scalar_one_or_none()


class DepartmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_by_id(self, dept_id: int) -> Department | None:
        return (
            await self._s.execute(select(Department).where(Department.dept_id == dept_id))
        ).scalar_one_or_none()


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, case: FraudCase) -> FraudCase:
        self._s.add(case)
        await self._s.flush()
        return case

    async def get_by_id(self, case_id: int) -> FraudCase | None:
        return (
            await self._s.execute(select(FraudCase).where(FraudCase.case_id == case_id))
        ).scalar_one_or_none()

    async def get_by_case_no(self, case_no: str) -> FraudCase | None:
        return (
            await self._s.execute(select(FraudCase).where(FraudCase.case_no == case_no))
        ).scalar_one_or_none()

    async def list_by_student(
        self,
        student_id: int,
        *,
        anonymous_case_ids: list[int] | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[FraudCase], int]:
        owner_filter = FraudCase.reporter_id == student_id
        if anonymous_case_ids:
            owner_filter = or_(owner_filter, FraudCase.case_id.in_(anonymous_case_ids))

        q = select(FraudCase).where(owner_filter)
        if status:
            q = q.where(FraudCase.status == status)
        total_result = await self._s.execute(
            select(func.count()).select_from(q.subquery())
        )
        total = total_result.scalar_one()
        items_result = await self._s.execute(
            q.order_by(FraudCase.created_at.desc()).offset(offset).limit(limit)
        )
        return list(items_result.scalars()), total

    async def add_anonymous_reporter(self, mapping: CaseAnonymousReporter) -> None:
        self._s.add(mapping)
        await self._s.flush()

    async def add_status_history(self, history: CaseStatusHistory) -> None:
        self._s.add(history)
        await self._s.flush()


class EvidenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, ev: EvidenceFile) -> EvidenceFile:
        self._s.add(ev)
        await self._s.flush()
        return ev

    async def list_by_case(self, case_id: int) -> list[EvidenceFile]:
        result = await self._s.execute(
            select(EvidenceFile)
            .where(EvidenceFile.case_id == case_id)
            .order_by(EvidenceFile.uploaded_at)
        )
        return list(result.scalars())

    async def count_by_case(self, case_id: int) -> int:
        result = await self._s.execute(
            select(func.count()).where(EvidenceFile.case_id == case_id)
        )
        return result.scalar_one()

    async def list_by_draft(self, draft_id: int) -> list[EvidenceFile]:
        result = await self._s.execute(
            select(EvidenceFile)
            .where(EvidenceFile.draft_id == draft_id)
            .order_by(EvidenceFile.uploaded_at)
        )
        return list(result.scalars())

    async def count_by_draft(self, draft_id: int) -> int:
        result = await self._s.execute(
            select(func.count()).where(EvidenceFile.draft_id == draft_id)
        )
        return result.scalar_one()

    async def get_by_id(self, file_id: int) -> EvidenceFile | None:
        return (
            await self._s.execute(select(EvidenceFile).where(EvidenceFile.file_id == file_id))
        ).scalar_one_or_none()

    async def delete(self, ev: EvidenceFile) -> None:
        await self._s.delete(ev)
        await self._s.flush()


class DraftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def add(self, draft: ReportDraft) -> ReportDraft:
        self._s.add(draft)
        await self._s.flush()
        return draft

    async def get_by_id(self, draft_id: int) -> ReportDraft | None:
        return (
            await self._s.execute(select(ReportDraft).where(ReportDraft.draft_id == draft_id))
        ).scalar_one_or_none()

    async def list_by_student(self, student_id: int) -> list[ReportDraft]:
        result = await self._s.execute(
            select(ReportDraft)
            .where(ReportDraft.student_id == student_id)
            .order_by(ReportDraft.updated_at.desc())
        )
        return list(result.scalars())

    async def delete(self, draft: ReportDraft) -> None:
        await self._s.delete(draft)
        await self._s.flush()

    async def delete_expired(self) -> int:
        """删除所有已过期草稿，返回删除数量。"""
        now = datetime.now(tz=UTC)
        result = await self._s.execute(
            select(ReportDraft).where(ReportDraft.expires_at < now)
        )
        drafts = list(result.scalars())
        for d in drafts:
            await self._s.delete(d)
        if drafts:
            await self._s.flush()
        return len(drafts)

    async def list_by_case_status_history(self, case_id: int) -> list[CaseStatusHistory]:
        result = await self._s.execute(
            select(CaseStatusHistory)
            .where(CaseStatusHistory.case_id == case_id)
            .order_by(CaseStatusHistory.created_at)
        )
        return list(result.scalars())
