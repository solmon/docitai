# Tasks: Tenant Management Service for Document Management System

**Input**: Design documents from `/specs/001-tenant-management/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT requested in the feature specification, focusing on implementation only.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

Following the Library-First principle from plan.md:
- **Libraries**: `libs/[library-name]/src/` and `libs/[library-name]/tests/`
- **API Service**: `apps/tenant-management-api/src/` and `apps/tenant-management-api/tests/`
- **Infrastructure**: `infra/`, `alembic/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure following Library-First architecture

- [ ] T001 Create project directory structure per implementation plan
- [ ] T002 Initialize Python 3.11+ project with pyproject.toml and requirements.txt
- [ ] T003 [P] Setup libs/tenant-management/ library structure with src/ and tests/ directories
- [ ] T004 [P] Setup libs/storage-abstraction/ library structure with src/ and tests/ directories
- [ ] T005 [P] Setup libs/rbac-enforcement/ library structure with src/ and tests/ directories
- [ ] T006 [P] Setup apps/tenant-management-api/ service structure with src/ and tests/ directories
- [ ] T007 [P] Configure pytest, pytest-asyncio, and httpx for testing framework
- [ ] T008 [P] Setup Alembic for database migrations in apps/tenant-management-api/alembic/
- [ ] T009 [P] Create Dockerfile for containerization in apps/tenant-management-api/Dockerfile
- [ ] T010 [P] Configure environment variables and settings management

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T011 Create base entity classes in libs/tenant-management/src/domain/base.py
- [ ] T012 [P] Setup database connection and SQLModel configuration in apps/tenant-management-api/src/config/database.py
- [ ] T013 [P] Implement JWT authentication middleware in libs/rbac-enforcement/src/middleware/auth.py
- [ ] T014 [P] Create RBAC permission decorators in libs/rbac-enforcement/src/decorators/permissions.py
- [ ] T015 [P] Setup tenant isolation middleware in apps/tenant-management-api/src/middleware/tenant.py
- [ ] T016 [P] Implement storage provider interfaces in libs/storage-abstraction/src/interfaces/provider.py
- [ ] T017 [P] Create encryption service for credentials in libs/tenant-management/src/infrastructure/encryption.py
- [ ] T018 Setup FastAPI application factory in apps/tenant-management-api/src/main.py
- [ ] T019 [P] Configure structured logging with tenant context in apps/tenant-management-api/src/config/logging.py
- [ ] T020 [P] Setup error handling and exception middleware in apps/tenant-management-api/src/middleware/errors.py

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Tenant Onboarding (Priority: P1) 🎯 MVP

**Goal**: Enable system administrators to onboard new tenants with basic information and subscription plans

**Independent Test**: Create a new tenant via API and verify it appears in tenant list with unique ID

### Implementation for User Story 1

- [ ] T021 [P] [US1] Create Tenant entity in libs/tenant-management/src/domain/entities/tenant.py
- [ ] T022 [P] [US1] Create TenantSettings value object in libs/tenant-management/src/domain/value_objects/tenant_settings.py
- [ ] T023 [P] [US1] Create subscription plan enums in libs/tenant-management/src/domain/enums/subscription.py
- [ ] T024 [US1] Implement TenantRepository interface in libs/tenant-management/src/domain/repositories/tenant_repository.py
- [ ] T025 [US1] Implement TenantRepository SQLModel implementation in libs/tenant-management/src/infrastructure/repositories/sqlmodel_tenant_repository.py
- [ ] T026 [US1] Create TenantService for business logic in libs/tenant-management/src/application/services/tenant_service.py
- [ ] T027 [US1] Create tenant request/response schemas in apps/tenant-management-api/src/api/schemas/tenant_schemas.py
- [ ] T028 [US1] Implement tenant management endpoints in apps/tenant-management-api/src/api/routers/tenants.py
- [ ] T029 [US1] Create database migration for tenant table in apps/tenant-management-api/alembic/versions/001_create_tenant_table.py
- [ ] T030 [US1] Add tenant validation and business rules in TenantService

