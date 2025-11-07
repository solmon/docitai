# Data Model — Tenant Management Service

This document extracts entities from the feature spec and Phase 0 decisions.

Entities

1) Tenant
- tenant_id: UUID (primary)
- name: string (unique within system)
- external_identifier: string (optional) — e.g., customer provided id
- status: enum [active, suspended, deactivated]
- metadata: jsonb (freeform)
- storage_config_id: UUID (FK)
- created_at, updated_at: timestamps

Validation rules:
- name required, 3-200 chars
- status default `active`

2) StorageConfig
- storage_config_id: UUID (primary)
- tenant_id: UUID (FK)
- storage_type: enum [s3, azure_blob, gcs, logical_namespace]
- location_identifier: string (bucket ARN, container name, or namespace)
- encrypted: boolean
- provisioned: boolean
- provisioning_status: enum [none, pending, failed, provisioned]
- created_at, updated_at

3) DocumentContainer
- container_id: UUID (primary)
- tenant_id: UUID (FK)
- name: string (e.g., invoices, contracts)
- default_retention_policy_id: UUID (FK)
- created_at, updated_at

4) RetentionPolicy
- policy_id: UUID (primary)
- tenant_id: UUID (FK, nullable for global template)
- scope: enum [container, tenant]
- duration_days: integer (number of days before action)
- action: enum [archive, delete, mark_expired]
- legal_hold: boolean
- version: integer
- created_by: user_id
- created_at, updated_at

5) User (Admin roles)
- user_id: UUID
- tenant_id: UUID (nullable for Super Admin)
- name: string
- email: string (unique)
- role: enum [super_admin, tenant_admin, user]
- status: enum [active, deactivated]
- created_at, updated_at

6) AuditLog
- audit_id: UUID
- tenant_id: UUID (nullable)
- user_id: UUID (actor)
- action: string
- payload: jsonb
- created_at: timestamp

7) UsageMetrics (aggregated)
- metrics_id: UUID
- tenant_id: UUID
- storage_bytes: bigint
- document_count: bigint
- active_user_count: integer
- snapshot_at: timestamp

Relationships
- Tenant 1→1 StorageConfig (current)
- Tenant 1→N DocumentContainer
- DocumentContainer N→1 RetentionPolicy (default)
- Tenant 1→N Users

Notes / Assumptions
- StorageConfig.provisioned true means platform attempted provisioning (per Phase0 decision). Provisioning is handled asynchronously.
- RetentionPolicy.tenant_id nullable allows global templates.
