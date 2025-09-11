# Tasks: Multitenant Document Management System (DMS)

**Input**: Design documents from `/specs/001-multitenant-document-management/`
**Prerequisites**: `plan.md`, `research.md`, `data-model.md`, `contracts/openapi.yaml`

## Execution Flow
- Tests-first (TDD): write failing contract & integration tests, then implement code to make them pass.
- Mark `[P]` for tasks that can run in parallel (different files/no dependency).

Format: `[ID] [P?] Description` (paths relative to repo root)

---

## Phase 3.1: Setup
- T001 Initialize repo layout for feature (backend/, frontend/, backend/prisma/) and create `backend/` and `frontend/` packages (monorepo). Path: `backend/`, `frontend/`.
- T002 Initialize backend package and install core deps: `backend/package.json` (NestJS + Fastify, Prisma, OpenFGA client, passport.js, storage SDKs). Path: `backend/package.json`.
- T003 Configure linting, formatting, CI skeleton, and repo scripts (ESLint, Prettier, pnpm workspace). Files: `.eslintrc`, `.prettierrc`, `.github/workflows/ci.yml`.
 - T003 Configure linting, formatting, CI skeleton, and repo scripts (ESLint, Prettier, pnpm workspace). Files: `.eslintrc`, `.prettierrc`, `.github/workflows/ci.yml`.
 - T004 [P] Frontend setup: initialize `frontend/` Next.js app, install Tailwind, Radix UI, shadcn components, Chart.js, and create base theme scaffolding (`frontend/package.json`, `frontend/tailwind.config.js`, `frontend/src/components/ui/*`).

---

## Phase 3.2: Tests First (TDD) ⚠️ MUST COMPLETE BEFORE ANY IMPLEMENTATION
CRITICAL: These tests MUST be created and MUST FAIL before the implementation tasks.

# Contract tests (derived from `specs/001-multitenant-document-management/contracts/openapi.yaml`)
- T004 [P] Contract test: List documents — `tests/contract/documents.list.test.js` — target endpoint: `GET /tenants/{tenantId}/documents` (use `specs/001-multitenant-document-management/contracts/openapi.yaml`).
- T005 [P] Contract test: Upload document — `tests/contract/documents.upload.test.js` — target endpoint: `POST /tenants/{tenantId}/documents` (multipart). Validate response codes and headers.
- T006 [P] Contract test: Download/preview — `tests/contract/documents.download.test.js` — target endpoint: `GET /tenants/{tenantId}/documents/{documentId}`.
- T007 [P] Contract test: Permissions enforcement — `tests/contract/documents.permissions.test.js` — ensure 403 for unauthorized users and 200 for permitted users.

# Integration tests (tenant-level behavior)
- T008 [P] Integration test: Tenant isolation — `tests/integration/tenant_isolation.test.js` — validate tenant A cannot see tenant B documents.
- T009 [P] Integration test: Permission inheritance & override — `tests/integration/permission_inheritance.test.js` — verify parent->child cascade and explicit override behavior.
- T010 [P] Integration test: Bulk upload & bulk download flow — `tests/integration/bulk_ops.test.js` — upload ZIP or simulate batch API, request ZIP download, validate manifest and per-file access checks.
- T011 [P] Integration test: Audit events logged — `tests/integration/audit_events.test.js` — verify Upload/Delete/View/Search produce AuditEvent with required fields in DB.
- T012 [P] Integration test: Search indexing (metadata) — `tests/integration/search_indexing.test.js` — index document metadata and search via API; expect found results.

Notes: Contract tests reference `specs/001-multitenant-document-management/contracts/openapi.yaml`. Integration tests should run against a test environment (Docker Compose or testcontainers) using real Postgres and a local storage adapter stub.

---

## Phase 3.3: Core Implementation (ONLY after tests exist and fail)
Order: implement minimal infra to make tests run and fail-green sequentially per dependency.

