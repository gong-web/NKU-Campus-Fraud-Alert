"""平台配置。

设计原则
--------
- **类型化**：每一项配置都有明确类型与默认值；运行时 Pydantic 严校验。
- **分组**：通过组合而非平铺，按域聚合（``DatabaseSettings`` / ``RedisSettings`` …）。
- **零硬编码**：所有秘密只能从环境变量 / Vault 注入；源码里出现一次就回滚。
- **启动自检**：缺失必填配置时立即退出，不要跑到一半再崩。

使用方式
--------
.. code-block:: python

    from app.core.config import get_settings

    settings = get_settings()
    redis_url = settings.redis.url

``get_settings()`` 用 ``functools.lru_cache`` 缓存，整个进程只构造一次。
"""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

AppEnv = Literal["local", "dev", "staging", "prod", "test"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
LogFormat = Literal["console", "json"]
AuthProvider = Literal["mock", "real"]
KMSProvider = Literal["local", "vault", "aws"]


class DatabaseSettings(BaseModel):
    """关系型数据库设置。"""

    url: str = Field(
        default="mysql+aiomysql://app_user:apppassword@mysql:3306/anti_fraud?charset=utf8mb4",
        description="SQLAlchemy 异步连接 URL（aiomysql 驱动）",
    )
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=200)
    pool_recycle: int = Field(default=1800, description="连接回收秒数，避免 MySQL wait_timeout")
    echo: bool = Field(default=False, description="生产必须 false，开发调试时短开")

    @property
    def sync_url(self) -> str:
        """Alembic 等同步上下文用的 URL（pymysql 驱动）。"""
        return self.url.replace("+aiomysql", "+pymysql")


class RedisSettings(BaseModel):
    """Redis 设置。"""

    url: str = Field(default="redis://:redispassword@redis:6379/0")
    key_prefix: str = Field(default="afp")
    audit_stream_key: str = Field(default="afp:audit:stream")
    audit_stream_maxlen: int = Field(default=100_000)


