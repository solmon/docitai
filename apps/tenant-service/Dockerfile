# syntax=docker/dockerfile:1.4
# Tenant Management Service - Production Dockerfile
# Multi-stage build for optimized image size

# ==============================================================================
# Stage 1: Build stage with dependencies
# ==============================================================================
FROM python:3.12-slim-bookworm AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
RUN pip install uv

WORKDIR /app

# Copy workspace root files for dependency resolution
COPY pyproject.toml ./
COPY apps/tenant-service/pyproject.toml apps/tenant-service/

# Copy library dependencies
COPY libs/database-core/pyproject.toml libs/database-core/
COPY libs/database-core/src/ libs/database-core/src/

COPY libs/storage-adapter/pyproject.toml libs/storage-adapter/
COPY libs/storage-adapter/src/ libs/storage-adapter/src/

COPY libs/tenant-auth/pyproject.toml libs/tenant-auth/
COPY libs/tenant-auth/src/ libs/tenant-auth/src/

COPY libs/compliance-engine/pyproject.toml libs/compliance-engine/
COPY libs/compliance-engine/src/ libs/compliance-engine/src/

COPY libs/fastapi-core/pyproject.toml libs/fastapi-core/
COPY libs/fastapi-core/fastapi_core/ libs/fastapi-core/fastapi_core/

# Copy application source
COPY apps/tenant-service/src/ apps/tenant-service/src/

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install libraries first (they're local dependencies)
RUN uv pip install ./libs/database-core \
    ./libs/storage-adapter \
    ./libs/tenant-auth \
    ./libs/compliance-engine \
    ./libs/fastapi-core

# Install application with production dependencies
RUN uv pip install ./apps/tenant-service

# ==============================================================================
# Stage 2: Production runtime
# ==============================================================================
FROM python:3.12-slim-bookworm AS production

# Labels for container metadata
LABEL org.opencontainers.image.title="Tenant Management Service" \
      org.opencontainers.image.description="Multi-tenant document management service" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="Docitai" \
      org.opencontainers.image.source="https://github.com/docitai/docitai"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Application configuration
    APP_ENV=production \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    APP_WORKERS=4 \
    # Python optimization
    PYTHONOPTIMIZE=2

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create necessary directories
RUN mkdir -p /app/logs /app/data \
    && chown -R appuser:appgroup /app

WORKDIR /app

# Switch to non-root user
USER appuser

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${APP_PORT}/health || exit 1

# Expose application port
EXPOSE ${APP_PORT}

# Default command using uvicorn
CMD ["sh", "-c", "uvicorn tenant_service.main:app --host ${APP_HOST} --port ${APP_PORT} --workers ${APP_WORKERS} --log-level info"]

# ==============================================================================
# Stage 3: Development runtime (for local development with hot reload)
# ==============================================================================
FROM python:3.12-slim-bookworm AS development

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    APP_ENV=development \
    APP_HOST=0.0.0.0 \
    APP_PORT=8000

# Install development dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Development runs as root for easier volume mounting
EXPOSE ${APP_PORT}

# Development command with hot reload
CMD ["uvicorn", "tenant_service.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
