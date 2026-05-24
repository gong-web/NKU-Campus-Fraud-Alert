"""测验主表（PRD UC-05 / UC-09）。

两种模式（``quiz_type``）：

- ``RANDOM``：学生主动发起的随机练习，题目从题库随机抽取 ``question_count`` 题。
- ``ASSIGNED``：管理员发起的指定测验，预绑定题目集合 + 参与范围 + 截止时间。

参与范围（存于 ``target_scope`` JSON）::

    {"type": "ALL"}                       # 全校
    {"type": "DEPT",  "dept_ids": [1,2]}   # 按院系
    {"type": "USERS", "user_ids": [...]}   # 按学生

状态（``status``）::

    ACTIVE     已发布、进行中（RANDOM 创建即 ACTIVE）
    CANCELLED  管理员手动撤回（ASSIGNED）
    FINISHED   截止时间到期自动结束（ASSIGNED）
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    ForeignKey,
    Index,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class QuizType:
    """测验模式。"""

    RANDOM = "RANDOM"
    ASSIGNED = "ASSIGNED"

    ALL: frozenset[str] = frozenset({RANDOM, ASSIGNED})


class QuizScopeType:
    """指定测验的参与范围（仅 ASSIGNED 模式有意义）。"""

    ALL = "ALL"
    DEPT = "DEPT"
    USERS = "USERS"

    ALL_VALUES: frozenset[str] = frozenset({ALL, DEPT, USERS})


class QuizStatus:
    """测验状态。"""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
    FINISHED = "FINISHED"

    ALL: frozenset[str] = frozenset({ACTIVE, CANCELLED, FINISHED})


class Quiz(Base, TimestampMixin):
    """测验主表。"""

    __tablename__ = "quizzes"
    __table_args__ = (
        Index("idx_quizzes_type_status", "quiz_type", "status"),
        Index("idx_quizzes_deadline", "deadline_at"),
        Index("idx_quizzes_created_by", "created_by"),
        Index("idx_quizzes_publish_level", "publish_level"),
        {"comment": "测验表 PRD UC-05/UC-09"},
    )

    quiz_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    quiz_type: Mapped[str] = mapped_column(
        String(16), nullable=False, comment="RANDOM=随机练习 / ASSIGNED=指定测验"
    )
    title: Mapped[str] = mapped_column(String(128), nullable=False, comment="测验标题")
    question_count: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=10,
        server_default="10",
        comment="题目数量，默认 10",
    )
    pass_score: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=60,
        server_default="60",
        comment="及格分（满分 100）",
    )
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=QuizStatus.ACTIVE,
        server_default=QuizStatus.ACTIVE,
        comment="ACTIVE / CANCELLED / FINISHED",
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="发起人 user_id（RANDOM 即学生本人）",
    )
    deadline_at: Mapped[datetime | None] = mapped_column(
        nullable=True, comment="截止时间（仅 ASSIGNED）"
    )
    target_scope: Mapped[dict[str, Any] | None] = mapped_column(
        JSON, nullable=True, comment="目标范围 JSON（仅 ASSIGNED）"
    )
    publish_level: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=2,
        server_default="2",
        comment="发布级别 1=院级/学院 2=校级",
    )
    reminder_sent: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0",
        comment="是否已发提醒 0/1"
    )

    def __repr__(self) -> str:
        return f"<Quiz {self.quiz_id} {self.quiz_type} [{self.status}]>"
