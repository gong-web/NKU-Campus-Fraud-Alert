"""安全测验 Schemas（UC-05 / UC-09）。

约定
----
- 所有 ID 字段以 ``str`` 暴露给前端（避免 JS 安全整数边界）。
- 选项字段用 ``Literal["A","B","C","D"]`` 防止非法值。
- 学生在答题中只能看到题干 + 4 个选项，不下发 ``correct_answer`` /
  ``explanation``；提交完成后才返回这两个字段（``QuestionResultOut``）。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

STRING_ID_CONFIG = ConfigDict(coerce_numbers_to_str=True)
STRING_ID_ATTR_CONFIG = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)

OptionLiteral = Literal["A", "B", "C", "D"]
QuizTypeLiteral = Literal["RANDOM", "ASSIGNED"]
QuizStatusLiteral = Literal["ACTIVE", "CANCELLED", "FINISHED"]
ScopeTypeLiteral = Literal["ALL", "DEPT", "USERS"]
DifficultyLiteral = Literal[1, 2, 3]


# ── 题库管理 ───────────────────────────────────────────────────────
class QuestionCreateIn(BaseModel):
    """新建题目入参。"""

    content: str = Field(min_length=1, max_length=500, description="题干")
    option_a: str = Field(min_length=1, max_length=512, description="选项 A")
    option_b: str = Field(min_length=1, max_length=512, description="选项 B")
    option_c: str = Field(min_length=1, max_length=512, description="选项 C")
    option_d: str = Field(min_length=1, max_length=512, description="选项 D")
    correct_answer: OptionLiteral = Field(description="正确答案 A/B/C/D")
    explanation: str | None = Field(
        default=None, max_length=2000, description="解析说明（建议结合知识库）"
    )
    fraud_type_id: int | None = Field(
        default=None, ge=1, description="关联诈骗类型（可选）"
    )
    knowledge_entry_id: int | None = Field(
        default=None, ge=1, description="答错时推送的知识库条目 ID（可选）"
    )
    difficulty: DifficultyLiteral = Field(
        default=1, description="难度 1=简单 / 2=中等 / 3=困难"
    )

    @field_validator("fraud_type_id", "knowledge_entry_id", mode="before")
    @classmethod
    def coerce_str_to_int(cls, v: object) -> object:
        if isinstance(v, str) and v.strip():
            return int(v)
        return v


class QuestionUpdateIn(BaseModel):
    """编辑题目入参（PATCH，全部字段可选）。"""

    content: str | None = Field(default=None, min_length=1, max_length=500)
    option_a: str | None = Field(default=None, min_length=1, max_length=512)
    option_b: str | None = Field(default=None, min_length=1, max_length=512)
    option_c: str | None = Field(default=None, min_length=1, max_length=512)
    option_d: str | None = Field(default=None, min_length=1, max_length=512)
    correct_answer: OptionLiteral | None = Field(default=None)
    explanation: str | None = Field(default=None, max_length=2000)
    fraud_type_id: int | None = Field(default=None, ge=1)
    knowledge_entry_id: int | None = Field(default=None, ge=1)
    difficulty: DifficultyLiteral | None = Field(default=None)
    is_active: bool | None = Field(
        default=None, description="是否启用（用于软删除）"
    )

    @field_validator("fraud_type_id", "knowledge_entry_id", mode="before")
    @classmethod
    def coerce_str_to_int(cls, v: object) -> object:
        if isinstance(v, str) and v.strip():
            return int(v)
        return v


class QuestionAdminOut(BaseModel):
    """管理员视角的题目详情（包含正确答案）。"""

    model_config = STRING_ID_ATTR_CONFIG

    question_id: str
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    explanation: str | None = None
    fraud_type_id: int | None = None
    knowledge_entry_id: str | None = None
    difficulty: int
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime


class QuestionStudentOut(BaseModel):
    """学生视角的题目（不含 ``correct_answer`` / ``explanation``）。"""

    model_config = STRING_ID_CONFIG

    question_id: str
    sort_order: int
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str


# ── 测验：发起与查看 ───────────────────────────────────────────────
class AssignedQuizCreateIn(BaseModel):
    """管理员发起指定测验（UC-09）。"""

    title: str = Field(min_length=1, max_length=128, description="测验标题")
    question_ids: list[int] = Field(
        min_length=1, max_length=100, description="题目 ID 列表（已选定，按顺序）"
    )
    pass_score: int = Field(
        default=60, ge=0, le=100, description="及格分（满分 100）"
    )
    deadline_at: datetime = Field(description="截止时间，必须在未来")
    scope_type: ScopeTypeLiteral = Field(
        description="参与范围 ALL=全校 / DEPT=按院系 / USERS=按学生"
    )
    dept_ids: list[int] | None = Field(
        default=None, description="院系 ID 列表（scope_type=DEPT 时必填）"
    )
    user_ids: list[int] | None = Field(
        default=None, description="学生 user_id 列表（scope_type=USERS 时必填）"
    )

    @field_validator("question_ids", mode="before")
    @classmethod
    def coerce_question_ids(cls, v: object) -> object:
        if isinstance(v, list):
            out: list[int] = []
            for x in v:
                if isinstance(x, str):
                    s = x.strip()
                    if not s:
                        continue
                    out.append(int(s))
                else:
                    out.append(int(x))
            return out
        return v

    @model_validator(mode="after")
    def _check_scope(self) -> AssignedQuizCreateIn:
        if self.scope_type == "DEPT":
            if not self.dept_ids:
                raise ValueError("scope_type=DEPT 时 dept_ids 必须非空")
        elif self.scope_type == "USERS" and not self.user_ids:
            raise ValueError("scope_type=USERS 时 user_ids 必须非空")
        return self


class QuizCancelIn(BaseModel):
    """管理员撤回测验入参。"""

    reason: str = Field(min_length=1, max_length=255, description="撤回原因（用于审计）")


class QuizListItemOut(BaseModel):
    """测验列表项（学生 / 管理员通用精简视图）。"""

    model_config = STRING_ID_ATTR_CONFIG

    quiz_id: str
    quiz_type: str
    title: str
    question_count: int
    pass_score: int
    status: str
    deadline_at: datetime | None = None
    created_at: datetime
    publish_level: int = Field(description="发布级别 1=院级/学院 2=校级")
    # 学生维度附加：本人在此测验上的答题状态
    my_attempt_status: str | None = Field(
        default=None, description="本人状态 IN_PROGRESS / SUBMITTED / null=未开始"
    )
    my_score: int | None = Field(default=None, description="本人得分（已提交时有值）")


class QuizDetailOut(BaseModel):
    """测验详情。"""

    model_config = STRING_ID_ATTR_CONFIG

    quiz_id: str
    quiz_type: str
    title: str
    question_count: int
    pass_score: int
    status: str
    created_by: str
    publish_level: int = Field(description="发布级别 1=院级/学院 2=校级")
    deadline_at: datetime | None = None
    target_scope: dict[str, Any] | None = None
    created_at: datetime


# ── 答题流程 ───────────────────────────────────────────────────────
class StartQuizOut(BaseModel):
    """开测响应（学生：随机练习 / 指定测验通用）。"""

    model_config = STRING_ID_CONFIG

    quiz_id: str
    attempt_id: str
    title: str
    pass_score: int
    question_count: int
    questions: list[QuestionStudentOut]


class SubmitAnswerItem(BaseModel):
    """单题作答。"""

    question_id: int = Field(ge=1)
    chosen_answer: OptionLiteral | None = Field(
        default=None, description="未作答传 null"
    )

    @field_validator("question_id", mode="before")
    @classmethod
    def coerce_question_id(cls, v: object) -> object:
        if isinstance(v, str) and v.strip():
            return int(v)
        return v


class SubmitQuizIn(BaseModel):
    """提交整张试卷。"""

    answers: list[SubmitAnswerItem] = Field(
        min_length=1, description="按题目顺序提交"
    )


class QuestionResultOut(BaseModel):
    """单题答题结果（含正确答案 + 解析 + 关联知识库）。"""

    model_config = STRING_ID_CONFIG

    question_id: str
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    chosen_answer: str | None = None
    is_correct: bool
    explanation: str | None = None
    knowledge_entry_id: str | None = Field(
        default=None, description="答错时推送的知识库条目 ID（前端跳转）"
    )


class SubmitQuizOut(BaseModel):
    """提交结果响应。"""

    model_config = STRING_ID_CONFIG

    quiz_id: str
    attempt_id: str
    score: int
    pass_score: int
    is_pass: bool
    correct_count: int
    total_count: int
    submitted_at: datetime
    results: list[QuestionResultOut]


class WrongQuestionOut(BaseModel):
    """错题汇总项（用于错题本）。"""

    model_config = STRING_ID_CONFIG

    question_id: str
    quiz_id: str
    attempt_id: str
    content: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str
    correct_answer: str
    chosen_answer: str | None
    explanation: str | None
    knowledge_entry_id: str | None
    wrong_at: datetime


class QuizHistoryItemOut(BaseModel):
    """学生个人中心：测验历史记录项。

    覆盖随机练习 + 指定测验的全部已提交答卷，按提交时间倒序。
    """

    model_config = STRING_ID_CONFIG

    attempt_id: str
    quiz_id: str
    quiz_type: str
    quiz_title: str
    pass_score: int
    score: int
    correct_count: int
    total_count: int
    is_pass: bool
    started_at: datetime
    submitted_at: datetime


# ── 报告 ────────────────────────────────────────────────────────────
class DepartmentCompletionItem(BaseModel):
    """院系完成率统计项。"""

    dept_id: int
    dept_name: str
    total_targets: int = Field(description="目标参与学生数")
    submitted_count: int = Field(description="已提交学生数")
    completion_rate: float = Field(description="完成率 0.0~1.0")
    pass_count: int = Field(description="及格学生数")
    pass_rate: float = Field(description="及格率 0.0~1.0（占已提交的比例）")
    avg_score: float = Field(description="平均分（已提交学生）")


class QuizCompletionReportOut(BaseModel):
    """指定测验完成率报告（管理员视角）。"""

    model_config = STRING_ID_CONFIG

    quiz_id: str
    title: str
    status: str
    deadline_at: datetime | None
    total_targets: int = Field(description="目标学生总数")
    submitted_count: int = Field(description="已提交学生数")
    completion_rate: float
    pass_rate: float
    avg_score: float
    by_department: list[DepartmentCompletionItem]
