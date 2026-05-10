"""Pydantic DTO 入参 / 出参定义。

约定（``docs/conventions.md``）
------------------------------
- 命名：``XxxIn`` / ``XxxOut``（``XxxCreate`` / ``XxxUpdate`` / ``XxxFilter``
  也可）
- 时间字段统一 ISO 8601 with timezone（FastAPI 默认 ``datetime`` 行为）
- 输入 DTO 通过 ``Field(min_length=...)`` 等做基础校验
- 输出 DTO 不应直接返回 ORM 对象——总是经过显式映射
"""

from app.schemas.common import (
    PageQuery,
    PaginationOut,
    StandardErrorResponse,
    StandardResponse,
)

__all__ = [
    "PageQuery",
    "PaginationOut",
    "StandardErrorResponse",
    "StandardResponse",
]
