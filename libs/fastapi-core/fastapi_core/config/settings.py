from .enums.log_level import LogLevel  # Importing an Enum for predefined log levels
from .env_loader import EnvSettings  # Importing the base environment settings class


class AppSettings(EnvSettings):
    """
    Application-specific settings class extending the base `EnvSettings`.

    Attributes
    ----------
        LOG_LEVEL (LogLevel): Specifies the logging level for the application.
                              Defaults to `LogLevel.DEBUG`. This is an Enum field,
                              ensuring that only valid, predefined log levels are allowed.

    """

    # Model configuration: allow population only for explicitly defined fields
    model_config = {
        "extra": "ignore",  # Ignore extra fields from the environment
        "populate_by_name": True,  # Allow population by explicitly defined fields
    }

    LOG_LEVEL: LogLevel = LogLevel.DEBUG  # Define the default log level


# Instantiate the settings object to make configurations accessible globally
app_settings = AppSettings()
