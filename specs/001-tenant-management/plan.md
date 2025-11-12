````markdown
# Implementation Plan: Tenant Management Service

**Branch**: `001-tenant-management` | **Date**: 2025-11-12 | **Spec**: [./spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-tenant-management/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Primary requirement: Build a microservice for tenant management in a document management system, supporting multi-tenancy, storage configuration, folder organization, and compliance policies. The service will expose RESTful APIs following DDD principles with FastAPI, SQLModel, and Pydantic, supporting both SQL Server and PostgreSQL databases. Technical approach emphasizes reusable libraries, async operations, and strict tenant isolation following the established monorepo architecture with fastapi-core library integration.

## Technical Context

**Language/Version**: Python 3.12+ (aligned with workspace requirements)  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic, Alembic (migrations), PyJWT (auth)  
**Storage**: PostgreSQL (primary), SQL Server (alternative) - multi-database support via SQLModel  
**Testing**: pytest with async support, contract testing, integration tests  
**Target Platform**: Linux containers, Kubernetes deployments, cloud-agnostic  
**Project Type**: Microservice with library-first architecture  
**Performance Goals**: 1000+ concurrent requests/second, <200ms p95 latency  
**Constraints**: <200ms p95 response time, strict tenant isolation, RBAC enforcement  
**Scale/Scope**: 1000+ tenants simultaneously, hierarchical folder structures up to 10 levels

**Architecture Decisions**:
- **Monorepo Integration**: Use existing uv workspace with individual project dependencies
- **Library Strategy**: Leverage fastapi-core for common FastAPI abstractions, create reusable libraries for cross-cutting concerns (auth, storage, compliance)
- **Database Support**: SQLModel provides abstraction for both PostgreSQL and SQL Server
- **Async Operations**: Full async/await pattern for database and external API calls
- **Dependency Management**: Project-specific dependencies in individual pyproject.toml, shared dependencies in workspace root

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Library-First**: Design emphasizes reusable libraries (storage abstraction, compliance engine, auth middleware) before service implementation  
✅ **Cloud Agnostic**: SQLModel provides database abstraction, storage configurations support multiple providers via adapter pattern  
✅ **Observability**: FastAPI-core provides structured logging, metrics, and tracing foundations; tenant-aware logging required  
✅ **Security by Design**: RBAC enforcement at API boundaries, tenant isolation in data model, encrypted credentials storage  
✅ **Role-Based Access Control**: Tenant-scoped permissions, inheritance from tenant to folder level, audit trail for all administrative actions  
✅ **Multi-Tenant Architecture**: All entities include tenant_id, cross-tenant access prevention, tenant-aware observability and configuration

**Pre-Phase 0 Status**: ✅ APPROVED - All constitution principles satisfied by design

**Post-Phase 1 Re-evaluation**:
✅ **Library-First**: Four new libraries created (storage-adapter, tenant-auth, compliance-engine, database-core) with focused responsibilities  
✅ **Cloud Agnostic**: Storage-adapter library implements provider pattern for AWS S3, Azure Blob, GCS with no runtime dependencies  
✅ **Observability**: Integration with fastapi-core logging, tenant-aware structured logs, metrics collection via prometheus-client  
✅ **Security by Design**: Encrypted storage credentials, JWT validation, RBAC middleware, audit trails in all operations  
✅ **Role-Based Access Control**: Hierarchical roles (System Admin, Tenant Admin, Folder Manager) with permission inheritance  
✅ **Multi-Tenant Architecture**: All data models include tenant_id, repository pattern enforces isolation, tenant-aware logging

**Final Status**: ✅ APPROVED - Design maintains constitution compliance with library-first implementation

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Microservice Application
apps/
└── tenant-service/
    ├── pyproject.toml          # Project-specific dependencies only
    ├── src/
    │   └── tenant_service/
    │       ├── main.py         # FastAPI app using fastapi-core
    │       ├── api/            # REST endpoints
    │       │   ├── v1/
    │       │   │   ├── tenants.py
    │       │   │   ├── storage.py
    │       │   │   ├── folders.py
    │       │   │   └── compliance.py
    │       │   └── dependencies.py
    │       ├── domain/         # DDD domain layer
    │       │   ├── entities/
    │       │   ├── value_objects/
    │       │   ├── aggregates/
    │       │   └── services/
    │       ├── application/    # Use cases and app services
    │       │   ├── commands/
    │       │   ├── queries/
    │       │   └── handlers/
    │       └── infrastructure/ # Data access and external integrations
    │           ├── repositories/
    │           ├── models/     # SQLModel ORM models
    │           └── adapters/
    └── tests/
        ├── contract/           # OpenAPI contract tests
        ├── integration/        # Database and external API tests
        └── unit/              # Domain and service unit tests

# Reusable Libraries (leveraging existing fastapi-core)
libs/
├── fastapi-core/              # Existing - FastAPI abstractions
├── storage-adapter/           # NEW - Multi-provider storage abstraction
│   ├── pyproject.toml
│   └── src/
│       └── storage_adapter/
│           ├── base.py        # Provider interface
│           ├── providers/     # S3, Azure Blob, GCS adapters
│           └── config.py
├── tenant-auth/               # NEW - Tenant-aware authentication
│   ├── pyproject.toml
│   └── src/
│       └── tenant_auth/
│           ├── rbac.py        # Role-based access control
│           ├── middleware.py  # FastAPI middleware
│           └── models.py
├── compliance-engine/         # NEW - Retention and compliance policies
│   ├── pyproject.toml
│   └── src/
│       └── compliance_engine/
│           ├── policies.py    # Policy definition and enforcement
│           ├── scheduler.py   # Retention policy execution
│           └── audit.py       # Audit trail functionality
└── database-core/             # NEW - Multi-database SQLModel support
    ├── pyproject.toml
    └── src/
        └── database_core/
            ├── base.py        # Base model with tenant_id
            ├── connection.py  # Multi-DB connection management
            └── migrations.py  # Alembic integration
```

**Structure Decision**: Microservice architecture with library-first approach. The tenant-service application assembles reusable libraries, each with focused responsibilities. Individual pyproject.toml files contain project-specific dependencies while shared dependencies remain in workspace root. This follows the established uv monorepo pattern and constitution requirements for library-first design and reusability.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations detected. All design decisions align with constitution principles:

- Library-first architecture successfully implemented
- Cloud provider abstraction maintains portability
- Multi-tenant design ensures strict isolation
- RBAC implementation provides comprehensive security
- Observability integrated throughout the stack

## Phase Completion Status

**Phase 0** ✅ **COMPLETE**: Research findings documented in [research.md](./research.md)
- Multi-database strategy with SQLModel async support
- Storage provider abstraction with async context managers  
- Tenant-aware RBAC with hierarchical permissions
- Compliance engine with automated policy enforcement
- Monorepo integration with UV workspace and individual pyproject.toml files

**Phase 1** ✅ **COMPLETE**: Design artifacts generated
- Data model: [data-model.md](./data-model.md) - SQLModel entities with tenant isolation
- API contracts: [contracts/openapi.yaml](./contracts/openapi.yaml) - RESTful API specification
- Quickstart guide: [quickstart.md](./quickstart.md) - Development and usage documentation
- Agent context: Updated via `.specify/scripts/bash/update-agent-context.sh`

**Phase 2**: Ready for task generation via `/speckit.tasks` command

## Generated Artifacts Summary

1. **Research Documentation**: Technical decisions for multi-database, storage abstraction, authentication, and compliance
2. **Data Model**: SQLModel entities using library-first approach with tenant isolation and RBAC support
3. **API Contracts**: OpenAPI 3.0 specification with comprehensive endpoint coverage and security schemes
4. **Implementation Guide**: Detailed quickstart with library integration examples and production considerations
5. **Agent Context**: Updated copilot-instructions.md with new technology stack and architectural decisions

**Next Steps**: Execute `/speckit.tasks` to generate implementation tasks based on this plan and design artifacts.
