"""匿名映射表（PRD 5.3.2 表 5.14）。

PRD 第 (五).3 节明确：本表与主业务表使用**不同**数据库账号。
- ``app_user`` 对本表无任何权限（连 SELECT 也没有）
- ``decrypt_user`` 仅用于司法协助查询时短暂连接

授权规则在 ``infra/docker/mysql/init/02_grants.sql`` 里实现。

ORM 层依然定义模型，但运行时业务代码绝不会经过 ``app_user`` 访问到——
即使应用代码错误地尝试 SELECT，数据库也会拒绝。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import VARBINARY, BigInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class AnonymousMapping(Base):
    __tablename__ = "anonymous_mappings"
    __table_args__ = {
        "comment": "匿名映射表（独立 DB 账号访问） - PRD 5.3.2 表 5.14",
    }

    mapping_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    report_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        comment="一对一关联事件主表 FraudReport.report_id",
    )
    encrypted_reporter_id: Mapped[bytes] = mapped_column(
        VARBINARY(128), nullable=False, comment="加密后的真实上报者 user_id"
    )
    encryption_key_version: Mapped[str] = mapped_column(
        String(32), nullable=False, comment="支持密钥轮转"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )
