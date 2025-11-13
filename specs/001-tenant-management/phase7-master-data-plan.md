# Phase 7: Master Data Management - Implementation Plan

**Date**: November 13, 2025  
**Status**: In Progress  
**User Story**: US5 - Master Data Management (Priority: P3)  
**Tasks**: T063-T072 (10 tasks total)  

---

## Overview

Implement tenant-specific document categories and types with custom attributes for document classification. This phase bridges folder organization (Phase 6) with documents that will be stored in Phase 8+.

**Goal**: Enable administrators to define master data (categories, types, attributes) that documents can be classified with.

---

## Task Breakdown

### T063: DocumentCategory Entity Model
**File**: `apps/tenant-service/src/tenant_service/infrastructure/models/document_category.py`

**Requirements**:
- Entity inheriting from TenantAwareBase
- Fields: id, tenant_id, name, description, color_code, icon, parent_category_id (optional hierarchy), sort_order, is_active, deleted_at
- Relationships: parent category (optional), document types in category
- Indexes: (tenant_id, name), (tenant_id, parent_category_id), (tenant_id, is_active)
- Request models: DocumentCategoryCreate, DocumentCategoryUpdate
- Response models: DocumentCategoryResponse, DocumentCategoryTreeResponse

**Purpose**: Define document classification hierarchy (e.g., Financial, Legal, HR, etc.)

---

### T064: DocumentType Entity Model
**File**: `apps/tenant-service/src/tenant_service/infrastructure/models/document_type.py`

**Requirements**:
- Entity inheriting from TenantAwareBase
- Fields: id, tenant_id, name, description, category_id (FK), file_extensions (JSON list), max_file_size, retention_days, custom_attributes (JSON), is_active, deleted_at
- Relationships: category, custom attributes
- Indexes: (tenant_id, category_id), (tenant_id, is_active)
- Request models: DocumentTypeCreate, DocumentTypeUpdate
- Response models: DocumentTypeResponse with nested attributes

**Purpose**: Define templates for specific document types (e.g., Invoice, Contract, Receipt)

---

### T065: CustomAttribute Value Object
**File**: `apps/tenant-service/src/tenant_service/domain/value_objects/custom_attribute.py`

**Requirements**:
- Immutable value object for custom attributes
- Fields: name, attribute_type (string, number, boolean, date, enum), required, default_value, validation_rules, enum_values (optional)
- Methods: validate(value), to_dict(), from_dict()
- Support attribute types:
  - `text`: Free text with optional max_length validation
  - `number`: Numeric with optional min/max
  - `boolean`: True/False
  - `date`: Date/datetime with format validation
  - `enum`: Predefined list of values
  - `json`: Complex JSON object

**Purpose**: Define custom metadata fields for document types

---

### T066: DocumentCategoryRepository
**File**: `apps/tenant-service/src/tenant_service/infrastructure/repositories/category_repository.py`

**Methods**:
- `create(category: DocumentCategory) -> DocumentCategory`
- `get_by_id(category_id: UUID, tenant_id: UUID) -> Optional[DocumentCategory]`
- `list_by_tenant(tenant_id: UUID, skip: int, limit: int) -> List[DocumentCategory]`
- `list_root_categories(tenant_id: UUID) -> List[DocumentCategory]` - No parent
- `list_by_parent(parent_id: UUID, tenant_id: UUID) -> List[DocumentCategory]`
- `get_category_tree(tenant_id: UUID) -> List[DocumentCategoryTree]` - Recursive tree
- `update(category: DocumentCategory) -> DocumentCategory`
- `soft_delete(category_id: UUID, tenant_id: UUID) -> bool`
- `restore(category_id: UUID, tenant_id: UUID) -> bool`
- `exists_by_name(name: str, tenant_id: UUID) -> bool`

**Purpose**: Data access for categories with tenant isolation

---

### T067: DocumentTypeRepository
**File**: `apps/tenant-service/src/tenant_service/infrastructure/repositories/document_type_repository.py`

