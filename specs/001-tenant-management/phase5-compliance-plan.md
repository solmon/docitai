# Phase 5: Compliance & Retention - Implementation Plan

**Date**: November 13, 2025  
**Status**: In Progress  
**Tasks**: T042-T053 (12 tasks)  
**User Story**: US4 - Compliance & Retention (Priority: P2)

---

## Overview

Implement retention policy engine with scheduled enforcement, audit trail for compliance tracking, and REST API for policy management. System will enforce automatic deletion/archival based on configured retention rules.

---

## Architecture

### RetentionPolicy Entity
```
RetentionPolicy
├── id: UUID (primary key)
├── tenant_id: UUID (multi-tenant isolation)
├── name: str (policy name)
├── description: Optional[str]
├── resource_type: ResourceType (document, folder, etc.)
├── retention_type: RetentionType (delete, archive)
├── retention_days: int
├── applies_to: AppliesTo (all, specific_categories, specific_folders)
├── filter_config: dict (JSON for category IDs, folder IDs, etc.)
├── is_active: bool
├── created_by: UUID (user_id)
├── created_at: datetime
├── updated_at: datetime
└── executed_count: int (audit)
```

### Audit Trail Entity
```
ComplianceAuditTrail
├── id: UUID
├── tenant_id: UUID
├── action_type: AuditActionType (policy_created, policy_executed, document_deleted, etc.)
├── resource_type: str (document, folder, policy)
├── resource_id: UUID
├── old_value: Optional[dict] (JSON for changes)
├── new_value: Optional[dict]
├── changed_by: UUID (user_id)
├── reason: Optional[str]
├── created_at: datetime
└── compliance_status: ComplianceStatus (success, failed, pending)
```

---

## Task Breakdown

### T042: RetentionPolicy Entity Model
**File**: `apps/tenant-service/src/tenant_service/infrastructure/models/retention_policy.py`

Create SQLModel entity with enums:
- `ResourceType`: document, folder, all
- `RetentionType`: delete, archive
- `AppliesTo`: all, specific_categories, specific_folders
- Request/Response models

### T043: ComplianceAuditTrail Entity Model
**File**: `apps/tenant-service/src/tenant_service/infrastructure/models/compliance_audit_trail.py`

Create audit trail entity with:
- `AuditActionType`: policy_created, policy_updated, policy_executed, document_deleted, document_archived, etc.
- `ComplianceStatus`: success, failed, pending
- Request/Response models

### T044: Policy Repository
**File**: `apps/tenant-service/src/tenant_service/infrastructure/repositories/retention_policy_repository.py`

CRUD operations with:
- `create()`: New policy
- `get_by_id()`: With tenant verification
- `list_by_tenant()`: All policies
- `list_active()`: Active policies for scheduler
- `update()`: Update policy fields
- `delete()`: Soft delete
- `increment_execution_count()`: Track execution

### T045: Audit Repository
**File**: `apps/tenant-service/src/tenant_service/infrastructure/repositories/compliance_audit_repository.py`

Audit trail operations:
- `log_action()`: Record audit entry
- `list_by_resource()`: Get audit trail for resource
- `list_by_tenant()`: All audit entries
- `list_by_action_type()`: Filter by action
- Immutable writes (append-only)

### T046: Policy Engine Service
**File**: `apps/tenant-service/src/tenant_service/domain/services/retention_policy_service.py`

Business logic:
- `create_policy()`: Validate and create
- `get_policy()`: With tenant verification
- `update_policy()`: Safe updates
- `delete_policy()`: Soft delete with audit
- `list_policies()`: Query with filters
- `execute_policy()`: Trigger deletion/archival
- `calculate_retention_date()`: When policy applies

### T047: Compliance Service
**File**: `apps/tenant-service/src/tenant_service/domain/services/compliance_service.py`

Audit trail management:
- `log_audit_action()`: Record action
- `get_resource_audit_trail()`: History for resource
- `get_tenant_audit_trail()`: All activity
- `export_audit_report()`: For compliance
- Immutable audit records

### T048: Scheduler Service
**File**: `apps/tenant-service/src/tenant_service/domain/services/scheduler_service.py`

APScheduler integration:
- `schedule_policy_execution()`: Daily policy checks
- `execute_pending_policies()`: Run retention logic
- `get_scheduled_jobs()`: List active jobs
- `cancel_job()`: Stop scheduled task
- Error handling and retry logic

### T049-T050: CQRS Handlers

**T049**: Policy Handlers
**File**: `apps/tenant-service/src/tenant_service/application/handlers/retention_policy_handler.py`

Handlers:
- `CreatePolicyHandler`: CreateRetentionPolicyCommand
- `UpdatePolicyHandler`: UpdateRetentionPolicyCommand
- `DeletePolicyHandler`: DeleteRetentionPolicyCommand

**T050**: Execution Handlers
**File**: `apps/tenant-service/src/tenant_service/application/handlers/policy_execution_handler.py`

Handlers:
- `ExecutePolicyHandler`: ExecuteRetentionPolicyCommand
- `VerifyComplianceHandler`: VerifyComplianceCommand

### T051-T053: REST API Endpoints

**T051**: Policy Management Endpoints
**File**: `apps/tenant-service/src/tenant_service/api/v1/retention_policies.py`

