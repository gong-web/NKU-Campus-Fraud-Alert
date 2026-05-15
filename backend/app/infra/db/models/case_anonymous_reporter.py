"""案件匿名上报者映射表（UC-01 / UC-10 司法协助）。

当学生选择匿名上报时：
  - fraud_cases.reporter_id 置 NULL
  - 真实 reporter user_id（AES-256-GCM 加密的字符串）存入此表
  - 仅持有 judicial:request_decrypt 权限的系统管理员可通过司法协助接口解密
  - 每次解密均记录原因并通知所有系统管理员

此表每案至多一条（case_id UNIQUE），原始加密字节直接存 VARBINARY，
不使用 EncryptedBinary（自动解密），确保 ORM 查询不会无意泄露。
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, LargeBinary, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base


class CaseAnonymousReporter(Base):
    """案件匿名上报者映射（每案至多一条）。"""

    __tablename__ = "case_anonymous_reporters"
    __table_args__ = {"comment": "案件匿名上报者映射表 PRD UC-01/UC-10"}

    mapping_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, comment="雪花算法生成")
    case_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fraud_cases.case_id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    reporter_user_id_enc: Mapped[bytes] = mapped_column(
        LargeBinary(128),
        nullable=False,
        comment="AES-256-GCM 加密的上报人 user_id（十进制字符串转 bytes）",
    )
    encryption_key_version: Mapped[str] = mapped_column(
        String(8), nullable=False, default="v1", comment="KMS 密钥版本"
    )
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.current_timestamp()
    )

    def __repr__(self) -> str:
        return f"<CaseAnonymousReporter case={self.case_id}>"
