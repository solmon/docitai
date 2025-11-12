# Phase 1: Data Model Design

**Feature**: Tenant Management Service for Document Management System  
**Date**: November 12, 2025  
**Status**: Complete

## Entity Definitions

### Core Domain Entities

#### Tenant
**Purpose**: Root aggregate representing an organization using the document management system

```python
class Tenant(BaseEntity):
    """Tenant aggregate root with business logic for onboarding and configuration"""
    
    # Identity
    tenant_id: str = Field(primary_key=True, description="Unique tenant identifier")
    
    # Business Information
    name: str = Field(max_length=255, description="Organization display name")
    contact_email: str = Field(description="Primary contact email for tenant")
    contact_phone: Optional[str] = Field(description="Primary contact phone")
    subscription_plan: SubscriptionPlan = Field(description="Current subscription level")
    
    # Operational
    status: TenantStatus = Field(default=TenantStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Configuration
    settings: TenantSettings = Field(description="Tenant-specific configuration")
    
    # Business Rules
    def can_create_folder(self) -> bool:
        """Check if tenant can create new folders based on subscription limits"""
        
    def can_configure_storage(self) -> bool:
        """Validate tenant permissions for storage configuration"""
        
    def apply_retention_policy(self, policy: RetentionPolicy) -> None:
        """Apply retention policy with business validation"""

class SubscriptionPlan(str, Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional" 
    ENTERPRISE = "enterprise"

class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"
    DEACTIVATED = "deactivated"

class TenantSettings(BaseModel):
    """Value object for tenant configuration"""
    max_folders: int = Field(default=100)
    max_storage_gb: int = Field(default=10)
    enable_compliance_audit: bool = Field(default=True)
    default_retention_days: int = Field(default=2555)  # 7 years
```

#### StorageConfiguration
**Purpose**: Tenant-specific storage provider configuration with encrypted credentials

```python
class StorageConfiguration(BaseEntity):
    """Storage configuration entity with encrypted credentials"""
    
    # Identity
    config_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.tenant_id", index=True)
    
    # Provider Configuration
    provider_type: StorageProviderType = Field(description="Cloud storage provider")
    provider_region: str = Field(description="Provider-specific region/location")
    
    # Connection Settings
    connection_config: EncryptedConnectionConfig = Field(description="Encrypted provider settings")
    
    # Operational
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_validated: Optional[datetime] = Field(description="Last successful connection test")
    
    # Business Rules
    async def validate_connection(self) -> ValidationResult:
        """Test connection to storage provider"""
        
    def encrypt_credentials(self) -> None:
        """Ensure credentials are properly encrypted"""

class StorageProviderType(str, Enum):
    AZURE_BLOB = "azure_blob"
    AWS_S3 = "aws_s3" 
    GOOGLE_CLOUD_STORAGE = "gcs"
    
class EncryptedConnectionConfig(BaseModel):
    """Value object for encrypted storage provider credentials"""
    endpoint_url: str
    access_key_encrypted: str  # AES-256 encrypted
    secret_key_encrypted: str  # AES-256 encrypted
    bucket_name: str
    additional_config: Dict[str, Any] = Field(default_factory=dict)
```

#### Folder
**Purpose**: Hierarchical organizational structure for document management

```python
class Folder(BaseEntity):
    """Folder entity supporting hierarchical organization with metadata"""
    
    # Identity  
    folder_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.tenant_id", index=True)
    
    # Hierarchy
    name: str = Field(max_length=255, description="Folder display name")
    parent_folder_id: Optional[str] = Field(foreign_key="folder.folder_id")
    path: str = Field(description="Full hierarchical path for efficient queries")
    level: int = Field(description="Depth in hierarchy (0 = root)")
    
    # Metadata
    description: Optional[str] = Field(description="Folder purpose description")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom attributes")
    
    # Operational
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    children: List["Folder"] = Relationship(back_populates="parent")
    parent: Optional["Folder"] = Relationship(back_populates="children")
    
    # Business Rules
    def validate_hierarchy(self) -> ValidationResult:
        """Prevent circular references and enforce depth limits"""
        
    def build_path(self) -> str:
        """Generate full hierarchical path"""
        
    def can_delete(self) -> bool:
        """Check if folder can be safely deleted"""
```

#### RetentionPolicy
**Purpose**: Data lifecycle and compliance rule management

