"""共享 schemas：分页、通用响应。"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PageQuery(BaseModel):
    """分页查询通用参数。"""

    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PaginationOut(BaseModel, Generic[T]):
    """分页响应（PRD 4.4 接口规范）。"""

    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    size: int = Field(ge=1)


class StandardResponse(BaseModel, Generic[T]):
    """统一成功响应。"""

    code: int = 0
    message: str = "ok"
    data: T | None = None
    trace_id: str | None = None


class StandardErrorResponse(BaseModel):
    """统一失败响应（OpenAPI 文档用，运行时由 errors.py 直接渲染）。"""

    code: int
    message: str
    data: Any | None = None
    trace_id: str | None = None
