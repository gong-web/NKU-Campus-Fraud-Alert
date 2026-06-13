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
        ┌──────────┴───────────┬──────────────────┬────────────────┐
        │                      │                  │                │
   ┌────▼─────┐         ┌──────▼──┐    ┌──────────▼────────┐ ┌────▼─────┐
   │  MySQL   │         │  Redis  │    │ 加密证据文件       │ │ KMS 抽象 │
   │ 单实例   │         │ 单实例  │    │ 本地或 MinIO/S3    │ │ Local/外部│
   └──────────┘         └─────────┘    └───────────────────┘ └──────────┘
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
| L3 数据泄露    | AES-256-GCM 字段加密；开发使用 LocalKMS；外部 KMS 和 `decrypt_user` 隔离是生产待办 |
| 审计被改       | `app_user` 仅 INSERT/SELECT；触发器拦截 UPDATE/DELETE；可选哈希链          |
| 司法协助滥用   | 5 分钟窗口 + 全员告警 + 水印                                                |
| 越权 SQL       | ORM 严禁拼字符串；分页参数硬上限；mypy `--strict`                           |

---

## 5. 部署拓扑与实现边界

### 5.1 当前演示环境

```text
[浏览器]
   ├─ HTTP → Vue 3 / Vite 开发服务器（5173）
   ├─ HTTP → 单个 Uvicorn / FastAPI 容器（8000）
   └─ 可选 HTTPS → Nginx 统一入口（edge profile）
                    ├─ 单实例 MySQL 8
                    ├─ 单实例 Redis 7.2
                    ├─ AES-256-GCM 加密后的 MinIO/S3 证据对象
                    ├─ LocalKMS（环境变量主密钥，仅开发/测试）
                    ├─ Mock CAS（可切换 Real CAS 3.0 Provider）
                    └─ Prometheus `/metrics` + 结构化日志
```

Docker Compose 默认通过 `STORAGE_BACKEND=s3` 将证据文件加密后写入 MinIO，
测试环境仍可使用 `STORAGE_BACKEND=local` 写入 `EVIDENCE_UPLOAD_DIR`。
MinIO 桶会在首次写入时自动检查并创建。

当前普通 `make up` 仍以轻量演示为主。需要展示统一入口时可启用
`edge` profile 启动 Nginx + 自签 TLS；需要展示监控面板时可启用
`observability` profile 启动 Prometheus 和 Grafana。MySQL 主从、
Redis Sentinel/Cluster、外部 Vault/AWS KMS 和集中日志平台仍属于正式
生产基础设施接入项。

### 5.2 生产目标（非本课程已部署范围）

```
[校园网用户] → Nginx / 负载均衡（TLS 终止）
                         → FastAPI 应用节点 × N
                         → MySQL 主库 + 只读副本
                         → Redis Sentinel / Cluster
                         → MinIO / S3（加密证据文件）
                         → Vault / 云 KMS
                         → Prometheus + Grafana、集中日志平台
```

学校数据中心内网；DMZ 部署应用服务器；DB / 文件 / KMS 不直暴。

Redis 保存在线会话，因此应用节点不需要粘性会话，具备横向扩展的基础。
但要真正实现节点故障自动接管，还必须配置负载均衡健康检查、至少两个应用
实例，以及 Redis 和数据库自身的高可用方案。当前定时任务随 FastAPI 进程
启动；扩容前还应将定时任务迁移到独立 worker，或增加分布式锁，避免多节点
重复执行。

MySQL 目前只有一个连接地址，没有读写路由。落地主从后需增加只读数据源，
并只把允许最终一致性的查询路由到副本；事务、审核状态和权限变更仍必须读取
主库。

对象存储已由 `storage_service` 适配为本地 / S3 双后端，上传前会先加密并
保留哈希、密钥版本和权限检查。生产环境还需配置桶权限、生命周期、备份策略
和跨可用区存储。生产 KMS 仍需实现当前占位的 Vault 或 AWS KMS Provider，
确保主密钥不与密文位于同一主机或同一配置文件。

Prometheus 指标采集可以旁路进行，应用日志也可异步采集；但审计日志不能
一概描述为“旁路且不阻塞”。普通审计默认写 Redis Stream，高敏操作的审计
会与业务事务同步写入，失败时会阻止操作完成，以保证合规一致性。

---

## 6. 与 PRD 的对照

- 系统整体架构：PRD 图 2.1 ✓
- ER 图：PRD 图 5.1，本骨架完成"用户与权限域 + 系统支撑域 + 匿名相关"
- 业务模型（FraudReport / WarningNotice / KnowledgeEntry / Quiz）由各 UC 负责人在自己的 PR 中按字典补齐，外键依然指向本骨架的 User / Department / FraudType。
