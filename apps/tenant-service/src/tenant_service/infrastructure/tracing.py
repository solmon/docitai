"""OpenTelemetry distributed tracing configuration and utilities.

This module provides:
- Tracer initialization and configuration
- Span context propagation
- Utility functions for creating spans
- Integration with tenant context
"""

import logging
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from tenant_service.config import settings

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[Tracer] = None
_propagator = TraceContextTextMapPropagator()


def init_tracing(
    service_name: str = "tenant-service",
    service_version: str = "0.1.0",
    exporter_endpoint: Optional[str] = None,
) -> Tracer:
    """
    Initialize OpenTelemetry tracing with the configured exporter.

    Args:
        service_name: Name of the service for trace identification
        service_version: Version of the service
        exporter_endpoint: Optional endpoint for OTLP/Jaeger exporter

    Returns:
        Configured Tracer instance
    """
    global _tracer

    if _tracer is not None:
        return _tracer

    # Create resource with service information
    resource = Resource.create(
        {
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            "deployment.environment": getattr(settings, "environment", "development"),
        }
    )

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Add span processor with exporter
    if exporter_endpoint:
        try:
            # Try to use OTLP exporter if endpoint is provided
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exporter = OTLPSpanExporter(endpoint=exporter_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
            logger.info(f"OpenTelemetry OTLP exporter configured: {exporter_endpoint}")
        except ImportError:
            logger.warning("OTLP exporter not available, falling back to console exporter")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        # Use console exporter for development
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        logger.info("OpenTelemetry console exporter configured (development mode)")

    # Set global tracer provider
    trace.set_tracer_provider(provider)

    # Get tracer instance
    _tracer = trace.get_tracer(service_name, service_version)

    logger.info(f"OpenTelemetry tracing initialized for {service_name} v{service_version}")
    return _tracer


def get_tracer() -> Tracer:
    """
    Get the global tracer instance.

    Returns:
        Tracer instance (initializes if not already done)
    """
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer


def shutdown_tracing() -> None:
    """Shutdown the tracer provider and flush pending spans."""
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.shutdown()
        logger.info("OpenTelemetry tracing shutdown complete")


@contextmanager
def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
    tenant_id: Optional[str] = None,
):
    """
    Create a new span as a context manager.

    Args:
        name: Name of the span
        kind: Kind of span (SERVER, CLIENT, INTERNAL, etc.)
        attributes: Optional attributes to add to the span
        tenant_id: Optional tenant ID for multi-tenant context

    Yields:
        The created Span object
    """
    tracer = get_tracer()

    # Build attributes
    span_attributes = attributes.copy() if attributes else {}
    if tenant_id:
        span_attributes["tenant.id"] = tenant_id

    with tracer.start_as_current_span(
        name,
        kind=kind,
        attributes=span_attributes,
    ) as span:
        try:
            yield span
        except Exception as e:
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.record_exception(e)
            raise


def add_span_attributes(attributes: Dict[str, Any]) -> None:
    """
    Add attributes to the current active span.

    Args:
        attributes: Dictionary of attributes to add
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add an event to the current active span.

    Args:
        name: Name of the event
        attributes: Optional attributes for the event
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        span.add_event(name, attributes=attributes or {})


def set_span_status(success: bool, message: Optional[str] = None) -> None:
    """
    Set the status of the current active span.

    Args:
        success: Whether the operation was successful
        message: Optional status message
    """
    span = trace.get_current_span()
    if span and span.is_recording():
        if success:
            span.set_status(Status(StatusCode.OK, message))
        else:
            span.set_status(Status(StatusCode.ERROR, message))


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID as a hex string.

    Returns:
        Trace ID string or None if no active span
    """
    span = trace.get_current_span()
    if span:
        context = span.get_span_context()
        if context.is_valid:
            return format(context.trace_id, "032x")
    return None


def get_span_id() -> Optional[str]:
    """
    Get the current span ID as a hex string.

    Returns:
        Span ID string or None if no active span
    """
    span = trace.get_current_span()
    if span:
        context = span.get_span_context()
        if context.is_valid:
            return format(context.span_id, "016x")
    return None


def extract_context_from_headers(headers: Dict[str, str]) -> Optional[trace.SpanContext]:
    """
    Extract trace context from HTTP headers.

    Args:
        headers: HTTP headers dictionary

    Returns:
        SpanContext if found in headers
    """
    carrier = dict(headers)
    context = _propagator.extract(carrier)
    return trace.get_current_span(context).get_span_context()


def inject_context_to_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject current trace context into HTTP headers.

    Args:
        headers: HTTP headers dictionary to update

    Returns:
        Updated headers dictionary
    """
    _propagator.inject(headers)
    return headers


def trace_function(
    name: Optional[str] = None,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to automatically trace a function.

    Args:
        name: Optional span name (defaults to function name)
        kind: Kind of span
        attributes: Optional attributes to add

    Returns:
        Decorated function
    """

    def decorator(func: Callable) -> Callable:
        span_name = name or func.__name__

        def wrapper(*args, **kwargs):
            with create_span(span_name, kind=kind, attributes=attributes):
                return func(*args, **kwargs)

        async def async_wrapper(*args, **kwargs):
            with create_span(span_name, kind=kind, attributes=attributes):
                return await func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio

        if asyncio.iscoroutinefunction(func):
            async_wrapper.__name__ = func.__name__
            async_wrapper.__doc__ = func.__doc__
            return async_wrapper
        else:
            wrapper.__name__ = func.__name__
            wrapper.__doc__ = func.__doc__
            return wrapper

    return decorator


class SpanContextLogger:
    """
    Logger adapter that includes trace context in log messages.

    Usage:
        logger = SpanContextLogger(logging.getLogger(__name__))
        logger.info("Processing request")  # Includes trace_id and span_id
    """

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def _add_trace_context(self, msg: str) -> str:
        """Add trace context to log message."""
        trace_id = get_trace_id()
        span_id = get_span_id()
        if trace_id:
            return f"[trace_id={trace_id} span_id={span_id}] {msg}"
        return msg

    def debug(self, msg: str, *args, **kwargs):
        self._logger.debug(self._add_trace_context(msg), *args, **kwargs)

    def info(self, msg: str, *args, **kwargs):
        self._logger.info(self._add_trace_context(msg), *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        self._logger.warning(self._add_trace_context(msg), *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        self._logger.error(self._add_trace_context(msg), *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        self._logger.critical(self._add_trace_context(msg), *args, **kwargs)

    def exception(self, msg: str, *args, **kwargs):
        self._logger.exception(self._add_trace_context(msg), *args, **kwargs)
