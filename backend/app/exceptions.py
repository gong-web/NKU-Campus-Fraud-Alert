"""平台异常体系。

设计原则
--------
- 每一类业务错误对应一个 ``AppException`` 子类；带固定 ``code`` 与 ``http_status``。
- 在 controller 层**不允许**抛 ``HTTPException``，统一抛本模块异常，由
  :mod:`app.api.errors` 全局处理器翻译为统一响应格式。
- 错误码字典见 ``docs/error-codes.md``，每段 1xxxx～9xxxx 分配如下：

    - 1xxxx — 通用（请求格式 / 参数 / 限流）
    - 2xxxx — 用户 / 权限域
    - 3xxxx — 事件上报域
    - 4xxxx — 预警与知识库
    - 5xxxx — 安全教育
    - 6xxxx — 审计 / 司法协助
    - 9xxxx — 外部依赖（CAS / KMS / 存储）
"""

from __future__ import annotations

from typing import Any


class AppException(Exception):
    """所有业务异常的基类。"""

    code: int = 10000
    http_status: int = 500
    default_message: str = "Internal error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: dict[str, Any] | None = None,
        code: int | None = None,
    ) -> None:
        super().__init__(message or self.default_message)
        self.message = message or self.default_message
        self.details = details or {}
        if code is not None:
            self.code = code


# ── 1xxxx · 通用 ──────────────────────────────────────────────────
class ValidationError(AppException):
    code = 10001
    http_status = 422
    default_message = "请求参数校验失败"


class NotFound(AppException):
    code = 10002
    http_status = 404
    default_message = "资源不存在"


class Conflict(AppException):
    code = 10003
    http_status = 409
    default_message = "资源冲突"


class RateLimited(AppException):
    code = 10004
    http_status = 429
    default_message = "请求过于频繁，请稍后再试"


class IdempotencyConflict(AppException):
    code = 10005
    http_status = 409
    default_message = "Idempotency-Key 已被使用且参数不一致"


# ── 2xxxx · 用户 / 权限域 ─────────────────────────────────────────
class Unauthenticated(AppException):
    """会话缺失 / 失效 / 被吊销。"""

    code = 20001
    http_status = 401
    default_message = "请先登录"


class PermissionDenied(AppException):
    """RBAC 拦截。"""

    code = 20002
    http_status = 403
    default_message = "权限不足"


class AccountDisabled(AppException):
    code = 20003
    http_status = 403
    default_message = "账号已被停用"


class SessionRevoked(AppException):
    code = 20004
    http_status = 401
    default_message = "会话已被吊销"


class CASTicketInvalid(AppException):
    code = 20005
    http_status = 401
    default_message = "CAS 票据无效或已过期"


class CASTicketReplay(AppException):
    code = 20006
    http_status = 401
    default_message = "CAS 票据已被使用（重放保护）"


class CASUnreachable(AppException):
    code = 90001
    http_status = 503
    default_message = "统一身份认证服务暂时不可用，请稍后再试"


class OpenRedirectBlocked(AppException):
    code = 20007
    http_status = 400
    default_message = "回跳地址不在白名单内"


# ── 6xxxx · 审计 / 司法协助 ─────────────────────────────────────
class AuditWriteFailed(AppException):
    code = 60001
    http_status = 500
    default_message = "写入审计日志失败"


class JudicialWindowExpired(AppException):
    code = 60002
    http_status = 410  # Gone
    default_message = "司法协助查询已过解密窗口（5 分钟），请重新申请"


class JudicialBadRequest(AppException):
    code = 60003
    http_status = 400
    default_message = "司法协助查询参数缺失（协查文书编号 / 申请理由）"


# ── 4xxxx · 预警与知识库 ─────────────────────────────────────────
# 设计：``WarningError`` / ``KnowledgeError`` 各自作为本域的基类，子类继承它
# 们以便 controller 用 ``except WarningError`` / ``except KnowledgeError`` 一
# 次性兜底捕获整族异常；具体子类再各自覆盖 ``code`` / ``http_status`` /
# ``default_message``，保持与 1xxxx 通用类（NotFound / Conflict /
# ValidationError）的语义一致。
class WarningError(AppException):
    """预警业务错误基类（4xxxx）。"""

    code = 40001
    http_status = 400
    default_message = "预警业务规则校验失败"


class WarningNotFound(WarningError):
    code = 40002
    http_status = 404
    default_message = "预警不存在"


class WarningOfflineConflict(WarningError):
    code = 40003
    http_status = 409
    default_message = "预警已下线"


class WarningInvalidParam(WarningError):
    code = 40004
    http_status = 422
    default_message = "预警参数非法"


class KnowledgeError(AppException):
    """知识库业务错误基类（4xxxx）。"""

    code = 40010
    http_status = 400
    default_message = "知识库条目业务规则校验失败"


class KnowledgeNotFound(KnowledgeError):
    code = 40011
    http_status = 404
    default_message = "知识库条目不存在"


class KnowledgeIllegalTransition(KnowledgeError):
    code = 40012
    http_status = 409
    default_message = "非法的条目状态转换"


class KnowledgeInvalidSearch(KnowledgeError):
    code = 40013
    http_status = 422
    default_message = "条目搜索参数非法"


# ── 9xxxx · 外部依赖 ──────────────────────────────────────────────
class ExternalServiceError(AppException):
    code = 90099
    http_status = 502
    default_message = "外部服务调用失败"


class KMSError(AppException):
    code = 90002
    http_status = 503
    default_message = "密钥管理服务调用失败"


class StorageError(AppException):
    code = 90003
    http_status = 503
    default_message = "对象存储服务调用失败"
