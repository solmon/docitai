# Phase 0: Research & Technical Decisions

**Feature**: Tenant Management Service for Document Management System  
**Date**: November 12, 2025  
**Status**: Complete

## Research Tasks

### 1. Cloud Storage Abstraction Layer Design

**Decision**: Implement Provider Pattern with async context managers and unified interface

**Rationale**: 
- Enables cloud-agnostic deployment as required by constitution
- Allows runtime provider switching based on tenant configuration
- Provides consistent error handling and retry logic across providers
- Supports both sync and async operations for scalability

**Alternatives Considered**:
- Direct SDK integration: Rejected due to cloud lock-in violation
- Plugin-based architecture: Rejected due to complexity vs benefit ratio
- Adapter pattern only: Rejected due to insufficient abstraction for tenant-specific configs

**Implementation Approach**:
```python
# Abstract interface in storage-abstraction library
class CloudStorageProvider(ABC):
    async def put_object(self, bucket: str, key: str, data: bytes, metadata: Dict) -> str
    async def get_object(self, bucket: str, key: str) -> bytes
    async def delete_object(self, bucket: str, key: str) -> bool
    async def list_objects(self, bucket: str, prefix: str) -> List[StorageObject]

# Provider implementations
class AzureBlobProvider(CloudStorageProvider): ...
class AWSS3Provider(CloudStorageProvider): ...
class GCSProvider(CloudStorageProvider): ...

# Factory for tenant-specific provider instantiation
class StorageProviderFactory:
    def get_provider(self, tenant_config: StorageConfig) -> CloudStorageProvider
```

### 2. Authentication Strategy & JWT Validation

**Decision**: JWT token validation with configurable identity providers using FastAPI security utilities

**Rationale**:
- Supports both internal and external identity providers (Auth0, Azure AD, etc.)
- Enables RBAC enforcement at API boundary as required by constitution
- Provides tenant-aware claims extraction for multi-tenant isolation
- Integrates with FastAPI dependency injection for clean separation

**Alternatives Considered**:
- Session-based auth: Rejected due to microservice scalability concerns
- API key only: Rejected due to insufficient RBAC capabilities
- OAuth2 flow handling: Out of scope, delegated to identity provider

**Implementation Approach**:
```python
# JWT validation dependency
class JWTValidator:
    def __init__(self, issuer: str, audience: str, jwks_url: str)
    async def validate_token(self, token: str) -> TokenClaims
    
class TokenClaims:
    user_id: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]

# FastAPI dependency
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenClaims:
    return await jwt_validator.validate_token(token)
```

### 3. RBAC Implementation & Permission Model

**Decision**: Hierarchical role model with tenant-scoped permissions and inheritance

**Rationale**:
- Supports both system administrators and tenant administrators as per spec
- Enables fine-grained permissions for folder and compliance operations
- Provides tenant isolation for role assignments
- Allows permission inheritance from tenant to folder levels

**Role Hierarchy**:
```
System Administrator (Global)
├── manage_tenants (create, update, delete tenants)
├── manage_storage_providers (configure global storage options)
└── manage_compliance_templates (define global compliance rules)

Tenant Administrator (Tenant-scoped)  
├── manage_tenant_config (update tenant settings)
├── manage_storage_config (configure tenant storage)
├── manage_folders (create, organize folder hierarchy)
├── manage_compliance_policies (set tenant/folder retention)
└── manage_master_data (define categories, document types)

Folder Manager (Folder-scoped)
├── manage_folder_metadata (update folder properties)
├── manage_folder_compliance (set folder-specific policies)
└── view_folder_contents (read folder structure)
```

