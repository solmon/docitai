"""Logging configuration with tenant context support."""

import json
import logging
from contextvars import ContextVar
from datetime import datetime
from typing import Any, Optional

# Context variables for tenant and user tracking
tenant_context: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)
user_context: ContextVar[Optional[str]] = ContextVar("user_id", default=None)
request_id_context: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class TenantAwareFormatter(logging.Formatter):
    """
    Custom log formatter that includes tenant and user context.

    Produces structured JSON logs with tenant context for easier correlation
    and multi-tenant log aggregation.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with tenant context.

        Args:
            record: LogRecord to format

        Returns:
            Formatted log string (JSON)
        """
        # Capture context variables
        tenant_id = tenant_context.get()
        user_id = user_context.get()
        request_id = request_id_context.get()

        # Build log entry
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add context information if available
        if tenant_id:
            log_entry["tenant_id"] = tenant_id
        if user_id:
            log_entry["user_id"] = user_id
        if request_id:
            log_entry["request_id"] = request_id

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add custom attributes from extra
        if hasattr(record, "extra"):
            log_entry.update(record.extra)

        return json.dumps(log_entry)


def configure_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging with tenant awareness.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level))

    # Create console handler with custom formatter
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, log_level))

    formatter = TenantAwareFormatter()
    handler.setFormatter(formatter)

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.LoggerAdapter:
    """
    Get a logger with tenant context support.

    Args:
        name: Logger name (typically __name__)

    Returns:
        LoggerAdapter with tenant context
    """
    logger = logging.getLogger(name)

    # Create adapter that injects context
    extra_dict: dict[str, Any] = {}

    if tenant_id := tenant_context.get():
        extra_dict["tenant_id"] = tenant_id
    if user_id := user_context.get():
        extra_dict["user_id"] = user_id

    return logging.LoggerAdapter(logger, extra_dict)


def set_tenant_context(tenant_id: str) -> None:
    """Set tenant context for current request."""
    tenant_context.set(tenant_id)


def set_user_context(user_id: str) -> None:
    """Set user context for current request."""
    user_context.set(user_id)


def set_request_id_context(request_id: str) -> None:
    """Set request ID context for current request."""
    request_id_context.set(request_id)


def clear_context() -> None:
    """Clear all context variables."""
    tenant_context.set(None)
    user_context.set(None)
    request_id_context.set(None)