**Checkpoint**: At this point, User Story 1 should be fully functional - tenants can be created, retrieved, updated, and listed

---

## Phase 4: User Story 2 - Storage Configuration (Priority: P2)

**Goal**: Enable administrators to configure cloud storage providers (Azure Blob, AWS S3, GCS) for tenants

**Independent Test**: Configure storage for an existing tenant and validate connection to storage provider

### Implementation for User Story 2

- [ ] T031 [P] [US2] Create StorageConfiguration entity in libs/tenant-management/src/domain/entities/storage_config.py
- [ ] T032 [P] [US2] Create cloud storage provider enums in libs/storage-abstraction/src/enums/providers.py
- [ ] T033 [P] [US2] Implement Azure Blob provider in libs/storage-abstraction/src/providers/azure_blob_provider.py
- [ ] T034 [P] [US2] Implement AWS S3 provider in libs/storage-abstraction/src/providers/aws_s3_provider.py
- [ ] T035 [P] [US2] Implement Google Cloud Storage provider in libs/storage-abstraction/src/providers/gcs_provider.py
- [ ] T036 [US2] Create StorageProviderFactory in libs/storage-abstraction/src/factories/provider_factory.py
- [ ] T037 [US2] Implement StorageConfigRepository interface in libs/tenant-management/src/domain/repositories/storage_config_repository.py
- [ ] T038 [US2] Implement StorageConfigRepository SQLModel implementation in libs/tenant-management/src/infrastructure/repositories/sqlmodel_storage_config_repository.py
- [ ] T039 [US2] Create StorageConfigService with validation logic in libs/tenant-management/src/application/services/storage_config_service.py
- [ ] T040 [US2] Create storage configuration schemas in apps/tenant-management-api/src/api/schemas/storage_schemas.py
- [ ] T041 [US2] Implement storage configuration endpoints in apps/tenant-management-api/src/api/routers/storage_config.py
- [ ] T042 [US2] Create database migration for storage_configuration table in apps/tenant-management-api/alembic/versions/002_create_storage_config_table.py
- [ ] T043 [US2] Add storage provider connection validation service

**Checkpoint**: Storage configuration should work independently - tenants can have storage configured and validated

---

## Phase 5: User Story 4 - Compliance and Data Retention (Priority: P2)

**Goal**: Enable configuration of data retention and compliance policies at tenant and folder levels

**Independent Test**: Configure retention policies and verify automatic policy enforcement logic

### Implementation for User Story 4

- [ ] T044 [P] [US4] Create RetentionPolicy entity in libs/tenant-management/src/domain/entities/retention_policy.py
- [ ] T045 [P] [US4] Create compliance framework enums in libs/tenant-management/src/domain/enums/compliance.py
- [ ] T046 [P] [US4] Create policy scope enums in libs/tenant-management/src/domain/enums/policy_scope.py
- [ ] T047 [US4] Implement RetentionPolicyRepository interface in libs/tenant-management/src/domain/repositories/retention_policy_repository.py
- [ ] T048 [US4] Implement RetentionPolicyRepository SQLModel implementation in libs/tenant-management/src/infrastructure/repositories/sqlmodel_retention_policy_repository.py
- [ ] T049 [US4] Create RetentionPolicyService with conflict resolution in libs/tenant-management/src/application/services/retention_policy_service.py
- [ ] T050 [US4] Create retention policy schemas in apps/tenant-management-api/src/api/schemas/retention_policy_schemas.py
- [ ] T051 [US4] Implement retention policy endpoints in apps/tenant-management-api/src/api/routers/retention_policies.py
- [ ] T052 [US4] Create database migration for retention_policy table in apps/tenant-management-api/alembic/versions/003_create_retention_policy_table.py
- [ ] T053 [US4] Add policy conflict detection and resolution logic

