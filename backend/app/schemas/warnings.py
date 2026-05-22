"""预警公告 Schemas（UC-03 / UC-07）。

字段约束尽量用 ``Field(...)`` 表达；跨字段校验（如 ``DEPARTMENT`` 必须
``target_dept_ids`` 非空）使用 ``model_validator``。所有 ID 字段统一以
``str`` 暴露给前端，避免 JS 安全整数边界问题。
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

STRING_ID_CONFIG = ConfigDict(coerce_numbers_to_str=True)
STRING_ID_ATTR_CONFIG = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)


WarningLevelLiteral = Literal[1, 2, 3]
WarningPushScopeLiteral = Literal["FULL_SCHOOL", "DEPARTMENT"]
WarningStatusLiteral = Literal["ONLINE", "OFFLINE"]


# ── 入参 ────────────────────────────────────────────────────────────
class WarningCreateIn(BaseModel):
    """发布预警入参（UC-03 步骤 4-6）。"""

    title: str = Field(min_length=2, max_length=128, description="预警标题")
    content: str = Field(
        min_length=10, max_length=5000, description="预警正文（建议 ≥ 200 字）"
    )
    warning_level: WarningLevelLiteral = Field(
        description="预警等级 1=提示 / 2=警告 / 3=紧急"
    )
    push_scope: WarningPushScopeLiteral = Field(
        description="推送范围 FULL_SCHOOL=全校 / DEPARTMENT=按院系",
    )
    target_dept_ids: list[int] | None = Field(
        default=None,
        description="目标院系 ID 列表；scope=DEPARTMENT 时必填、非空",
    )
    related_case_no: str | None = Field(
        default=None,
        max_length=32,
        description="关联案件编号（可选）",
    )
    expires_at: datetime | None = Field(
        default=None, description="过期时间，留空表示长期有效"
    )

    @model_validator(mode="after")
    def _check_dept_targets(self) -> WarningCreateIn:
        if self.push_scope == "DEPARTMENT":
            if not self.target_dept_ids:
                raise ValueError("push_scope=DEPARTMENT 时 target_dept_ids 必须非空")
            if any(d <= 0 for d in self.target_dept_ids):
                raise ValueError("target_dept_ids 元素必须 ≥ 1")
        return self


class WarningAppendIn(BaseModel):
    """追加后续说明入参（UC-07 步骤 8）。"""

    appendix: str = Field(
        min_length=5, max_length=2000, description="追加说明正文（≥5 字）"
    )


class WarningOfflineIn(BaseModel):
    """手动下线预警入参（UC-07 步骤 6）。"""

    reason: str = Field(
        min_length=2, max_length=200, description="下线原因（用于审计）"
    )


class WarningListQuery(BaseModel):
    """预警列表查询参数。"""

    status: WarningStatusLiteral | None = Field(
        default=None, description="状态筛选 ONLINE / OFFLINE，留空表示全部"
    )
    warning_level: WarningLevelLiteral | None = Field(
        default=None, description="等级筛选 1/2/3"
    )
    keyword: str | None = Field(
        default=None, max_length=128, description="标题 / 正文模糊搜索关键字"
    )
    page: int = Field(default=1, ge=1, description="页码（从 1 开始）")
    size: int = Field(default=20, ge=1, le=100, description="每页条数（1-100）")


# ── 出参 ────────────────────────────────────────────────────────────
class WarningListItemOut(BaseModel):
    """预警列表项（学生 / 审核管理员通用精简视图）。"""

    model_config = STRING_ID_ATTR_CONFIG

    warning_id: str = Field(description="预警 ID（雪花，字符串）")
    title: str = Field(description="预警标题")
    warning_level: int = Field(description="预警等级 1/2/3")
    status: str = Field(description="状态 ONLINE / OFFLINE")
    push_scope: str = Field(description="推送范围 FULL_SCHOOL / DEPARTMENT")
    publisher_name: str | None = Field(
        default=None, description="发布人姓名（可空，便于展示）"
    )
    published_at: datetime = Field(description="发布时间")


class WarningOut(BaseModel):
    """预警详情（学生端 / 审核端通用）。"""

    model_config = STRING_ID_ATTR_CONFIG

    warning_id: str = Field(description="预警 ID（雪花，字符串）")
    title: str = Field(description="预警标题")
    content: str = Field(description="预警正文")
    warning_level: int = Field(description="预警等级 1=提示 / 2=警告 / 3=紧急")
    push_scope: str = Field(description="推送范围 FULL_SCHOOL / DEPARTMENT")
    publisher_id: str = Field(description="发布人 user_id（雪花，字符串）")
    publisher_name: str | None = Field(
        default=None, description="发布人姓名（可空）"
    )
    target_dept_ids: list[int] = Field(
        default_factory=list,
        description="目标院系 ID 列表；FULL_SCHOOL 时为空数组",
    )
    status: str = Field(description="状态 ONLINE / OFFLINE")
    appendix: str | None = Field(
        default=None, description="追加后续说明，未追加则为 null"
    )
    related_case_no: str | None = Field(
        default=None, description="关联案件编号（可选）"
    )
    published_at: datetime = Field(description="发布时间")
    expires_at: datetime | None = Field(
        default=None, description="过期时间（可选）"
    )
    offline_at: datetime | None = Field(
        default=None, description="下线时间（仅 OFFLINE 状态有值）"
    )
    offline_reason: str | None = Field(
        default=None, description="下线原因（仅 OFFLINE 状态有值）"
    )
