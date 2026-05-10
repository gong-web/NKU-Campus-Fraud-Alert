"""院系表（PRD 5.3.1 表 5.6）。"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base

# MySQL 用 BIGINT；SQLite 自增主键必须 INTEGER（仅测试 in-memory 用）
_DeptIdType = BigInteger().with_variant(Integer(), "sqlite")


class Department(Base):
    """院系（组织架构最小单元，承载推送范围）。"""

    __tablename__ = "departments"
    __table_args__ = {"comment": "院系表 - PRD 5.3.1 表 5.6"}

    dept_id: Mapped[int] = mapped_column(
        _DeptIdType, primary_key=True, autoincrement=True, comment="院系唯一标识"
    )
    dept_code: Mapped[str] = mapped_column(
        String(16), unique=True, nullable=False, comment="院系编码，用于案件编号生成"
    )
    dept_name: Mapped[str] = mapped_column(String(64), nullable=False, comment="院系中文全称")
    parent_dept_id: Mapped[int | None] = mapped_column(
        _DeptIdType,
        ForeignKey("departments.dept_id", ondelete="RESTRICT"),
        nullable=True,
        comment="上级院系（支持多层级组织）",
    )
    dept_level: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, server_default="1", comment="1=学院 / 2=专业"
    )
    sort_order: Mapped[int] = mapped_column(
        nullable=False, default=0, server_default="0", comment="显示排序权重"
    )

    def __repr__(self) -> str:
        return f"<Department {self.dept_code} ({self.dept_id})>"
