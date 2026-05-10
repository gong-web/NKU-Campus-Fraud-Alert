"""按配置切换 Real / Mock CAS Provider。"""

from __future__ import annotations

from functools import lru_cache

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infra.cas.base import AuthProvider
from app.infra.cas.mock import MockCASProvider
from app.infra.cas.real import RealCASProvider

logger = get_logger(__name__)


def build_auth_provider() -> AuthProvider:
    """根据 ``settings.auth_provider`` 构造一个新的 Provider。"""
    settings = get_settings()
    if settings.auth_provider == "mock":
        if settings.app_env == "prod":
            # config.py 已拦截，这里兜底
            raise RuntimeError("生产环境禁止使用 Mock CAS")
        logger.info("auth_provider_mock_enabled")
        return MockCASProvider()
    return RealCASProvider()


@lru_cache(maxsize=1)
def get_auth_provider() -> AuthProvider:
    """全局单例（FastAPI dependency 用）。"""
    return build_auth_provider()
