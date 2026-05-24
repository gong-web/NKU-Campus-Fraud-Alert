"""ORM 模型集合。

按 PRD 5.3 数据字典分包。本地基提交聚焦于：

- 用户与权限域：``User`` / ``Department`` / ``Role`` / ``Permission`` / ``RolePermission``
- 系统支撑域：``Notification`` / ``AuditLog`` / ``Session`` / ``SystemConfig``
- 司法协助：``AnonymousMapping`` / ``AnonymousDecryptLog``
- 上报业务域（UC-01/02/06）：``FraudType`` / ``FraudCase`` / ``EvidenceFile``
  / ``CaseStatusHistory`` / ``CaseAnonymousReporter`` / ``ReportDraft``
- 审核与告警（UC-06）：``KnowledgeDraft`` / ``AggregateAlertLog``
- 预警公告（UC-03/UC-07）：``WarningNotice`` / ``WarningTarget``
- 知识库（UC-04/UC-08）：``KnowledgeEntry`` / ``KnowledgeEntryHistory``

所有模型在本文件中显式 import，使 Alembic 自动迁移与 SQLAlchemy 元数据扫
描都能找到。
"""

from app.infra.db.models.aggregate_alert_log import AggregateAlertLog
from app.infra.db.models.anonymous_decrypt_log import AnonymousDecryptLog

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

# UC-04/08：知识库
from app.infra.db.models.knowledge_entry import KnowledgeEntry
from app.infra.db.models.knowledge_entry_history import KnowledgeEntryHistory
from app.infra.db.models.notification import Notification
from app.infra.db.models.permission import Permission
from app.infra.db.models.question_bank import QuestionBank
from app.infra.db.models.quiz import Quiz
from app.infra.db.models.quiz_attempt import QuizAttempt
from app.infra.db.models.quiz_attempt_answer import QuizAttemptAnswer
from app.infra.db.models.quiz_question import QuizQuestion
from app.infra.db.models.report_draft import ReportDraft
from app.infra.db.models.role import Role
from app.infra.db.models.role_permission import RolePermission
from app.infra.db.models.session import SessionRecord
from app.infra.db.models.system_config import SystemConfig
from app.infra.db.models.user import User

# UC-03/07：预警公告
from app.infra.db.models.warning_notice import WarningNotice
from app.infra.db.models.warning_target import WarningTarget

__all__ = [
    "AggregateAlertLog",
    "AnonymousDecryptLog",
    "AnonymousMapping",
    "AuditLog",
    "CaseAnonymousReporter",
    "CaseStatusHistory",
    "Department",
    "EvidenceFile",
    "FraudCase",
    "FraudType",
    "KnowledgeDraft",
    "KnowledgeEntry",
    "KnowledgeEntryHistory",
    "Notification",
    "Permission",
    "QuestionBank",
    "Quiz",
    "QuizAttempt",
    "QuizAttemptAnswer",
    "QuizQuestion",
    "ReportDraft",
    "Role",
    "RolePermission",
    "SessionRecord",
    "SystemConfig",
    "User",
    "WarningNotice",
    "WarningTarget",
]
