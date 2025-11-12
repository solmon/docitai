import logging
import os
from typing import Any

from pydantic import ValidationError
from pydantic_settings import BaseSettings

from .cli_env import APP_ENV
from .enums.app_env import AppEnv


# Configure a logger for the module
logger = logging.getLogger(__name__)


class EnvSettings(BaseSettings):
    """
    A configuration class to load and validate environment variables using Pydantic's BaseSettings.

    When an instance of `EnvSettings` is created, it automatically attempts to load the appropriate `.env` file
    based on the application's runtime mode (production or development). It validates the loaded environment
    variables and logs errors if they occur.

    This class ensures:
    1. The correct `.env` file is used (e.g., `.env` for production or `.env.development` for development).
    2. The `.env` file exists before loading.
    3. The environment variables are validated against the defined schema.
    """

    class Config:
        """
        Configuration class for Pydantic BaseSettings.

        Attributes
        ----------
            env_file (str): Specifies the environment file to use based on the runtime mode.
            env_file_encoding (str): Defines the encoding for the environment file (default is UTF-8).

        """

        env_file = ".env" if APP_ENV == AppEnv.PRODUCTION else ".env.development"
        env_file_encoding = "utf-8"

    @classmethod
    def _load_env_file(cls) -> str:
        """
        Checks if the specified `.env` file exists.

        Returns
        -------
            str: The path to the `.env` file.

        Raises
        ------
            FileNotFoundError: If the `.env` file does not exist.

        """
        env_file_path = cls.Config.env_file  # Get the environment file path from the Config class.

        # Check if the file exists on the filesystem.
        if not os.path.isfile(env_file_path):
            logger.error("Environment file '%s' not found.", env_file_path)
            raise FileNotFoundError(f"Environment file '{env_file_path}' not found.")

        return env_file_path

    def __init__(self, **values: Any) -> None:
        """
        Initializes the EnvSettings instance.

        - Ensures the appropriate `.env` file is present.
        - Validates the environment variables using Pydantic.

        When an instance is created:
        1. The `_load_env_file` method is called to check the existence of the `.env` file.
        2. The parent class constructor (`BaseSettings.__init__`) is invoked to load and validate settings.

        Args:
        ----
            values (Any): Additional settings values.

        Raises:
        ------
            FileNotFoundError: If the `.env` file is not found.
            ValidationError: If validation of the environment variables fails.

        """
        try:
            # Ensure the `.env` file exists before proceeding.
            self._load_env_file()

            # Call the parent class's constructor to initialize and validate settings.
            super().__init__(**values)
        except ValidationError as e:
            # Log validation errors and re-raise the exception.
            logger.error("Validation error occurred: %s", e)
            raise
