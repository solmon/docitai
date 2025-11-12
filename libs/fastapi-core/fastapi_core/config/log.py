# Inspired by https://github.com/opsmill/infrahub/blob/b3fa9b0aeab5b31e9efdbf2071457b0faab6a333/backend/infrahub/log.py

import logging
import socket
from typing import TYPE_CHECKING, Any, cast

import structlog

from .cli_env import APP_ENV
from .enums.app_env import AppEnv
from .pretty_console_renderer import PrettyConsoleRenderer
from .settings import app_settings


if TYPE_CHECKING:
    from structlog.types import Processor

# Retrieve the hostname once
HOSTNAME = socket.gethostname()


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a structured logger with the given name."""
    return structlog.stdlib.get_logger(name)


def get_log_context() -> dict[str, Any]:
    """Retrieve the current log context data."""
    return structlog.contextvars.get_contextvars()


def add_to_log_context(key: str, value: Any) -> None:
    """Set a key-value pair in the log context."""
    structlog.contextvars.bind_contextvars(**{key: value})


def clear_log_context() -> None:
    """Clear the structlog context variables."""
    structlog.contextvars.clear_contextvars()


def configure_logging(app_name: str) -> None:
    # Read log level from AppSettings
    # without upper root_logger.setLevel(log_level) will fail.
    log_level = app_settings.LOG_LEVEL.upper()  # pylint: disable=no-member

    def add_global_log_fields(_: Any, __: Any, event_dict: dict[str, Any]) -> dict[str, Any]:
        # Add custom fields to every log event
        event_dict["name"] = app_name
        event_dict["hostname"] = HOSTNAME
        return event_dict

    # Define common processors
    shared_processors: list[Processor] = [
        # Merge context vars into log events
        structlog.contextvars.merge_contextvars,
        # Add the name of the logger to event dict.
        structlog.stdlib.add_logger_name,
        # Add log level to event dict.
        structlog.stdlib.add_log_level,
        # Perform %-style formatting.
        structlog.stdlib.PositionalArgumentsFormatter(),
        # Add a timestamp in ISO 8601 format.
        structlog.processors.TimeStamper(fmt="iso", utc=APP_ENV == AppEnv.PRODUCTION),
        # Add the custom fields processor
        cast(structlog.types.Processor, add_global_log_fields),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        # If some value is in bytes, decode it to a Unicode str.
        structlog.processors.UnicodeDecoder(),
        # Add callsite parameters.
        structlog.processors.CallsiteParameterAdder(
            {
                # structlog.processors.CallsiteParameter.FILENAME,
                # structlog.processors.CallsiteParameter.FUNC_NAME,
                # structlog.processors.CallsiteParameter.LINENO,
                # structlog.processors.CallsiteParameter.THREAD,
                # structlog.processors.CallsiteParameter.THREAD_NAME,
                structlog.processors.CallsiteParameter.PROCESS,
            }
        ),
    ]

    if APP_ENV == AppEnv.PRODUCTION:
        shared_processors.extend(
            [
                # print structured tracebacks
                structlog.processors.dict_tracebacks,
                # Format the exception only for JSON logs, as we want to pretty-print them when
                # using the ConsoleRenderer
                structlog.processors.format_exc_info,
            ]
        )

    # Configure structlog
    structlog.configure(
        processors=shared_processors
        + [
            # Prepare event dict for `ProcessorFormatter`.
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Choose log renderer based on environment
    log_renderer = (
        structlog.processors.JSONRenderer()
        if APP_ENV == AppEnv.PRODUCTION
        # Pretty printing when we run in a terminal session.
        # Automatically prints pretty tracebacks when "rich" is installed
        else PrettyConsoleRenderer()  # structlog.dev.ConsoleRenderer()
    )

    # Set up formatter and handler
    formatter = structlog.stdlib.ProcessorFormatter(
        # These run ONLY on `logging` entries that do NOT originate within
        # structlog.
        foreign_pre_chain=shared_processors,
        # These run on ALL entries after the pre_chain is done.
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            cast(structlog.types.Processor, log_renderer),
        ],
    )
    handler = logging.StreamHandler()
    # Use OUR `ProcessorFormatter` to format all `logging` entries.
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for _log in ["uvicorn", "uvicorn.error", "sqlalchemy.engine.Engine"]:
        # Clear the log handlers for uvicorn loggers, and enable propagation
        # so the messages are caught by our root logger and formatted correctly
        # by structlog
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

    # Since we re-create the access logs ourselves, to add all information
    # in the structured log (see the `logging_middleware` in main.py), we clear
    # the handlers and prevent the logs to propagate to a logger higher up in the
    # hierarchy (effectively rendering them silent).
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False