**Methods**:
- `create(doc_type: DocumentType) -> DocumentType`
- `get_by_id(type_id: UUID, tenant_id: UUID) -> Optional[DocumentType]`
- `list_by_tenant(tenant_id: UUID, skip: int, limit: int) -> List[DocumentType]`
- `list_by_category(category_id: UUID, tenant_id: UUID) -> List[DocumentType]`
- `list_active(tenant_id: UUID) -> List[DocumentType]` - Only active types
- `update(doc_type: DocumentType) -> DocumentType`
- `soft_delete(type_id: UUID, tenant_id: UUID) -> bool`
- `restore(type_id: UUID, tenant_id: UUID) -> bool`
- `exists_by_name(name: str, tenant_id: UUID) -> bool`
- `count_by_category(category_id: UUID, tenant_id: UUID) -> int`

**Purpose**: Data access for document types with tenant isolation

---

### T068: MasterDataService
**File**: `apps/tenant-service/src/tenant_service/domain/services/master_data_service.py`

**Business Logic**:
- `create_category(tenant_id, name, description, parent_id) -> DocumentCategory`
  - Validate category uniqueness per tenant
  - Prevent circular references (if hierarchical)
  - Validate parent exists if provided
- `create_document_type(tenant_id, category_id, name, description, attributes) -> DocumentType`
  - Validate category exists
  - Validate custom attributes schema
  - Support file_extensions and max_file_size
- `update_category(category_id, tenant_id, updates) -> DocumentCategory`
  - Prevent circular references on parent change
  - Validate no active documents if deleting
- `update_document_type(type_id, tenant_id, updates) -> DocumentType`
  - Validate custom attributes if changed
  - Prevent active usage if deleting
- `delete_category(category_id, tenant_id) -> bool`
  - Soft delete with cascade to types (if configured)
  - Check for active document types
- `delete_document_type(type_id, tenant_id) -> bool`
  - Soft delete with audit logging
  - Warn if documents using this type
- `get_category_hierarchy(tenant_id) -> List[DocumentCategoryTree]`
  - Recursive tree retrieval
- `validate_document_attributes(doc_type: DocumentType, values: dict) -> bool`
  - Validate custom attributes against schema
  - Type checking, required fields, enum values, ranges

**Purpose**: Business logic for master data with validation

---

### T069: Master Data Command Handlers
**File**: `apps/tenant-service/src/tenant_service/application/handlers/master_data_handler.py`

**Commands & Handlers**:

```python
class CreateCategoryCommand:
    tenant_id: UUID
    name: str
    description: str
    parent_category_id: Optional[UUID]

class CreateCategoryHandler:
    async def handle(self, cmd: CreateCategoryCommand) -> DocumentCategoryResponse

class UpdateCategoryCommand:
    tenant_id: UUID
    category_id: UUID
    name: Optional[str]
    description: Optional[str]
    parent_category_id: Optional[UUID]

class UpdateCategoryHandler:
    async def handle(self, cmd: UpdateCategoryCommand) -> DocumentCategoryResponse

class DeleteCategoryCommand:
    tenant_id: UUID
    category_id: UUID

class DeleteCategoryHandler:
    async def handle(self, cmd: DeleteCategoryCommand) -> bool

class CreateDocumentTypeCommand:
    tenant_id: UUID
    category_id: UUID
    name: str
    description: str
    file_extensions: List[str]
    max_file_size: int
    custom_attributes: List[CustomAttribute]

class CreateDocumentTypeHandler:
    async def handle(self, cmd: CreateDocumentTypeCommand) -> DocumentTypeResponse

class UpdateDocumentTypeCommand:
    tenant_id: UUID
    type_id: UUID
    updates: dict

class UpdateDocumentTypeHandler:
    async def handle(self, cmd: UpdateDocumentTypeCommand) -> DocumentTypeResponse

class DeleteDocumentTypeCommand:
    tenant_id: UUID
    type_id: UUID

class DeleteDocumentTypeHandler:
    async def handle(self, cmd: DeleteDocumentTypeCommand) -> bool
```

