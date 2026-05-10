"""ORM 模型集合。

按 PRD 5.3 数据字典分包。本地基提交聚焦于：

- 用户与权限域：``User`` / ``Department`` / ``Role`` / ``Permission`` / ``RolePermission``
- 系统支撑域：``Notification`` / ``AuditLog`` / ``Session`` / ``SystemConfig``
- 司法协助：``AnonymousMapping`` / ``AnonymousDecryptLog``

业务域表（``FraudReport`` / ``WarningNotice`` / ``KnowledgeEntry`` / ``Quiz``
等）由各 UC 负责人在自己的 PR 中按字典补齐。

所有模型在本文件中显式 import，使 Alembic 自动迁移与 SQLAlchemy 元数据扫
描都能找到。
"""

from app.infra.db.models.anonymous_decrypt_log import AnonymousDecryptLog

# 司法协助
from app.infra.db.models.anonymous_mapping import AnonymousMapping
from app.infra.db.models.audit_log import AuditLog
from app.infra.db.models.department import Department
from app.infra.db.models.notification import Notification
from app.infra.db.models.permission import Permission
from app.infra.db.models.role import Role
from app.infra.db.models.role_permission import RolePermission
from app.infra.db.models.session import SessionRecord
from app.infra.db.models.system_config import SystemConfig
from app.infra.db.models.user import User

__all__ = [
    "AnonymousDecryptLog",
    "AnonymousMapping",
    "AuditLog",
    "Department",
    "Notification",
    "Permission",
    "Role",
    "RolePermission",
    "SessionRecord",
    "SystemConfig",
    "User",
]