- T013 [P] Prisma schema and initial migration — `backend/prisma/schema.prisma` (Tenant, User, Role, Group, Folder, Document, AuditEvent, StorageObject). Run `pnpm --filter backend prisma migrate dev`.
- T014 [P] Generate Prisma Client — `backend/node_modules/.prisma` (dev step: `pnpm --filter backend prisma generate`).
- T015 [P] Implement model layer / entities — `backend/src/models/*` (one file per entity: `tenant.model.ts`, `user.model.ts`, `document.model.ts`, `folder.model.ts`, `audit.model.ts`).
- T016 [P] Storage adapter interface & provider stubs — `backend/src/adapters/storage-adapter.ts`, `backend/src/adapters/azure.adapter.ts`, `backend/src/adapters/s3.adapter.ts`, `backend/src/adapters/gcs.adapter.ts`.
- T017 [P] Implement `DocumentService` (upload, download, list, metadata) — `backend/src/services/document.service.ts`.
- T018 [P] Implement `PermissionsService` (OpenFGA client wrapper) — `backend/src/services/permissions.service.ts`.
- T019 [P] Implement `AuditService` to write AuditEvent → DB (and optional forwarder to ELK) — `backend/src/services/audit.service.ts`.
- T020 [P] Implement `SearchService` (metadata indexing + optional full-text interface) — `backend/src/services/search.service.ts`.
- T021 [P] Implement `PreviewService` (generate previews for supported types) — `backend/src/services/preview.service.ts` (can be async worker).
- T022 [P] Controllers / endpoints per contract — `backend/src/controllers/documents.controller.ts` (implement routes matching openapi.yaml).
- T023 Auth middleware/tenant context extraction (OIDC/JWT) — `backend/src/middleware/auth.middleware.ts` (ensures `tenantId` present in request context).

Implementation notes:
- Keep services small and testable. Each service file should have its own unit tests (Phase 3.5).
- Use dependency injection in NestJS modules.

---

## Phase 3.4: Integration & Async Workflows
- T024 Connect DocumentService to storage adapters and implement per-tenant storage mapping — `backend/src/config/storage.ts`.
- T025 Implement asynchronous indexer worker and queue (RabbitMQ/Redis queues) — `backend/src/workers/indexer.worker.ts`.
- T026 Implement bulk ZIP generator and download endpoint — `backend/src/services/bulk.service.ts`, temporary object location config.
- T027 Implement resumable/chunked upload protocol and server handlers — `backend/src/services/upload.resumable.ts` and `backend/src/controllers/upload.controller.ts`.
- T028 Hook audit writes into service operation paths and ensure transactional ordering where practical — `backend/src/hooks/audit.hook.ts`.

---

## Phase 3.5: Frontend (basic flows) — create failing integration tests before heavy UI work
- T029 [P] Frontend contract/integration test: Document list page (`frontend/src/pages/tenant/[tenantId]/documents.tsx`) — `tests/integration/frontend_documents.test.js`.
- T030 [P] Frontend: Upload form and folder navigation components — `frontend/src/components/upload/*`, `frontend/src/components/folder/*`.
- T031 [P] Frontend: Preview component integration — `frontend/src/components/preview/*`.

---

## Phase 3.6: Observability, Security & Operations
- T032 [P] Structured logging and metrics instrumentation — `backend/src/lib/logging.ts`, `backend/src/lib/metrics.ts`.
- T033 [P] Audit retention and export job (configurable per tenant) — `backend/src/services/auditRetention.ts`.
- T034 [P] CI: Add contract & integration job steps in `.github/workflows/ci.yml` to run tests and fail the pipeline on regressions.
- T035 [P] Security review checklist and automated linters (secret scanning, dependency audits).

---

## Phase 3.7: Polish & Acceptance
- T036 [P] Unit tests for all services and edge cases — `tests/unit/**`.
- T037 [P] Update `specs/001-multitenant-document-management/quickstart.md` with exact commands and CI dev notes.
- T038 [P] Generate API docs from OpenAPI and publish under `docs/api/`.
- T039 [P] Complete compliance documentation and data processing agreements for GDPR/HIPAA where applicable.
- T040 Release: bump version, changelog, and prepare deployment manifests for Kubernetes — `deploy/` (helm/chart templates).

---

## Dependencies & Ordering (high level)
- All contract tests (T004-T007) and integration tests (T008-T012) MUST exist and fail before core implementation (T013-T023) starts.
- T013 (Prisma schema) must be in place before model implementation T015 and DB-backed integration tests T026.
- Storage adapter implementation (T016) is required before bulk ops (T026) and downloads (T022).
- PermissionsService (T018) and AuditService (T019) must be integrated early to ensure tests validate security and audit logging.

## Parallel Execution Examples
- Launch T004-T012 in parallel to create failing tests across contracts and integrations.
- Run T013 & T016 in parallel (schema + adapter scaffolding) because they touch different files.

## Validation Checklist (GATE before claiming done)
- [ ] Each contract in `specs/.../contracts/` has a corresponding contract test in `tests/contract/`.
- [ ] Each entity in `data-model.md` has a model creation task.
- [ ] All critical integration tests exist for tenant isolation, permission inheritance, bulk ops, audit, and search.
- [ ] Tests fail first, then implementation makes them pass.

---

When you want, I can now:
- scaffold selected files (Prisma schema, contract test files, backend module skeleton) and run the contract tests to show failing results, or
- push this `tasks.md` and open a PR draft.
