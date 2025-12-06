"""Unit tests for OpenTelemetry distributed tracing."""

import pytest
from unittest.mock import MagicMock
from opentelemetry.trace import SpanKind

from tenant_service.infrastructure.tracing import (
    init_tracing,
    get_tracer,
    create_span,
    add_span_attributes,
    add_span_event,
    set_span_status,
    get_trace_id,
    get_span_id,
    extract_context_from_headers,
    inject_context_to_headers,
    trace_function,
    SpanContextLogger,
)


class TestTracerInitialization:
    """Tests for tracer initialization."""

    def test_init_tracing_returns_tracer(self):
        """Test that init_tracing returns a valid tracer."""
        tracer = init_tracing(service_name="test-service", service_version="1.0.0")
        assert tracer is not None

    def test_get_tracer_returns_same_instance(self):
        """Test that get_tracer returns the same tracer instance."""
        tracer1 = get_tracer()
        tracer2 = get_tracer()
        assert tracer1 is tracer2

    def test_init_tracing_with_console_exporter(self):
        """Test initialization with console exporter (no endpoint)."""
        tracer = init_tracing(
            service_name="console-test",
            service_version="1.0.0",
            exporter_endpoint=None,
        )
        assert tracer is not None


class TestSpanCreation:
    """Tests for span creation and management."""

    def test_create_span_basic(self):
        """Test basic span creation."""
        with create_span("test-span") as span:
            assert span is not None
            assert span.is_recording()

    def test_create_span_with_attributes(self):
        """Test span creation with attributes."""
        attributes = {"key1": "value1", "key2": 123}
        with create_span("test-span", attributes=attributes) as span:
            assert span is not None

    def test_create_span_with_tenant_id(self):
        """Test span creation with tenant context."""
        with create_span("test-span", tenant_id="tenant-123") as span:
            assert span is not None

    def test_create_span_with_kind(self):
        """Test span creation with different kinds."""
        for kind in [SpanKind.SERVER, SpanKind.CLIENT, SpanKind.INTERNAL]:
            with create_span("test-span", kind=kind) as span:
                assert span is not None

    def test_create_span_captures_exception(self):
        """Test that exceptions are recorded in spans."""
        with pytest.raises(ValueError):
            with create_span("error-span"):
                raise ValueError("Test error")


class TestSpanAttributes:
    """Tests for span attribute management."""

    def test_add_span_attributes(self):
        """Test adding attributes to current span."""
        with create_span("test-span"):
            # Should not raise
            add_span_attributes({"attr1": "value1", "attr2": 42})

    def test_add_span_attributes_no_active_span(self):
        """Test adding attributes when no span is active."""
        # Should not raise even without active span
        add_span_attributes({"attr1": "value1"})


class TestSpanEvents:
    """Tests for span event recording."""

    def test_add_span_event(self):
        """Test adding events to current span."""
        with create_span("test-span"):
            add_span_event("test-event", {"key": "value"})

    def test_add_span_event_no_attributes(self):
        """Test adding event without attributes."""
        with create_span("test-span"):
            add_span_event("simple-event")

    def test_add_span_event_no_active_span(self):
        """Test adding event when no span is active."""
        # Should not raise
        add_span_event("orphan-event")


class TestSpanStatus:
    """Tests for span status management."""

    def test_set_span_status_success(self):
        """Test setting successful status."""
        with create_span("test-span"):
            set_span_status(True, "Operation successful")

    def test_set_span_status_failure(self):
        """Test setting failure status."""
        with create_span("test-span"):
            set_span_status(False, "Operation failed")

    def test_set_span_status_no_message(self):
        """Test setting status without message."""
        with create_span("test-span"):
            set_span_status(True)


