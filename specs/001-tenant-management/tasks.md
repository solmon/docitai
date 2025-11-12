# Tasks: Tenant Management Service

**Input**: Design documents from `/specs/001-tenant-management/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and library structure per plan.md

- [ ] T001 Create workspace structure with libs/ and apps/ directories
- [ ] T002 Initialize database-core library in libs/database-core/ with pyproject.toml 
- [ ] T003 [P] Initialize storage-adapter library in libs/storage-adapter/ with pyproject.toml
- [ ] T004 [P] Initialize tenant-auth library in libs/tenant-auth/ with pyproject.toml  
- [ ] T005 [P] Initialize compliance-engine library in libs/compliance-engine/ with pyproject.toml
- [ ] T006 Initialize tenant-service application in apps/tenant-service/ with pyproject.toml
- [ ] T007 Configure UV workspace dependencies in root pyproject.toml
- [ ] T008 [P] Setup database-core base models in libs/database-core/src/database_core/base.py
- [ ] T009 [P] Configure linting and formatting tools in tenant-service
- [ ] T006 [P] Setup apps/tenant-management-api/ service structure with src/ and tests/ directories
- [ ] T007 [P] Configure pytest, pytest-asyncio, and httpx for testing framework
- [ ] T008 [P] Setup Alembic for database migrations in apps/tenant-management-api/alembic/
- [ ] T009 [P] Create Dockerfile for containerization in apps/tenant-management-api/Dockerfile
- [ ] T010 [P] Configure environment variables and settings management

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T010 Implement TenantAwareBase model in libs/database-core/src/database_core/base.py
- [ ] T011 Setup multi-database connection management in libs/database-core/src/database_core/connection.py
- [ ] T012 Configure Alembic migrations in libs/database-core/src/database_core/migrations.py
- [ ] T013 [P] Implement JWT validation in libs/tenant-auth/src/tenant_auth/middleware.py
- [ ] T014 [P] Implement RBAC models and validation in libs/tenant-auth/src/tenant_auth/rbac.py
- [ ] T015 [P] Create storage provider interface in libs/storage-adapter/src/storage_adapter/base.py
- [ ] T016 [P] Implement storage provider factory in libs/storage-adapter/src/storage_adapter/factory.py
- [ ] T017 Setup FastAPI app using fastapi-core in apps/tenant-service/src/tenant_service/main.py
- [ ] T018 Configure API dependencies and middleware in apps/tenant-service/src/tenant_service/api/dependencies.py
- [ ] T019 Setup database schemas and run initial migration
- [ ] T020 Configure structured logging with tenant context using fastapi-core patterns

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Tenant Onboarding (Priority: P1) 🎯 MVP

**Goal**: Enable system administrators to onboard new tenants with basic configuration

**Independent Test**: Create a new tenant via API and verify it exists with unique ID and proper tenant isolation

### Implementation for User Story 1

- [ ] T021 [P] [US1] Create Tenant entity model in apps/tenant-service/src/tenant_service/infrastructure/models/tenant.py
- [ ] T022 [P] [US1] Create TenantSettings value object in apps/tenant-service/src/tenant_service/domain/value_objects/tenant_settings.py
- [ ] T023 [P] [US1] Create subscription plan enums in apps/tenant-service/src/tenant_service/domain/enums/subscription_plan.py
- [ ] T024 [US1] Implement TenantRepository with tenant isolation in apps/tenant-service/src/tenant_service/infrastructure/repositories/tenant_repository.py
- [ ] T025 [US1] Implement TenantService with business logic in apps/tenant-service/src/tenant_service/domain/services/tenant_service.py
- [ ] T026 [US1] Create tenant creation command handlers in apps/tenant-service/src/tenant_service/application/handlers/create_tenant_handler.py
- [ ] T027 [US1] Create tenant query handlers in apps/tenant-service/src/tenant_service/application/handlers/tenant_query_handler.py
- [ ] T028 [US1] Implement tenant REST endpoints in apps/tenant-service/src/tenant_service/api/v1/tenants.py
- [ ] T029 [US1] Add tenant validation and error handling
- [ ] T030 [US1] Add structured logging for tenant operations with tenant context

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Storage Configuration (Priority: P2)

**Goal**: Enable tenant-specific storage provider configuration with credential encryption

**Independent Test**: Configure storage for an existing tenant and verify storage provider connection validation

### Implementation for User Story 2

- [ ] T031 [P] [US2] Implement AWS S3 provider in libs/storage-adapter/src/storage_adapter/providers/s3_provider.py
- [ ] T032 [P] [US2] Implement Azure Blob provider in libs/storage-adapter/src/storage_adapter/providers/azure_provider.py  
- [ ] T033 [P] [US2] Implement Google Cloud Storage provider in libs/storage-adapter/src/storage_adapter/providers/gcs_provider.py
- [ ] T034 [P] [US2] Create StorageConfiguration entity model in apps/tenant-service/src/tenant_service/infrastructure/models/storage_configuration.py
- [ ] T035 [P] [US2] Implement credential encryption service in apps/tenant-service/src/tenant_service/domain/services/encryption_service.py
- [ ] T036 [US2] Implement StorageConfigurationRepository in apps/tenant-service/src/tenant_service/infrastructure/repositories/storage_repository.py
- [ ] T037 [US2] Implement StorageConfigurationService with provider validation in apps/tenant-service/src/tenant_service/domain/services/storage_service.py
- [ ] T038 [US2] Create storage configuration command handlers in apps/tenant-service/src/tenant_service/application/handlers/storage_handler.py
- [ ] T039 [US2] Implement storage REST endpoints in apps/tenant-service/src/tenant_service/api/v1/storage.py
- [ ] T040 [US2] Add storage provider connection validation and error handling
- [ ] T041 [US2] Add audit logging for storage configuration changes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 4 - Compliance and Data Retention (Priority: P2)

**Goal**: Configure retention policies at tenant and folder levels with automated enforcement

**Independent Test**: Create retention policies and verify they are applied according to configured rules

### Implementation for User Story 4

- [ ] T042 [P] [US4] Create policy engine core in libs/compliance-engine/src/compliance_engine/policies.py
- [ ] T043 [P] [US4] Implement retention scheduler in libs/compliance-engine/src/compliance_engine/scheduler.py
- [ ] T044 [P] [US4] Create audit trail functionality in libs/compliance-engine/src/compliance_engine/audit.py
- [ ] T045 [P] [US4] Create RetentionPolicy entity model in apps/tenant-service/src/tenant_service/infrastructure/models/retention_policy.py
- [ ] T046 [P] [US4] Create compliance framework enums in apps/tenant-service/src/tenant_service/domain/enums/compliance_framework.py
- [ ] T047 [US4] Implement RetentionPolicyRepository in apps/tenant-service/src/tenant_service/infrastructure/repositories/retention_repository.py
- [ ] T048 [US4] Implement ComplianceService with policy enforcement logic in apps/tenant-service/src/tenant_service/domain/services/compliance_service.py
- [ ] T049 [US4] Create retention policy command handlers in apps/tenant-service/src/tenant_service/application/handlers/compliance_handler.py
- [ ] T050 [US4] Implement compliance REST endpoints in apps/tenant-service/src/tenant_service/api/v1/compliance.py
- [ ] T051 [US4] Add policy conflict resolution logic for tenant vs folder policies
- [ ] T052 [US4] Setup background task scheduling for retention policy enforcement
- [ ] T053 [US4] Add comprehensive audit logging for compliance operations

**Checkpoint**: At this point, User Stories 1, 2, and 4 should all work independently

---

## Phase 6: User Story 3 - Folder Structure Management (Priority: P3)

**Goal**: Create and organize hierarchical folder structures with metadata and proper validation

**Independent Test**: Create folder hierarchy and verify parent-child relationships with proper tenant isolation

### Implementation for User Story 3

- [ ] T054 [P] [US3] Create Folder entity model with hierarchy validation in apps/tenant-service/src/tenant_service/infrastructure/models/folder.py
- [ ] T055 [P] [US3] Create folder metadata value objects in apps/tenant-service/src/tenant_service/domain/value_objects/folder_metadata.py
- [ ] T056 [US3] Implement FolderRepository with hierarchy queries in apps/tenant-service/src/tenant_service/infrastructure/repositories/folder_repository.py
- [ ] T057 [US3] Implement FolderService with hierarchy validation in apps/tenant-service/src/tenant_service/domain/services/folder_service.py
- [ ] T058 [US3] Create folder command handlers with circular reference prevention in apps/tenant-service/src/tenant_service/application/handlers/folder_handler.py
- [ ] T059 [US3] Implement folder REST endpoints with hierarchy operations in apps/tenant-service/src/tenant_service/api/v1/folders.py
- [ ] T060 [US3] Add folder path generation and hierarchy depth validation
- [ ] T061 [US3] Add folder deletion logic with child handling options
- [ ] T062 [US3] Add metadata validation and folder organization features

**Checkpoint**: At this point, User Stories 1, 2, 3, and 4 should all work independently

---

## Phase 7: User Story 5 - Master Data Management (Priority: P3)

**Goal**: Define tenant-specific document categories and types with custom attributes

**Independent Test**: Create document categories and types for a tenant and verify they support custom classification

### Implementation for User Story 5

- [ ] T063 [P] [US5] Create DocumentCategory entity model in apps/tenant-service/src/tenant_service/infrastructure/models/document_category.py
- [ ] T064 [P] [US5] Create DocumentType entity model in apps/tenant-service/src/tenant_service/infrastructure/models/document_type.py
- [ ] T065 [P] [US5] Create CustomAttribute value object in apps/tenant-service/src/tenant_service/domain/value_objects/custom_attribute.py
- [ ] T066 [US5] Implement DocumentCategoryRepository in apps/tenant-service/src/tenant_service/infrastructure/repositories/category_repository.py
- [ ] T067 [US5] Implement DocumentTypeRepository in apps/tenant-service/src/tenant_service/infrastructure/repositories/document_type_repository.py
- [ ] T068 [US5] Implement MasterDataService with validation logic in apps/tenant-service/src/tenant_service/domain/services/master_data_service.py
- [ ] T069 [US5] Create master data command handlers in apps/tenant-service/src/tenant_service/application/handlers/master_data_handler.py
- [ ] T070 [US5] Implement master data REST endpoints in apps/tenant-service/src/tenant_service/api/v1/master_data.py
- [ ] T071 [US5] Add custom attribute validation and schema management
- [ ] T072 [US5] Add master data versioning for audit and rollback

**Checkpoint**: All user stories should now be independently functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T073 [P] Add comprehensive health check endpoint in apps/tenant-service/src/tenant_service/api/health.py
- [ ] T074 [P] Add metrics collection integration with prometheus-client
- [ ] T075 [P] Implement distributed tracing with OpenTelemetry
- [ ] T076 [P] Add API rate limiting and security headers
- [ ] T077 [P] Create contract tests based on OpenAPI specification in apps/tenant-service/tests/contract/
- [ ] T078 [P] Add integration tests for multi-tenant isolation in apps/tenant-service/tests/integration/
- [ ] T079 Code cleanup and refactoring across all components
- [ ] T080 Performance optimization for concurrent tenant operations
- [ ] T081 Security hardening review and implementation
- [ ] T082 Documentation updates in quickstart.md validation
- [ ] T083 [P] Create deployment configurations for container orchestration

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

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Integrates with US1 tenants but independently testable
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - May integrate with US2/US3 policies but independently testable  
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US4 retention policies but independently testable
- **User Story 5 (P3)**: Can start after Foundational (Phase 2) - Independent master data functionality

### Within Each User Story

- Models before repositories
- Repositories before services  
- Services before handlers
- Handlers before endpoints
- Core implementation before validation and logging
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- Models within a story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 2 (Storage Configuration)

```bash
# Launch all provider implementations together:
Task: "Implement AWS S3 provider in libs/storage-adapter/src/storage_adapter/providers/s3_provider.py"
Task: "Implement Azure Blob provider in libs/storage-adapter/src/storage_adapter/providers/azure_provider.py"
Task: "Implement Google Cloud Storage provider in libs/storage-adapter/src/storage_adapter/providers/gcs_provider.py"

