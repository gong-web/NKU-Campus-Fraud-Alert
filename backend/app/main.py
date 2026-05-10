"""FastAPI 应用工厂。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import install_error_handlers
from app.api.middleware import (
    CSRFRequiredHeaderMiddleware,
    SecurityHeadersMiddleware,
    TraceIdMiddleware,
)
from app.api.v1 import build_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.infra.cache.client import close_redis
from app.infra.cache.rbac_cache import RBACCache
from app.infra.db.session import dispose_engine, uow
from app.infra.repositories.role import RoleRepository

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """应用生命周期。"""
    settings = get_settings()
    configure_logging(level=settings.log_level, log_format=settings.log_format)
    logger.info(
        "app_starting",
        env=settings.app_env,
        version=settings.app_version,
        auth_provider=settings.auth_provider,
        kms_provider=settings.kms_provider,
    )

    # 启动期把 RBAC 加载进 Redis（便于 require_permission O(1) 查询）
    try:
        async with uow() as session:
            roles = RoleRepository(session)
            mapping = await roles.list_role_permissions_full()
        await RBACCache().load(mapping)
    except Exception as exc:
        logger.warning(
            "rbac_load_skipped_at_startup",
            error=str(exc),
            note="将首次鉴权失败时回退到 DB；建议执行 `make migrate && make seed`",
        )

    yield

    logger.info("app_shutting_down")
    await close_redis()
    await dispose_engine()


def create_app() -> FastAPI:
    """构造 FastAPI 实例（main 入口 + 测试 fixture 共用）。"""
    settings = get_settings()
    docs_url = "/docs" if settings.openapi_enabled else None
    redoc_url = "/redoc" if settings.openapi_enabled else None
    openapi_url = "/openapi.json" if settings.openapi_enabled else None

    app = FastAPI(
        title="Anti-Fraud Platform · Backend",
        version=settings.app_version,
        description="校园电信诈骗上报与预警平台 — 后端 API",
        docs_url=docs_url,
        redoc_url=redoc_url,
        openapi_url=openapi_url,
        lifespan=lifespan,
    )

    # ── Middleware（顺序：内 → 外） ──────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CSRFRequiredHeaderMiddleware)
    app.add_middleware(TraceIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_list or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Trace-Id"],
    )

    install_error_handlers(app)

    # ── Routes ─────────────────────────────────────────────
    @app.get("/healthz", tags=["meta"], include_in_schema=False)
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/readyz", tags=["meta"], include_in_schema=False)
    async def readyz() -> dict[str, str]:
        # 简化版；可扩展为依次 ping DB / Redis / KMS
        return {"status": "ok"}

    if settings.observability.prometheus_enabled:
        try:
            from fastapi import Response
            from prometheus_client import (
                CONTENT_TYPE_LATEST,
                generate_latest,
            )

            @app.get(
                settings.observability.prometheus_path,
                tags=["meta"],
                include_in_schema=False,
            )
            async def metrics() -> Response:
                return Response(
                    content=generate_latest(),
                    media_type=CONTENT_TYPE_LATEST,
                )

        except ImportError as exc:
            # prometheus_client 在 pyproject 里已声明；走到这里说明镜像被裁剪
            # 或开发者跳过依赖安装。打日志而非沉默吞掉。
            logger.warning("prometheus_client_unavailable", reason=str(exc))

    app.include_router(build_v1_router())

    return app


app = create_app()
