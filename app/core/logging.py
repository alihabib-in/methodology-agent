import logging
import sys
import time
import uuid
from contextvars import ContextVar

LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def configure_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        stream=sys.stdout,
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


def new_request_id() -> str:
    return uuid.uuid4().hex[:12]


def log_operation(
    logger: logging.Logger,
    operation: str,
    *,
    model: str | None = None,
    language: str | None = None,
    latency_ms: float | None = None,
    status: str = "ok",
    error: str | None = None,
) -> None:
    parts = [f"operation={operation}", f"status={status}"]
    if model:
        parts.append(f"model={model}")
    if language:
        parts.append(f"language={language}")
    if latency_ms is not None:
        parts.append(f"latency_ms={latency_ms:.1f}")
    if error:
        parts.append(f"error={error}")
    logger.info(" ".join(parts))
