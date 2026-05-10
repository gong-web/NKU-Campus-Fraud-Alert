"""结构化日志（structlog）。

铁律
----
- 全平台**只允许**通过 :func:`get_logger` 拿 logger，禁用 :mod:`logging` 的直接
  调用与 ``print()``。
- 强制字段：``timestamp / level / logger / event / trace_id / user_id / source_ip``。
- 使用 KV 形式而不是字符串拼接：``logger.info("user_login", user_id=u.id)``，
  绝不 ``logger.info(f"login {u.id}")``，否则丢失结构化检索能力。

trace_id 上下文
---------------
在请求中间件里调用 :func:`bind_request_context`，把 ``trace_id``、``user_id``、
``source_ip`` 写入 ``contextvars``；后续所有日志自动带上这些字段，无需手工传。
"""

from __future__ import annotations

import logging
import sys
from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, cast

import structlog

if TYPE_CHECKING:
    from structlog.types import EventDict, Processor

# ── contextvars：跨函数自动注入 ─────────────────────────────────
_trace_id_var: ContextVar[str | None] = ContextVar("trace_id", default=None)
_user_id_var: ContextVar[int | None] = ContextVar("user_id", default=None)
_source_ip_var: ContextVar[str | None] = ContextVar("source_ip", default=None)


def bind_request_context(
    *, trace_id: str | None, user_id: int | None, source_ip: str | None
) -> None:
    """把当前请求的上下文绑定到日志 contextvars。"""
    _trace_id_var.set(trace_id)
    _user_id_var.set(user_id)
    _source_ip_var.set(source_ip)


def clear_request_context() -> None:
    """请求结束时清除上下文（防止协程串台）。"""
    _trace_id_var.set(None)
    _user_id_var.set(None)
    _source_ip_var.set(None)


def _add_request_context(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """structlog processor：自动注入 trace_id / user_id / source_ip。"""
    if (tid := _trace_id_var.get()) is not None:
        event_dict.setdefault("trace_id", tid)
    if (uid := _user_id_var.get()) is not None:
        event_dict.setdefault("user_id", uid)
    if (sip := _source_ip_var.get()) is not None:
        event_dict.setdefault("source_ip", sip)
    return event_dict


def _drop_color_message_key(_: Any, __: str, event_dict: EventDict) -> EventDict:
    """uvicorn 默认会塞 color_message，结构化日志里去掉。"""
    event_dict.pop("color_message", None)
    return event_dict


def configure_logging(*, level: str = "INFO", log_format: str = "console") -> None:
    """初始化日志体系（main.py 启动时调用一次）。"""
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        _add_request_context,
        _drop_color_message_key,
        timestamper,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.processors.format_exc_info,
            (
                structlog.processors.JSONRenderer(serializer=_orjson_dumps)
                if log_format == "json"
                else structlog.dev.ConsoleRenderer(colors=True)
            ),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(_level_to_int(level)),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # 接管 stdlib logging：让 uvicorn / sqlalchemy 的日志也走 structlog
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        structlog.stdlib.ProcessorFormatter(
            foreign_pre_chain=shared_processors,
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                (
                    structlog.processors.JSONRenderer(serializer=_orjson_dumps)
                    if log_format == "json"
                    else structlog.dev.ConsoleRenderer(colors=False)
                ),
            ],
        )
    )
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(_level_to_int(level))

    for noisy in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).handlers.clear()
        logging.getLogger(noisy).propagate = True


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """全平台唯一获取 logger 入口。"""
    return cast(structlog.stdlib.BoundLogger, structlog.get_logger(name))


def _level_to_int(level: str) -> int:
    return logging.getLevelNamesMapping().get(level.upper(), logging.INFO)


def _orjson_dumps(obj: Any, **_: Any) -> str:
    import orjson

    return orjson.dumps(obj, default=str).decode("utf-8")