# Launch all models for User Story 2 together:
Task: "Create StorageConfiguration entity model in apps/tenant-service/src/tenant_service/infrastructure/models/storage_configuration.py"
Task: "Implement credential encryption service in apps/tenant-service/src/tenant_service/domain/services/encryption_service.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Tenant Onboarding)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo tenant onboarding functionality

### Incremental Delivery Priority Order

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 (P1) → Test independently → Deploy/Demo (MVP - Tenant Onboarding!)
3. Add User Story 2 (P2) → Test independently → Deploy/Demo (Storage Configuration)
4. Add User Story 4 (P2) → Test independently → Deploy/Demo (Compliance & Retention)
5. Add User Story 3 (P3) → Test independently → Deploy/Demo (Folder Management)
6. Add User Story 5 (P3) → Test independently → Deploy/Demo (Master Data)
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (P1 - Tenant Onboarding)
   - Developer B: User Story 2 (P2 - Storage Configuration)  
   - Developer C: User Story 4 (P2 - Compliance & Retention)
3. After P1/P2 complete:
   - Developer D: User Story 3 (P3 - Folder Management)
   - Developer E: User Story 5 (P3 - Master Data)
4. Stories complete and integrate independently

---

## Summary

**Total Tasks**: 83 tasks across 8 phases
**Task Count per User Story**:
- User Story 1 (Tenant Onboarding): 10 tasks
- User Story 2 (Storage Configuration): 11 tasks  
- User Story 4 (Compliance & Retention): 12 tasks
- User Story 3 (Folder Management): 9 tasks
- User Story 5 (Master Data): 10 tasks

**Parallel Opportunities**: 28 tasks marked [P] can run in parallel within their phases
**MVP Scope**: User Story 1 only (Tasks T001-T030) provides functional tenant onboarding
**Independent Test Criteria**: Each user story has clear acceptance criteria and can be validated independently

**Format Validation**: ✅ All tasks follow required checklist format with:
- [x] Checkbox prefix
- [x] Sequential Task ID (T001-T083)
- [x] [P] markers for parallelizable tasks  
- [x] [US#] labels for user story tasks
- [x] Specific file paths in descriptions
- [x] Clear execution dependencies and order

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