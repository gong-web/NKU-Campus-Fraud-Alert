from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.infra.cache.rbac_cache import RBACCache
from app.infra.db.models import (
    CaseAnonymousReporter,
    CaseStatusHistory,
    EvidenceFile,
    FraudCase,
    FraudType,
    Permission,
    Role,
    RolePermission,
    User,
)
from app.infra.db.models.audit_log import AuditLog
from app.infra.db.models.department import Department
from app.infra.repositories.role import RoleRepository
from app.services import permissions as perm
from app.services.storage_service import save_evidence_file

pytestmark = pytest.mark.integration


@pytest.fixture
async def seed_admin_module(db_session, tmp_path, monkeypatch):
    import app.services.storage_service as storage_service

    monkeypatch.setattr(storage_service, "_UPLOAD_DIR", tmp_path)

    dept = Department(dept_code="CS", dept_name="计算机学院", dept_level=1, sort_order=1)
    db_session.add(dept)
    await db_session.flush()

    student_role = Role(role_code="STUDENT", role_name="学生", role_level=1)
    reviewer_role = Role(role_code="REVIEWER", role_name="院级审核员", role_level=1)
    sys_role = Role(role_code="SYS_ADMIN", role_name="系统管理员", role_level=1)
    db_session.add_all([student_role, reviewer_role, sys_role])
    await db_session.flush()

    perms = [
        Permission(permission_code=perm.REPORT_READ_ALL, permission_name="审核列表", resource_type="REPORT", action_type="READ"),
        Permission(permission_code=perm.REPORT_REVIEW, permission_name="审核", resource_type="REPORT", action_type="REVIEW"),
        Permission(permission_code=perm.REPORT_VIEW_EVIDENCE, permission_name="查看证据", resource_type="REPORT", action_type="READ"),
    ]
    db_session.add_all(perms)
    await db_session.flush()
    db_session.add_all(
        [
            RolePermission(role_id=reviewer_role.role_id, permission_id=perms[0].permission_id),
            RolePermission(role_id=reviewer_role.role_id, permission_id=perms[1].permission_id),
            RolePermission(role_id=reviewer_role.role_id, permission_id=perms[2].permission_id),
        ]
    )

    reviewer = User(
        user_id=6101,
        cas_account="reviewer_admin",
        real_name="审核员",
        department_id=dept.dept_id,
        role_id=reviewer_role.role_id,
    )
    sysadmin = User(
        user_id=6102,
        cas_account="sys_admin_case",
        real_name="系统管理员",
        department_id=dept.dept_id,
        role_id=sys_role.role_id,
    )
    reporter = User(
        user_id=6103,
        cas_account="student_case",
        real_name="学生乙",
        department_id=dept.dept_id,
        role_id=student_role.role_id,
        email_encrypted="student_case@example.com",
        phone_encrypted="13812345678",
    )
    db_session.add_all([reviewer, sysadmin, reporter])
    await db_session.flush()

    fraud_type = FraudType(
        type_code="ADMINTEST",
        type_name="管理员测试",
        description="管理员测试类型",
        is_active=True,
        sort_order=1,
    )
    db_session.add(fraud_type)
    await db_session.flush()

    case = FraudCase(
        case_id=6201,
        case_no="2026-CS-006201",
        title="待审核案件",
        description="这是一个用于管理员审核接口的测试案件描述",
        fraud_type_id=fraud_type.type_id,
        incident_date=date(2026, 5, 1),
        reporter_id=reporter.user_id,
        is_anonymous=False,
        dept_code="CS",
        status="PENDING",
    )
    anon_case = FraudCase(
        case_id=6202,
        case_no="2026-CS-006202",
        title="匿名案件",
        description="这是一个匿名上报测试案件描述",
        fraud_type_id=fraud_type.type_id,
        incident_date=date(2026, 5, 2),
        reporter_id=None,
        is_anonymous=True,
        dept_code="CS",
        status="REVIEWING",
        reviewer_id=reviewer.user_id,
    )
    db_session.add_all([case, anon_case])
    await db_session.flush()

    db_session.add(
        CaseAnonymousReporter(
            mapping_id=7201,
            case_id=anon_case.case_id,
            reporter_user_id_enc=__import__("app.core.security", fromlist=["encrypt_field"]).encrypt_field(str(reporter.user_id)).payload,
            encryption_key_version="v1",
        )
    )

    storage_path, file_hash, key_version = await save_evidence_file(
        entity_type="case",
        entity_id=case.case_id,
        file_id=7301,
        raw_content=b"fake-image-content",
    )
    db_session.add(
        EvidenceFile(
            file_id=7301,
            case_id=case.case_id,
            draft_id=None,
            original_name="付款凭证.png",
            file_size=18,
            mime_type="image/png",
            storage_path=storage_path,
            file_hash=file_hash,
            encryption_key_version=key_version,
            uploaded_by=reporter.user_id,
        )
    )
    await db_session.commit()

    async with __import__("app.infra.db.session", fromlist=["uow"]).uow() as session:
        mapping = await RoleRepository(session).list_role_permissions_full()
    await RBACCache().load(mapping)

    return {"case": case, "anon_case": anon_case, "evidence_id": 7301}


