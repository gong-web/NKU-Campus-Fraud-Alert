# 系统架构

> 本文是项目代码组织的"地图"。任何一行业务代码都应该能在本图里找到位置。

---

## 1. 分层（Hexagonal / Clean Architecture 简化版）

```
┌─────────────────────────────────────────────────────┐
│ frontend  Vue 3 SPA · Element Plus · 设计系统        │
└──────────────────▲──────────────────────────────────┘
                   │ axios (cookie + CSRF + JSON)
┌──────────────────┴──────────────────────────────────┐
│ backend                                             │
│                                                     │
│ ┌─────────────────────────────────────────────┐     │
│ │ api/         协议转换、鉴权、异常翻译         │     │
│ │   - deps.py  get_current_user / require_*   │     │
│ │   - errors.py 全局异常处理器                  │     │
│ │   - middleware.py trace_id / CSRF / sec     │     │
│ │   - v1/      controller（路由聚合）          │     │
│ └─────────────────▲───────────────────────────┘     │
│                   │                                 │
│ ┌─────────────────┴───────────────────────────┐     │
│ │ services/    用例编排（auth / user / audit /│     │
│ │              judicial）                     │     │
│ └─────────────────▲───────────────────────────┘     │
│                   │                                 │
│ ┌─────────────────┴───────────────────────────┐     │
│ │ infra/                                      │     │
│ │   - db/         SQLAlchemy 2 async + 模型    │     │
│ │   - cache/      Redis（session/RBAC/audit）  │     │
│ │   - cas/        Real / Mock provider        │     │
│ │   - repositories/                          │     │
│ └─────────────────────────────────────────────┘     │
│                                                     │
│ core/   配置 · 日志 · 安全 · 雪花 ID · KMS           │
│ domain/ 纯 Python 领域对象（UserSnapshot 等）        │
│ schemas/ Pydantic DTO（入参 / 出参）                │
│ exceptions.py  AppException 体系                    │
└─────────────────────────────────────────────────────┘
                   │
        ┌──────────┴───────────┬──────────┬────────┐
        │                      │          │        │
   ┌────▼─────┐         ┌──────▼──┐  ┌────▼───┐ ┌─▼────┐
   │  MySQL   │         │  Redis  │  │ MinIO  │ │ KMS  │
   │  (8.0)   │         │  (7.x)  │  │ (S3)   │ │ Vault│
   └──────────┘         └─────────┘  └────────┘ └──────┘
```

---

## 2. 为什么这样分层

1. **api 不许 import SQLAlchemy `Session`**：让 controller 永远薄。
2. **service 不许 import FastAPI**：业务逻辑不绑死 Web 框架，方便复用为 CLI / cron。
3. **infra/repositories 是单一可测点**：所有数据访问走它，单元测试直接 fake。
4. **domain 纯 Python**：跨 service 传递数据时用值对象（如 `UserSnapshot`），不传 ORM。

> 对于 1 年期课程项目，本架构在"完全平铺"和"严格 DDD"之间取折中。

---

## 3. 一次请求的旅程

例：`POST /api/v1/users` 创建账号

1. 前端 axios 自动带 `cookie + X-Requested-With`。
2. Nginx (生产) → Uvicorn → FastAPI。
3. **Middleware** `TraceIdMiddleware` 生成 trace_id 写到 `request.state` 与日志 contextvars。
4. **Middleware** `CSRFRequiredHeaderMiddleware` 检查 `X-Requested-With`。
5. Controller `users.create_user` 通过 `Depends(require_permission("user:create"))` 鉴权：
   - `get_current_user` 拿 cookie → Redis touch → 返回 `UserSnapshot`
   - `require_permission` 在 RBAC 缓存里查 `user:create` 是否在角色权限集合中
6. Pydantic 校验请求体；不通过 → `RequestValidationError` → 错误处理器返回 422 + 10001。
7. Controller 调 `UserService.create_user(...)` → `uow()` 开事务：
   - `UserRepository.add(...)` 写库
   - `audit_service.write(..., sync=True, session=session)` 同事务落审计
   - 事务原子提交
8. 返回 `UserOut` Pydantic → JSON。
9. `TraceIdMiddleware` 把 `X-Trace-Id` 写到响应头。

---

## 4. 安全设计要点

| 风险           | 缓解                                                                       |
| -------------- | -------------------------------------------------------------------------- |
| CSRF           | SameSite=Lax + 强制 `X-Requested-With` header                              |
| XSS            | HttpOnly Cookie + 前端 v-text；CSP `default-src 'none'` (API)              |
| 会话固定       | 登录成功后**重新生成** session_id（UUIDv4）                                |
| 重放攻击       | CAS ticket 5 分钟 Redis 去重                                               |
| 横向越权       | RBAC 装饰器 + 资源 owner 校验（service 层）                                |
| L3 数据泄露    | AES-256-GCM 字段加密；KMS 托管 DEK；DB 账号 `decrypt_user` 隔离匿名映射     |
| 审计被改       | `app_user` 仅 INSERT/SELECT；触发器拦截 UPDATE/DELETE；可选哈希链          |
| 司法协助滥用   | 5 分钟窗口 + 全员告警 + 水印                                                |
| 越权 SQL       | ORM 严禁拼字符串；分页参数硬上限；mypy `--strict`                           |

---

## 5. 部署拓扑（生产建议，非本课程范围）

```
[校园网用户] → Nginx (TLS 终止) → Uvicorn × N → MySQL 主从
                              → Redis 哨兵
                              → MinIO / NAS（证据文件）
                              → Vault（KMS）
                              → ELK / Prometheus（旁路）
```

学校数据中心内网；DMZ 部署应用服务器；DB / 文件 / KMS 不直暴。

---

## 6. 与 PRD 的对照

- 系统整体架构：PRD 图 2.1 ✓
- ER 图：PRD 图 5.1，本骨架完成"用户与权限域 + 系统支撑域 + 匿名相关"
- 业务模型（FraudReport / WarningNotice / KnowledgeEntry / Quiz）由各 UC 负责人在自己的 PR 中按字典补齐，外键依然指向本骨架的 User / Department / FraudType。
