# syntax=docker/dockerfile:1.7
# ──────────────────────────────────────────────────────────────────
# Anti-Fraud Backend · 多阶段 Dockerfile
#  - builder: 装依赖 (uv)
#  - dev:     带热重载的开发镜像
#  - runtime: 最小化运行镜像 (≤ 200 MB 目标)
# ──────────────────────────────────────────────────────────────────

ARG PYTHON_VERSION=3.11

FROM python:${PYTHON_VERSION}-slim AS base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    TZ=Asia/Shanghai
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# ── builder：装依赖 ────────────────────────────────────────────────
FROM base AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# uv 比 pip 快约 10x
COPY --from=ghcr.io/astral-sh/uv:0.4.18 /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock* ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --all-extras --dev || \
    uv sync --no-install-project --all-extras --dev

# The current uv.lock was generated before the test group and security bumps.
# Keep the dev/runtime image merge-ready by forcing patched packages and test tools
# until the lockfile is regenerated in a dependency maintenance PR.
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv/bin/python \
        "cryptography>=46.0.7,<47.0" \
        "lxml>=6.1,<7.0" \
        "black>=26.3.1,<27.0" \
        "pytest>=9.0.3,<10.0" \
        "pytest-asyncio>=1.3,<2.0" \
        "pytest-cov>=5.0,<7.0" \
        "pytest-mock>=3.14,<4.0" \
        "pytest-xdist>=3.5,<4.0" \
        "factory-boy>=3.3,<4.0" \
        "fakeredis>=2.23,<3.0" \
        "freezegun>=1.5,<2.0" \
        "respx>=0.21,<1.0" \
        "aiosqlite>=0.20,<1.0"

# ── dev：带热重载，目标 docker-compose 的 backend.target=dev ────
FROM builder AS dev
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--proxy-headers"]

# ── runtime：生产镜像 ─────────────────────────────────────────────
FROM base AS runtime
RUN groupadd --system --gid 1000 app \
 && useradd --system --uid 1000 --gid app --home-dir /app --shell /usr/sbin/nologin app

# 仅拷依赖 + 应用代码（不带测试 / 文档）
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY --chown=app:app app /app/app
COPY --chown=app:app alembic /app/alembic
COPY --chown=app:app alembic.ini /app/alembic.ini

USER app
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/healthz || exit 1

# 4 worker × Uvicorn for typical 4-core box
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