**Purpose**: CQRS commands for master data operations

---

### T070: Master Data REST Endpoints
**File**: `apps/tenant-service/src/tenant_service/api/v1/master_data.py`

**Endpoints**:

#### Categories
```
POST   /api/v1/master-data/categories              - Create category
GET    /api/v1/master-data/categories              - List categories (paginated)
GET    /api/v1/master-data/categories/tree         - Get category hierarchy
GET    /api/v1/master-data/categories/{id}         - Get category details
PUT    /api/v1/master-data/categories/{id}         - Update category
DELETE /api/v1/master-data/categories/{id}         - Delete category

POST   /api/v1/master-data/categories/{id}/restore - Restore deleted category
```

#### Document Types
```
POST   /api/v1/master-data/types                   - Create document type
GET    /api/v1/master-data/types                   - List document types (paginated)
GET    /api/v1/master-data/types?category_id=...   - Filter by category
GET    /api/v1/master-data/types/{id}              - Get document type details
PUT    /api/v1/master-data/types/{id}              - Update document type
DELETE /api/v1/master-data/types/{id}              - Delete document type

POST   /api/v1/master-data/types/{id}/restore      - Restore deleted type
GET    /api/v1/master-data/types/{id}/schema       - Get custom attributes schema
```

**All endpoints**:
- Require JWT authentication with tenant context extraction
- Enforce multi-tenant isolation via tenant_id
- Return proper error codes (400, 404, 409, 500)
- Include pagination for list endpoints (limit: 50 default, max 100)
- Support soft delete filtering (include_deleted query param)

**Purpose**: RESTful API for master data management

---

### T071: Custom Attribute Validation & Schema Management
**File**: `apps/tenant-service/src/tenant_service/domain/services/master_data_service.py` (added methods)

**Validation Logic**:
- `validate_attribute_schema(attributes: List[CustomAttribute]) -> List[ValidationError]`
  - Check attribute names are unique and valid identifiers
  - Check attribute types are supported
  - Validate enum_values for enum type
  - Validate default values match type
  - Check required fields
- `validate_document_data(doc_type: DocumentType, data: dict) -> List[ValidationError]`
  - Check all required attributes present
  - Type coercion and validation
  - Range validation for numbers
  - Enum value validation
  - Date format validation
  - Nested JSON validation
- `get_attribute_constraints(attribute: CustomAttribute) -> dict`
  - Return JSON schema representation for API documentation

**Constraints**:
- Max 50 custom attributes per document type
- Attribute name max 100 characters, alphanumeric + underscore
- Enum values max 1000 per attribute
- Total custom attributes size < 10KB per document

**Purpose**: Runtime validation of custom attributes

---

### T072: Master Data Versioning for Audit & Rollback
**File**: `apps/tenant-service/src/tenant_service/infrastructure/models/master_data_version.py`

**Entity**: MasterDataVersion (immutable audit trail)
- Fields: id, tenant_id, entity_type (category/type), entity_id, version_number, changes (JSON), changed_by, changed_at
- Indexes: (tenant_id, entity_type, entity_id), (tenant_id, changed_at)

**Service Methods**:
- `record_version(entity_type, entity_id, tenant_id, changes, user_id) -> MasterDataVersion`
  - Create immutable version record
- `get_version_history(entity_id, tenant_id) -> List[MasterDataVersion]`
  - Retrieve all versions for entity
- `get_version(entity_id, version_number, tenant_id) -> MasterDataVersion`
  - Retrieve specific version
- `rollback_to_version(entity_id, version_number, tenant_id) -> Entity`
  - Restore entity to previous version (creates new version)

**Audit Integration**:
- Integrate with ComplianceAuditTrail from Phase 5
- Log all master data changes with user attribution
- Preserve full change history

**Purpose**: Complete audit trail for compliance and rollback capability

---

## Architecture Decisions

### Hierarchy Design
- Categories support optional parent_category_id for organizational hierarchy
- Document types are always under a category (required FK)
- Prevents deep nesting (max 5 levels for categories)