**Implementation Approach**:
```python
# RBAC enforcement decorator
def require_permission(permission: str, scope: ResourceScope = ResourceScope.GLOBAL):
    def decorator(func):
        async def wrapper(current_user: TokenClaims, resource_id: str = None):
            if not rbac_service.has_permission(current_user, permission, scope, resource_id):
                raise HTTPException(403, "Insufficient permissions")
            return await func(current_user, resource_id)
        return wrapper
    return decorator

# Usage example
@require_permission("manage_folders", ResourceScope.TENANT)
async def create_folder(current_user: TokenClaims, tenant_id: str, folder_data: FolderCreate):
    # Implementation with automatic tenant_id validation
```

### 4. Multi-Database Strategy & Connection Management

**Decision**: SQLModel with async connection pooling and tenant-aware connection routing

**Rationale**:
- SQLModel provides Pydantic integration for type safety and API generation
- Async support essential for handling 1000+ concurrent requests
- Connection pooling reduces database overhead for multi-tenant operations
- Tenant-aware routing enables future database sharding if needed

**Alternatives Considered**:
- SQLAlchemy Core: Rejected due to lack of Pydantic integration
- Django ORM: Rejected due to FastAPI ecosystem mismatch
- Database-per-tenant: Rejected due to operational complexity at scale

**Implementation Approach**:
```python
# Database configuration
class DatabaseConfig:
    primary_url: str  # PostgreSQL
    secondary_url: str  # SQL Server (optional)
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30

# Async session management
class DatabaseManager:
    def __init__(self, config: DatabaseConfig)
    async def get_session(self, tenant_id: str = None) -> AsyncSession
    async def health_check(self) -> DatabaseHealth

# Tenant-aware repository base
class TenantAwareRepository:
    def __init__(self, session: AsyncSession, tenant_id: str)
    async def create(self, entity: BaseEntity) -> BaseEntity
    async def get_by_id(self, entity_id: str) -> Optional[BaseEntity]
    # Automatic tenant_id filtering in all queries
```

### 5. Threat Model & Security Implementation

**Decision**: Multi-layered security with encryption, tenant isolation, and audit logging

**Threat Model Summary**:
- **T1**: Cross-tenant data access via API parameter manipulation
- **T2**: Privilege escalation through role/permission bypass  
- **T3**: Data exposure via storage provider configuration manipulation
- **T4**: Compliance policy bypass leading to data retention violations
- **T5**: Audit trail tampering or loss

**Security Mitigations**:
```python
# T1 Mitigation: Tenant isolation enforcement
class TenantIsolationMiddleware:
    async def __call__(self, request: Request, call_next):
        # Extract tenant_id from JWT and validate against request parameters
        # Block cross-tenant access attempts
        
# T2 Mitigation: Permission validation at repository layer
class SecureRepository(TenantAwareRepository):
    async def get_by_id(self, entity_id: str, required_permission: str = None):
        # Double-check permissions even at data layer
        
# T3 Mitigation: Storage config encryption
class EncryptedStorageConfig(StorageConfig):
    @field_validator('credentials')
    def encrypt_credentials(cls, v):
        return encryption_service.encrypt(v)

# T4 Mitigation: Immutable compliance audit
class ComplianceAuditLog:
    # Append-only audit trail with cryptographic integrity
    
# T5 Mitigation: Distributed audit logging
# All operations logged to external audit service with tamper detection
```

**Encryption Strategy**:
- Credentials: AES-256 encryption with key rotation
- Data at rest: Delegated to storage provider (Azure/AWS/GCS encryption)
- Data in transit: TLS 1.3 for all communications
- Database: Transparent data encryption (TDE) when available

## Research Outcomes Summary

All NEEDS CLARIFICATION items resolved:
1. ✅ Cloud storage abstraction: Provider pattern with async interface
2. ✅ Authentication strategy: JWT validation with configurable providers  
3. ✅ RBAC implementation: Hierarchical roles with tenant-scoped permissions
4. ✅ Multi-database strategy: SQLModel with async pooling and tenant routing
5. ✅ Security implementation: Multi-layered defense with encryption and audit

**Next Phase**: Proceed to Phase 1 (Design & Contracts) with constitution compliance validation.