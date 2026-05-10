"""仓储模式（Repository Pattern）。

业务服务（``app.services``）只通过仓储接口访问数据；不直接操作 SQLAlchemy
``Session``。这一层让我们可以在测试里用 fake / 内存实现而不动业务代码。

骨架提交聚焦于：
- :class:`UserRepository`        — 用户读写
- :class:`RoleRepository`        — 角色 / 角色权限
- :class:`PermissionRepository`  — 权限码字典
- :class:`AuditRepository`       — 审计日志（只允许 INSERT / SELECT）
- :class:`AnonymousMappingRepository` — 匿名映射（独立 DB 账号访问）
"""

from app.infra.repositories.anonymous import AnonymousMappingRepository
from app.infra.repositories.audit import AuditRepository
from app.infra.repositories.permission import PermissionRepository
from app.infra.repositories.role import RoleRepository
from app.infra.repositories.user import UserRepository

__all__ = [
    "AnonymousMappingRepository",
    "AuditRepository",
    "PermissionRepository",
    "RoleRepository",
    "UserRepository",
]