class TestTraceContext:
    """Tests for trace context extraction and propagation."""

    def test_get_trace_id_with_active_span(self):
        """Test getting trace ID from active span."""
        with create_span("test-span"):
            trace_id = get_trace_id()
            # Trace ID should be a 32-character hex string
            assert trace_id is not None
            assert len(trace_id) == 32

    def test_get_span_id_with_active_span(self):
        """Test getting span ID from active span."""
        with create_span("test-span"):
            span_id = get_span_id()
            # Span ID should be a 16-character hex string
            assert span_id is not None
            assert len(span_id) == 16

    def test_get_trace_id_no_active_span(self):
        """Test getting trace ID when no span is active."""
        # May return None or an invalid trace ID
        get_trace_id()  # Just ensure it doesn't raise

    def test_inject_context_to_headers(self):
        """Test injecting trace context into headers."""
        with create_span("test-span"):
            headers = {}
            result = inject_context_to_headers(headers)
            assert isinstance(result, dict)

    def test_extract_context_from_headers(self):
        """Test extracting trace context from headers."""
        headers = {"traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"}
        extract_context_from_headers(headers)  # Should not raise


class TestTraceDecorator:
    """Tests for trace_function decorator."""

    def test_trace_sync_function(self):
        """Test tracing a synchronous function."""

        @trace_function()
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"

    def test_trace_sync_function_with_name(self):
        """Test tracing with custom span name."""

        @trace_function(name="custom-span")
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"

    def test_trace_sync_function_with_attributes(self):
        """Test tracing with attributes."""

        @trace_function(attributes={"operation": "test"})
        def my_func():
            return "result"

        result = my_func()
        assert result == "result"

    @pytest.mark.asyncio
    async def test_trace_async_function(self):
        """Test tracing an asynchronous function."""

        @trace_function()
        async def my_async_func():
            return "async result"

        result = await my_async_func()
        assert result == "async result"

    def test_trace_function_preserves_name(self):
        """Test that decorator preserves function name."""

        @trace_function()
        def original_name():
            pass

        assert original_name.__name__ == "original_name"


class TestSpanContextLogger:
    """Tests for SpanContextLogger adapter."""

    def test_logger_info(self):
        """Test info logging with trace context."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        with create_span("test-span"):
            logger.info("Test message")

        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Test message" in call_args

    def test_logger_error(self):
        """Test error logging with trace context."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        with create_span("test-span"):
            logger.error("Error message")

        mock_logger.error.assert_called_once()

    def test_logger_warning(self):
        """Test warning logging with trace context."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        logger.warning("Warning message")
        mock_logger.warning.assert_called_once()

    def test_logger_debug(self):
        """Test debug logging."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        logger.debug("Debug message")
        mock_logger.debug.assert_called_once()

    def test_logger_critical(self):
        """Test critical logging."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        logger.critical("Critical message")
        mock_logger.critical.assert_called_once()

    def test_logger_exception(self):
        """Test exception logging."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        logger.exception("Exception occurred")
        mock_logger.exception.assert_called_once()

    def test_logger_includes_trace_id(self):
        """Test that trace ID is included in log message."""
        mock_logger = MagicMock()
        logger = SpanContextLogger(mock_logger)

        with create_span("test-span"):
            logger.info("Test message")

        call_args = mock_logger.info.call_args[0][0]
        assert "trace_id=" in call_args
        assert "span_id=" in call_args


class TestTracingPerformance:
    """Performance tests for tracing operations."""

    def test_span_creation_performance(self):
        """Test that span creation is fast enough."""
        import time

        iterations = 100
        start = time.time()

        for _ in range(iterations):
            with create_span("perf-test"):
                pass

        duration = time.time() - start
        avg_duration_ms = (duration / iterations) * 1000

        # Each span should take less than 1ms on average
        assert avg_duration_ms < 1.0, f"Span creation too slow: {avg_duration_ms:.2f}ms"

    def test_attribute_recording_performance(self):
        """Test that attribute recording is fast."""
        import time

        iterations = 100
        start = time.time()

        with create_span("perf-test"):
            for _ in range(iterations):
                add_span_attributes(
                    {
                        "attr1": "value1",
                        "attr2": 42,
                        "attr3": True,
                    }
                )

        duration = time.time() - start
        total_ms = duration * 1000

        # 100 attribute recordings should take less than 50ms total
        assert total_ms < 50, f"Attribute recording too slow: {total_ms:.2f}ms"
