<!--
SYNC IMPACT REPORT

Version change: template (unspecified) → 1.0.0

Modified Principles:
- [NEW] Library-First (added as Principle I)
- [NEW] Cloud Agnostic (added as Principle II)
- [NEW] Observability (added as Principle III)
- [NEW] Security by Design (added as Principle IV)
- [NEW] Role-Based Access Control (RBaC) (added as Principle V)
- [NEW] Multi-Tenant Architecture (added as Principle VI)

Added sections:
- Design Tenets & Constraints
- Development Workflow & Quality Gates
- Implementation Guardrails; Examples: Do's and Don'ts

Removed sections: none

Templates reviewed (consistency check):
- `templates/spec-template.md` ⚠ pending — recommend adding explicit checks for tenant awareness, cloud-agnostic constraints, and RBAC requirements
- `templates/plan-template.md` ⚠ pending — recommend adding constitution check items for Cloud Agnostic and Multi-Tenant
- `templates/tasks-template.md` ✅ aligned for TDD and observability, but may need small updates to require tenant-aware tests and RBAC validation tasks

Follow-up TODOs:
- TODO(RATIFICATION_DATE): confirm ratification date and amend if it should differ from creation date
- TASK: update `templates/spec-template.md` and `templates/plan-template.md` to include mandatory constitution-driven checklist entries (tenant_id, rbac scopes, cloud-agnostic deployment notes)
-->

# Speckit Constitution
## Core Principles

### I. Library-First (NON-NEGOTIABLE)
All capabilities MUST be implemented first as reusable, well-documented libraries before being embedded into services or applications.
- Rule: A library is the unit of design, testing, versioning, and documentation. Services SHOULD assemble libraries; they must not contain unique, unshared business logic.
- Rationale: Promotes composability, reduces duplication across services, and enables independent testing and versioned rollout of behavior.

### II. Cloud Agnostic (NON-NEGOTIABLE)
Design and build systems to operate across multiple cloud providers and on-premises environments without requiring provider-specific runtime code.
- Rule: No service MAY hard-code provider-specific APIs or SDKs without an abstraction layer. Infrastructure-specific provisioning and configuration MUST be expressed as adapters or providers.
- Rationale: Avoids vendor lock-in, enables portability and resilience, and allows migration or multi-cloud strategies.

### III. Observability (NON-NEGOTIABLE)
Every component MUST be instrumented with metrics, structured logs, and distributed tracing.
- Rule: Libraries and services MUST emit contextual telemetry (tenant, request-id, operation, error codes) and expose metrics that map to SLOs.
- Rationale: Observability is essential for debugging, performance tuning, incident response, and capacity planning.

### IV. Security by Design
Security MUST be embedded at every layer: data protection, secure communication, identity management, and threat modeling are required artifacts of design.
- Rule: Threat modeling and data classification MUST occur during Phase 0/Phase 1. Sensitive data MUST be encrypted at rest and in transit. Secrets MUST be managed by a secure secret store; no secrets in code.
- Rationale: Proactive security reduces risk and cost of breaches. Security requirements MUST be visible to developers early in the lifecycle.

### V. Role-Based Access Control (RBaC)
Access control MUST be strictly enforced using role-based policies across all layers (APIs, services, storage, UIs). No component may bypass centralized or federated RBAC enforcement.
- Rule: AuthN/Org/Role claims MUST be attached to requests and enforced at the API boundary and on resource access. Privilege escalation paths MUST be documented and minimized.
- Rationale: RBAC provides explicit, auditable access rules necessary for multi-tenant systems and compliance.

### VI. Multi-Tenant Architecture
Systems MUST support multi-tenancy with strong tenant isolation, scalable resource allocation, tenant-aware observability, and per-tenant configuration.
- Rule: All persistent data MUST include tenant scoping (tenant_id), and cross-tenant data access MUST be prevented by design. Monitoring and logs MUST be tenant-aware (tagged and filterable).
- Rationale: Multi-tenant support provides operational efficiency while requiring strict isolation to protect data and compliance boundaries.