**Checkpoint**: Retention policies should work independently - policies can be created and conflict resolution works

---

## Phase 6: User Story 3 - Folder Structure Management (Priority: P3)

**Goal**: Enable creation and organization of hierarchical folder structures for tenants

**Independent Test**: Create folder hierarchy and verify parent-child relationships with metadata

### Implementation for User Story 3

- [ ] T054 [P] [US3] Create Folder entity in libs/tenant-management/src/domain/entities/folder.py
- [ ] T055 [P] [US3] Create folder hierarchy validation service in libs/tenant-management/src/domain/services/folder_hierarchy_service.py
- [ ] T056 [US3] Implement FolderRepository interface in libs/tenant-management/src/domain/repositories/folder_repository.py
- [ ] T057 [US3] Implement FolderRepository SQLModel implementation in libs/tenant-management/src/infrastructure/repositories/sqlmodel_folder_repository.py
- [ ] T058 [US3] Create FolderService with hierarchy management in libs/tenant-management/src/application/services/folder_service.py
- [ ] T059 [US3] Create folder schemas in apps/tenant-management-api/src/api/schemas/folder_schemas.py
- [ ] T060 [US3] Implement folder management endpoints in apps/tenant-management-api/src/api/routers/folders.py
- [ ] T061 [US3] Create database migration for folder table in apps/tenant-management-api/alembic/versions/004_create_folder_table.py
- [ ] T062 [US3] Add circular reference prevention and path generation logic

**Checkpoint**: Folder management should work independently - hierarchical folders can be created and managed

---

## Phase 7: User Story 5 - Master Data Management (Priority: P3)

**Goal**: Enable definition of document categories and types with custom attributes for tenant-specific taxonomy

**Independent Test**: Define document categories and types, verify custom attributes work for document classification

### Implementation for User Story 5

- [ ] T063 [P] [US5] Create DocumentCategory entity in libs/tenant-management/src/domain/entities/document_category.py
- [ ] T064 [P] [US5] Create DocumentType entity in libs/tenant-management/src/domain/entities/document_type.py
- [ ] T065 [P] [US5] Create CustomAttribute value object in libs/tenant-management/src/domain/value_objects/custom_attribute.py
- [ ] T066 [US5] Implement DocumentCategoryRepository interface in libs/tenant-management/src/domain/repositories/document_category_repository.py
- [ ] T067 [US5] Implement DocumentTypeRepository interface in libs/tenant-management/src/domain/repositories/document_type_repository.py
- [ ] T068 [US5] Implement DocumentCategoryRepository SQLModel implementation in libs/tenant-management/src/infrastructure/repositories/sqlmodel_document_category_repository.py
- [ ] T069 [US5] Implement DocumentTypeRepository SQLModel implementation in libs/tenant-management/src/infrastructure/repositories/sqlmodel_document_type_repository.py
- [ ] T070 [US5] Create DocumentCategoryService in libs/tenant-management/src/application/services/document_category_service.py
- [ ] T071 [US5] Create DocumentTypeService in libs/tenant-management/src/application/services/document_type_service.py
- [ ] T072 [US5] Create master data schemas in apps/tenant-management-api/src/api/schemas/master_data_schemas.py
- [ ] T073 [US5] Implement document category endpoints in apps/tenant-management-api/src/api/routers/document_categories.py
- [ ] T074 [US5] Implement document type endpoints in apps/tenant-management-api/src/api/routers/document_types.py
- [ ] T075 [US5] Create database migrations for master data tables in apps/tenant-management-api/alembic/versions/005_create_master_data_tables.py

**Checkpoint**: Master data management should work independently - categories and types can be defined with custom attributes

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and system-wide enhancements

