"""Structured JSON logging configuration."""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from typing import Any

# Context variables for request correlation
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def __init__(
        self,
        indent: int | None = None,
        ensure_ascii: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize JSON formatter.

        Args:
            indent: Indentation for JSON output
            ensure_ascii: Whether to escape unicode
            **kwargs: Additional fields to include in all logs
        """
        super().__init__()
        self.indent = indent
        self.ensure_ascii = ensure_ascii
        self.extra_fields = kwargs

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        # Build base log entry
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add request/correlation ID if available
        request_id = request_id_var.get()
        if request_id:
            log_entry["request_id"] = request_id

        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_entry["correlation_id"] = correlation_id

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        if record.stack_info:
            log_entry["stack"] = self.formatStack(record.stack_info)

        # Add extra fields from kwargs
        log_entry.update(self.extra_fields)

        # Add any extra attributes from the record
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "levelname", "levelno", "pathname",
                "filename", "msecs", "lineno", "asctime", "created",
                "relativeCreated", "thread", "threadName", "process_name",
                "process", "getMessage", "exc_info", "stack_info",
            ):
                log_entry[key] = value

        return json.dumps(
            log_entry,
            indent=self.indent,
            ensure_ascii=self.ensure_ascii,
            default=str,
        )


class RequestIdFilter(logging.Filter):
    """Filter to add request ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add request ID to record if available."""
        request_id = request_id_var.get()
        if request_id:
            record.request_id = request_id
        return True


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to record if available."""
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def setup_logging(
    level: str = "INFO",
    format: str = "json",
    **kwargs: Any,
) -> None:
    """Configure application-wide logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format (json or plain)
        **kwargs: Additional fields to include in all logs
    """
    # Create formatter
    if format == "json":
        formatter = JSONFormatter(**kwargs)
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RequestIdFilter())
    console_handler.addFilter(CorrelationIdFilter())

    root_logger.addHandler(console_handler)

    # Set default request ID for any logs during startup
    request_id_var.set(str(uuid.uuid4()))


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_request_id(request_id: str | None = None) -> str:
    """Set the current request ID.

    Args:
        request_id: Optional request ID (generated if not provided)

    Returns:
        The request ID
    """
    if request_id is None:
        request_id = str(uuid.uuid4())

    request_id_var.set(request_id)
    return request_id


def get_request_id() -> str | None:
    """Get the current request ID.

    Returns:
        Current request ID or None
    """
    return request_id_var.get()


def set_correlation_id(correlation_id: str | None = None) -> str:
    """Set the current correlation ID.

    Args:
        correlation_id: Optional correlation ID (generated if not provided)

    Returns:
        The correlation ID
    """
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())

    correlation_id_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> str | None:
    """Get the current correlation ID.

    Returns:
        Current correlation ID or None
    """
    return correlation_id_var.get()


# Create default application logger
logger = get_logger("vansure")