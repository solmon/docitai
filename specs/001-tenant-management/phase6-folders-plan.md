# Phase 6: Folder Management - Implementation Plan

**Date**: November 13, 2025  
**Status**: In Progress  
**Tasks**: T054-T062 (9 tasks)  
**User Story**: US3 - Folder Management (Priority: P3)

---

## Overview

Implement hierarchical folder structure with parent/child relationships, path generation, soft deletion with cascading, and REST API for folder operations. Folders enable document organization and access control delegation.

---

## Architecture

### Folder Entity
```
Folder
├── id: UUID (primary key)
├── tenant_id: UUID (multi-tenant isolation)
├── name: str (folder name)
├── parent_id: Optional[UUID] (parent folder reference)
├── path: str (computed path like /root/documents/invoices)
├── description: Optional[str]
├── owner_id: UUID (creator/owner)
├── is_archived: bool
├── child_count: int (cached for performance)
├── depth: int (hierarchy level)
├── created_at: datetime
├── updated_at: datetime
└── deleted_at: Optional[datetime] (soft delete)
```

### Folder Relationships
```
Tenant (1) ─── (n) Folders
                    ├─ Parent/Child: Self-referencing
                    └─ Owner (User)

Folder (1) ─── (n) Folders (children)
Folder (1) ─── (n) Documents (Phase 7)
```

---

## Task Breakdown

### T054: Folder Entity Model
**File**: `apps/tenant-service/src/tenant_service/infrastructure/models/folder.py`

Create SQLModel entity:
- `id`, `tenant_id`, `name`, `parent_id` (self-referencing FK)
- `path`: Computed hierarchical path
- `description`, `owner_id`, `is_archived`, `deleted_at`
- `child_count`: Cache for optimization
- `depth`: Nesting level (prevent deep nesting)
- Request/Response models

### T055: Folder Enums
**File**: `apps/tenant-service/src/tenant_service/domain/enums/folder_types.py`

Enums:
- `FolderOperation`: create, move, delete, archive
- `FolderStatus`: active, archived, deleted

### T056: Folder Repository
**File**: `apps/tenant-service/src/tenant_service/infrastructure/repositories/folder_repository.py`

Methods:
- `create()`: Create folder with path generation
- `get_by_id()`: Retrieve with tenant verification
- `get_by_path()`: Find folder by full path
- `list_by_parent()`: Get children of folder
- `list_by_tenant()`: All folders (root level)
- `get_root_folders()`: Top-level folders (parent_id is null)
- `list_all_descendants()`: Get all children recursively
- `update()`: Update folder (name, description)
- `soft_delete()`: Mark as deleted
- `get_tree()`: Return folder hierarchy
- `move_folder()`: Change parent (with path update)
- `increment_child_count()`: Track children
- `decrement_child_count()`: Track children

### T057: Folder Service
**File**: `apps/tenant-service/src/tenant_service/domain/services/folder_service.py`

Business logic:
- `create_folder()`: Validate parent exists, generate path
- `get_folder()`: Retrieve with tenant check
- `list_root_folders()`: Top-level navigation
- `get_folder_tree()`: Recursive hierarchy
- `update_folder()`: Safe updates
- `move_folder()`: Change parent, update paths recursively
- `delete_folder()`: Cascade soft delete to children
- `restore_folder()`: Undelete folder and children
- `get_breadcrumb()`: Parent path navigation
- `validate_path()`: Prevent circular references
- `calculate_path()`: Generate full path string

### T058-T060: CQRS Handlers (3 tasks)

**T058**: Create/Update Handlers
**File**: `apps/tenant-service/src/tenant_service/application/handlers/folder_handler.py`

Handlers:
- `CreateFolderHandler`: CreateFolderCommand
- `UpdateFolderHandler`: UpdateFolderCommand
- `MoveFolderHandler`: MoveFolderCommand

**T059**: Delete Handlers
**File**: `apps/tenant-service/src/tenant_service/application/handlers/folder_deletion_handler.py`

Handlers:
- `DeleteFolderHandler`: DeleteFolderCommand (cascade)
- `RestoreFolderHandler`: RestoreFolderCommand

**T060**: Query Handlers
**File**: `apps/tenant-service/src/tenant_service/application/handlers/folder_query_handler.py`

Handlers:
- `GetFolderTreeHandler`: GetFolderTreeQuery
- `GetBreadcrumbHandler`: GetBreadcrumbQuery

### T061-T062: REST API Endpoints (2 tasks)

**T061**: Folder CRUD Endpoints
**File**: `apps/tenant-service/src/tenant_service/api/v1/folders.py`

Endpoints:
```
POST   /api/v1/folders                  - Create folder
GET    /api/v1/folders/{id}            - Get folder
GET    /api/v1/folders                 - List root folders
GET    /api/v1/folders/{id}/children   - Get children
GET    /api/v1/folders/{id}/tree       - Get hierarchy
PUT    /api/v1/folders/{id}            - Update folder
POST   /api/v1/folders/{id}/move       - Move folder
DELETE /api/v1/folders/{id}            - Delete folder (cascade)
POST   /api/v1/folders/{id}/restore    - Restore folder
GET    /api/v1/folders/{id}/breadcrumb - Get path navigation
```

**T062**: Integration & Testing
- Register router in main.py
- Create test fixtures
- Integration tests

---

## Database Schema

