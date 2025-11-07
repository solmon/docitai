# Phase 0 — Research & Decisions

Feature: Tenant Management Service (feature 002)

Purpose: Resolve ambiguities from the spec so Phase 1 design can proceed.

Decisions (assumptions made — confirm with stakeholder):

1) Storage provisioning behavior
- Decision: Support both approaches: allow Super Admin to provide an existing object store identifier (e.g., S3 bucket ARN, Azure container name) or request automatic provisioning. Automatic provisioning will be implemented as an optional orchestration step that calls infra tooling (not included in MVP). Default: accept existing bucket/namespace; provide an API flag `provision=true` to request provisioning (will return a provisioning task and status).
- Rationale: Accepting existing identifiers keeps onboarding fast and avoids permission/provisioning complexity; provisioning automation can be added incrementally.

2) Retention enforcement action
- Decision: Retention policies support three actions: `archive` (move to cold storage/mark archived), `delete` (permanent deletion), and `mark_expired` (flag for manual review). By default, tenant policies use `archive` for safety. Legal hold prevents deletion/archive and must be an explicit override by Super Admin with audit justification.
- Rationale: Safer default (archive) reduces data-loss risk and aligns with compliance requirements.

3) Tenant Admin overrides
- Decision: Super Admins can set tenant-level defaults. Tenant Admins may create or request container-level policies but cannot override legal-hold or stricter-than-default Super Admin policies. Overrides require an approval workflow (out of scope for MVP — will be represented as request/approve metadata).

4) Performance / scale targets
- Decision (assumption): Design for eventual scale of ~1M documents per large tenant; initial deployment target is 10k–100k documents per tenant. Specific SLAs (throughput, latency) are TBD — mark for follow-up.

5) Data access after tenant deactivation
- Decision (assumption): Deactivation marks tenant read-only and prevents new ingestion; data retention and export are preserved for a default 90-day window unless legal retention requires longer. Export and restore APIs will be provided.

Open questions (recommend confirm before implementation):
- Should onboarding support multi-region bucket provisioning automatically? (affects infra design)
- Who can approve Tenant Admin overrides (automated role, Super Admin manually, or delegated approver)?
- Exact retention durations and default templates (e.g., 90 days invoices, 7 years contracts).

Rationale and alternatives considered
- Alternative (provisioning-only): force all tenants to use platform-provisioned buckets. Rejected because many customers already manage storage and would prefer to reuse existing buckets.
- Alternative (deletion-only retention): simpler but has higher compliance and legal risk — rejected.

Next steps from research
- Confirm open questions with product owner.
- Proceed to Phase 1 design using the above decisions as defaults; mark any remaining open items in `data-model.md` and `contracts/` as [ASSUMPTION].
