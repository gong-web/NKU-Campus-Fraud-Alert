# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased] - 2026-05-21 · @lht  - 新增 UC-03/04/07/08 预警与知识库模块

### Added — 预警公告（UC-03 / UC-07）

- 后端：`WarningNotice` / `WarningTarget` 两张表 + Alembic 迁移；`POST /admin/warnings`、`GET /warnings`、`POST /admin/warnings/{id}/append`、`POST /admin/warnings/{id}/offline`、管理员侧 `GET/list` 接口完整闭环。
- 业务规则：`warning_level=3`（紧急）发布额外校验登录用户 `Role.role_level == 2`（校级 reviewer）；`push_scope=DEPARTMENT` 必须携带 `target_dept_ids`；同事务内 `audit.write(sync=True, session=session)` + `send_notification`（事务内 fan-out 给学生）；紧急级邮件占位（`_send_email_for_urgent`）。
- 状态机：`ONLINE → OFFLINE`；OFFLINE 不可追加；重复 offline 触发 `WarningOfflineConflict (40003)`。
- 前端：`/admin/warnings`（列表 / 编辑器 / 详情）+ `/student/warnings`（列表 / 详情）+ 学生端首页紧急横幅。

### Added — 知识库（UC-04 / UC-08）

- 后端：`KnowledgeEntry` / `KnowledgeEntryHistory` 两张表 + MySQL 8 FULLTEXT(ngram) 索引；`DRAFT → PENDING → PUBLISHED → OFFLINE` 状态机（`backend/app/services/state_machine.py`）；版本号自增 + 整行 JSON 快照入历史。
- 接口：作者 `POST /admin/knowledge/drafts` → `submit` → 校级 reviewer `approve` / `reject` → `offline`；学生侧 `GET /knowledge` 全文搜索 + 推荐相关条目。
- 前端：`/admin/knowledge`（列表 / 编辑器 / 详情，含驳回原因 + 状态徽章）+ `/student/knowledge`（搜索 / 详情）。

### Tests

- 后端集成：`tests/integration/test_warnings.py`（7 用例）、`tests/integration/test_knowledge.py`（7 用例）。
- 后端单元：`tests/unit/test_warning_state.py`（5 用例）、`tests/unit/test_knowledge_state_machine.py`（27 用例）。
- 全仓 108 / 108 测试绿。

### Removed

- 学生端预警「已读 / 未读」功能：删除 `WarningRead` 模型、`warning_reads` 表（迁移 + downgrade 同步）、`mark_read` / `count_reads` 仓储方法、Schema 上的 `has_read` / `read_count` 字段，以及前端三处展示与 CSS。

---

## [Unreleased]

### Added — 地基工程（Foundation）

- 仓库骨架：monorepo（backend / frontend / infra / docs / scripts / .github）。
- 一键启动：`docker-compose` + `Makefile`，冷启动 ≤ 60s，新人 30 分钟可跑通。
- CI/CD：GitHub Actions（lint / test / build / security 四段流水线）。
- 后端骨架：FastAPI + SQLAlchemy 2.x async + Alembic + Pydantic Settings v2。
- 鉴权：CAS 3.0 协议（含 Mock CAS 本地开发模式）+ Redis Session（30 分钟滑动过期）。
- 权限装饰器：`get_current_user` / `require_role` / `require_permission` / `require_self_or_role`。
- 账号管理（UC-10）：CRUD + CSV 批量导入 + 角色变更立即生效。
- 司法协助查询（UC-10 备选 A2）：5 分钟解密窗口 + 全员告警 + 水印 + 物理隔离 DB 账号。
- 审计 SDK：显式调用 + 装饰器双形式，异步落库 + 本地 fallback + 链式哈希。
- 数据建模：用户与权限域 5 张表 + 系统支撑域 4 张表（其余业务表由各模块负责人补充）。
- 设计系统：tokens.css + 8 个 `App*` 基础组件 + 三态（空 / 加载 / 错误）官方实现。
- 文档：getting-started、architecture、conventions、api-guide、error-codes、permissions、risks、ADR ≥ 8 篇。

### Security

- 字段级 AES-256-GCM 加密（手机号、邮箱、匿名映射真实身份）。
- 审计表 `audit_logs` 数据库账号仅授 INSERT/SELECT，无 UPDATE/DELETE。
- AnonymousMapping 使用独立 DB 账号 `decrypt_user`，业务账号无访问权限。
- CSRF / XSS / 会话固定 / 重放 / 横向越权 全部缓解（详见 `docs/architecture.md` 安全章节）。

### Notes

- 本仓库为课程项目，1 年期；以"够用、稳定、可演示"为优先于"再优雅一点点"。
- 关键决策记录在 `docs/adr/` 共 8 篇。