Endpoints:
```
POST   /api/v1/policies                    - Create policy
GET    /api/v1/policies/{policy_id}       - Get policy
GET    /api/v1/policies                   - List policies
PUT    /api/v1/policies/{policy_id}       - Update policy
DELETE /api/v1/policies/{policy_id}       - Delete policy
POST   /api/v1/policies/{policy_id}/execute - Execute policy (manual trigger)
```

**T052**: Audit Trail Endpoints
**File**: `apps/tenant-service/src/tenant_service/api/v1/compliance_audit.py`

Endpoints:
```
GET /api/v1/audit/{resource_type}/{resource_id} - Resource audit trail
GET /api/v1/audit                               - Tenant audit trail
GET /api/v1/audit/export                        - Export audit report
```

**T053**: Integration & Testing
- Register routes in main.py
- Update conftest.py with policy fixtures
- Create integration tests

---

## Enums & Value Objects

### ResourceType
```python
class ResourceType(str, Enum):
    DOCUMENT = "document"
    FOLDER = "folder"
    ALL = "all"
```

### RetentionType
```python
class RetentionType(str, Enum):
    DELETE = "delete"
    ARCHIVE = "archive"
```

### AppliesTo
```python
class AppliesTo(str, Enum):
    ALL = "all"
    SPECIFIC_CATEGORIES = "specific_categories"
    SPECIFIC_FOLDERS = "specific_folders"
```

### AuditActionType
```python
class AuditActionType(str, Enum):
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_EXECUTED = "policy_executed"
    POLICY_DELETED = "policy_deleted"
    DOCUMENT_DELETED = "document_deleted"
    DOCUMENT_ARCHIVED = "document_archived"
    FOLDER_DELETED = "folder_deleted"
    COMPLIANCE_VERIFIED = "compliance_verified"
```

### ComplianceStatus
```python
class ComplianceStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
```

---

## Database Migrations

Alembic migrations needed:
1. Create `retention_policies` table
2. Create `compliance_audit_trail` table
3. Add indexes on `tenant_id`, `resource_type`, `is_active`, `created_at`
4. Add foreign key to `tenants` table

---

## Scheduler Configuration

APScheduler setup in `main.py`:
```python
scheduler = BackgroundScheduler()
scheduler.add_job(
    execute_retention_policies,
    'cron',
    hour=2,  # Run at 2 AM daily
    id='retention_policy_execution',
    replace_existing=True
)
scheduler.start()
```

---

## API Examples

### Create Retention Policy
```bash
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{
    "name": "Delete old documents",
    "description": "Remove documents older than 90 days",
    "resource_type": "document",
    "retention_type": "delete",
    "retention_days": 90,
    "applies_to": "all",
    "filter_config": {},
    "is_active": true
  }'
```

### Execute Policy Manually
```bash
curl -X POST http://localhost:8000/api/v1/policies/{policy_id}/execute \
  -H "Authorization: Bearer JWT_TOKEN"
```

### Get Audit Trail
```bash
curl -X GET "http://localhost:8000/api/v1/audit?limit=50&offset=0" \
  -H "Authorization: Bearer JWT_TOKEN"
```

---

## Security & Compliance

1. **Audit Trail Immutability**: All writes to audit trail are append-only
2. **Tenant Isolation**: All policies and audit records scoped by tenant_id
3. **Permission Checks**: Only COMPLIANCE_ADMIN can create/modify policies
4. **Change Tracking**: All policy changes logged with user ID
5. **Deletion Safety**: Soft deletes with audit trail preservation
6. **Retention Verification**: System verifies before deleting data

---

## Error Handling

- `PolicyNotFoundError`: Policy doesn't exist
- `TenantIsolationViolationError`: Cross-tenant access attempt
- `InvalidRetentionConfigError`: Invalid policy configuration
- `SchedulerError`: Background job execution failure
- `ComplianceVerificationError`: Policy execution failure

---

## Integration Points

1. **Tenant Service**: Verify tenant exists and is active
2. **Storage Service**: Handle document archival/deletion
3. **Folder Service**: Handle folder deletion cascades (Phase 6)
4. **Authentication**: Extract user context for audit trail
5. **Logging**: All policy execution logged for debugging

---

## Testing Strategy

1. **Unit Tests**: Policy creation, validation, retention calculation
2. **Integration Tests**: Policy execution, audit logging, tenant isolation
3. **Scheduler Tests**: Background job execution, error handling
4. **Compliance Tests**: Audit trail immutability, permission enforcement

---

## Next Phase (Phase 6)

Folder Management will use retention policies:
- Folders can be deleted only if retention period passed
- Folder deletion cascades to child folders and documents
- All deletions logged to audit trail

---

## Deliverables

- ✅ 2 SQLModel entities (RetentionPolicy, ComplianceAuditTrail)
- ✅ 2 repositories with isolation enforcement
- ✅ 3 domain services (policy, compliance, scheduler)
- ✅ 5 CQRS handlers
- ✅ 8 REST API endpoints
- ✅ Integration with APScheduler
- ✅ 5 enums/value objects
- ✅ Comprehensive error handling
- ✅ Audit trail immutability

---

Continue? `yes` to start T042