### Custom Attributes
- Stored as JSON array in DocumentType
- Deserialized to CustomAttribute value objects
- Validated at runtime when creating documents
- Support for complex types (enum, date ranges, etc.)

### Soft Delete Strategy
- Categories and types use soft delete (deleted_at timestamp)
- Allows restore operations
- Hidden from list queries by default
- Audit trail preserved

### Multi-Tenancy
- All operations scoped by tenant_id
- Cannot cross-tenant access via repository queries
- Tenant validation at API layer

---

## Integration Points

1. **Phase 6 (Folders)**: Master data independent of folder hierarchy
2. **Phase 5 (Compliance)**: Can apply retention policies to document types
3. **Future (Documents)**: Documents reference document_type_id, validate attributes
4. **Future (Search)**: Use categories/types for faceted search filters

---

## Error Handling

- `CategoryNotFoundError`: Category doesn't exist
- `DocumentTypeNotFoundError`: Type doesn't exist  
- `CircularReferenceError`: Category parent creates cycle
- `DuplicateNameError`: Category/type name exists in tenant
- `InvalidAttributeSchemaError`: Custom attributes invalid
- `ValidationError`: Document data fails attribute validation
- `ConflictError`: Cannot delete category with active types

---

## Performance Considerations

1. **Category Tree Caching**: Cache full hierarchy with expiration
2. **Custom Attributes**: Keep schema in memory for validation
3. **Soft Delete Filtering**: Indexed on (tenant_id, is_active)
4. **Lazy Loading**: Don't load custom attributes unless needed

---

## File Statistics (Estimated)

| Component | Lines |
|-----------|-------|
| DocumentCategory model | ~80 |
| DocumentType model | ~100 |
| CustomAttribute value object | ~120 |
| DocumentCategoryRepository | ~150 |
| DocumentTypeRepository | ~140 |
| MasterDataService | ~350 |
| Master Data Handlers | ~180 |
| REST API Endpoints | ~400 |
| MasterDataVersion model | ~50 |
| **Total Phase 7** | **~1,570** |

---

## Schedule

**Parallel Groups** (can run simultaneously):
- T063-T065: Models & Value Objects
- T066-T067: Repositories (after models)
- T068-T069: Services & Handlers (after repos)
- T070-T072: API & Versioning (after handlers)

**Sequential Dependencies**:
T063, T064, T065 → T066, T067 → T068, T069 → T070, T071, T072

**Estimated Time**: 2-3 hours for full implementation

---

## Testing Strategy

**Unit Tests** (20+ tests):
- CustomAttribute validation
- Master data service business logic
- Repository CRUD operations
- Circular reference prevention
- Attribute schema validation

**Integration Tests** (10+ tests):
- Create category and types
- Update category hierarchy
- Delete with cascade behavior
- Multi-tenant isolation
- Soft delete filtering

**Contract Tests** (6+ tests):
- All 13 endpoints via OpenAPI spec
- Request/response validation
- Error scenarios (404, 409, 400)

---

## Success Criteria

✅ Create, read, update, delete categories and types  
✅ Support custom attributes with type validation  
✅ Enforce multi-tenant isolation  
✅ Prevent circular references  
✅ Support soft delete with restore  
✅ Audit all changes with versioning  
✅ All 13 endpoints functional  
✅ <100ms response time for list operations  

---

## Next Steps

1. Start with T063-T065 (models in parallel)
2. Implement T066-T067 (repositories)
3. Implement T068-T069 (services/handlers)
4. Implement T070-T072 (API/versioning)
5. Register master_data router in main.py
6. Write tests
7. Proceed to Phase 8 (Polish & Production)

---

## Status

- [x] Phase 7 plan created
- [ ] T063-T065: Models (in progress)
- [ ] T066-T067: Repositories
- [ ] T068-T069: Services & Handlers
- [ ] T070-T072: API & Versioning
- [ ] Tests & Integration
- [ ] Phase 7 complete

Continue? `yes` to start implementation
