"""Performance optimization utilities for tenant service.

This module provides utilities for optimizing database queries,
connection pooling, and caching for high-concurrency tenant operations.
"""

import logging
from functools import lru_cache
from typing import Any, Optional, TypeVar

from sqlmodel import Session

logger = logging.getLogger(__name__)

T = TypeVar("T")


# Connection pool configuration for high-concurrency scenarios
POOL_CONFIG = {
    "pool_size": 20,  # Base pool size
    "max_overflow": 10,  # Additional connections when pool is full
    "pool_timeout": 30,  # Seconds to wait for connection
    "pool_recycle": 3600,  # Recycle connections after 1 hour
    "pool_pre_ping": True,  # Verify connection health before use
}


class QueryOptimizer:
    """
    Query optimization utilities for tenant operations.

    Provides methods for optimizing common query patterns
    in multi-tenant scenarios.
    """

    @staticmethod
    def batch_insert(session: Session, objects: list[Any], batch_size: int = 100) -> int:
        """
        Insert objects in batches for better performance.

        Args:
            session: Database session
            objects: List of SQLModel objects to insert
            batch_size: Number of objects per batch

        Returns:
            Total number of objects inserted
        """
        total = 0
        for i in range(0, len(objects), batch_size):
            batch = objects[i : i + batch_size]
            session.add_all(batch)
            session.flush()
            total += len(batch)
        session.commit()
        logger.debug(f"Batch inserted {total} objects in {(total + batch_size - 1) // batch_size} batches")
        return total

    @staticmethod
    def bulk_update(
        session: Session,
        model_class: type[T],
        updates: list[dict[str, Any]],
        id_field: str = "id",
    ) -> int:
        """
        Perform bulk update operations.

        Args:
            session: Database session
            model_class: SQLModel class to update
            updates: List of dicts with 'id' and fields to update
            id_field: Name of the ID field

        Returns:
            Number of records updated
        """
        count = 0
        for update_data in updates:
            obj_id = update_data.pop(id_field, None)
            if obj_id is None:
                continue

            stmt = session.query(model_class).filter(getattr(model_class, id_field) == obj_id)
            if stmt.update(update_data, synchronize_session=False):
                count += 1

        session.commit()
        logger.debug(f"Bulk updated {count} records")
        return count


class TenantCache:
    """
    Simple in-memory cache for tenant data.

    Used for caching frequently accessed tenant metadata
    to reduce database queries.
    """

    _cache: dict[str, Any] = {}
    _max_size: int = 1000

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        """Get cached value."""
        return cls._cache.get(key)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """Set cached value with LRU eviction."""
        if len(cls._cache) >= cls._max_size:
            # Simple LRU: remove first item (oldest)
            oldest_key = next(iter(cls._cache))
            del cls._cache[oldest_key]
        cls._cache[key] = value

    @classmethod
    def invalidate(cls, key: str) -> None:
        """Invalidate cached value."""
        cls._cache.pop(key, None)

    @classmethod
    def invalidate_tenant(cls, tenant_id: str) -> None:
        """Invalidate all cached values for a tenant."""
        keys_to_remove = [k for k in cls._cache if k.startswith(f"tenant:{tenant_id}:")]
        for key in keys_to_remove:
            del cls._cache[key]
        logger.debug(f"Invalidated {len(keys_to_remove)} cache entries for tenant {tenant_id}")

    @classmethod
    def clear(cls) -> None:
        """Clear entire cache."""
        cls._cache.clear()


@lru_cache(maxsize=100)
def get_subscription_plan_limits(plan: str) -> dict[str, int]:
    """
    Get cached subscription plan limits.

    Args:
        plan: Subscription plan name

    Returns:
        Dict of plan limits
    """
    limits = {
        "starter": {
            "max_folders": 100,
            "max_storage_gb": 10,
            "max_document_types": 20,
            "max_retention_policies": 5,
            "api_rate_limit": 100,  # requests per minute
        },
        "professional": {
            "max_folders": 500,
            "max_storage_gb": 100,
            "max_document_types": 100,
            "max_retention_policies": 25,
            "api_rate_limit": 500,
        },
        "enterprise": {
            "max_folders": 10000,
            "max_storage_gb": 1000,
            "max_document_types": 1000,
            "max_retention_policies": 100,
            "api_rate_limit": 2000,
        },
    }
    return limits.get(plan, limits["starter"])


class ConnectionPoolMetrics:
    """Metrics for connection pool monitoring."""

    active_connections: int = 0
    total_connections: int = 0
    wait_count: int = 0
    overflow_count: int = 0

    @classmethod
    def record_connection_acquired(cls) -> None:
        cls.active_connections += 1
        cls.total_connections += 1

    @classmethod
    def record_connection_released(cls) -> None:
        cls.active_connections -= 1

    @classmethod
    def record_wait(cls) -> None:
        cls.wait_count += 1

    @classmethod
    def record_overflow(cls) -> None:
        cls.overflow_count += 1

    @classmethod
    def get_stats(cls) -> dict[str, int]:
        return {
            "active_connections": cls.active_connections,
            "total_connections": cls.total_connections,
            "wait_count": cls.wait_count,
            "overflow_count": cls.overflow_count,
        }


# Index recommendations for optimal query performance
INDEX_RECOMMENDATIONS = """
-- Recommended database indexes for optimal performance

-- Tenant table indexes
CREATE INDEX IF NOT EXISTS idx_tenant_name ON tenants(name);
CREATE INDEX IF NOT EXISTS idx_tenant_subscription ON tenants(subscription_plan);
CREATE INDEX IF NOT EXISTS idx_tenant_active ON tenants(is_active) WHERE is_active = true;

-- Folder table indexes
CREATE INDEX IF NOT EXISTS idx_folder_tenant_parent ON folders(tenant_id, parent_id);
CREATE INDEX IF NOT EXISTS idx_folder_tenant_path ON folders(tenant_id, path);
CREATE INDEX IF NOT EXISTS idx_folder_tenant_owner ON folders(tenant_id, owner_id);
CREATE INDEX IF NOT EXISTS idx_folder_not_deleted ON folders(tenant_id) WHERE deleted_at IS NULL;

-- Storage configuration indexes
CREATE INDEX IF NOT EXISTS idx_storage_tenant ON storage_configurations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_storage_provider ON storage_configurations(provider_type);

-- Retention policy indexes
CREATE INDEX IF NOT EXISTS idx_retention_tenant ON retention_policies(tenant_id);
CREATE INDEX IF NOT EXISTS idx_retention_scope ON retention_policies(scope_type, scope_id);
CREATE INDEX IF NOT EXISTS idx_retention_active ON retention_policies(is_active) WHERE is_active = true;

-- Document type/category indexes
CREATE INDEX IF NOT EXISTS idx_doctype_tenant ON document_types(tenant_id);
CREATE INDEX IF NOT EXISTS idx_doctype_category ON document_types(category_id);
CREATE INDEX IF NOT EXISTS idx_category_tenant ON document_categories(tenant_id);

-- Audit trail indexes
CREATE INDEX IF NOT EXISTS idx_audit_tenant ON compliance_audit_trail(tenant_id);
CREATE INDEX IF NOT EXISTS idx_audit_resource ON compliance_audit_trail(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON compliance_audit_trail(created_at DESC);
"""
