# Tenant Service

Tenant management microservice for Document Management System core onboarding, storage, compliance, and master data.

## Features

- **Tenant Onboarding** (Priority: P1)
- **Storage Configuration** (Priority: P2)
- **Compliance & Retention** (Priority: P2)
- **Folder Management** (Priority: P3)
- **Master Data Management** (Priority: P3)

## Architecture

- **Domain-Driven Design**: Domain, Application, Infrastructure layers
- **Repository Pattern**: Data access abstraction with tenant isolation
- **OpenAPI 3.0**: Contract-first API design
- **Multi-tenant**: Built-in tenant isolation enforcement

## Installation

```bash
cd apps/tenant-service
uv pip install -e ".[dev]"
```

## Running

```bash
uvicorn tenant_service.main:app --reload
```

## API Documentation

Interactive API docs available at: `http://localhost:8000/docs`
