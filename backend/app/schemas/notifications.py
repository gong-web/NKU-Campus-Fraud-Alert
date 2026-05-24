"""站内通知 Schemas（公共组件，全平台共用）。

字段约束尽量用 ``Field(...)`` 表达；ID 字段统一以 ``str`` 暴露给前端，
避免 JS 安全整数边界问题。后端模型字段为 BigInteger（雪花），通过
``coerce_numbers_to_str`` 自动转字符串。
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

STRING_ID_ATTR_CONFIG = ConfigDict(from_attributes=True, coerce_numbers_to_str=True)


# ── 出参 ────────────────────────────────────────────────────────────
class NotificationOut(BaseModel):
    """单条通知详情（学生 / 管理员通用）。"""

    model_config = STRING_ID_ATTR_CONFIG

    notification_id: str = Field(description="通知 ID（雪花，字符串）")
    type: str = Field(description="通知类型 REPORT_RESOLVED / WARNING_PUBLISHED / QUIZ_ASSIGNED ...")
    title: str = Field(description="通知标题")
    content: str = Field(description="通知正文（截断后摘要）")
    related_object_type: str | None = Field(
        default=None, description="关联对象类型，如 fraud_case / warning_notice / quiz"
    )
    related_object_id: str | None = Field(
        default=None, description="关联对象 ID（雪花字符串），可空"
    )
    is_read: bool = Field(description="是否已读")
    created_at: datetime = Field(description="创建时间")
    read_at: datetime | None = Field(default=None, description="已读时间，未读为 null")


class UnreadCountOut(BaseModel):
    """未读数量响应。"""

    count: int = Field(ge=0, description="当前用户的未读通知数量")


class MarkReadOut(BaseModel):
    """标记单条已读响应。"""

    success: bool = Field(description="是否实际更新了一行（重复标记返回 false）")


class MarkAllReadOut(BaseModel):
    """一键全部已读响应。"""

    marked: int = Field(ge=0, description="本次实际标记为已读的条数")
