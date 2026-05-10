"""应用中间件：trace_id、CSRF 防护、安全 Header。"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.ids import new_trace_id
from app.core.logging import bind_request_context, clear_request_context, get_logger

logger = get_logger(__name__)


class TraceIdMiddleware(BaseHTTPMiddleware):
    """在每个请求生成 trace_id，写入 ``request.state`` 与响应头。"""

    HEADER_NAME = "X-Trace-Id"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        trace_id = request.headers.get(self.HEADER_NAME) or new_trace_id()
        request.state.trace_id = trace_id

        # 提前绑定 trace_id 到日志（user_id / source_ip 待 deps.get_current_user 填）
        bind_request_context(
            trace_id=trace_id,
            user_id=None,
            source_ip=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)
        finally:
            clear_request_context()
        response.headers[self.HEADER_NAME] = trace_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """添加常见安全 Header（CSP / X-Frame-Options / Referrer-Policy 等）。"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        resp = await call_next(request)
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        resp.headers.setdefault("Permissions-Policy", "interest-cohort=()")
        # API 一般不需要 inline JS；CSP 主要意义在前端容器
        resp.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'none'; frame-ancestors 'none'",
        )
        return resp


class CSRFRequiredHeaderMiddleware(BaseHTTPMiddleware):
    """所有写接口要求 ``X-Requested-With: XMLHttpRequest``（与 SameSite=Lax 双保险）。"""

    SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS"})
    HEADER_NAME = "x-requested-with"
    EXPECTED_VALUE = "XMLHttpRequest"

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method.upper() in self.SAFE_METHODS:
            return await call_next(request)
        # 登录回调（CAS 重定向是 GET，已经被 SAFE_METHODS 跳过）
        # API 路径要求带 header；非 /api/ 前缀（如健康检查）放过
        if not request.url.path.startswith("/api/"):
            return await call_next(request)
        if request.headers.get(self.HEADER_NAME, "") != self.EXPECTED_VALUE:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=400,
                content={
                    "code": 10010,
                    "message": "CSRF: 缺少 X-Requested-With 头",
                    "data": None,
                    "trace_id": getattr(request.state, "trace_id", None),
                },
            )
        return await call_next(request)
