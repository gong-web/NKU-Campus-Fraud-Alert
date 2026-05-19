"""ORM 模型集合。

按 PRD 5.3 数据字典分包。本地基提交聚焦于：

- 用户与权限域：``User`` / ``Department`` / ``Role`` / ``Permission`` / ``RolePermission``
- 系统支撑域：``Notification`` / ``AuditLog`` / ``Session`` / ``SystemConfig``
- 司法协助：``AnonymousMapping`` / ``AnonymousDecryptLog``
- 上报业务域（UC-01/02/06）：``FraudType`` / ``FraudCase`` / ``EvidenceFile``
  / ``CaseStatusHistory`` / ``CaseAnonymousReporter`` / ``ReportDraft``

所有模型在本文件中显式 import，使 Alembic 自动迁移与 SQLAlchemy 元数据扫
描都能找到。
"""

from app.infra.db.models.anonymous_decrypt_log import AnonymousDecryptLog
from app.infra.db.models.aggregate_alert_log import AggregateAlertLog

# 司法协助
from app.infra.db.models.anonymous_mapping import AnonymousMapping
from app.infra.db.models.audit_log import AuditLog

# UC-01/02/06：上报业务域
from app.infra.db.models.case_anonymous_reporter import CaseAnonymousReporter
from app.infra.db.models.case_status_history import CaseStatusHistory
from app.infra.db.models.department import Department
from app.infra.db.models.evidence_file import EvidenceFile
from app.infra.db.models.fraud_case import FraudCase
from app.infra.db.models.fraud_type import FraudType
from app.infra.db.models.knowledge_draft import KnowledgeDraft
from app.infra.db.models.notification import Notification
from app.infra.db.models.permission import Permission
from app.infra.db.models.report_draft import ReportDraft
from app.infra.db.models.role import Role
from app.infra.db.models.role_permission import RolePermission
from app.infra.db.models.session import SessionRecord
from app.infra.db.models.system_config import SystemConfig
from app.infra.db.models.user import User

__all__ = [
    "AnonymousDecryptLog",
    "AggregateAlertLog",
    "AnonymousMapping",
    "AuditLog",
    "CaseAnonymousReporter",
    "CaseStatusHistory",
    "Department",
    "EvidenceFile",
    "FraudCase",
    "FraudType",
    "KnowledgeDraft",
    "Notification",
    "Permission",
    "ReportDraft",
    "Role",
    "RolePermission",
    "SessionRecord",
    "SystemConfig",
    "User",
]
