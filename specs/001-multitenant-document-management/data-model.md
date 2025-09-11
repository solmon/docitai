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
