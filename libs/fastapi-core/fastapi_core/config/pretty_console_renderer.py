import json
import warnings
from collections.abc import MutableMapping
from io import StringIO
from typing import Any

from colorama import Fore, Style, init
from structlog.dev import ConsoleRenderer, plain_traceback
from structlog.processors import _figure_out_exc_info


# Initialize colorama for cross-platform colored output
init()


class PrettyConsoleRenderer(ConsoleRenderer):
    """
    A custom log renderer for pretty-printing logs in the console.
    Combines structured logging with colored output for better readability.
    """

    def __init__(self) -> None:
        """Initialize the renderer. Inherits from `structlog.dev.ConsoleRenderer`."""
        super().__init__()

    def __call__(self, _: Any, __: Any, event_dict: MutableMapping[str, Any]) -> str:
        """
        Render a log event as a string with colored and JSON-formatted output.
        Inspired by structlog.dev.ConsoleRenderer __call__ method for stack and exception printing
        https://github.com/hynek/structlog/blob/b488a8bf589a01aabc41e3bf8df81a9848cd426c/src/structlog/dev.py#L712

        Args:
        ----
            _ (Any): Placeholder for the logger instance (not used).
            __ (Any): Placeholder for the logger's name (not used).
            event_dict (MutableMapping[str, Any]): Log event dictionary.

        Returns:
        -------
            str: The formatted log string.

        """
        # Extract special fields
        stack = event_dict.pop("stack", None)
        exc = event_dict.pop("exception", None)
        exc_info = event_dict.pop("exc_info", None)

        # Separate fields for primary fields rendering and additional JSON data
        primary_keys = {
            "timestamp",
            "level",
            "event",
            "process",
            "name",
            "hostname",
        }  # hostname is not required in console.
        primary_event_dict = {}
        json_event_dict = {}

        for k, v in event_dict.items():
            if k in primary_keys:
                primary_event_dict[k] = v
            else:
                json_event_dict[k] = v

        # Prepare the log output
        sio = StringIO()

        # Format primary log fields
        primary_rendered = self._format_primary_event(primary_event_dict)
        sio.write(primary_rendered)

        # Add additional JSON-formatted fields if present
        if json_event_dict:
            formatted_json = json.dumps(json_event_dict, indent=2, sort_keys=True)
            sio.write("\n" + formatted_json)

        # Append stack trace if available
        if stack:
            sio.write("\n" + stack)
            if exc_info or exc:
                sio.write("\n\n" + "=" * 79 + "\n")

        # Handle exception information
        exc_info = _figure_out_exc_info(exc_info)

        if exc_info:
            self._exception_formatter(sio, exc_info)
        elif exc is not None:
            if self._exception_formatter is not plain_traceback:
                warnings.warn(
                    "Remove `format_exc_info` from your processor chain if you want pretty exceptions.",
                    stacklevel=2,
                )
            sio.write("\n" + exc)

        return sio.getvalue()

    def _format_primary_event(self, event_dict: dict[str, Any]) -> str:
        """
        Format the primary log event fields with color for the console.

        Args:
        ----
            event_dict (dict[str, Any]): Dictionary of primary log fields.

        Returns:
        -------
            str: The formatted string with colored log levels and messages.

        """
        timestamp = event_dict.get("timestamp", "")
        level = event_dict.get("level", "").upper()
        message = event_dict.get("event", "")
        name = event_dict.get("name", "")
        process = event_dict.get("process", "")

        # Define color codes based on log levels
        level_colors = {
            "DEBUG": Fore.GREEN,
            "INFO": Fore.BLUE,
            "WARNING": Fore.YELLOW,
            "ERROR": Fore.RED,
            "FATAL": Fore.MAGENTA,
            "CRITICAL": Fore.RED + Style.BRIGHT,
        }
        level_color = level_colors.get(level, Fore.RESET)

        # Format the message with color
        formatted_message = (
            f"[{timestamp}] {level_color}{level}{Style.RESET_ALL} "
            f"({name}/{process}): {Fore.GREEN}{message}{Style.RESET_ALL}"
        )
        return formatted_message