@pytest.mark.asyncio
async def test_admin_detail_auto_open_detail(client: AsyncClient, seed_admin_module, db_session) -> None:
    case = seed_admin_module["case"]
    login = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "reviewer_admin"})
    assert login.status_code == 200, login.text

    resp = await client.get(f"/api/v1/admin/reports/{case.case_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "REVIEWING"

    histories = (
        await db_session.execute(
            select(CaseStatusHistory).where(CaseStatusHistory.case_id == case.case_id)
        )
    ).scalars().all()
    assert len(histories) == 1

    audits = (await db_session.execute(select(AuditLog))).scalars().all()
    assert {a.operation_type for a in audits} >= {"STATE_CHANGE_OPEN_DETAIL", "REPORT_DETAIL_VIEW"}


@pytest.mark.asyncio
async def test_admin_resolve_accepts_short_demo_text(client: AsyncClient, seed_admin_module) -> None:
    case = seed_admin_module["case"]
    login = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "reviewer_admin"})
    assert login.status_code == 200, login.text

    detail = await client.get(f"/api/v1/admin/reports/{case.case_id}")
    assert detail.status_code == 200, detail.text
    assert detail.json()["status"] == "REVIEWING"

    resp = await client.post(
        f"/api/v1/admin/reports/{case.case_id}/resolve",
        json={
            "desensitized_summary": "1",
            "identification_points": "1",
            "prevention_advice": "1",
            "internal_remark": "1",
        },
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "HANDLED"


@pytest.mark.asyncio
async def test_admin_evidence_requires_confirmation_header(client: AsyncClient, seed_admin_module) -> None:
    case = seed_admin_module["case"]
    evidence_id = seed_admin_module["evidence_id"]
    login = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "reviewer_admin"})
    assert login.status_code == 200, login.text

    resp = await client.get(f"/api/v1/admin/reports/{case.case_id}/evidence/{evidence_id}")
    assert resp.status_code == 412, resp.text

    ok = await client.get(
        f"/api/v1/admin/reports/{case.case_id}/evidence/{evidence_id}",
        headers={"X-Confirm-Sensitive-Access": "yes"},
    )
    assert ok.status_code == 200, ok.text
    assert ok.content == b"fake-image-content"
    assert ok.headers["content-disposition"].startswith(
        "inline; filename=\"evidence\"; filename*=UTF-8''"
    )
    assert "%E4%BB%98%E6%AC%BE%E5%87%AD%E8%AF%81.png" in ok.headers["content-disposition"]


@pytest.mark.asyncio
async def test_admin_contact_request_for_anonymous_forbidden(client: AsyncClient, seed_admin_module) -> None:
    anon_case = seed_admin_module["anon_case"]
    login = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "reviewer_admin"})
    assert login.status_code == 200, login.text

    resp = await client.post(f"/api/v1/admin/reports/{anon_case.case_id}/contact-request")
    assert resp.status_code == 403, resp.text


@pytest.mark.asyncio
async def test_sysadmin_can_decrypt_anonymous_reporter(client: AsyncClient, seed_admin_module) -> None:
    anon_case = seed_admin_module["anon_case"]
    login = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sys_admin_case"})
    assert login.status_code == 200, login.text

    resp = await client.post(
        f"/api/v1/admin/reports/{anon_case.case_id}/decrypt-anonymous",
        json={"reason": "配合公安机关调查与校内联动排查，需要确认匿名上报者身份。", "approver_id": 6102},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["user_id"] == "6103"
    assert body["real_name"] == "学生乙"
