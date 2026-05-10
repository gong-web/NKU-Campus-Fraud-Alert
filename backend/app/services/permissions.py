"""平台全部权限码常量。

约定（``docs/conventions.md``）
------------------------------
- 格式：``<resource>:<action>``
- ``resource``：单数名词（``user``、``report``、``warning``、``kb``、``quiz``、
  ``audit``、``judicial``）。
- ``action``：动词（``create``、``read``、``update``、``delete``、``review``、
  ``publish``、``offline``、``export``）。

新模块加权限码时**必须**先在本文件登记 + 同步到 ``docs/permissions.md``，
再加到 ``Permission`` 表 + ``RolePermission`` 矩阵——这是地基组的硬规矩。
"""

from __future__ import annotations

from typing import Final

# ── 用户域 (UC-10) ─────────────────────────────────────────────────
USER_CREATE: Final[str] = "user:create"
USER_READ: Final[str] = "user:read"
USER_UPDATE: Final[str] = "user:update"
USER_DISABLE: Final[str] = "user:disable"
USER_BATCH_IMPORT: Final[str] = "user:batch_import"

# ── 审计 (UC-10 备选 A1) ───────────────────────────────────────────
AUDIT_READ: Final[str] = "audit:read"
AUDIT_EXPORT: Final[str] = "audit:export"

# ── 司法协助 (UC-10 备选 A2) ───────────────────────────────────────
JUDICIAL_REQUEST_DECRYPT: Final[str] = "judicial:request_decrypt"

# ── 系统配置 ───────────────────────────────────────────────────────
SYSTEM_CONFIG_READ: Final[str] = "system_config:read"
SYSTEM_CONFIG_UPDATE: Final[str] = "system_config:update"

# ── 上报 (UC-01 / UC-02 / UC-06) ───────────────────────────────────
REPORT_CREATE: Final[str] = "report:create"
REPORT_READ_OWN: Final[str] = "report:read_own"
REPORT_READ_ALL: Final[str] = "report:read_all"
REPORT_REVIEW: Final[str] = "report:review"
REPORT_VIEW_EVIDENCE: Final[str] = "report:view_evidence"

# ── 预警 (UC-03 / UC-07) ───────────────────────────────────────────
WARNING_READ: Final[str] = "warning:read"
WARNING_PUBLISH: Final[str] = "warning:publish"
WARNING_APPEND: Final[str] = "warning:append"
WARNING_OFFLINE: Final[str] = "warning:offline"

# ── 知识库 (UC-04 / UC-08) ─────────────────────────────────────────
KB_READ: Final[str] = "kb:read"
KB_CREATE: Final[str] = "kb:create"
KB_REVIEW: Final[str] = "kb:review"
KB_OFFLINE: Final[str] = "kb:offline"

# ── 测验 (UC-05 / UC-09) ───────────────────────────────────────────
QUIZ_TAKE: Final[str] = "quiz:take"
QUIZ_BANK_MANAGE: Final[str] = "quiz:bank_manage"
QUIZ_ASSIGN: Final[str] = "quiz:assign"


# ── 默认角色 → 权限矩阵（seed 时灌入） ─────────────────────────
ROLE_PERMISSIONS_DEFAULT: Final[dict[str, set[str]]] = {
    "STUDENT": {
        REPORT_CREATE,
        REPORT_READ_OWN,
        WARNING_READ,
        KB_READ,
        QUIZ_TAKE,
    },
    "REVIEWER": {
        REPORT_READ_ALL,
        REPORT_REVIEW,
        REPORT_VIEW_EVIDENCE,
        WARNING_READ,
        WARNING_PUBLISH,
        WARNING_APPEND,
        WARNING_OFFLINE,
        KB_READ,
        KB_CREATE,
        KB_REVIEW,
        KB_OFFLINE,
        QUIZ_BANK_MANAGE,
        QUIZ_ASSIGN,
    },
    "SYS_ADMIN": {
        USER_CREATE,
        USER_READ,
        USER_UPDATE,
        USER_DISABLE,
        USER_BATCH_IMPORT,
        AUDIT_READ,
        AUDIT_EXPORT,
        JUDICIAL_REQUEST_DECRYPT,
        SYSTEM_CONFIG_READ,
        SYSTEM_CONFIG_UPDATE,
    },
}


def all_permission_codes() -> set[str]:
    """所有已登记的权限码（用于 seed 与 lint 一致性校验）。"""
    return {
        v for k, v in globals().items() if not k.startswith("_") and isinstance(v, str) and ":" in v
    }
