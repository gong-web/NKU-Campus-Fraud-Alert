"""End-to-end smoke test for UC-03/04/07/08 routers.

Run inside backend container:
    docker exec anti-fraud-backend python /app/scripts/smoke_uc04_uc08.py
"""
from __future__ import annotations

import json
import sys
from typing import Any

import httpx

BASE = "http://localhost:8000/api/v1"
HEADERS = {"X-Requested-With": "XMLHttpRequest"}


def fail(msg: str) -> None:
    print(f"\n[FAIL] {msg}")
    sys.exit(1)


def check(cond: bool, msg: str) -> None:
    if not cond:
        fail(msg)
    print(f"  [OK] {msg}")


def login(client: httpx.Client, account: str) -> dict[str, Any]:
    r = client.post(
        f"{BASE}/auth/cas/mock-login",
        headers=HEADERS,
        json={"cas_account": account},
    )
    check(r.status_code == 200, f"mock-login {account} -> 200 (got {r.status_code}: {r.text[:200]})")
    me = r.json()
    print(f"  user_id={me['user_id']} role={me['role_code']}/{me.get('role_id')} perms={len(me.get('permissions', []))}")
    return me


def main() -> None:
    print("=== UC-03/04/07/08 end-to-end smoke ===")

    school = httpx.Client(timeout=15.0)
    student = httpx.Client(timeout=15.0)

    # 1. Login school reviewer (role_level=2 → can create/review/offline KB + publish warnings)
    print("\n[1] Login: reviewer_school001")
    me_school = login(school, "reviewer_school001")
    school_user_id = me_school["user_id"]

    print("\n[1b] Login: student001")
    me_student = login(student, "student001")
    _ = me_student

    # ── 2. KB CREATE ───────────────────────────────────────────────
    print("\n[2] POST /admin/knowledge -> create DRAFT")
    r = school.post(
        f"{BASE}/admin/knowledge",
        headers=HEADERS,
        json={
            "title": "[smoke] 冒充客服退款诈骗",
            "fraud_type_id": 1,
            "desensitized_summary": "学生 X 接到自称客服来电……（脱敏摘要）",
            "identification_points": "1. 主动联系；2. 要求屏幕共享；3. 索要验证码",
            "prevention_advice": "1. 不点不明链接；2. 不开屏幕共享；3. 拨打官方核实",
            "peak_periods": "开学季 / 双十一",
            "source_type": "CASE",
            "source_reference": "案件编号 C-SMOKE-001",
        },
    )
    check(r.status_code == 201, f"create -> 201 (got {r.status_code}: {r.text[:300]})")
    entry = r.json()
    entry_id = entry["entry_id"]
    print(f"  entry_id={entry_id} status={entry['status']} version={entry['version']}")
    check(entry["status"] == "DRAFT", "initial status DRAFT")
    check(entry["version"] == 1, "initial version=1")

    # ── 3. SUBMIT ───────────────────────────────────────────────────
    print("\n[3] POST /admin/knowledge/{id}/submit -> PENDING")
    r = school.post(f"{BASE}/admin/knowledge/{entry_id}/submit", headers=HEADERS)
    check(r.status_code == 200, f"submit -> 200 (got {r.status_code}: {r.text[:300]})")
    check(r.json()["status"] == "PENDING", "post-submit status PENDING")

    # ── 4. APPROVE ──────────────────────────────────────────────────
    print("\n[4] POST /admin/knowledge/{id}/review APPROVE -> PUBLISHED")
    r = school.post(
        f"{BASE}/admin/knowledge/{entry_id}/review",
        headers=HEADERS,
        json={"action": "APPROVE", "review_note": "smoke approve"},
    )
    check(r.status_code == 200, f"review -> 200 (got {r.status_code}: {r.text[:300]})")
    body = r.json()
    check(body["status"] == "PUBLISHED", "post-approve status PUBLISHED")
    check(body.get("published_at") is not None, "published_at populated")

    # ── 5. HISTORY ──────────────────────────────────────────────────
    print("\n[5] GET /admin/knowledge/{id}/history (event-source check)")
    r = school.get(f"{BASE}/admin/knowledge/{entry_id}/history", headers=HEADERS)
    check(r.status_code == 200, f"history -> 200 (got {r.status_code}: {r.text[:300]})")
    hist = r.json()
    print(f"  history rows = {len(hist)}")
    actions = [h["action"] for h in hist]
    versions = [h["version"] for h in hist]
    print(f"  actions={actions} versions={versions}")
    check("CREATE" in actions, "history contains CREATE")
    check("SUBMIT" in actions, "history contains SUBMIT")
    check("APPROVE" in actions, "history contains APPROVE")
    # Regression check: CREATE+SUBMIT both at v=1 means the unique-constraint bug is gone
    create_v = next(h["version"] for h in hist if h["action"] == "CREATE")
    submit_v = next(h["version"] for h in hist if h["action"] == "SUBMIT")
    check(create_v == submit_v == 1, f"CREATE+SUBMIT both at v=1 (got {create_v},{submit_v}) — UniqueConstraint regression check")

    # ── 6. PUBLIC LIST ──────────────────────────────────────────────
    print("\n[6] GET /knowledge (student) — should see PUBLISHED")
    r = student.get(f"{BASE}/knowledge?page=1&size=20", headers=HEADERS)
    check(r.status_code == 200, f"public list -> 200 (got {r.status_code}: {r.text[:300]})")
    plist = r.json()
    ids_seen = [it["entry_id"] for it in plist["items"]]
    check(str(entry_id) in ids_seen or entry_id in ids_seen, f"published entry visible to student (got {ids_seen})")

    # ── 7. PUBLIC DETAIL ────────────────────────────────────────────
    print("\n[7] GET /knowledge/{id} (student)")
    r = student.get(f"{BASE}/knowledge/{entry_id}", headers=HEADERS)
    check(r.status_code == 200, f"public detail -> 200 (got {r.status_code}: {r.text[:300]})")
    det = r.json()
    check(det.get("status") == "PUBLISHED", "public detail status PUBLISHED")

    # ── 8. OFFLINE ─────────────────────────────────────────────────
    print("\n[8] POST /admin/knowledge/{id}/offline -> OFFLINE")
    r = school.post(
        f"{BASE}/admin/knowledge/{entry_id}/offline",
        headers=HEADERS,
        json={"reason": "smoke offline"},
    )
    check(r.status_code == 200, f"offline -> 200 (got {r.status_code}: {r.text[:300]})")

    print("\n[9] GET /admin/knowledge?status=OFFLINE — entry must appear")
    r = school.get(f"{BASE}/admin/knowledge?status=OFFLINE&size=100", headers=HEADERS)
    check(r.status_code == 200, f"admin list OFFLINE -> 200 (got {r.status_code}: {r.text[:300]})")
    found = any(
        (it.get("entry_id") == entry_id or it.get("entry_id") == str(entry_id))
        for it in r.json()["items"]
    )
    check(found, "offlined entry appears in admin OFFLINE list")

    print("\n[10] GET /knowledge/{id} (student) on OFFLINE — must be 404")
    r = student.get(f"{BASE}/knowledge/{entry_id}", headers=HEADERS)
    check(r.status_code in (403, 404), f"OFFLINE detail hidden from student (got {r.status_code})")

    # ── 11. WARNING LIFECYCLE ───────────────────────────────────────
    print("\n[11] POST /admin/warnings -> publish")
    r = school.post(
        f"{BASE}/admin/warnings",
        headers=HEADERS,
        json={
            "title": "[smoke] 冒充客服退款电话激增",
            "content": "近日多名同学接到冒充客服电话，请提高警惕。",
            "warning_level": 2,
            "push_scope": "FULL_SCHOOL",
        },
    )
    check(r.status_code == 201, f"publish warning -> 201 (got {r.status_code}: {r.text[:300]})")
    warning = r.json()
    warning_id = warning["warning_id"]
    print(f"  warning_id={warning_id} status={warning['status']}")

    print("\n[12] GET /warnings (student)")
    r = student.get(f"{BASE}/warnings?size=50", headers=HEADERS)
    check(r.status_code == 200, f"warnings list -> 200 (got {r.status_code}: {r.text[:300]})")

    print("\n[13] GET /warnings/{id} (student)")
    r = student.get(f"{BASE}/warnings/{warning_id}", headers=HEADERS)
    check(r.status_code == 200, f"warning detail -> 200 (got {r.status_code}: {r.text[:300]})")

    print("\n[14] POST /admin/warnings/{id}/append")
    r = school.post(
        f"{BASE}/admin/warnings/{warning_id}/append",
        headers=HEADERS,
        json={"appendix": "更新：已抓获嫌疑人 1 名。"},
    )
    check(r.status_code == 200, f"append warning -> 200 (got {r.status_code}: {r.text[:300]})")
    body = r.json()
    check("更新" in (body.get("appendix") or ""), "appendix saved")

    print("\n[15] POST /admin/warnings/{id}/offline")
    r = school.post(
        f"{BASE}/admin/warnings/{warning_id}/offline",
        headers=HEADERS,
        json={"reason": "smoke offline"},
    )
    check(r.status_code == 200, f"offline warning -> 200 (got {r.status_code}: {r.text[:300]})")

    # ── 16. FAILURE PATHS ───────────────────────────────────────────
    print("\n[16] Failure: GET /admin/knowledge/9999999999 -> 404")
    r = school.get(f"{BASE}/admin/knowledge/9999999999", headers=HEADERS)
    check(r.status_code == 404, f"missing entry -> 404 (got {r.status_code})")

    print("\n[17] Failure: REJECT without review_note -> 4xx")
    # Build a brand-new DRAFT then submit, then reject without note
    r = school.post(
        f"{BASE}/admin/knowledge",
        headers=HEADERS,
        json={
            "title": "[smoke-fail] 反例条目（用于触发 REJECT 校验失败）",
            "fraud_type_id": 1,
            "desensitized_summary": "用于反例测试的脱敏摘要文本（至少 20 字）。" * 2,
            "identification_points": "用于反例测试的识别要点（至少 10 字）。",
            "prevention_advice": "用于反例测试的防范建议（至少 10 字）。",
            "source_type": "CASE",
        },
    )
    check(r.status_code == 201, f"create reject-test entry -> 201 (got {r.status_code})")
    bad_id = r.json()["entry_id"]
    r = school.post(f"{BASE}/admin/knowledge/{bad_id}/submit", headers=HEADERS)
    check(r.status_code == 200, f"submit reject-test entry -> 200 (got {r.status_code})")
    r = school.post(
        f"{BASE}/admin/knowledge/{bad_id}/review",
        headers=HEADERS,
        json={"action": "REJECT"},  # no review_note
    )
    check(r.status_code in (400, 422), f"REJECT-without-note -> 4xx (got {r.status_code}: {r.text[:200]})")

    print("\n=== ALL CHECKS PASSED ===")
    print(json.dumps({
        "kb_entry_id": entry_id,
        "warning_id": warning_id,
        "school_user_id": school_user_id,
    }, indent=2))


if __name__ == "__main__":
    main()
