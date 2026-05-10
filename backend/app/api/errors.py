"""全局异常处理器（统一响应格式 + 不泄露 traceback）。

响应格式
--------
成功（service / controller 直接返回业务对象，FastAPI 自动 JSON 化）::

    { "code": 0, "message": "ok", "data": {...} }

失败（本模块统一翻译）::

    {
      "code": 20002,
      "message": "权限不足",
      "data": null,
      "trace_id": "5fa3..."
    }

PRD 第 4 章可维护性："响应体统一采用结构化文本格式"。
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.exceptions import AppException, Unauthenticated

logger = get_logger(__name__)


def _trace_id(request: Request) -> str | None:
    return getattr(request.state, "trace_id", None)


def _err_payload(
    *,
    code: int,
    message: str,
    trace_id: str | None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {
        "code": code,
        "message": message,
        "data": None,
        "trace_id": trace_id,
    }
    if details:
        body["details"] = details
    return body


def install_error_handlers(app: FastAPI) -> None:
    """挂载全局异常处理器。"""

    @app.exception_handler(AppException)
    async def _handle_app(request: Request, exc: AppException) -> JSONResponse:
        logger.info(
            "app_exception",
            code=exc.code,
            message=exc.message,
            http_status=exc.http_status,
            details=exc.details,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.http_status,
            content=_err_payload(
                code=exc.code,
                message=exc.message,
                trace_id=_trace_id(request),
                details=exc.details or None,
            ),
            headers={"X-Trace-Id": _trace_id(request) or ""} if _trace_id(request) else None,
        )

    @app.exception_handler(RequestValidationError)
    async def _handle_validation(request: Request, exc: RequestValidationError) -> JSONResponse:
        logger.info(
            "request_validation_error",
            path=request.url.path,
            errors=exc.errors()[:10],
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_err_payload(
                code=10001,
                message="请求参数校验失败",
                trace_id=_trace_id(request),
                details={"errors": exc.errors()[:10]},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # 401 / 403 走我们的 AppException 路径；这里仅捕获 framework 内部抛的（如 method_not_allowed）
        if exc.status_code == 401:
            wrapped = Unauthenticated(str(exc.detail) or "未认证")
            return await _handle_app(request, wrapped)
        return JSONResponse(
            status_code=exc.status_code,
            content=_err_payload(
                code=10000 + exc.status_code,
                message=str(exc.detail) or "HTTP error",
                trace_id=_trace_id(request),
            ),
        )

    @app.exception_handler(Exception)
    async def _handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "unhandled_exception",
            error=str(exc),
            error_type=type(exc).__name__,
            path=request.url.path,
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content=_err_payload(
                code=10000,
                message="服务器内部错误",
                trace_id=_trace_id(request),
            ),
        )