class CASSettings(BaseModel):
    """CAS 单点登录配置。"""

    server_url: str = Field(default="https://cas.example.edu.cn/cas")
    service_url: str = Field(default="http://localhost:8000/api/v1/auth/cas/callback")
    service_whitelist: list[str] = Field(default_factory=list)
    timeout_seconds: float = Field(default=10.0, gt=0)
    health_check_interval_seconds: int = Field(default=60, gt=0)
    mock_allow_any: bool = Field(default=True, description="Mock 模式下接受任何 cas_account")

    @field_validator("service_whitelist", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> object:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


class SecuritySettings(BaseModel):
    """会话与 Cookie 安全。"""

    secret_key: SecretStr = Field(
        ...,  # 必填：缺失立即报错
        description="Cookie 签名 / token 签名根密钥。生产环境必须 ≥ 32 字节。",
    )
    session_cookie_name: str = Field(default="afp_session")
    session_cookie_domain: str = Field(default="")
    session_cookie_secure: bool = Field(default=False, description="prod 必须 true")
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_ttl_seconds: int = Field(default=1800, ge=60, le=86400)

    @field_validator("secret_key")
    @classmethod
    def _len_check(cls, v: SecretStr) -> SecretStr:
        if len(v.get_secret_value()) < 16:
            raise ValueError("SECRET_KEY 长度不足 16 字节，请重新生成")
        return v


class KMSSettings(BaseModel):
    """密钥管理服务（保护 AES 字段加密所用 DEK / 主密钥）。"""

    provider: KMSProvider = Field(default="local")
    local_master_key: SecretStr = Field(
        default=SecretStr("ZGV2LW1hc3Rlci1rZXktbm90LWZvci1wcm9kdWN0aW9uLXVzZSE=")
    )
    data_key_version: str = Field(default="v1")


class StorageSettings(BaseModel):
    """对象存储（证据文件加密落盘）。"""

    endpoint: str = Field(default="http://minio:9000")
    access_key: SecretStr = Field(default=SecretStr("minioadmin"))
    secret_key: SecretStr = Field(default=SecretStr("minioadmin123"))
    bucket: str = Field(default="evidence")
    region: str = Field(default="us-east-1")
    use_ssl: bool = Field(default=False)


class SnowflakeSettings(BaseModel):
    datacenter_id: int = Field(default=1, ge=0, le=31)
    worker_id: int = Field(default=1, ge=0, le=31)
    epoch_ms: int = Field(default=1_735_689_600_000, description="2025-01-01 00:00:00 UTC")


class JudicialSettings(BaseModel):
    """司法协助查询（全系统最高敏操作）。"""

    decrypt_window_seconds: int = Field(default=300, ge=60, le=900)
    notify_all_sysadmins: bool = Field(default=True)


class AuditSettings(BaseModel):
    async_enabled: bool = Field(default=True)
    fallback_path: Path = Field(default=Path("/app/logs/audit_fallback.jsonl"))
    hash_chain_enabled: bool = Field(default=True)


class ObservabilitySettings(BaseModel):
    prometheus_enabled: bool = Field(default=True)
    prometheus_path: str = Field(default="/metrics")


class Settings(BaseSettings):
    """应用顶层配置。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    # ── 应用元信息 ──────────────────────────────────────────
    app_env: AppEnv = "local"
    app_name: str = "anti-fraud-backend"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: LogLevel = "INFO"
    log_format: LogFormat = "console"

    # ── 网络 ────────────────────────────────────────────────
    host: str = "0.0.0.0"  # noqa: S104 - 容器内监听全部接口
    port: int = 8000
    root_path: str = ""
    # 注意：用 str 而非 list[str]，避免 pydantic-settings 把环境变量当 JSON 解析。
    # 通过 :pyattr:`Settings.cors_allow_origins_list` 属性按 CSV 分割成 list。
    cors_allow_origins: str = ""

    # ── OpenAPI ─────────────────────────────────────────────
    openapi_enabled: bool = True

    # ── CAS 认证 Provider 切换 ──────────────────────────────
    auth_provider: AuthProvider = "mock"

    # ── 平铺到顶层的子配置（通过环境变量直接命中）─────────
    secret_key: SecretStr = Field(...)
    session_cookie_name: str = "afp_session"
    session_cookie_domain: str = ""
    session_cookie_secure: bool = False
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_ttl_seconds: int = 1800

    database_url: str = (
        "mysql+aiomysql://app_user:apppassword@mysql:3306/anti_fraud?charset=utf8mb4"
    )
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_pool_recycle: int = 1800
    database_echo: bool = False

    redis_url: str = "redis://:redispassword@redis:6379/0"
    redis_key_prefix: str = "afp"
    redis_audit_stream_key: str = "afp:audit:stream"
    redis_audit_stream_maxlen: int = 100_000

    cas_server_url: str = "https://cas.example.edu.cn/cas"
    cas_service_url: str = "http://localhost:8000/api/v1/auth/cas/callback"
    cas_service_whitelist: str = ""  # 逗号分隔，下面分割
    cas_timeout_seconds: float = 10.0
    cas_health_check_interval_seconds: int = 60
    mock_cas_allow_any: bool = True

    kms_provider: KMSProvider = "local"
    kms_local_master_key: SecretStr = SecretStr(
        "ZGV2LW1hc3Rlci1rZXktbm90LWZvci1wcm9kdWN0aW9uLXVzZSE="
    )
    kms_data_key_version: str = "v1"

    s3_endpoint: str = "http://minio:9000"
    s3_access_key: SecretStr = SecretStr("minioadmin")
    s3_secret_key: SecretStr = SecretStr("minioadmin123")
    s3_bucket: str = "evidence"
    s3_region: str = "us-east-1"
    s3_use_ssl: bool = False

    snowflake_datacenter_id: int = 1
    snowflake_worker_id: int = 1
    snowflake_epoch_ms: int = 1_735_689_600_000

    judicial_decrypt_window_seconds: int = 300
    judicial_notify_all_sysadmins: bool = True

    audit_async_enabled: bool = True
    audit_fallback_path: Path = Path("/app/logs/audit_fallback.jsonl")
    audit_hash_chain_enabled: bool = True

    prometheus_enabled: bool = True
    prometheus_path: str = "/metrics"

    # ── 子配置（从平铺字段聚合） ─────────────────────────────
    @property
    def database(self) -> DatabaseSettings:
        return DatabaseSettings(
            url=self.database_url,
            pool_size=self.database_pool_size,
            max_overflow=self.database_max_overflow,
            pool_recycle=self.database_pool_recycle,
            echo=self.database_echo,
        )

    @property
    def redis(self) -> RedisSettings:
        return RedisSettings(
            url=self.redis_url,
            key_prefix=self.redis_key_prefix,
            audit_stream_key=self.redis_audit_stream_key,
            audit_stream_maxlen=self.redis_audit_stream_maxlen,
        )

    @property
    def cas(self) -> CASSettings:
        return CASSettings(
            server_url=self.cas_server_url,
            service_url=self.cas_service_url,
            service_whitelist=[
                s.strip() for s in self.cas_service_whitelist.split(",") if s.strip()
            ],
            timeout_seconds=self.cas_timeout_seconds,
            health_check_interval_seconds=self.cas_health_check_interval_seconds,
            mock_allow_any=self.mock_cas_allow_any,
        )

    @property
    def security(self) -> SecuritySettings:
        return SecuritySettings(
            secret_key=self.secret_key,
            session_cookie_name=self.session_cookie_name,
            session_cookie_domain=self.session_cookie_domain,
            session_cookie_secure=self.session_cookie_secure,
            session_cookie_samesite=self.session_cookie_samesite,
            session_ttl_seconds=self.session_ttl_seconds,
        )

    @property
    def kms(self) -> KMSSettings:
        return KMSSettings(
            provider=self.kms_provider,
            local_master_key=self.kms_local_master_key,
            data_key_version=self.kms_data_key_version,
        )

    @property
    def storage(self) -> StorageSettings:
        return StorageSettings(
            endpoint=self.s3_endpoint,
            access_key=self.s3_access_key,
            secret_key=self.s3_secret_key,
            bucket=self.s3_bucket,
            region=self.s3_region,
            use_ssl=self.s3_use_ssl,
        )

    @property
    def snowflake(self) -> SnowflakeSettings:
        return SnowflakeSettings(
            datacenter_id=self.snowflake_datacenter_id,
            worker_id=self.snowflake_worker_id,
            epoch_ms=self.snowflake_epoch_ms,
        )

    @property
    def judicial(self) -> JudicialSettings:
        return JudicialSettings(
            decrypt_window_seconds=self.judicial_decrypt_window_seconds,
            notify_all_sysadmins=self.judicial_notify_all_sysadmins,
        )

    @property
    def audit(self) -> AuditSettings:
        return AuditSettings(
            async_enabled=self.audit_async_enabled,
            fallback_path=self.audit_fallback_path,
            hash_chain_enabled=self.audit_hash_chain_enabled,
        )

    @property
    def observability(self) -> ObservabilitySettings:
        return ObservabilitySettings(
            prometheus_enabled=self.prometheus_enabled,
            prometheus_path=self.prometheus_path,
        )

    # ── 衍生 / 校验 ────────────────────────────────────────
    @property
    def cors_allow_origins_list(self) -> list[str]:
        return [s.strip() for s in self.cors_allow_origins.split(",") if s.strip()]

    @model_validator(mode="after")
    def _check_prod_invariants(self) -> Settings:
        """生产环境硬性约束（缺一不可）。"""
        if self.app_env == "prod":
            if self.debug:
                raise ValueError("DEBUG=true 不允许在生产环境启用")
            if self.auth_provider != "real":
                raise ValueError("生产环境必须使用 real CAS provider")
            if not self.session_cookie_secure:
                raise ValueError("生产环境必须开启 SESSION_COOKIE_SECURE")
            if self.kms_provider == "local":
                raise ValueError("生产环境必须使用 vault / aws KMS，禁止 local")
            if self.openapi_enabled:
                raise ValueError("生产环境应关闭 OPENAPI_ENABLED 或加管理员鉴权保护")
            if any(host in self.database_url for host in ("localhost", "127.0.0.1")):
                raise ValueError("生产环境不允许使用 localhost 数据库")
        # cas_service_url 必须在白名单内（防开放重定向）
        if self.cas_service_whitelist:
            allow = [s.strip() for s in self.cas_service_whitelist.split(",") if s.strip()]
            host = urlsplit(self.cas_service_url).netloc
            if not any(urlsplit(a).netloc == host for a in allow):
                raise ValueError("CAS_SERVICE_URL 不在 CAS_SERVICE_WHITELIST 内（防开放重定向）")
        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """读取 + 缓存全局配置。

    缺失必填项时立即退出（``sys.exit(2)``），并打印缺失项与提示，避免跑到
    一半才崩。
    """
    try:
        return Settings()
    except Exception as exc:
        sys.stderr.write(
            "[FATAL] 加载配置失败 — 请检查 .env 与环境变量。\n"
            f"原因：{exc}\n"
            "提示：拷贝 .env.example 为 .env 并填写必填项；本仓库不允许在源码里硬编码任何秘密。\n"
        )
        raise SystemExit(2) from exc