- [ ] T076 [P] Add comprehensive error handling across all endpoints
- [ ] T077 [P] Implement API versioning and OpenAPI documentation generation
- [ ] T078 [P] Add tenant-aware metrics collection for observability
- [ ] T079 [P] Implement audit logging for all administrative operations
- [ ] T080 [P] Add health check endpoints for monitoring
- [ ] T081 [P] Setup Docker Compose for local development environment
- [ ] T082 [P] Create Kubernetes deployment manifests in infra/k8s/
- [ ] T083 Performance optimization and database indexing
- [ ] T084 Security hardening and credential encryption validation
- [ ] T085 Integration validation with quickstart.md scenarios

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-7)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P2 → P3 → P3)
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 - Tenant Onboarding (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 - Storage Configuration (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 (requires existing tenants)
- **User Story 4 - Compliance and Data Retention (P2)**: Can start after Foundational (Phase 2) - Can work with US3 for folder-level policies
- **User Story 3 - Folder Structure Management (P3)**: Can start after Foundational (Phase 2) - May reference US4 policies
- **User Story 5 - Master Data Management (P3)**: Can start after Foundational (Phase 2) - Independent of other stories

### Within Each User Story

- Domain entities and value objects before repositories
- Repository interfaces before implementations
- Services before API endpoints
- Database migrations alongside entity creation
- Core implementation before integration features

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Domain entities within a story marked [P] can run in parallel
- Provider implementations in US2 marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1 (Tenant Onboarding)

```bash
# Launch all domain objects for User Story 1 together:
Task T021: "Create Tenant entity in libs/tenant-management/src/domain/entities/tenant.py"
Task T022: "Create TenantSettings value object in libs/tenant-management/src/domain/value_objects/tenant_settings.py"
Task T023: "Create subscription plan enums in libs/tenant-management/src/domain/enums/subscription.py"

# After domain objects, launch service layer:
Task T024: "Implement TenantRepository interface"
Task T025: "Implement TenantRepository SQLModel implementation"
```

## Parallel Example: User Story 2 (Storage Configuration)

```bash
# Launch all storage providers together:
Task T033: "Implement Azure Blob provider"
Task T034: "Implement AWS S3 provider" 
Task T035: "Implement Google Cloud Storage provider"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 - Tenant Onboarding
4. **STOP and VALIDATE**: Test tenant creation, retrieval, update independently
5. Deploy/demo basic tenant management capability

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP - Basic tenant management)
3. Add User Story 2 → Test independently → Deploy/Demo (Tenant management + Storage configuration)
4. Add User Story 4 → Test independently → Deploy/Demo (+ Compliance policies)
5. Add User Story 3 → Test independently → Deploy/Demo (+ Folder organization)
6. Add User Story 5 → Test independently → Deploy/Demo (+ Master data management)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational phase completion:

1. **Developer A**: User Story 1 (Tenant Onboarding) - Highest priority
2. **Developer B**: User Story 2 (Storage Configuration) - High priority, integrates with A
3. **Developer C**: User Story 4 (Compliance/Retention) - High priority, independent
4. **Developer D**: User Story 3 (Folder Management) - Medium priority
5. **Developer E**: User Story 5 (Master Data) - Medium priority, independent

Stories complete and integrate independently, enabling continuous deployment.

---

## Summary

- **Total Tasks**: 85 tasks across 8 phases
- **Task Distribution**: 
  - Setup: 10 tasks
  - Foundational: 10 tasks  
  - US1 (Tenant Onboarding): 10 tasks
  - US2 (Storage Configuration): 13 tasks
  - US4 (Compliance/Retention): 10 tasks
  - US3 (Folder Management): 9 tasks
  - US5 (Master Data): 13 tasks
  - Polish: 10 tasks
- **Parallel Opportunities**: 45+ tasks marked [P] for parallel execution
- **Independent Test Criteria**: Each user story has clear acceptance criteria and can be validated independently
- **MVP Scope**: User Story 1 (Tenant Onboarding) provides foundational tenant management capability
- **Library-First Architecture**: Tasks organized to build reusable libraries before service composition

All tasks follow the required checklist format with IDs, parallel markers, story labels, and exact file paths for immediate execution.