# ──────────────────────────────────────────────────────────────────
# Anti-Fraud Platform · Makefile
#
# 设计原则：所有日常动作都是单条 `make <target>`，新人不必记 docker 命令。
# 每个 target 顶部有一行 ## 注释，自动出现在 `make help`。
# ──────────────────────────────────────────────────────────────────

SHELL := /bin/bash
COMPOSE := docker compose
PROJECT := anti-fraud
SERVICE ?= backend

.DEFAULT_GOAL := help

.PHONY: help bootstrap up down restart logs ps build \
        migrate post-grants new-migration downgrade seed reset \
        test test-backend test-frontend smoke \
        lint lint-backend lint-frontend format \
        verify-audit shell-backend shell-db shell-redis \
        clean

help:  ## 显示本 Makefile 全部 target
	@awk 'BEGIN {FS = ":.*##"; printf "\n\033[1mUsage:\033[0m make \033[36m<target>\033[0m\n\n\033[1mTargets:\033[0m\n"} \
	      /^[a-zA-Z_-]+:.*?##/ {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# ── 初始化 ─────────────────────────────────────────────────────────
bootstrap:  ## 拷贝各子项目的 .env.example → .env（首次启动前执行）
	@for f in backend/.env.example frontend/.env.example infra/.env.example; do \
		dst=$${f%.example}; \
		if [ ! -f $$dst ]; then cp $$f $$dst && echo "created $$dst"; \
		else echo "skip $$dst (already exists)"; fi; \
	done

# ── 容器生命周期 ──────────────────────────────────────────────────
up:  ## 启动全部服务（带健康检查）
	$(COMPOSE) up -d --remove-orphans

down:  ## 停止并删除所有容器
	$(COMPOSE) down --remove-orphans

restart:  ## 重启全部服务
	$(MAKE) down && $(MAKE) up

build:  ## 重新构建镜像
	$(COMPOSE) build --pull

logs:  ## 跟随日志，可指定 s=<service>
	$(COMPOSE) logs -f --tail=200 $(s)

ps:  ## 列出全部容器状态
	$(COMPOSE) ps

# ── 数据库 ─────────────────────────────────────────────────────────
migrate:  ## 运行 Alembic 迁移到最新版本，并应用迁移后精细授权
	$(COMPOSE) exec backend alembic upgrade head
	$(MAKE) post-grants

post-grants:  ## 应用 MySQL 表级最小权限 + audit_logs 不可变触发器
	@MYSQL_ROOT_PASSWORD=$$(grep MYSQL_ROOT_PASSWORD infra/.env | cut -d= -f2); \
	$(COMPOSE) exec -T mysql mysql -uroot -p$$MYSQL_ROOT_PASSWORD anti_fraud < infra/docker/mysql/post_migration/01_grants.sql

downgrade:  ## 回退一个版本（NAME=-1 时）
	$(COMPOSE) exec backend alembic downgrade -1

new-migration:  ## 生成迁移脚本：make new-migration NAME=add_xxx
	@test -n "$(NAME)" || (echo "ERROR: NAME required, e.g. make new-migration NAME=add_xxx"; exit 1)
	$(COMPOSE) exec backend alembic revision --autogenerate -m "$(NAME)"

seed:  ## 灌入种子数据（院系 / 诈骗类型 / 测试账号 / 角色权限矩阵）
	$(COMPOSE) exec backend python -m app.infra.db.seed

reset:  ## 危险操作：drop → create → migrate → seed
	@read -p "Will DROP and re-create database. Continue? [y/N] " ans && [ "$$ans" = "y" ] || exit 1
	$(COMPOSE) exec backend python -m scripts.reset_db
	$(MAKE) migrate
	$(MAKE) seed

# ── 测试 ───────────────────────────────────────────────────────────
test: test-backend test-frontend  ## 运行所有测试

test-backend:  ## 仅后端测试（unit + integration）
	$(COMPOSE) exec backend pytest -ra --cov=app --cov-report=term-missing

test-frontend:  ## 仅前端测试
	$(COMPOSE) exec frontend npm run test

smoke:  ## 5 分钟冒烟测试（登录 → 上报 → 审核 → 预警 → 答题）
	$(COMPOSE) exec backend pytest tests/e2e/test_smoke.py -v

# ── 代码质量 ──────────────────────────────────────────────────────
lint: lint-backend lint-frontend  ## 全仓 lint

lint-backend:  ## 后端 lint：Ruff + Black --check + Mypy
	$(COMPOSE) exec backend bash -c "ruff check . && black --check . && mypy app"

lint-frontend:  ## 前端 lint：ESLint + Stylelint + tsc --noEmit
	$(COMPOSE) exec frontend bash -c "npm run lint && npm run typecheck"

format:  ## 自动格式化全仓代码
	$(COMPOSE) exec backend bash -c "ruff check --fix . && black ."
	$(COMPOSE) exec frontend npm run format

# ── 审计与运维 ────────────────────────────────────────────────────
verify-audit:  ## 校验审计日志哈希链完整性
	$(COMPOSE) exec backend python -m scripts.verify_audit_chain

shell-backend:  ## 进入 backend 容器
	$(COMPOSE) exec backend bash

shell-db:  ## 进入 MySQL 命令行
	$(COMPOSE) exec mysql mysql -uroot -p$$(grep MYSQL_ROOT_PASSWORD infra/.env | cut -d= -f2) anti_fraud

shell-redis:  ## 进入 Redis CLI
	$(COMPOSE) exec redis redis-cli

# ── 清理 ───────────────────────────────────────────────────────────
clean:  ## 清理本地 cache 与临时产物
	@find . -type d -name __pycache__ -prune -exec rm -rf {} \;
	@find . -type d -name .pytest_cache -prune -exec rm -rf {} \;
	@find . -type d -name .mypy_cache -prune -exec rm -rf {} \;
	@find . -type d -name .ruff_cache -prune -exec rm -rf {} \;
	@find . -type d -name node_modules -prune -exec rm -rf {} \;
	@find . -type d -name dist -prune -exec rm -rf {} \;
	@echo "cleaned."
