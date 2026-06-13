# 30 分钟新人上手指南

> 本指南目标：**任何一位非项目成员的同学**拿到仓库后，30 分钟内可以本地跑通登录流程。

> 如果你卡在某一步超过 5 分钟，**先在 PR 里把"这一步该补什么"提出来**，再继续——这是组长承诺。

---

## 1. 前置依赖

| 工具    | 推荐版本 | 检查命令               |
| ------- | -------- | ---------------------- |
| Docker  | ≥ 24     | `docker --version`     |
| Compose | v2       | `docker compose version` |
| Make    | ≥ 4      | `make --version`       |
| Git     | ≥ 2.30   | `git --version`        |

如要本地跑后端 / 前端（不通过容器），还需：

| 工具       | 推荐版本 | 安装提示                                           |
| ---------- | -------- | -------------------------------------------------- |
| Python     | 3.11     | macOS `brew install python@3.11`；其它平台用 `pyenv` |
| Node.js    | 20       | `nvm install 20`                                   |
| uv         | latest   | `pip install uv` 或 `brew install uv`              |

---

## 2. 各平台快速通道

### macOS

```bash
brew install --cask docker
brew install make git
git clone <repo-url> anti-fraud-platform && cd anti-fraud-platform
make bootstrap                # 拷贝 .env.example → .env
make up && make migrate && make seed
open http://localhost:5173
```

### Windows（WSL2）

> 推荐统一在 WSL2 Ubuntu 22.04 内开发。Docker Desktop 启用 WSL2 集成。

```bash
sudo apt-get update && sudo apt-get install -y make git
git clone <repo-url> anti-fraud-platform && cd anti-fraud-platform
make bootstrap
make up && make migrate && make seed
```

浏览器（Windows 端）打开 `http://localhost:5173`。

### Linux（Ubuntu 22.04）

```bash
sudo apt-get update && sudo apt-get install -y docker.io docker-compose-plugin make git
sudo usermod -aG docker $USER && newgrp docker
git clone <repo-url> anti-fraud-platform && cd anti-fraud-platform
make bootstrap
make up && make migrate && make seed
xdg-open http://localhost:5173
```

---

## 3. 第一次登录（Mock 模式）

种子数据预置了：

- 1 个 SysAdmin：`sysadmin001`
- 2 个 Reviewer：`reviewer_dept001`（院系级） / `reviewer_school001`（校级）
- 5 个 Student：`student001` ~ `student005`
- 8 条覆盖全部案件状态的演示上报（其中 1 条为匿名案件）
- 草稿、预警、知识审核状态、测验历史、错题和站内通知

打开 `http://localhost:5173` → **Mock 登录** → 输入任一账号 → 跳到对应工作台。

司法协助演示可直接使用事件 ID `990000000000000005` 和案件编号
`2026-CS-900005`。seed 可重复执行且不会重复插入；若要把已经操作过的
演示数据恢复到初始状态，需要执行会清空数据库的 `make reset`。

---

## 4. 常见故障 & 自救

| 现象                                       | 检查                                                                  |
| ------------------------------------------ | --------------------------------------------------------------------- |
| `make up` 卡在 `mysql: starting`           | `docker logs anti-fraud-mysql` 看错误；通常是端口 3306 已占用         |
| 前端访问 `/api/...` 报 CORS                | 检查 `backend/.env` 的 `CORS_ALLOW_ORIGINS` 是否含 `http://localhost:5173` |
| `make migrate` 报 `Unknown column ...`     | 删 volume：`docker compose down -v && make up && make migrate && make seed` |
| 登录后立即跳回登录页                       | 浏览器 DevTools 看 Cookie 是否被设置；本地 http 下 `SESSION_COOKIE_SECURE` 必须是 false |

---

## 5. 自检清单（30 分钟内全部应通过）

- [ ] 浏览器能打开 `http://localhost:5173/login`
- [ ] Mock 登录 `student001` 能跳到 `/student/home`
- [ ] Mock 登录 `sysadmin001` 能进 `/sys/users` 看到列表
- [ ] `http://localhost:8000/docs` 能看到 OpenAPI
- [ ] `make test-backend` 全绿

如有任何一条不通过，请在 `docs/risks.md` 里登记一行，并 @ 组长。
