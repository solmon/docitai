"""Settings and configuration for Tenant Service."""

from typing import Literal

from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration."""

    database_url: str = "postgresql://user:password@localhost:5432/tenant_db"
    database_type: Literal["postgresql", "sqlserver"] = "postgresql"
    echo_sql: bool = False

    class Config:
        env_prefix = "DB_"


class AppSettings(BaseSettings):
    """Application settings."""

    app_name: str = "Tenant Management Service"
    app_version: str = "0.1.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # Logging
    log_level: str = "INFO"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # Database
    database: DatabaseSettings = DatabaseSettings()

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False


# Load settings
settings = AppSettings()
