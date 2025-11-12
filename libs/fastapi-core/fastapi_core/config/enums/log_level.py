from enum import Enum


class LogLevel(str, Enum):
    """
    Enum representing valid log levels.
    These log levels correspond to Python's standard logging levels as defined in:
    `.../python3.12/logging/__init__.py` in the `_levelToName` dictionary.
    """

    DEBUG = "debug"  # Debugging messages, typically verbose output.
    INFO = "info"  # Informational messages that represent the normal operation of the application.
    WARNING = "warning"  # Indicates a potential issue or cautionary message.
    ERROR = "error"  # Errors that prevent some function from working but do not crash the program.
    CRITICAL = "critical"  # Very serious errors that may cause the program to exit.
