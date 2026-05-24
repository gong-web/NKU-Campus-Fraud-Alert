# 审核中段接口契约

## 审计工具

```python
async def audit.write(
    *,
    operator: UserSnapshot | None,
    op_type: str,
    obj_type: str,
    obj_id: str | int,
    before: dict | None = None,
    after: dict | None = None,
    sync: bool | None = None,
    session: AsyncSession | None = None,
) -> int | None
```

- 强一致场景必须传 `session`
- 审核中段使用的关键操作：
  - `STATE_CHANGE_OPEN_DETAIL`
  - `STATE_CHANGE_RESOLVE`
  - `STATE_CHANGE_REJECT`
  - `STATE_CHANGE_TRANSFER_POLICE`
  - `REPORT_DETAIL_VIEW`
  - `VIEW_EVIDENCE`
  - `VIEW_CONTACT_INFO`
  - `DECRYPT_ANONYMOUS`
  - `AGGREGATE_ALERT_TRIGGERED`

## 通知服务

> 站内通知是一个全平台共用的横切组件（审核 / 预警 / 知识库 / 测验）。

```python
async def send_notification(
    *,
    recipient_id: int,
    type: str,
    title: str,
    content: str,
    related_object_type: str | None = None,
    related_object_id: int | None = None,
    db_session: AsyncSession | None = None,
) -> int
```

- 支持外部 `db_session`
- 通知中心 API：
  - `GET  /api/v1/notifications/my` — 当前用户通知列表（分页）
  - `GET  /api/v1/notifications/my/unread-count` — 未读数（铃铛红点轮询）
  - `PATCH /api/v1/notifications/{id}/read` — 标记单条已读
  - `PATCH /api/v1/notifications/my/read-all` — 一键全部已读
- 典型通知类型（type 字段示例）：
  - 审核模块：`REPORT_RESOLVED` / `REPORT_REJECTED` / `REPORT_TRANSFERRED`
  - 预警模块：`WARNING_PUBLISHED`
  - 知识库模块：`KB_APPROVED` / `KB_REJECTED`
  - 测验模块（UC-05 / UC-09）：`QUIZ_ASSIGNED` / `QUIZ_DEADLINE_REMINDER`

## 知识库草稿适配

```python
async def create_knowledge_draft_from_report(
    *,
    report_id: int,
    desensitized_summary: str,
    identification_points: str,
    prevention_advice: str,
    fraud_type_id: int,
    author_id: int,
    db_session: AsyncSession | None = None,
) -> int
```

- 当前仓库先落到 `knowledge_drafts` 表
- 后续知识库模块可直接复用该表，或保留同签名适配到正式服务

## 审核模块对外提供

```python
async def count_recent_reports_by_type(*, hours: int) -> dict[int, int]
async def get_report_by_case_no(*, case_no: str) -> FraudCase | None
```
