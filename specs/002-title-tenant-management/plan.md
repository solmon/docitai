# Implementation Plan: Tenant Management Service

**Branch**: `002-title-tenant-management` | **Date**: 2025-10-24 | **Spec**: `/home/solmon/github/docitai/specs/002-title-tenant-management/spec.md`
**Input**: Feature specification from `/home/solmon/github/docitai/specs/002-title-tenant-management/spec.md`

## Execution Flow (/plan command scope)
```
1. Load feature spec from Input path
   → If not found: ERROR "No feature spec at {path}"
2. Fill Technical Context (scan for NEEDS CLARIFICATION)
   → Detect Project Type from context (web=frontend+backend, mobile=app+api)
   → Set Structure Decision based on project type
3. Evaluate Constitution Check section below
   → If violations exist: Document in Complexity Tracking
   → If no justification possible: ERROR "Simplify approach first"
   → Update Progress Tracking: Initial Constitution Check
4. Execute Phase 0 → research.md
   → If NEEDS CLARIFICATION remain: ERROR "Resolve unknowns"
5. Execute Phase 1 → contracts, data-model.md, quickstart.md, agent-specific template file (e.g., `CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for GitHub Copilot, or `GEMINI.md` for Gemini CLI).
6. Re-evaluate Constitution Check section
   → If new violations: Refactor design, return to Phase 1
   → Update Progress Tracking: Post-Design Constitution Check
