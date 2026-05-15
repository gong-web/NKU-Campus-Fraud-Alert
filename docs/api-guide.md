# 添加一个新接口的 5 步教程

> 严格按这 5 步操作即可获得：CSRF 防护 / 鉴权 / 审计 / 错误处理 / OpenAPI 自动文档 / 单元测试模板。**不许跳步**。

---

## Demo：实现一个"提交事件草稿"接口

### Step 1 · 写 Pydantic schema

`backend/app/schemas/reports.py`：

```python
from pydantic import BaseModel, Field

class ReportDraftCreateIn(BaseModel):
    fraud_type_id: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=10, max_length=10_000)

class ReportDraftOut(BaseModel):
    draft_id: int
    title: str
```

### Step 2 · 写 service

`backend/app/services/report_service.py`：

```python
from app.domain.user_snapshot import UserSnapshot
from app.services.audit_service import get_audit_service

class ReportService:
    def __init__(self) -> None:
        self._audit = get_audit_service()

    async def create_draft(
        self, *, body: "ReportDraftCreateIn", current: UserSnapshot
    ) -> dict:
        # 1) 业务规则校验（用 ValidationError）
        # 2) 仓储调用（infra/repositories/report_draft.py）
        # 3) 审计：草稿是 L2，建议异步落库
        await self._audit.write(
            operator=current,
            op_type="REPORT_DRAFT_CREATE",
            obj_type="report_draft",
            obj_id=str(draft_id),
            after={"title": body.title[:80]},
        )
        return {"draft_id": draft_id, "title": body.title}
```

### Step 3 · 注册 router

`backend/app/api/v1/reports.py`：

```python
from fastapi import APIRouter, Depends
from app.api.deps import require_permission
from app.domain.user_snapshot import UserSnapshot
from app.services import permissions as perm
from app.schemas.reports import ReportDraftCreateIn, ReportDraftOut
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["reports (UC-01)"])
_svc = ReportService()

@router.post("/drafts", response_model=ReportDraftOut, status_code=201)
async def create_draft(
    body: ReportDraftCreateIn,
    current: UserSnapshot = Depends(require_permission(perm.REPORT_CREATE)),
) -> ReportDraftOut:
    data = await _svc.create_draft(body=body, current=current)
    return ReportDraftOut(**data)
```

### Step 4 · 加权限装饰器（已在 Step 3 完成）

任意鉴权点都用 `Depends(require_role(...))` / `Depends(require_permission(...))` / `Depends(require_self_or_role(...))`。  
**禁止** `if user.role == ...`。  
所有权限码先在 `services/permissions.py` 登记，再加到 `Permission` 表 + `RolePermission` 表（迁移脚本里写好），再写到 `docs/permissions.md`。

### Step 5 · 写测试

`backend/tests/integration/test_report_draft.py`：

```python
import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

@pytest.mark.asyncio
async def test_create_draft(client: AsyncClient, seed_minimum):
    # 登录学生
    r = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "student001"})
    assert r.status_code == 200

    # 提交草稿
    r = await client.post(
        "/api/v1/reports/drafts",
        json={"fraud_type_id": 1, "title": "刷单兼职可疑", "description": "x" * 200},
    )
    assert r.status_code == 201
    assert r.json()["title"] == "刷单兼职可疑"

@pytest.mark.asyncio
async def test_other_role_blocked(client: AsyncClient, seed_minimum):
    r = await client.post("/api/v1/auth/cas/mock-login", json={"cas_account": "sysadmin001"})
    assert r.status_code == 200
    r = await client.post("/api/v1/reports/drafts", json={...})
    # SysAdmin 没 report:create
    assert r.status_code == 403
```

---

## 已实现接口示例（UC-01 / UC-02，@yxq）

> 以下为真实已落地接口，可直接在 `http://localhost:8000/docs` 验证。

### POST /api/v1/reports — 提交诈骗事件上报

