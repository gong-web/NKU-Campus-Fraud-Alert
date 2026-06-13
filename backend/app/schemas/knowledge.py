"""知识库 Schemas（UC-04 / UC-08）。

字段约束尽量用 ``Field(...)`` 表达；跨字段校验（如审核 REJECT 必填 review_note）
使用 ``model_validator``。所有 ID 字段统一以 ``str`` 暴露给前端。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STRING_ID_CONFIG = ConfigDict(coerce_numbers_to_str=True)
STRING_ID_ATTR_CONFIG = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)


KnowledgeSourceTypeLiteral = Literal["CASE", "SCHOOL", "NATIONAL"]
KnowledgeStatusLiteral = Literal["DRAFT", "PENDING", "PUBLISHED", "OFFLINE"]
KnowledgeListStatusLiteral = Literal[
    "DRAFT", "PENDING", "PUBLISHED", "OFFLINE", "ALL"
]
KnowledgeReviewActionLiteral = Literal["APPROVE", "REJECT"]
KnowledgeListSortLiteral = Literal["published_at_desc", "hot"]


# ── 入参 ────────────────────────────────────────────────────────────
class KnowledgeCreateIn(BaseModel):
    """新建知识库条目入参（UC-04 步骤 4）。"""

    title: str = Field(min_length=1, max_length=128, description="条目标题")
    fraud_type_id: int = Field(ge=1, description="所属诈骗类型 ID")
    desensitized_summary: str = Field(
        min_length=1, max_length=1000, description="脱敏案例摘要"
    )
    identification_points: str = Field(
        min_length=1, max_length=2000, description="识别要点（建议条目化）"
    )
    prevention_advice: str = Field(
        min_length=1, max_length=2000, description="防范建议"
    )
    peak_periods: str | None = Field(
        default=None,
        max_length=255,
        description="高发时间段（自然语言文字描述，可选）",
    )
    source_type: KnowledgeSourceTypeLiteral = Field(
        default="CASE",
        description="来源类型 CASE=校内案件 / SCHOOL=校方公告 / NATIONAL=反诈中心",
    )
    source_reference: str | None = Field(
        default=None,
        max_length=255,
        description="来源引用说明（链接或文献编号，可选）",
    )


class KnowledgeUpdateIn(BaseModel):
    """编辑知识库条目入参（PATCH，全部字段可选）。"""

    title: str | None = Field(
        default=None, min_length=1, max_length=128, description="条目标题"
    )
    fraud_type_id: int | None = Field(
        default=None, ge=1, description="所属诈骗类型 ID"
    )
    desensitized_summary: str | None = Field(
        default=None, min_length=1, max_length=1000, description="脱敏案例摘要"
    )
    identification_points: str | None = Field(
        default=None, min_length=1, max_length=2000, description="识别要点"
    )
    prevention_advice: str | None = Field(
        default=None, min_length=1, max_length=2000, description="防范建议"
    )
    peak_periods: str | None = Field(
        default=None, max_length=255, description="高发时间段（可选）"
    )
    source_type: KnowledgeSourceTypeLiteral | None = Field(
        default=None,
        description="来源类型 CASE / SCHOOL / NATIONAL",
    )
    source_reference: str | None = Field(
        default=None, max_length=255, description="来源引用说明（可选）"
    )


class KnowledgeReviewIn(BaseModel):
    """校级审核入参（UC-08 步骤 4）。"""

    action: KnowledgeReviewActionLiteral = Field(
        description="审核动作 APPROVE=通过发布 / REJECT=驳回回草稿"
    )
    review_note: str | None = Field(
        default=None,
        max_length=500,
        description="审核备注；REJECT 时必填",
    )

    @model_validator(mode="after")
    def _check_reject_note(self) -> KnowledgeReviewIn:
        if self.action == "REJECT":
            note = (self.review_note or "").strip()
            if len(note) < 1:
                raise ValueError("REJECT 时必须填写 review_note")
        return self


class KnowledgeOfflineIn(BaseModel):
    """下线条目入参（UC-08 步骤 6）。"""

    reason: str = Field(
        min_length=1, max_length=500, description="下线原因（用于审计）"
    )


class KnowledgeListQuery(BaseModel):
    """知识库列表查询参数。

    - 学生端：``status`` 应固定为 ``PUBLISHED``（API 层强制）。
    - 管理端：``status`` 可传 ``ALL`` 表示不限。
    """

    keyword: str | None = Field(
        default=None, max_length=128, description="标题 / 摘要模糊搜索关键字"
    )
    fraud_type_id: int | None = Field(
        default=None, ge=1, description="诈骗类型筛选"
    )
    status: KnowledgeListStatusLiteral | None = Field(
        default=None,
        description="状态筛选；管理端可传 ALL，学生端固定 PUBLISHED",
    )
    page: int = Field(default=1, ge=1, description="页码（从 1 开始）")
    size: int = Field(default=20, ge=1, le=100, description="每页条数（1-100）")
    sort: KnowledgeListSortLiteral = Field(
        default="published_at_desc",
        description="排序方式 published_at_desc=发布时间倒序 / hot=热度（暂按浏览量）",
    )


# ── 出参 ────────────────────────────────────────────────────────────
class KnowledgeListItemOut(BaseModel):
    """知识库列表项（不含完整 ``prevention_advice``，体积更小）。"""

    model_config = STRING_ID_ATTR_CONFIG

    entry_id: str = Field(description="条目 ID（雪花，字符串）")
    title: str = Field(description="条目标题")
    fraud_type_id: int = Field(description="所属诈骗类型 ID")
    fraud_type_name: str | None = Field(
        default=None, description="诈骗类型显示名（来自 join，可空）"
    )
    desensitized_summary: str = Field(description="脱敏摘要（用于卡片展示）")
    status: str = Field(description="状态 DRAFT / PENDING / PUBLISHED / OFFLINE")
    version: int = Field(description="版本号")
    author_id: str = Field(description="作者 user_id（雪花，字符串）")
    author_name: str | None = Field(
        default=None, description="作者姓名（来自 join，可空）"
    )
    published_at: datetime | None = Field(
        default=None, description="首次发布时间，未发布为 null"
    )
    updated_at: datetime = Field(description="最近更新时间")


class KnowledgeOut(BaseModel):
    """知识库条目详情。"""

    model_config = STRING_ID_ATTR_CONFIG

    entry_id: str = Field(description="条目 ID（雪花，字符串）")
    title: str = Field(description="条目标题")
    fraud_type_id: int = Field(description="所属诈骗类型 ID")
    fraud_type_name: str | None = Field(
        default=None, description="诈骗类型显示名（来自 join，可空）"
    )
    desensitized_summary: str = Field(description="脱敏案例摘要")
    identification_points: str = Field(description="识别要点")
    prevention_advice: str = Field(description="防范建议")
    peak_periods: str | None = Field(
        default=None, description="高发时间段（可选）"
    )
    source_type: str = Field(description="来源类型 CASE / SCHOOL / NATIONAL")
    source_reference: str | None = Field(
        default=None, description="来源引用说明（可选）"
    )
    status: str = Field(description="状态 DRAFT / PENDING / PUBLISHED / OFFLINE")
    version: int = Field(description="版本号（每次状态变更后由业务层 +1）")
    author_id: str = Field(description="作者 user_id（雪花，字符串）")
    author_name: str | None = Field(
        default=None, description="作者姓名（来自 join，可空）"
    )
    reviewer_id: str | None = Field(
        default=None, description="审核人 user_id（雪花，字符串），未审核为 null"
    )
    reviewer_name: str | None = Field(
        default=None, description="审核人姓名（来自 join，可空）"
    )
    review_note: str | None = Field(
        default=None, description="审核备注 / 驳回原因，未审核为 null"
    )
    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="最近更新时间")
    published_at: datetime | None = Field(
        default=None, description="首次发布时间，未发布为 null"
    )
    offlined_at: datetime | None = Field(
        default=None, description="下线时间（仅 OFFLINE 状态有值）"
    )


class KnowledgeDetailOut(KnowledgeOut):
    """知识库条目详情（含相关条目推荐）。"""

    related: list[KnowledgeListItemOut] = Field(
        default_factory=list,
        description="同 fraud_type_id 最近 3 条已发布条目（不含本身）",
    )
