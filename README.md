# 校园电信诈骗上报与预警平台 · Anti-Fraud Platform

> 南开大学 · 软件工程课程项目（2026）
>
> 本仓库实现 PRD《校园电信诈骗上报与预警平台 — 软件需求分析文档》中所定义的全部业务功能。当前提交聚焦于 **地基工程**：登录、账号与权限管理、项目骨架、审计 SDK，以及供其余 4 名团队成员复用的横切基础设施。

---

## 1. 一句话定位

让全校学生用最低成本上报疑似电信诈骗、让审核管理员快速流转处理、让所有相关角色第一时间收到精准预警，并把每一次案件沉淀为可检索的反诈知识。

## 2. 仓库结构（monorepo · 单仓多包）

```
anti-fraud-platform/
├── backend/        # FastAPI 后端服务（Python 3.11+）
├── frontend/       # Vue 3 + TypeScript SPA
├── infra/          # Docker Compose 环境变量与 MySQL 初始化脚本
├── docs/           # 设计文档、ADR、运维手册、贡献规范
├── scripts/        # 一键脚本（setup / reset_db / seed / verify_audit_chain）
├── .github/        # CI/CD workflow、Issue/PR 模板、CODEOWNERS
├── docker-compose.yml
├── Makefile
└── README.md
```

详细分层与每个目录的职责，见 [`docs/architecture.md`](docs/architecture.md)。

## 3. 快速开始（≤ 30 分钟）

> 完整新人指南见 [`docs/getting-started.md`](docs/getting-started.md)（含 macOS / Windows-WSL2 / Linux 三平台分支）。

### 前置依赖

| 工具         | 版本                    | 安装提示              |
| ------------ | ----------------------- | --------------------- |
| Docker       | ≥ 24                    | 含 Docker Compose v2  |
| Make         | ≥ 4                     | macOS/Linux 自带      |
| Git          | ≥ 2.30                  | —                     |
| Node.js      | ≥ 20（仅本地前端开发）  | 通过 `nvm` 管理       |
| Python       | ≥ 3.11（仅本地后端开发）| 通过 `uv` 管理        |

### 三步起飞

```bash
# 1. 克隆仓库 + 拷贝环境变量样板
git clone <repo-url> anti-fraud-platform
cd anti-fraud-platform
make bootstrap                # 复制各子项目的 .env.example → .env

# 2. 启动整套环境（mysql + redis + minio + backend + frontend）
make up

# 3. 跑数据库迁移 + 种子数据
make migrate && make seed
```

启动完成后：

- 前端：<http://localhost:5173>
- 后端 OpenAPI：<http://localhost:8000/docs>（仅 dev 环境暴露）
- MinIO 控制台：<http://localhost:9001>（账号见 `.env.example`）

默认 **Mock CAS 模式**：登录页直接输入种子账号（如 `student001` / `reviewer_dept001` / `sysadmin001`）即可，无须接入真 CAS。

## 4. 常用命令

| 命令                  | 说明                                                                  |
| --------------------- | --------------------------------------------------------------------- |
| `make up`             | 启动全部服务（含健康检查）                                            |
| `make down`           | 关停所有服务                                                          |
| `make logs`           | 跟随所有服务日志（`make logs s=backend` 跟随单服务）                  |
| `make migrate`        | 运行 Alembic 数据库迁移                                               |
| `make seed`           | 种子数据：账号权限 + 全状态案件 + 草稿/预警/知识/测验/通知             |
| `make reset`          | 一键重置：drop → create → migrate → seed                             |
| `make new-migration NAME=add_xxx` | 生成一个新的 Alembic 迁移脚本                              |
| `make test`           | 后端 + 前端全套测试                                                   |
| `make lint`           | 全仓 lint（Ruff + Black + Mypy + ESLint + Stylelint）                 |
| `make smoke`          | 5 分钟冒烟测试（登录 → 上报 → 审核 → 发预警 → 答题）                  |
| `make verify-audit`   | 校验审计日志哈希链完整性                                              |

## 5. 贡献指南（团队成员必读）

- 分支：`feature/<姓名缩写>-<UC编号>-<简述>`，禁止直接推 `main` / `develop`。
- 提交信息：[Conventional Commits](https://www.conventionalcommits.org/)（`feat:` / `fix:` / `docs:` / ...），由 commitlint 强制拦截。
- 每个 PR 必须填写模板五栏 + 至少 1 人 approve + CI 全绿。
- 涉及 `backend/app/api/auth/`、`backend/app/services/audit_service.py`、`backend/alembic/` 的改动必须由组长（CODEOWNER）亲审。
- 完整规范：[`docs/conventions.md`](docs/conventions.md)。

## 6. 五条铁律（违反一次 revert）

1. **零硬编码秘密** —— 通过环境变量 / KMS 注入。
2. **零 `print` / 零裸 `try/except: pass`** —— 日志只能走 `structlog`。
3. **零无测试合并** —— 任何 PR 必带测试。
4. **零绕过 RBAC** —— 不允许 `if user.role == 'reviewer'` 这类 ad-hoc 判断。
5. **零绕过审计** —— L2/L3 操作必须走 `audit.write()`。

## 7. 文档地图

| 文档                                              | 内容                                                  |
| ------------------------------------------------- | ----------------------------------------------------- |
| [getting-started](docs/getting-started.md)        | 30 分钟新人上手指南（macOS / WSL2 / Linux）           |
| [architecture](docs/architecture.md)              | 系统架构、分层职责、关键决策                          |
| [conventions](docs/conventions.md)                | 命名 / 错误码 / 日志 / 接口 / 提交信息全部规约        |
| [api-guide](docs/api-guide.md)                    | 5 步教程：如何添加一个新接口                          |
| [error-codes](docs/error-codes.md)                | 错误码字典（按业务域分号段）                          |
| [permissions](docs/permissions.md)                | 全平台权限码清单                                      |
| [demo-feature-checklist](docs/demo-feature-checklist.md) | 完整功能演示清单、角色脚本与验收项              |
| [demo-runbook-detailed](docs/demo-runbook-detailed.md) | 精细化实操演示手册（点击步骤 / 讲解话术 / 截图） |
| [risks](docs/risks.md)                            | 风险登记册（每周更新）                                |
| [adr/](docs/adr/)                                 | 架构决策记录（≥ 8 篇）                                |
| [CHANGELOG](CHANGELOG.md)                         | 发版变更日志（Keep a Changelog 格式）                 |

## 8. 联系人

| 模块                                         | CODEOWNER                                |
| -------------------------------------------- | ---------------------------------------- |
| 项目骨架 / 登录 / 审计（地基）               | @gong-web（巩岱松）                      |
| 前端 UI / 设计系统 / 截图自动化              | @gong-web（巩岱松）                      |
| 上报与状态流转 (UC-01/02)                    | TBD                                      |
| 审核与预警 (UC-06/07)                        | @gzh / @lht                              |
| 知识库与测验 (UC-04/05/08/09)                | @lht / @tsy                              |
| 仪表盘与报表                                 | TBD                                      |

详见 [`.github/CODEOWNERS`](.github/CODEOWNERS)。

---

> **Boring is beautiful**：本项目只用最朴素、最被验证的方案。如果一个新方案不能比现有方案明显更优，那就别上。
