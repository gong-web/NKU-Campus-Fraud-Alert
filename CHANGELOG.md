# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 与 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

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