7. Plan Phase 2 → Describe task generation approach (DO NOT create tasks.md)
8. STOP - Ready for /tasks command
```

**IMPORTANT**: The /plan command STOPS at step 7. Phases 2-4 are executed by other commands:
- Phase 2: /tasks command creates tasks.md
- Phase 3-4: Implementation execution (manual or via tools)

## Summary
Primary requirement: Provide Tenant (District) lifecycle management for the DMS, enabling Super Admins to onboard tenants, configure tenant storage, and allow Tenant Admins to manage users and retention policies. The service must ensure tenant data segregation, auditability, and retention policy enforcement.

Technical approach (from Phase 0 research decisions): implement as a standalone backend service (tenant-service) following the repository's constitutional constraints (API-first, OpenAPI contracts, NestJS + Prisma + Postgres). Support both existing-storage identifiers and optional provisioning orchestration; retention supports archive/delete/mark_expired with legal-hold semantics. Defaults and open items are documented in `research.md`.

## Technical Context
**Language/Version**: TypeScript / Node.js (NestJS) — aligns with repo constitution
**Primary Dependencies**: NestJS (Fastify), Prisma ORM, OpenAPI (OpenAPI 3.0), OpenFGA for authorization (tenant-aware), Postgres for primary data store
**Storage**: Postgres for metadata; object storage (S3/GCS/Azure) for document storage (managed externally or provisioned)
**Testing**: Contract-first tests (OpenAPI schema validation), integration tests exercising Postgres and storage interactions (per constitution: tests must drive development)
**Target Platform**: Linux servers / containerized (Kubernetes optional)
**Project Type**: Backend microservice (monorepo under `apps/tenant-service`)
**Performance Goals**: Initial target: moderate scale; design for horizontal scaling; exact SLA TBD (see research.md)
**Constraints**: Must follow API-first approach and OpenAPI contracts; use Prisma and Postgres per constitution; use OpenFGA for authorization model
**Scale/Scope**: Design for up to ~1M documents per large tenant (assumption in research)

## Constitution Check
*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Initial assessment against `/memory/constitution.md`:
- API-first: PASS — plan generates OpenAPI contract in `/specs/002-title-tenant-management/contracts/openapi.yaml`.
- NestJS / Prisma / Postgres: PLAN aligns with constitution choices (no violation).
- Authorization model: Plan assumes OpenFGA for relationship-based authorization — aligns with constitution.
- Testing guidance: Constitution discouraged TDD and tests earlier, however the plan enforces contract-first testing and failing contract tests (this is a minor deviation from constitution wording (III) which instructs no unit tests; we will follow the plan's contract-first approach but keep test scope limited to integration/contract tests to respect constitution note about single-person project. Documented below in Complexity Tracking.

Complexity Tracking (justification for deviation):
- Deviation: Plan includes contract & integration tests (contract-first) despite constitution's "Don't write unit tests" guidance. Why needed: Contract tests are required to validate API-first approach and ensure backward-compatible contracts across services; they are lightweight and necessary for a multi-service monorepo. Simpler alternative (no tests) rejected due to risk of silent contract drift.

Gate result: PASS with noted deviation documented above.

## Project Structure

### Documentation (this feature)
```
specs/[###-feature]/
├── plan.md              # This file (/plan command output)
├── research.md          # Phase 0 output (/plan command)
├── data-model.md        # Phase 1 output (/plan command)
├── quickstart.md        # Phase 1 output (/plan command)
├── contracts/           # Phase 1 output (/plan command)
└── tasks.md             # Phase 2 output (/tasks command - NOT created by /plan)
```

### Source Code (repository root)
```
# Option 1: Monorepo (DEFAULT)
apps/
├── app1/
├── app2/
├── cli/

libs/
├── util/
├── uicomponents/

infra/
├── helm/
├── local/

```

**Structure Decision**: [DEFAULT to Option 1 unless Technical Context indicates web/mobile app]

## Phase 0: Outline & Research
Phase 0 executed: `research.md` created. All spec [NEEDS CLARIFICATION] markers were addressed via documented decisions and a small set of assumptions (see `research.md`). Remaining open questions are listed in that file and should be confirmed by the product owner.

## Phase 1: Design & Contracts
Phase 1 executed: generated `data-model.md`, `contracts/openapi.yaml`, and `quickstart.md`. These artifacts are in the specs directory and reflect Phase 0 decisions.

Next Phase 1 tasks (recommended):
- Generate contract test stubs (one per endpoint) that assert OpenAPI request/response shapes. These tests should fail until the implementation exists (TDD contract-first).
- Generate integration scenarios from acceptance criteria (one per acceptance scenario in the spec).

Artifacts produced:
- `/home/solmon/github/docitai/specs/002-title-tenant-management/research.md`
- `/home/solmon/github/docitai/specs/002-title-tenant-management/data-model.md`
- `/home/solmon/github/docitai/specs/002-title-tenant-management/contracts/openapi.yaml`
- `/home/solmon/github/docitai/specs/002-title-tenant-management/quickstart.md`

Post-design constitution check: PASS (see Complexity Tracking for documented test scope deviation)

## Phase 2: Task Planning Approach
This plan stops at Phase 2 planning description. The `/tasks` command will generate `tasks.md` using `/templates/tasks-template.md` as input and the artifacts created here.

Strategy highlights:
- Contract tests first (one per OpenAPI endpoint)
- Data model & migrations next
- Service layer and storage provisioning orchestration after models
- Integration tests covering each acceptance scenario

Estimated initial task count: 20–30 tasks (contract tests, models, services, integration scenarios, infra hooks for provisioning).

NOTE: Do NOT create `tasks.md` in this `/plan` command. Use `/tasks` to generate tasks.

## Phase 3+: Future Implementation
*These phases are beyond the scope of the /plan command*

**Phase 3**: Task execution (/tasks command creates tasks.md)  
**Phase 4**: Implementation (execute tasks.md following constitutional principles)  
**Phase 5**: Validation (run tests, execute quickstart.md, performance validation)

## Complexity Tracking
*Fill ONLY if Constitution Check has violations that must be justified*

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |



## Progress Tracking
**Phase Status**:
- [x] Phase 0: Research complete (/plan command)
- [x] Phase 1: Design complete (/plan command)
- [x] Phase 2: Task planning complete (approach described)
- [ ] Phase 3: Tasks generated (/tasks command)
- [ ] Phase 4: Implementation complete
- [ ] Phase 5: Validation passed

**Gate Status**:
- [x] Initial Constitution Check: PASS
- [x] Post-Design Constitution Check: PASS
- [x] All NEEDS CLARIFICATION resolved (with assumptions documented)
- [x] Complexity deviations documented

---
*Based on Constitution v2.1.1 - See `/memory/constitution.md`*