### folders table
```sql
CREATE TABLE folders (
  id UUID PRIMARY KEY,
  tenant_id UUID NOT NULL INDEX,
  parent_id UUID,
  name VARCHAR NOT NULL,
  path VARCHAR NOT NULL,
  description VARCHAR,
  owner_id UUID NOT NULL,
  is_archived BOOLEAN DEFAULT FALSE,
  deleted_at TIMESTAMP,
  child_count INT DEFAULT 0,
  depth INT DEFAULT 0,
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  FOREIGN KEY (tenant_id) REFERENCES tenants(id),
  FOREIGN KEY (parent_id) REFERENCES folders(id),
  UNIQUE (tenant_id, path),
  CHECK (depth <= 20)  -- Prevent deep nesting
);
```

### Indexes
- `(tenant_id, parent_id)` - Find children
- `(tenant_id, path)` - Direct path lookup
- `(tenant_id, is_archived)` - Filter active/archived
- `(tenant_id, deleted_at)` - Soft delete queries

---

## Path Generation

Path format: `/root/documents/invoices/2024`

Algorithm:
1. Get parent folder
2. If parent exists, get parent's path
3. Append current folder name
4. Validate path doesn't exist for tenant
5. Store full path for O(1) lookup

Example:
```python
# Parent: path = "/documents"
# New folder name: "invoices"
# Result: "/documents/invoices"

# Deep nesting:
# "/root" → "/root/level1" → "/root/level1/level2" → etc.
```

---

## Cascade Deletion

When folder deleted:
1. Mark folder as deleted
2. Recursively mark all children as deleted
3. Log each deletion to audit trail
4. Update child_count for parent
5. Mark documents in folder as archived (Phase 7)

Example:
```
Delete /root/archive
└─ Delete /root/archive/2023
   └─ Delete /root/archive/2023/01
      └─ Archive 150 documents
```

---

## Circular Reference Prevention

Validate when moving folder:
1. Get target parent
2. Verify target is not current folder's descendant
3. Prevent: moving `/root` under `/root/child`
4. Raise `CircularReferenceError` if invalid

---

## API Examples

### Create Root Folder
```bash
curl -X POST http://localhost:8000/api/v1/folders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{
    "name": "Documents",
    "description": "All company documents",
    "parent_id": null
  }'
```

### Create Nested Folder
```bash
curl -X POST http://localhost:8000/api/v1/folders \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{
    "name": "Invoices",
    "description": "2024 invoices",
    "parent_id": "uuid-of-documents-folder"
  }'
```

### Get Folder Tree
```bash
curl -X GET http://localhost:8000/api/v1/folders/{id}/tree \
  -H "Authorization: Bearer JWT_TOKEN"
```

Response:
```json
{
  "id": "uuid",
  "name": "Documents",
  "path": "/Documents",
  "children": [
    {
      "id": "uuid",
      "name": "Invoices",
      "path": "/Documents/Invoices",
      "children": [
        {
          "id": "uuid",
          "name": "2024",
          "path": "/Documents/Invoices/2024",
          "children": []
        }
      ]
    }
  ]
}
```

### Move Folder
```bash
curl -X POST http://localhost:8000/api/v1/folders/{folder_id}/move \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer JWT_TOKEN" \
  -d '{
    "new_parent_id": "uuid-of-target-folder"
  }'
```

### Delete Folder (Cascade)
```bash
curl -X DELETE http://localhost:8000/api/v1/folders/{id} \
  -H "Authorization: Bearer JWT_TOKEN"
```

Logs:
- Folder deletion
- All child folder deletions
- All document archival

---

## Security & Isolation

✅ **Tenant Isolation**: All folders scoped by tenant_id  
✅ **Access Control**: Only tenant members can access folders  
✅ **Owner Verification**: Check user is owner for modifications  
✅ **Circular Reference Prevention**: Validate tree integrity  
✅ **Soft Delete**: Preserve audit trail  
✅ **Cascade Audit**: Log all deletions  

---

## Constraints

- **Max Path Length**: 500 characters
- **Max Depth**: 20 levels (prevents abuse)
- **Max Children**: Unlimited per folder
- **Path Uniqueness**: One path per tenant
- **Name Validation**: 1-255 characters, no leading/trailing spaces

---

## Performance Considerations

1. **Path Caching**: Store full path in database for O(1) lookups
2. **Child Count Cache**: Update atomically with inserts/deletes
3. **Depth Tracking**: Prevent deep nesting (> 20 levels)
4. **Soft Delete Flag**: Efficient visibility queries
5. **Indexes**: (tenant_id, parent_id) for tree traversal

---

## Integration Points

1. **Retention Policies**: Apply policies to folders
2. **Documents**: Store parent_folder_id reference (Phase 7)
3. **Audit Trail**: Log folder operations
4. **Access Control**: Inherit tenant permissions

---

## Error Handling

- `FolderNotFoundError`: Folder doesn't exist
- `CircularReferenceError`: Moving folder under itself
- `MaxDepthExceededError`: Nesting too deep
- `ParentNotFoundError`: Parent folder invalid
- `FolderAlreadyExistsError`: Path already exists

---

## Testing Strategy

1. **Unit Tests**: Path generation, validation, circular reference detection
2. **Integration Tests**: Folder creation, moving, cascading deletion
3. **Concurrency Tests**: Parallel operations on same folder
4. **Audit Tests**: All deletions logged

---

## Deliverables

- ✅ 1 SQLModel entity (Folder)
- ✅ 2 Enums (FolderOperation, FolderStatus)
- ✅ 1 Repository with tree traversal
- ✅ 1 Domain service with path logic
- ✅ 5 CQRS handlers
- ✅ 9 REST API endpoints
- ✅ Cascade deletion support
- ✅ Circular reference prevention

---

## Next Phase (Phase 7)

Master Data will reference folders:
- Documents have `parent_folder_id` reference
- Categories organized in folders
- Retention policies applied to folders

---

Continue? `yes` to start T054
