"""Prometheus metrics collection for FastAPI applications."""

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Create custom registry
METRICS_REGISTRY = CollectorRegistry()


# ==================== Metrics Definitions ====================

# HTTP Request Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code'],
    registry=METRICS_REGISTRY,
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=METRICS_REGISTRY,
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

http_requests_in_progress = Gauge(
    'http_requests_in_progress',
    'HTTP requests in progress',
    ['method', 'endpoint'],
    registry=METRICS_REGISTRY,
)

# API Error Metrics
api_errors_total = Counter(
    'api_errors_total',
    'Total API errors',
    ['endpoint', 'status_code', 'error_type'],
    registry=METRICS_REGISTRY,
)

# Database Metrics
db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['query_type', 'table'],
    registry=METRICS_REGISTRY,
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

db_connections_active = Gauge(
    'db_connections_active',
    'Active database connections',
    registry=METRICS_REGISTRY,
)

db_connections_total = Counter(
    'db_connections_total',
    'Total database connections',
    ['status'],
    registry=METRICS_REGISTRY,
)

db_errors_total = Counter(
    'db_errors_total',
    'Total database errors',
    ['error_type'],
    registry=METRICS_REGISTRY,
)

# Tenant Metrics
active_tenants = Gauge(
    'active_tenants',
    'Number of active tenants',
    registry=METRICS_REGISTRY,
)

tenant_api_requests = Counter(
    'tenant_api_requests_total',
    'Total API requests by tenant',
    ['tenant_id'],
    registry=METRICS_REGISTRY,
)

# Storage Metrics
storage_usage_bytes = Gauge(
    'storage_usage_bytes',
    'Storage usage in bytes by tenant',
    ['tenant_id', 'storage_type'],
    registry=METRICS_REGISTRY,
)

documents_total = Gauge(
    'documents_total',
    'Total documents by tenant',
    ['tenant_id'],
    registry=METRICS_REGISTRY,
)

# Authentication Metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['method', 'result'],
    registry=METRICS_REGISTRY,
)

auth_failures_total = Counter(
    'auth_failures_total',
    'Total authentication failures',
    ['method', 'reason'],
    registry=METRICS_REGISTRY,
)

# Cache Metrics
cache_hits_total = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_type'],
    registry=METRICS_REGISTRY,
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_type'],
    registry=METRICS_REGISTRY,
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_type'],
    registry=METRICS_REGISTRY,
)

# Business Logic Metrics
document_created_total = Counter(
    'documents_created_total',
    'Total documents created',
    ['document_type'],
    registry=METRICS_REGISTRY,
)

document_deleted_total = Counter(
    'documents_deleted_total',
    'Total documents deleted',
    ['document_type'],
    registry=METRICS_REGISTRY,
)

compliance_audit_recorded = Counter(
    'compliance_audit_records_total',
    'Total compliance audit records',
    ['action_type'],
    registry=METRICS_REGISTRY,
)

retention_policy_executions = Counter(
    'retention_policy_executions_total',
    'Total retention policy executions',
    ['policy_id', 'result'],
    registry=METRICS_REGISTRY,
)


# ==================== Utility Functions ====================

def get_metrics_summary() -> dict:
    """Get summary of current metrics."""
    return {
        "http_requests_total": http_requests_total.collect(),
        "http_request_duration": http_request_duration_seconds.collect(),
        "api_errors_total": api_errors_total.collect(),
        "db_query_duration": db_query_duration_seconds.collect(),
        "active_tenants": active_tenants._value.get(),
    }


def record_http_request(
    method: str,
    endpoint: str,
    status_code: int,
    duration_seconds: float,
    tenant_id: Optional[str] = None,
) -> None:
    """Record HTTP request metrics.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status_code: HTTP status code
        duration_seconds: Request duration
        tenant_id: Optional tenant ID for tenant metrics
    """
    http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration_seconds)
    
    if tenant_id:
        tenant_api_requests.labels(tenant_id=tenant_id).inc()
    
    # Record errors if status >= 400
    if status_code >= 400:
        error_type = "client_error" if status_code < 500 else "server_error"
        api_errors_total.labels(
            endpoint=endpoint,
            status_code=status_code,
            error_type=error_type,
        ).inc()


def record_db_query(
    query_type: str,
    table: str,
    duration_seconds: float,
) -> None:
    """Record database query metrics.
    
    Args:
        query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        duration_seconds: Query duration
    """
    db_query_duration_seconds.labels(query_type=query_type, table=table).observe(duration_seconds)


def record_db_error(error_type: str) -> None:
    """Record database error.
    
    Args:
        error_type: Type of error (connection, query, validation, etc.)
    """
    db_errors_total.labels(error_type=error_type).inc()


def record_auth_attempt(method: str, result: str) -> None:
    """Record authentication attempt.
    
    Args:
        method: Authentication method (jwt, basic, etc.)
        result: Result (success, failure)
    """
    auth_attempts_total.labels(method=method, result=result).inc()


def record_auth_failure(method: str, reason: str) -> None:
    """Record authentication failure.
    
    Args:
        method: Authentication method
        reason: Failure reason (invalid_token, expired_token, etc.)
    """
    auth_failures_total.labels(method=method, reason=reason).inc()


def record_cache_hit(cache_type: str) -> None:
    """Record cache hit.
    
    Args:
        cache_type: Type of cache (redis, memory, etc.)
    """
    cache_hits_total.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str) -> None:
    """Record cache miss.
    
    Args:
        cache_type: Type of cache
    """
    cache_misses_total.labels(cache_type=cache_type).inc()


def record_document_created(document_type: str) -> None:
    """Record document creation.
    
    Args:
        document_type: Type of document created
    """
    document_created_total.labels(document_type=document_type).inc()


def record_document_deleted(document_type: str) -> None:
    """Record document deletion.
    
    Args:
        document_type: Type of document deleted
    """
    document_deleted_total.labels(document_type=document_type).inc()


def record_compliance_audit(action_type: str) -> None:
    """Record compliance audit.
    
    Args:
        action_type: Type of audit action
    """
    compliance_audit_recorded.labels(action_type=action_type).inc()


def record_retention_policy_execution(policy_id: str, result: str) -> None:
    """Record retention policy execution.
    
    Args:
        policy_id: ID of retention policy
        result: Execution result (success, failure, skipped)
    """
    retention_policy_executions.labels(policy_id=policy_id, result=result).inc()


# ==================== Prometheus Endpoint ====================

def get_metrics_text() -> str:
    """Get metrics in Prometheus text format.
    
    Returns:
        Prometheus metrics as text
    """
    return generate_latest(METRICS_REGISTRY).decode('utf-8')
