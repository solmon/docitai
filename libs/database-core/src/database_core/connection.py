"""Multi-database connection management for PostgreSQL and SQL Server support."""

import logging

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine


logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database connections with support for multiple database types.

    Supports both PostgreSQL and SQL Server with automatic dialect detection.
    Handles connection pooling and engine lifecycle management.
    """

    _engine: Engine | None = None
    _database_url: str | None = None
    _database_type: str = "postgresql"

    @classmethod
    def initialize(
        cls,
        database_url: str,
        database_type: str = "postgresql",
        echo_sql: bool = False,
        pool_size: int = 20,
    ) -> Engine:
        """
        Initialize database connection and create engine.

        Args:
            database_url: Database connection string
            database_type: Type of database ('postgresql' or 'sqlserver')
            echo_sql: Enable SQL query logging
            pool_size: Connection pool size

        Returns:
            SQLAlchemy Engine instance

        """
        cls._database_url = database_url
        cls._database_type = database_type

        # Create engine with appropriate pool configuration
        if database_type == "sqlserver":
            from sqlalchemy.pool import NullPool

            pool_class = NullPool
            connect_args = {"check_same_thread": False}
        else:
            from sqlalchemy.pool import QueuePool

            pool_class = QueuePool
            connect_args = {"check_same_thread": False}

        cls._engine = create_engine(
            database_url,
            echo=echo_sql,
            poolclass=pool_class,
            pool_size=pool_size,
            max_overflow=10,
            connect_args=connect_args,
        )

        logger.info(f"Database engine initialized: type={database_type}, url={database_url.split('@')[0]}***")

        return cls._engine

    @classmethod
    def get_engine(cls) -> Engine:
        """Get the current database engine."""
        if cls._engine is None:
            raise RuntimeError("Database engine not initialized. Call initialize() first.")
        return cls._engine

    @classmethod
    def create_db_and_tables(cls) -> None:
        """Create all database tables from SQLModel metadata."""
        engine = cls.get_engine()
        SQLModel.metadata.create_all(engine)
        logger.info("Database tables created/verified")

    @classmethod
    def get_session(cls) -> Session:
        """Get a new database session."""
        engine = cls.get_engine()
        return Session(engine)

    @classmethod
    def close(cls) -> None:
        """Close database connection."""
        if cls._engine:
            cls._engine.dispose()
            cls._engine = None
            logger.info("Database connection closed")


def get_db_session():
    """Dependency for FastAPI to inject database session."""
    session = DatabaseManager.get_session()
    try:
        yield session
    finally:
        session.close()
