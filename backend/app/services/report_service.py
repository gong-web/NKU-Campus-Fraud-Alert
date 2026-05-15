"""上报业务服务层（UC-01 / UC-02）。"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import UploadFile

from app.core.ids import make_case_no
from app.core.logging import get_logger
from app.core.security import encrypt_field
from app.core.snowflake import next_snowflake_id
from app.domain.user_snapshot import UserSnapshot
from app.exceptions import AppException, PermissionDenied
from app.infra.db.models.case_anonymous_reporter import CaseAnonymousReporter
from app.infra.db.models.case_status_history import CaseStatusHistory
from app.infra.db.models.evidence_file import EvidenceFile
from app.infra.db.models.fraud_case import CaseStatus, FraudCase
from app.infra.db.models.report_draft import ReportDraft
from app.infra.db.session import uow
from app.infra.repositories.report import (
    DepartmentRepository,
    DraftRepository,
    EvidenceRepository,
    FraudTypeRepository,
    ReportRepository,
)
from app.schemas.reports import (
    DraftOut,
    DraftSaveIn,
    EvidenceFileOut,
    FraudTypeOut,
    ReportCreateIn,
    ReportDetailOut,
    ReportOut,
    StatusHistoryOut,
)
from app.services.audit_service import get_audit_service
from app.services.storage_service import (
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
    MAX_FILES_PER_CASE,
    delete_evidence_file,
    save_evidence_file,
)

logger = get_logger(__name__)

_DRAFT_TTL_DAYS = 30


class BusinessError(AppException):
    """业务规则校验失败（上报域 3xxxx）。

    ``code`` 参数接收 HTTP 状态码（400 / 404 / 422），内部自动映射到 3xxxx 应用错误码。
    """

    default_message = "业务规则校验失败"
    _APP_CODE_MAP = {400: 30001, 404: 30002, 422: 30004}

    def __init__(self, message: str, code: int = 400) -> None:
        self.http_status = code  # 必须在 super().__init__ 之前设置实例属性
        super().__init__(message, code=self._APP_CODE_MAP.get(code, 30001))


# ── 诈骗类型 ────────────────────────────────────────────────────────
async def list_fraud_types() -> list[FraudTypeOut]:
    async with uow() as session:
        repo = FraudTypeRepository(session)
        types = await repo.list_active()
        return [FraudTypeOut.model_validate(t) for t in types]


# ── 上报 ─────────────────────────────────────────────────────────────
async def create_report(
    data: ReportCreateIn,
    *,
    current: UserSnapshot,
) -> ReportOut:
    """学生提交一条上报（UC-01）。

    1. 验证诈骗类型有效
    2. 查询院系 code（用于案件编号）
    3. 生成雪花 ID + 案件编号
    4. 写 fraud_cases；匿名时写 case_anonymous_reporters
    5. 写初始状态历史
    6. 写审计日志（异步）
    7. 通知审核员（占位，等 Person 5 通知服务落地后激活）
    """
    async with uow() as session:
        fraud_type_repo = FraudTypeRepository(session)
        dept_repo = DepartmentRepository(session)
        report_repo = ReportRepository(session)

        # 1. 验证诈骗类型
        fraud_type = await fraud_type_repo.get_by_id(data.fraud_type_id)
        if fraud_type is None or not fraud_type.is_active:
            raise BusinessError("无效的诈骗类型", code=422)

        # 2. 查院系 code
        dept = await dept_repo.get_by_id(current.department_id)
        dept_code = dept.dept_code if dept else "UNKNOWN"

        # 3. 生成 ID + 案件编号（用雪花 ID 低 6 位作为序列，概率唯一）
        case_id = next_snowflake_id()
        seq = case_id % 1_000_000
        case_no = make_case_no(dept_code=dept_code, sequence=seq)

        # 4. 创建案件
        reporter_id: int | None = None if data.is_anonymous else current.user_id
        case = FraudCase(
            case_id=case_id,
            case_no=case_no,
            title=data.title,
            description=data.description,
            fraud_type_id=data.fraud_type_id,
            incident_date=data.incident_date,
            amount=data.amount,
            fraud_method=data.fraud_method,
            status=CaseStatus.PENDING,
            reporter_id=reporter_id,
            is_anonymous=data.is_anonymous,
            contact_way=data.contact_way,
            dept_code=dept_code,
        )
        await report_repo.add(case)

        # 4b. 匿名上报：加密真实身份写入映射表
        if data.is_anonymous:
            encrypted = encrypt_field(str(current.user_id))
            mapping = CaseAnonymousReporter(
                mapping_id=next_snowflake_id(),
                case_id=case_id,
                reporter_user_id_enc=encrypted.payload,
                encryption_key_version=encrypted.version,
            )
            await report_repo.add_anonymous_reporter(mapping)

        # 5. 写初始状态历史
        history = CaseStatusHistory(
            history_id=next_snowflake_id(),
            case_id=case_id,
            from_status=None,
            to_status=CaseStatus.PENDING,
            operator_id=current.user_id,
            note="学生上报，自动进入待审核",
        )
        await report_repo.add_status_history(history)

    # 6. 审计（异步，不阻塞响应）
    audit = get_audit_service()
    await audit.write(
        operator=current,
        op_type="REPORT_CREATE",
        obj_type="fraud_case",
        obj_id=str(case_id),
        after={"case_no": case_no, "is_anonymous": data.is_anonymous},
    )

    logger.info("report_created", case_no=case_no, user_id=current.user_id, anonymous=data.is_anonymous)

    return ReportOut(
        case_id=case.case_id,
        case_no=case.case_no,
        title=case.title,
        status=case.status,
        fraud_type_id=case.fraud_type_id,
        fraud_type_name=fraud_type.type_name,
        incident_date=case.incident_date,
        amount=case.amount,
        is_anonymous=case.is_anonymous,
        dept_code=case.dept_code,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


# ── 证据上传 ─────────────────────────────────────────────────────────
async def upload_evidence(
    case_id: int,
    file: UploadFile,
    *,
    current: UserSnapshot,
) -> EvidenceFileOut:
    """上传证据图片（UC-01）。

    调用方需要持有 report:create 权限且是该案件的上报人（或管理员）。
    文件经 AES-256-GCM 加密后写入本地磁盘。
    """
    async with uow() as session:
        report_repo = ReportRepository(session)
        evidence_repo = EvidenceRepository(session)

        case = await report_repo.get_by_id(case_id)
        if case is None:
            raise BusinessError("案件不存在", code=404)

        # 权限：非匿名案件的上报人 或 拥有 report:review 权限的审核员
        is_own = not case.is_anonymous and case.reporter_id == current.user_id
        if not is_own and current.role_code not in {"REVIEWER", "SYS_ADMIN"}:
            raise PermissionDenied("只能为自己的案件上传证据")

        # 数量限制
        existing_count = await evidence_repo.count_by_case(case_id)
        if existing_count >= MAX_FILES_PER_CASE:
            raise BusinessError(f"每案最多上传 {MAX_FILES_PER_CASE} 张证据", code=422)

        # 读取并校验
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise BusinessError(f"单文件不能超过 {MAX_FILE_SIZE // 1024 // 1024} MB", code=422)

        mime = file.content_type or "application/octet-stream"
        if mime not in ALLOWED_MIME_TYPES:
            raise BusinessError(f"不支持的文件类型: {mime}", code=422)

        # 加密写盘
        file_id = next_snowflake_id()
        storage_path, file_hash, key_version = await save_evidence_file(
            entity_type="case",
            entity_id=case_id,
            file_id=file_id,
            raw_content=content,
        )

        ev = EvidenceFile(
            file_id=file_id,
            case_id=case_id,
            draft_id=None,
            original_name=file.filename or "unknown",
            file_size=len(content),
            mime_type=mime,
            storage_path=storage_path,
            file_hash=file_hash,
            encryption_key_version=key_version,
            uploaded_by=current.user_id,
        )
        await evidence_repo.add(ev)

    logger.info("evidence_uploaded", case_id=case_id, file_id=file_id, size=len(content))
    return EvidenceFileOut.model_validate(ev)


# ── 我的上报 ─────────────────────────────────────────────────────────
async def list_my_reports(
    *,
    current: UserSnapshot,
    status: str | None = None,
    page: int = 1,
    size: int = 20,
) -> tuple[list[ReportOut], int]:
    """返回当前学生的上报列表（UC-02）。"""
    offset = (page - 1) * size
    async with uow() as session:
        report_repo = ReportRepository(session)
        fraud_type_repo = FraudTypeRepository(session)

        cases, total = await report_repo.list_by_reporter(
            current.user_id, status=status, offset=offset, limit=size
        )

        # 批量获取 fraud_type 名称
        type_id_set = {c.fraud_type_id for c in cases}
        type_names: dict[int, str] = {}
        for tid in type_id_set:
            ft = await fraud_type_repo.get_by_id(tid)
            if ft:
                type_names[tid] = ft.type_name

        results = [
            ReportOut(
                case_id=c.case_id,
                case_no=c.case_no,
                title=c.title,
                status=c.status,
                fraud_type_id=c.fraud_type_id,
                fraud_type_name=type_names.get(c.fraud_type_id),
                incident_date=c.incident_date,
                amount=c.amount,
                is_anonymous=c.is_anonymous,
                dept_code=c.dept_code,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in cases
        ]
    return results, total


async def get_report_detail(
    case_id: int,
    *,
    current: UserSnapshot,
) -> ReportDetailOut:
    """获取上报详情 + 处理时间线（UC-02）。"""
    async with uow() as session:
        report_repo = ReportRepository(session)
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)
        fraud_type_repo = FraudTypeRepository(session)

        case = await report_repo.get_by_id(case_id)
        if case is None:
            raise BusinessError("案件不存在", code=404)

        # 权限：只能看自己的案件（除非是审核员）
        is_own = not case.is_anonymous and case.reporter_id == current.user_id
        if not is_own and current.role_code not in {"REVIEWER", "SYS_ADMIN"}:
            raise PermissionDenied("无权查看此案件")

        # 状态历史
        histories = await draft_repo.list_by_case_status_history(case_id)
        history_out = [
            StatusHistoryOut(
                history_id=h.history_id,
                from_status=h.from_status,
                to_status=h.to_status,
                operator_id=h.operator_id,
                note=h.note,
                created_at=h.created_at,
            )
            for h in histories
        ]

        evidence_count = await evidence_repo.count_by_case(case_id)
        fraud_type = await fraud_type_repo.get_by_id(case.fraud_type_id)

    return ReportDetailOut(
        case_id=case.case_id,
        case_no=case.case_no,
        title=case.title,
        description=case.description,
        status=case.status,
        fraud_type_id=case.fraud_type_id,
        fraud_type_name=fraud_type.type_name if fraud_type else None,
        incident_date=case.incident_date,
        amount=case.amount,
        fraud_method=case.fraud_method,
        is_anonymous=case.is_anonymous,
        contact_way=case.contact_way,
        dept_code=case.dept_code,
        review_note=case.review_note,
        reviewed_at=case.reviewed_at,
        created_at=case.created_at,
        updated_at=case.updated_at,
        history=history_out,
        evidence_count=evidence_count,
    )


# ── 草稿 ─────────────────────────────────────────────────────────────
async def create_draft(
    data: DraftSaveIn,
    *,
    current: UserSnapshot,
) -> DraftOut:
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        now = datetime.now(tz=UTC)
        draft = ReportDraft(
            draft_id=next_snowflake_id(),
            student_id=current.user_id,
            title=data.title,
            description=data.description,
            fraud_type_id=data.fraud_type_id,
            incident_date=data.incident_date,
            amount=data.amount,
            fraud_method=data.fraud_method,
            is_anonymous=data.is_anonymous,
            contact_way=data.contact_way,
            expires_at=now + timedelta(days=_DRAFT_TTL_DAYS),
        )
        await draft_repo.add(draft)
        ev_count = await evidence_repo.count_by_draft(draft.draft_id)

    return _draft_to_out(draft, evidence_count=ev_count)


async def update_draft(
    draft_id: int,
    data: DraftSaveIn,
    *,
    current: UserSnapshot,
) -> DraftOut:
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        draft = await draft_repo.get_by_id(draft_id)
        if draft is None:
            raise BusinessError("草稿不存在", code=404)
        if draft.student_id != current.user_id:
            raise PermissionDenied("无权修改他人草稿")

        draft.title = data.title
        draft.description = data.description
        draft.fraud_type_id = data.fraud_type_id
        draft.incident_date = data.incident_date
        draft.amount = data.amount
        draft.fraud_method = data.fraud_method
        draft.is_anonymous = data.is_anonymous
        draft.contact_way = data.contact_way
        # 刷新过期时间
        draft.expires_at = datetime.now(tz=UTC) + timedelta(days=_DRAFT_TTL_DAYS)

        await session.flush()
        ev_count = await evidence_repo.count_by_draft(draft_id)

    return _draft_to_out(draft, evidence_count=ev_count)


async def get_draft(draft_id: int, *, current: UserSnapshot) -> DraftOut:
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        draft = await draft_repo.get_by_id(draft_id)
        if draft is None:
            raise BusinessError("草稿不存在", code=404)
        if draft.student_id != current.user_id:
            raise PermissionDenied("无权查看他人草稿")

        ev_count = await evidence_repo.count_by_draft(draft_id)

    return _draft_to_out(draft, evidence_count=ev_count)


async def list_drafts(*, current: UserSnapshot) -> list[DraftOut]:
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        drafts = await draft_repo.list_by_student(current.user_id)
        results = []
        for d in drafts:
            ev_count = await evidence_repo.count_by_draft(d.draft_id)
            results.append(_draft_to_out(d, evidence_count=ev_count))

    return results


async def delete_draft(draft_id: int, *, current: UserSnapshot) -> None:
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        draft = await draft_repo.get_by_id(draft_id)
        if draft is None:
            raise BusinessError("草稿不存在", code=404)
        if draft.student_id != current.user_id:
            raise PermissionDenied("无权删除他人草稿")

        # 删除关联证据文件
        evidence_files = await evidence_repo.list_by_draft(draft_id)
        for ev in evidence_files:
            await delete_evidence_file(ev.storage_path)
            await evidence_repo.delete(ev)

        await draft_repo.delete(draft)


async def upload_draft_evidence(
    draft_id: int,
    file: UploadFile,
    *,
    current: UserSnapshot,
) -> EvidenceFileOut:
    """为草稿上传证据图片。"""
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        draft = await draft_repo.get_by_id(draft_id)
        if draft is None:
            raise BusinessError("草稿不存在", code=404)
        if draft.student_id != current.user_id:
            raise PermissionDenied("无权为他人草稿上传证据")

        existing_count = await evidence_repo.count_by_draft(draft_id)
        if existing_count >= MAX_FILES_PER_CASE:
            raise BusinessError(f"每案最多上传 {MAX_FILES_PER_CASE} 张证据", code=422)

        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise BusinessError(f"单文件不能超过 {MAX_FILE_SIZE // 1024 // 1024} MB", code=422)

        mime = file.content_type or "application/octet-stream"
        if mime not in ALLOWED_MIME_TYPES:
            raise BusinessError(f"不支持的文件类型: {mime}", code=422)

        file_id = next_snowflake_id()
        storage_path, file_hash, key_version = await save_evidence_file(
            entity_type="draft",
            entity_id=draft_id,
            file_id=file_id,
            raw_content=content,
        )

        ev = EvidenceFile(
            file_id=file_id,
            case_id=None,
            draft_id=draft_id,
            original_name=file.filename or "unknown",
            file_size=len(content),
            mime_type=mime,
            storage_path=storage_path,
            file_hash=file_hash,
            encryption_key_version=key_version,
            uploaded_by=current.user_id,
        )
        await evidence_repo.add(ev)

    return EvidenceFileOut.model_validate(ev)


async def delete_draft_evidence(
    draft_id: int,
    file_id: int,
    *,
    current: UserSnapshot,
) -> None:
    async with uow() as session:
        draft_repo = DraftRepository(session)
        evidence_repo = EvidenceRepository(session)

        draft = await draft_repo.get_by_id(draft_id)
        if draft is None:
            raise BusinessError("草稿不存在", code=404)
        if draft.student_id != current.user_id:
            raise PermissionDenied("无权操作他人草稿")

        ev = await evidence_repo.get_by_id(file_id)
        if ev is None or ev.draft_id != draft_id:
            raise BusinessError("文件不存在", code=404)

        await delete_evidence_file(ev.storage_path)
        await evidence_repo.delete(ev)


# ── 内部工具 ──────────────────────────────────────────────────────────
def _draft_to_out(draft: ReportDraft, *, evidence_count: int) -> DraftOut:
    return DraftOut(
        draft_id=draft.draft_id,
        title=draft.title,
        description=draft.description,
        fraud_type_id=draft.fraud_type_id,
        incident_date=draft.incident_date,
        amount=draft.amount,
        fraud_method=draft.fraud_method,
        is_anonymous=draft.is_anonymous,
        contact_way=draft.contact_way,
        created_at=draft.created_at,
        updated_at=draft.updated_at,
        expires_at=draft.expires_at,
        evidence_count=evidence_count,
    )
