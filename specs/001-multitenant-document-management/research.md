# Research: Multitenant Document Management System

Decisions made to resolve NEEDS CLARIFICATION from spec and plan template.

1) Search Engine
- Decision: Use OpenSearch (managed or self-hosted) with option to switch to Elasticsearch. Rationale: open-source, API-compatible, and simpler licensing for single-developer projects.

2) Audit Retention Default
- Decision: Default retention 90 days for detailed audit events, with configurable export to SIEM. Rationale: balances storage cost and compliance; configurable per-tenant.

3) File Size Limits & Chunking
- Decision: Support multipart/chunked uploads up to 100GB via streaming uploads; default single-file API limits to 5GB (can be increased per-tenant). Rationale: S3/Blob support multipart; large file handling requires streaming and background processing.

4) Testing Policy
- Decision: Contract-first automated validation using OpenAPI contract tests and lightweight integration smoke tests for critical flows (upload, download, permission enforcement). Unit/TDD is deprioritized per constitution.

5) Storage Adapter Strategy
- Decision: Implement a storage adapter interface with provider implementations for S3-compatible, Azure Blob, and GCS. Use abstraction to allow per-tenant routing.

6) Search Indexing Strategy
- Decision: Index metadata synchronously on upload; schedule full-text extraction (if enabled) asynchronously with a document processing queue. Provide eventual consistency guarantees for search.

7) Authorization
- Decision: Use OpenFGA for relationship-based authorization; enforce checks at API gateway/microservice layer before data access.

Alternatives considered are noted inline in each section.

Status: Research phase completed; items above were used to generate design artifacts.
# Phase 0 — Research: Multitenant DMS

Date: 2025-09-11

## Unknowns extracted from spec
- Preferred search engine: Elasticsearch vs OpenSearch
- Authentication/Identity provider and SSO flows (OIDC connectors, SAML)
- Audit retention policy and export formats for SIEM
- File size limits, chunking strategy, and streaming uploads
- Performance SLAs (requests/sec, latency)
- Compliance scope (which tenants require GDPR/HIPAA)

## Decisions and rationale (proposed defaults to continue design)

1. Search engine: OpenSearch (self-hosted or managed) recommended
   - Rationale: OpenSearch is community-driven, AWS-managed options available; compatible with Elasticsearch APIs. If a customer requires Elasticsearch specifically, support via configuration.
   - Alternatives: Elasticsearch (hosted or managed). Choose based on customer preference and licensing.

2. Authentication: Support OIDC (OAuth2/OpenID Connect) primary; fallback to JWT for service-to-service and internal tokens.
   - Rationale: OIDC supports SSO and integrates with identity providers (Azure AD, Okta). Passport.js + passport-openidconnect for NestJS.
   - Actions: Document required OIDC metadata and tenant-level identity mapping.

3. Audit retention: Default retention 365 days for audit logs with configurable tenant override; allow export to SIEM via webhook or CSV/NDJSON export.
   - Rationale: 1 year balances storage cost and audit needs; adjust per tenant/regulatory needs.
   - Actions: Expose retention config per tenant and an export API.

4. File size limits & chunking: Support streaming multipart uploads with chunked uploads for files >100MB. Recommend chunk size 50MB and resumable upload tokens.
   - Rationale: Large files common; resumable uploads avoid re-uploading after failures.

5. Performance SLAs: Defer exact numbers to stakeholder input; plan for horizontal scaling (stateless app servers + autoscaling, async indexing) and aim for p95 < 300ms for metadata ops in first iteration.

6. Compliance: Default to GDPR controls (data export, erase) in platform; HIPAA support as opt-in tenant-level configuration with required BAAs and encryption/access controls.

## Output
- Decisions above to be used as defaults for Phase 1 design documents.