```python
class RetentionPolicy(BaseEntity):
    """Retention policy entity for compliance and data lifecycle management"""
    
    # Identity
    policy_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.tenant_id", index=True)
    
    # Scope
    scope_type: PolicyScope = Field(description="Application scope of policy")
    scope_id: Optional[str] = Field(description="Specific folder ID if folder-scoped")
    
    # Policy Definition
    name: str = Field(max_length=255, description="Policy display name")
    retention_period_days: int = Field(description="Document retention duration")
    compliance_framework: ComplianceFramework = Field(description="Regulatory framework")
    
    # Actions
    retention_action: RetentionAction = Field(description="Action when retention period expires")
    
    # Operational
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    effective_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Business Rules
    def applies_to_folder(self, folder_id: str) -> bool:
        """Check if policy applies to specific folder"""
        
    def calculate_expiry_date(self, document_date: datetime) -> datetime:
        """Calculate when document expires under this policy"""

class PolicyScope(str, Enum):
    TENANT = "tenant"
    FOLDER = "folder"

class ComplianceFramework(str, Enum):
    GDPR = "gdpr"
    HIPAA = "hipaa" 
    SOX = "sox"
    CUSTOM = "custom"

class RetentionAction(str, Enum):
    DELETE = "delete"
    ARCHIVE = "archive"
    NOTIFY_ONLY = "notify_only"
```

#### DocumentCategory & DocumentType (Master Data)
**Purpose**: Tenant-specific taxonomy for document classification

```python
class DocumentCategory(BaseEntity):
    """Master data for document classification"""
    
    # Identity
    category_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.tenant_id", index=True)
    
    # Classification
    name: str = Field(max_length=255, description="Category display name")
    description: Optional[str] = Field(description="Category purpose and usage")
    parent_category_id: Optional[str] = Field(foreign_key="document_category.category_id")
    
    # Configuration
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Business Rules
    def can_delete(self) -> bool:
        """Check if category can be safely removed"""

class DocumentType(BaseEntity):
    """Document type template with custom attributes"""
    
    # Identity
    type_id: str = Field(primary_key=True)
    tenant_id: str = Field(foreign_key="tenant.tenant_id", index=True)
    
    # Definition
    name: str = Field(max_length=255, description="Document type name")
    description: Optional[str] = Field(description="Type purpose and usage")
    
    # Schema
    custom_attributes: List[CustomAttribute] = Field(description="Configurable document attributes")
    validation_rules: Dict[str, Any] = Field(default_factory=dict)
    
    # Operational
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class CustomAttribute(BaseModel):
    """Value object for document type custom attributes"""
    name: str
    attribute_type: AttributeType
    is_required: bool = False
    default_value: Optional[Any] = None
    validation_pattern: Optional[str] = None

class AttributeType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    BOOLEAN = "boolean"
    SELECT = "select"
```

## Aggregate Boundaries & Relationships

### Tenant Aggregate
- **Root**: Tenant
- **Entities**: StorageConfiguration, RetentionPolicy (tenant-scoped), DocumentCategory, DocumentType
- **Business Rules**: 
  - Storage configuration changes require tenant validation
  - Retention policies inherit from tenant defaults
  - Master data is tenant-isolated

### Folder Aggregate  
- **Root**: Folder
- **Entities**: RetentionPolicy (folder-scoped)
- **Value Objects**: FolderMetadata
- **Business Rules**:
  - Hierarchy validation prevents cycles
  - Path updates cascade to children
  - Deletion validates empty folder or handles children

## Data Validation Rules

### Cross-Entity Validation
```python
class TenantDataValidator:
    """Domain service for cross-entity validation"""
    
    async def validate_storage_config(self, tenant_id: str, config: StorageConfiguration) -> ValidationResult:
        """Validate storage config against tenant limits and existing configs"""
        
    async def validate_folder_hierarchy(self, folder: Folder) -> ValidationResult:
        """Ensure folder hierarchy integrity and depth limits"""
        
    async def validate_retention_policy_conflict(self, policy: RetentionPolicy) -> ValidationResult:
        """Check for conflicting retention policies and resolve precedence"""
```

### State Transitions
```python
# Tenant lifecycle
ACTIVE → SUSPENDED (administrative action)
SUSPENDED → ACTIVE (reactivation) 
ACTIVE → DEACTIVATED (permanent closure)
PENDING_ACTIVATION → ACTIVE (onboarding completion)

# Storage Configuration lifecycle  
DRAFT → ACTIVE (validation success)
ACTIVE → INACTIVE (administrative disable)
ACTIVE → ERROR (connection failure)

# Folder lifecycle
CREATED → ACTIVE (immediate)
ACTIVE → ARCHIVED (retention policy)
ARCHIVED → DELETED (final cleanup)
```

## Multi-Tenant Isolation Strategy

### Data Isolation
- All entities include `tenant_id` as mandatory field
- Repository layer automatically filters by tenant context
- Database constraints prevent cross-tenant foreign keys
- Indexes optimized for tenant-scoped queries

### Configuration Isolation
- Storage configurations are tenant-specific
- Retention policies scoped by tenant and folder
- Master data (categories, types) completely tenant-isolated
- No shared configuration between tenants

### Audit & Compliance Isolation
- All operations include tenant context in audit logs
- Compliance policies enforced per-tenant
- Retention actions scoped to tenant boundaries
- Cross-tenant operations explicitly prohibited and logged

This data model ensures strict tenant isolation, supports the hierarchical folder organization requirements, enables compliance policy enforcement, and provides the foundation for role-based access control implementation.