**权限**：`report:create`（STUDENT 默认具备）  
**说明**：支持实名与匿名，匿名时服务端加密真实身份后写入隔离表。

```http
POST /api/v1/reports
Content-Type: application/json
X-Requested-With: XMLHttpRequest
Cookie: afp_session=<登录后的 session>

{
  "title": "收到可疑退款短信",
  "description": "收到自称银行客服的短信，要求点击链接退款，链接疑似钓鱼网站。",
  "fraud_type_id": 1,
  "incident_date": "2026-05-01",
  "amount": "500.00",
  "fraud_method": "假冒银行客服+钓鱼链接",
  "is_anonymous": false,
  "contact_way": "13800000000"
}
```

成功响应 `201 Created`：

```json
{
  "case_id": 123456789012345678,
  "case_no": "2026-UNKNOWN-345678",
  "title": "收到可疑退款短信",
  "status": "PENDING",
  "fraud_type_id": 1,
  "fraud_type_name": "电信诈骗",
  "incident_date": "2026-05-01",
  "amount": "500.00",
  "is_anonymous": false,
  "dept_code": "UNKNOWN",
  "created_at": "2026-05-01T10:30:00+08:00",
  "updated_at": "2026-05-01T10:30:00+08:00"
}
```

失败响应（诈骗类型不存在）`422 Unprocessable Entity`：

```json
{ "code": 30004, "message": "无效的诈骗类型", "data": null, "trace_id": "..." }
```

---

### POST /api/v1/drafts — 保存草稿

**权限**：`report:create`  
**说明**：所有字段均可选，草稿 30 天后自动清理。

```http
POST /api/v1/drafts
Content-Type: application/json
X-Requested-With: XMLHttpRequest
Cookie: afp_session=<session>

{
  "title": "刷单兼职诈骗",
  "description": "对方要求先垫付资金做任务，到达一定金额后消失。",
  "fraud_type_id": 2,
  "is_anonymous": true
}
```

成功响应 `201 Created`：

```json
{
  "draft_id": 234567890123456789,
  "title": "刷单兼职诈骗",
  "description": "对方要求先垫付资金做任务，到达一定金额后消失。",
  "fraud_type_id": 2,
  "incident_date": null,
  "amount": null,
  "fraud_method": null,
  "is_anonymous": true,
  "contact_way": null,
  "created_at": "2026-05-01T10:35:00+08:00",
  "updated_at": "2026-05-01T10:35:00+08:00",
  "expires_at": "2026-05-31T10:35:00+08:00",
  "evidence_count": 0
}
```

---

### GET /api/v1/reports/my — 我的上报列表

**权限**：`report:read_own`  
**分页**：`?page=1&size=20`，可加 `&status=PENDING` 筛选。

```http
GET /api/v1/reports/my?page=1&size=20
Cookie: afp_session=<session>
```

成功响应 `200 OK`：

```json
{
  "items": [
    {
      "case_id": 123456789012345678,
      "case_no": "2026-UNKNOWN-345678",
      "title": "收到可疑退款短信",
      "status": "PENDING",
      "fraud_type_id": 1,
      "fraud_type_name": "电信诈骗",
      "incident_date": "2026-05-01",
      "amount": "500.00",
      "is_anonymous": false,
      "dept_code": "UNKNOWN",
      "created_at": "2026-05-01T10:30:00+08:00",
      "updated_at": "2026-05-01T10:30:00+08:00"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

---

## 完成后检查清单（PR 审查时也会问）

- [ ] schema 输入有最大长度限制（防 DoS）
- [ ] service 不直接 import SQLAlchemy `Session`
- [ ] 审计 SDK 至少调用一次（除非是只读接口）
- [ ] 测试覆盖：成功 + 至少 1 条失败路径
- [ ] OpenAPI `/docs` 看得到本接口
- [ ] 错误码（如有新建）已加到 `docs/error-codes.md`
