# Data Model: Multitenant Document Management

## Entities

1) Tenant
- tenant_id: UUID (PK)
- name: string
- config: JSON (storage mapping, feature flags)
- created_at: timestamp

2) User
- user_id: UUID (PK)
- tenant_id: UUID (FK)
- email: string
- display_name: string
- roles: string[]
- last_active: timestamp

3) Folder
- folder_id: UUID (PK)
- tenant_id: UUID (FK)
- parent_id: UUID (nullable)
- name: string
- path: string (materialized path)
- acl: JSON (list of ACL entries)
- created_at: timestamp

4) Document
- document_id: UUID (PK)
- tenant_id: UUID (FK)
- folder_id: UUID (FK)
- name: string
- version: int
- storage_provider: enum (s3|azure|gcs)
- storage_container: string
- object_key: string
- size: bigint
- uploader_id: UUID
- tags: JSON
- metadata: JSON
- created_at: timestamp

5) AuditEvent
- event_id: UUID (PK)
- tenant_id: UUID
- user_id: UUID
- action: enum (upload|delete|view|download|search|permission_change)
- document_id: UUID (nullable)
- ip_address: string
- timestamp: timestamp
- context: JSON

6) StorageObject (optional table for mapping/cache)
- id: UUID
- provider, container, object_key, encryption_meta

Indexes and Relationships
- Index: (tenant_id, document_id) for fast lookups
- Index: full-text index in OpenSearch for metadata and extracted text
- Foreign keys: document -> folder -> tenant

Notes on Permissions
- Use OpenFGA tuples externally; store effective ACL snapshots in `Folder.acl` for fast checks and auditing. Recompute on permission updates.
# Phase 1 — Data Model

Date: 2025-09-11

## Entities

### Tenant
- tenant_id: uuid (PK)
- name: string
- config: jsonb (storage mapping, flags)
- created_at: timestamp

### User
- user_id: uuid (PK)
- tenant_id: uuid (FK)
- email: string
- display_name: string
- roles: jsonb or relation to Role
- last_active: timestamp

### Role
- role_id: uuid
- tenant_id: uuid
- name: string
- permissions: jsonb

### Group
- group_id: uuid
- tenant_id: uuid
- name: string
- members: relation -> User

### Folder
- folder_id: uuid
- tenant_id: uuid
- parent_id: uuid (nullable)
- name: string
- acl: jsonb (list of permissions)
- created_at: timestamp

### Document
- document_id: uuid
- tenant_id: uuid
- name: string
- version: int
- storage_key: string
- size: bigint
- uploader_id: uuid
- folder_id: uuid
- tags: jsonb
- metadata: jsonb
- created_at: timestamp

### AuditEvent
- event_id: uuid
- tenant_id: uuid
- user_id: uuid
- action: string
- document_id: uuid (nullable)
- ip_address: inet
- timestamp: timestamp
- context: jsonb

### StorageObject
- provider: enum (azure, s3, gcs)
- container: string
- object_key: string
- encryption_meta: jsonb

## Notes
- Use Prisma schema to represent relationships; store ACLs and tags as JSONB for flexible tenant-driven extensions.
