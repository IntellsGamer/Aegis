"""Structured logging configuration (JSON in production, human in dev)."""
from __future__ import annotations

import json
import logging
import sys
import time
from typing import Any


class JsonFormatter(logging.Formatter):
    """Emit each log record as a single line of JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("trace_id", "user_id", "request_id", "path", "method", "status"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class ContextFilter(logging.Filter):
    """Copy trace/request context attrs onto LogRecords."""

    def __init__(self) -> None:
        super().__init__()
        self.extra: dict[str, Any] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        for key, value in self.extra.items():
            setattr(record, key, value)
        return True


context_filter = ContextFilter()

_REQUEST_LOGGER = "aegis"


def configure_logging(environment: str = "development") -> None:
    root = logging.getLogger()
    root.handlers.clear()
    fmt = (
        "%(asctime)s %(levelname)-7s %(name)s: %(message)s"
        if environment != "production"
        else ""
    )
    handler = logging.StreamHandler(sys.stdout)
    if environment == "production":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(fmt))
    handler.addFilter(context_filter)
    root.addHandler(handler)
    root.setLevel(logging.INFO if environment != "debug" else logging.DEBUG)


def get_logger(name: str = _REQUEST_LOGGER) -> logging.Logger:
    return logging.getLogger(name)


def set_context(**kwargs: Any) -> None:
    """Attach request-scoped context (trace_id, user_id...) to log records."""
    context_filter.extra.update(kwargs)


def clear_context() -> None:
    context_filter.extra.clear()
