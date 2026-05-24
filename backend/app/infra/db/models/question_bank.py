"""题库表（PRD UC-05 / UC-09 安全测验）。

题库与测验解耦：题目只在 ``question_bank`` 中维护，``quizzes`` 通过
``quiz_questions`` 关联表挑选题目；这样 "指定测验" 和 "随机练习"
可以共享题库，避免题目数据重复。

本平台暂只支持单选题（``correct_answer`` 取 ``A`` / ``B`` / ``C`` / ``D``）。
如未来扩展为多选，需要加 ``question_type`` 字段并写迁移。
"""

from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey, Index, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db.base import Base, TimestampMixin


class QuestionDifficulty:
    """题目难度常量。"""

    EASY = 1
    MEDIUM = 2
    HARD = 3

    ALL: frozenset[int] = frozenset({EASY, MEDIUM, HARD})


class QuestionBank(Base, TimestampMixin):
    """题库主表 — 全平台共用的客观题库（单选）。"""

    __tablename__ = "question_bank"
    __table_args__ = (
        Index("idx_qbank_fraud_type", "fraud_type_id"),
        Index("idx_qbank_is_active", "is_active"),
        Index("idx_qbank_difficulty", "difficulty"),
        {"comment": "题库表 PRD UC-05/UC-09"},
    )

    question_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="题干")
    option_a: Mapped[str] = mapped_column(String(512), nullable=False, comment="选项 A")
    option_b: Mapped[str] = mapped_column(String(512), nullable=False, comment="选项 B")
    option_c: Mapped[str] = mapped_column(String(512), nullable=False, comment="选项 C")
    option_d: Mapped[str] = mapped_column(String(512), nullable=False, comment="选项 D")
    correct_answer: Mapped[str] = mapped_column(
        String(1), nullable=False, comment="正确答案 A / B / C / D"
    )
    explanation: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="解析（学生答错时展示）"
    )
    fraud_type_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("fraud_types.type_id", ondelete="SET NULL"),
        nullable=True,
        comment="关联诈骗类型（可空）",
    )
    knowledge_entry_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("knowledge_entries.entry_id", ondelete="SET NULL"),
        nullable=True,
        comment="答错时推送的知识库条目（可空）",
    )
    difficulty: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=QuestionDifficulty.EASY,
        server_default=str(QuestionDifficulty.EASY),
        comment="难度 1=简单 / 2=中等 / 3=困难",
    )
    is_active: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=1,
        server_default="1",
        comment="是否启用（软删除：禁用后随机抽题与指定测验不再纳入）",
    )
    created_by: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False,
        comment="创建者 user_id",
    )

    def __repr__(self) -> str:
        return f"<QuestionBank {self.question_id} diff={self.difficulty}>"