## Design Tenets & Constraints

- Minimal Surface Area: Prefer small, composable libraries over large monoliths. Each library SHOULD have a single responsibility and a minimal, well-documented public API.
- Explicit Contracts: All inter-library and inter-service interactions MUST be governed by explicit contracts (OpenAPI, protobuf, or similar) and accompanied by contract tests.
- Tenant-Aware by Default: Designs MUST assume multi-tenancy unless explicitly scoped otherwise, with justification documented in research.md.
- Portable Configuration: Configuration MUST drive deployment differences; code MUST not branch on provider-specific runtime checks.
- Observability as First-class Output: Instrumentation MUST be included in the library API surface (hooks, context propagation) so composed services inherit observability.

## Development Workflow & Quality Gates

1. Test-First (TDD) is mandatory for functional work: write failing tests (contract or integration) before implementation.
2. Contract Tests: Create contract tests from OpenAPI/contract artifacts; these tests MUST fail until the implementation exists.
3. CI Gates: PRs MUST pass unit tests, contract tests, linting, and static analysis. Merge to main is blocked until gates pass.
4. Security & Compliance Gate: Threat model, data classification, and RBAC checks MUST be present for any feature touching sensitive data or cross-tenant functionality.
5. Observability Gate: New libraries or services MUST include metrics and traces mapped to at least one SLO or operational dashboard.

## Governance

Amendments
- The Constitution is the source of truth for architecture and development constraints. Amendments require a documented proposal, a rationale, a migration plan, and approval by the Architecture Council (or designated maintainers).
- Amendment workflow: PR to repository → `Constitution Change` label → Architecture Council review → 2 approving reviews (one security/platform engineer) → merge.

Versioning
- Versioning follows semantic-style governance for the Constitution itself. Initial publication is `1.0.0`.
- Bump rules:
	- MAJOR: Backward-incompatible principle changes (removing or redefining core principles)
	- MINOR: Adding a new principle or materially expanding guidance
	- PATCH: Clarifications, wording edits, typo fixes

Compliance
- All PRs that implement features or infra changes MUST reference the Constitution check in the `plan.md` and confirm compliance or document justified deviations in Complexity Tracking.
- Periodic review: The platform/architecture team MUST perform a compliance review every 6 months or after any major incident.

**Version**: 1.0.0 | **Ratified**: 2025-11-11 | **Last Amended**: 2025-11-11

## Implementation Guardrails

- Library Ownership: Every library MUST have an owner and a clear compatibility policy. Owners are responsible for semantic versioning and migrations.
- Abstractions for Cloud Providers: Provider-specific integrations MUST be implemented as thin adapters behind an abstracted provider interface. Tests MUST include provider-agnostic integration paths.
- Observability Defaults: Libraries SHOULD provide sensible default metric names and structured log keys. Context propagation MUST include tenant_id and request_id.
- RBAC Enforcement: Authorization checks MUST be implemented at the boundary and validated by automated tests (unit + integration). Privileged actions MUST have audit events.
- Data Residency: If a tenant requires specific data residency, that requirement MUST be captured in the spec and a supported deployment path documented.

## Examples — Do's and Don'ts

Do:
- DO build a reusable `file-storage` library and implement S3/GCS adapters behind a provider interface.
- DO include tenant_id in every persisted record and log line for cross-tenant visibility.
- DO create contract tests from OpenAPI and commit them before implementation.
- DO include metrics and traces that map to business SLOs (e.g., request latency p95).

Don't:
- DON'T put tenant-specific business logic only inside a single service with no library or reuse path.
- DON'T hard-code cloud provider SDK calls in business logic — use an adapter or provider layer.
- DON'T bypass RBAC checks by adding `admin` flags in DB without review and audit events.
- DON'T ship services without basic metrics, logging, and a tracing header propagation chain.

## Notes & Rationale

- This Constitution is intentionally prescriptive where safety, portability, and operational excellence matter. Where trade-offs are required, deviations MUST be documented and approved.

