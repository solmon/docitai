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
# Abstract interface in storage-adapter library (new cross-cutting library)
class CloudStorageProvider(ABC):
    async def put_object(self, bucket: str, key: str, data: bytes, metadata: Dict) -> str
    async def get_object(self, bucket: str, key: str) -> bytes
    async def delete_object(self, bucket: str, key: str) -> bool
    async def list_objects(self, bucket: str, prefix: str) -> List[StorageObject]

# Provider implementations in storage-adapter library
class AzureBlobProvider(CloudStorageProvider): ...
class AWSS3Provider(CloudStorageProvider): ...
class GCSProvider(CloudStorageProvider): ...

# Factory for tenant-specific provider instantiation
class StorageProviderFactory:
    def get_provider(self, tenant_config: StorageConfig) -> CloudStorageProvider
```

**Monorepo Integration**:
- Storage-adapter library with own pyproject.toml containing provider-specific SDKs
- Shared in workspace root: aiofiles, pydantic for common async/validation needs
- Project-specific: boto3 (S3), azure-storage-blob (Azure), google-cloud-storage (GCS)

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
# JWT validation in tenant-auth library (new cross-cutting library)
class JWTValidator:
    def __init__(self, issuer: str, audience: str, jwks_url: str)
    async def validate_token(self, token: str) -> TokenClaims
    
class TokenClaims:
    user_id: str
    tenant_id: str
    roles: List[str]
    permissions: List[str]

# FastAPI dependency using fastapi-core patterns
async def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenClaims:
    return await jwt_validator.validate_token(token)
```

**FastAPI-Core Integration**:
- Leverage existing fastapi-core middleware patterns for consistent request/response handling
- Extend fastapi-core logging with tenant context injection
- Use fastapi-core app factory pattern for service initialization
- Tenant-auth library integrates with fastapi-core security middleware

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
# Database configuration in database-core library (new cross-cutting library)
class DatabaseConfig:
    primary_url: str  # PostgreSQL
    secondary_url: str  # SQL Server (optional)
    pool_size: int = 20
    max_overflow: int = 30
    pool_timeout: int = 30

# Async session management in database-core library
class DatabaseManager:
    def __init__(self, config: DatabaseConfig)
    async def get_session(self, tenant_id: str = None) -> AsyncSession
    async def health_check(self) -> DatabaseHealth

# Tenant-aware repository base in database-core library
class TenantAwareRepository:
    def __init__(self, session: AsyncSession, tenant_id: str)
    async def create(self, entity: BaseEntity) -> BaseEntity
    async def get_by_id(self, entity_id: str) -> Optional[BaseEntity]
    # Automatic tenant_id filtering in all queries
```

**Monorepo Dependency Strategy**:
- database-core library dependencies: SQLModel, asyncpg (PostgreSQL), aioodbc (SQL Server), alembic
- Workspace root shared dependencies: pydantic (used across all libraries), pytest (testing)
- Individual project dependencies only for specific database drivers and provider-specific needs

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

### 6. Cross-Cutting Library Strategy & UV Monorepo Integration

**Decision**: Create four new reusable libraries leveraging existing fastapi-core foundation

**Rationale**:
- Follows constitution requirement for library-first architecture
- Enables reuse across future microservices in the document management system
- Individual pyproject.toml files allow precise dependency management
- UV workspace integration provides efficient dependency resolution and caching

**Library Architecture**:
1. **storage-adapter** (NEW): Cloud provider abstraction with async interface
   - Dependencies: boto3, azure-storage-blob, google-cloud-storage, aiofiles
   - Scope: Multi-provider storage operations with tenant-aware configurations

2. **tenant-auth** (NEW): Authentication and RBAC middleware for FastAPI
   - Dependencies: PyJWT, passlib, python-multipart
   - Scope: JWT validation, role-based authorization, tenant isolation

3. **compliance-engine** (NEW): Policy engine for retention and compliance automation
   - Dependencies: celery (background tasks), croniter (scheduling)
   - Scope: Policy definition, automated enforcement, audit trail generation

4. **database-core** (NEW): Multi-database SQLModel foundation with tenant awareness
   - Dependencies: SQLModel, asyncpg, aioodbc, alembic
   - Scope: Database abstraction, connection management, tenant-scoped repositories

**Dependency Management Strategy**:
```toml
# Workspace root pyproject.toml (shared across monorepo)
[project]
dependencies = [
    "fastapi>=0.115.12",     # Used by fastapi-core and tenant-service
    "pydantic>=2.10.4",      # Used by all libraries for validation
    "uvicorn>=0.34.0",       # Server for all FastAPI services
    "pytest>=8.3.4",        # Testing across all projects
    "structlog>=24.4.0"      # Logging from fastapi-core
]

# Individual library pyproject.toml (project-specific only)
[project]  # storage-adapter example
dependencies = [
    "storage-adapter",       # Self-reference for uv workspace
    "boto3>=1.34.0",        # S3 provider specific
    "azure-storage-blob>=12.19.0",  # Azure provider specific
    "google-cloud-storage>=2.10.0", # GCS provider specific
    "aiofiles>=23.2.0"      # Async file operations
]
```

**Integration with FastAPI-Core**:
- Extend existing app factory patterns for tenant-service initialization
- Leverage middleware framework for tenant-auth integration
- Use configuration management patterns for multi-database setup
- Extend logging context with tenant-aware structured logging

## Research Outcomes Summary

All NEEDS CLARIFICATION items resolved:
1. ✅ Cloud storage abstraction: Provider pattern with async interface
2. ✅ Authentication strategy: JWT validation with configurable providers  
3. ✅ RBAC implementation: Hierarchical roles with tenant-scoped permissions
4. ✅ Multi-database strategy: SQLModel with async pooling and tenant routing
5. ✅ Security implementation: Multi-layered defense with encryption and audit
6. ✅ Library strategy: Four cross-cutting libraries with UV monorepo integration

**Library Creation Plan**:
- ✅ Use existing fastapi-core as foundation
- ✅ Create storage-adapter, tenant-auth, compliance-engine, database-core libraries
- ✅ Individual pyproject.toml with project-specific dependencies only
- ✅ Workspace root dependencies for commonly reused packages

**Next Phase**: Proceed to Phase 1 (Design & Contracts) with constitution compliance validation.