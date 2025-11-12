# Phase 1: Quickstart Guide

**Feature**: Tenant Management Service for Document Management System  
**Date**: November 12, 2025  
**Status**: Complete

## Overview

The Tenant Management Service is a microservice that provides comprehensive multi-tenant administration capabilities for document management systems. It enables system administrators to onboard tenants, configure cloud-agnostic storage, organize hierarchical folder structures, and enforce compliance policies with strict tenant isolation and role-based access control.

## Architecture Summary

### Core Principles
- **Library-First**: Reusable business logic packaged as libraries
- **Cloud Agnostic**: Support for Azure Blob, AWS S3, Google Cloud Storage via abstraction layer
- **Multi-Tenant**: Strict tenant isolation with tenant-aware operations
- **Security by Design**: RBAC enforcement, encryption, comprehensive audit trails
- **Observability**: Structured logging, metrics, and distributed tracing

### Technology Stack
- **API Framework**: FastAPI with async support
- **Data Layer**: SQLModel (PostgreSQL primary, SQL Server secondary)
- **Authentication**: JWT with configurable identity providers
- **Storage Abstraction**: Provider pattern for cloud storage
- **Testing**: pytest with contract validation
- **Deployment**: Docker containers, Kubernetes orchestration

## Key Components

### 1. Core Libraries
```
libs/
├── tenant-management/      # Business logic and domain entities
├── storage-abstraction/    # Cloud provider abstraction layer
└── rbac-enforcement/       # Role-based access control
```

### 2. API Service
```
apps/tenant-management-api/ # FastAPI service composition
```

### 3. Domain Entities
- **Tenant**: Organization with subscription and settings
- **StorageConfiguration**: Encrypted cloud provider settings
- **Folder**: Hierarchical document organization
- **RetentionPolicy**: Compliance and data lifecycle rules
- **DocumentCategory/Type**: Master data for classification

## Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (or SQL Server)
- Docker & Kubernetes (for deployment)
- Cloud storage account (Azure/AWS/GCS)

### 1. Environment Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure database
export DATABASE_URL="postgresql://user:pass@localhost/tenant_mgmt"

# Configure JWT validation
export JWT_ISSUER="https://your-identity-provider.com"
export JWT_AUDIENCE="tenant-management-api"
export JWKS_URL="https://your-identity-provider.com/.well-known/jwks.json"

# Configure encryption
export ENCRYPTION_KEY="your-aes-256-encryption-key"
```

### 2. Database Migration
```bash
# Initialize database schema
alembic upgrade head

# Create initial system admin user (via identity provider)
# Ensure JWT includes role: "system_administrator"
```

### 3. Run Service
```bash
# Development mode
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (with gunicorn)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## API Usage Examples

### 1. Create New Tenant
```bash
curl -X POST https://api.example.com/tenant-management/v1/tenants \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "contact_email": "admin@acme.com", 
    "contact_phone": "+1-555-123-4567",
    "subscription_plan": "professional",
    "settings": {
      "max_folders": 500,
      "max_storage_gb": 100,
      "enable_compliance_audit": true,
      "default_retention_days": 2555
    }
  }'
```

### 2. Configure Storage Provider
```bash
curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/storage-config \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider_type": "azure_blob",
    "provider_region": "East US",
    "connection_config": {
      "endpoint_url": "https://storage.blob.core.windows.net/",
      "access_key": "storage_account_name",
      "secret_key": "storage_account_key", 
      "bucket_name": "acme-documents",
      "additional_config": {
        "sas_token_expiry_hours": 24
      }
    }
  }'
```

### 3. Create Folder Structure
```bash
# Create root folder
curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/folders \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Legal Documents",
    "description": "All legal and compliance documents",
    "metadata": {
      "department": "legal",
      "classification": "confidential"
    }
  }'

# Create subfolder
curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/folders \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Contracts",
    "parent_folder_id": "folder_legal_001",
    "description": "Customer and vendor contracts",
    "metadata": {
      "document_type": "contracts",
      "retention_category": "high"
    }
  }'
```

### 4. Set Retention Policy
```bash
curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/retention-policies \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "scope_type": "folder",
    "scope_id": "folder_contracts_001",
    "name": "Contract Retention - GDPR",
    "retention_period_days": 2555,
    "compliance_framework": "gdpr",
    "retention_action": "archive",
    "effective_date": "2025-01-01T00:00:00Z"
  }'
```

### 5. Define Document Categories
```bash
curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/document-categories \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Financial Records",
    "description": "Invoices, receipts, tax documents"
  }'

curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/document-types \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Invoice",
    "description": "Customer invoice document",
    "custom_attributes": [
      {
        "name": "invoice_number",
        "attribute_type": "text",
        "is_required": true,
        "validation_pattern": "^INV-[0-9]{6}$"
      },
      {
        "name": "amount",
        "attribute_type": "number",
        "is_required": true
      },
      {
        "name": "due_date",
        "attribute_type": "date",
        "is_required": true
      }
    ]
  }'
```

## Role-Based Access Control

### System Administrator Permissions
- `manage_tenants`: Create, update, delete tenants
- `manage_storage_providers`: Configure global storage options  
- `manage_compliance_templates`: Define global compliance rules

### Tenant Administrator Permissions (Tenant-Scoped)
- `manage_tenant_config`: Update tenant settings
- `manage_storage_config`: Configure tenant storage
- `manage_folders`: Create, organize folder hierarchy
- `manage_compliance_policies`: Set retention policies
- `manage_master_data`: Define categories, document types

### JWT Token Claims Required
```json
{
  "user_id": "user_123",
  "tenant_id": "tenant_12345",
  "roles": ["tenant_administrator"],
  "permissions": [
    "manage_folders",
    "manage_storage_config", 
    "manage_compliance_policies"
  ],
  "iss": "https://identity-provider.com",
  "aud": "tenant-management-api",
  "exp": 1672531200
}
```

## Monitoring & Observability

### Health Checks
```bash
# Service health
curl https://api.example.com/tenant-management/v1/health

# Storage configuration validation
curl -X POST https://api.example.com/tenant-management/v1/tenants/tenant_12345/storage-config/validate \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Metrics (Prometheus format)
- `tenant_operations_total{tenant_id, operation, status}`
- `storage_operations_duration_seconds{provider, operation}`
- `folder_hierarchy_depth{tenant_id}`
- `retention_policies_active{tenant_id, compliance_framework}`
- `rbac_authorization_checks_total{permission, result}`

### Structured Logging
All log entries include:
```json
{
  "timestamp": "2025-11-12T10:30:00Z",
  "level": "INFO",
  "service": "tenant-management-api",
  "tenant_id": "tenant_12345",
  "user_id": "user_123",
  "request_id": "req_abc123",
  "operation": "create_folder",
  "message": "Folder created successfully",
  "metadata": {
    "folder_id": "folder_001",
    "parent_id": "folder_root"
  }
}
```

## Deployment

### Docker Container
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tenant-management-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: tenant-management-api
  template:
    spec:
      containers:
      - name: api
        image: tenant-management-api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secret
              key: url
        resources:
          requests:
            memory: "256Mi"
            cpu: "200m"
          limits:
            memory: "512Mi" 
            cpu: "500m"
```

## Security Considerations

### Data Protection
- All credentials encrypted with AES-256
- TLS 1.3 for all communications
- Secrets managed via Kubernetes secrets or external secret stores
- No sensitive data in logs or error messages

### Tenant Isolation
- All database queries include tenant_id filter
- Middleware validates JWT tenant claims against request parameters
- Cross-tenant access attempts logged as security events
- Storage configurations provide tenant-specific bucket isolation

### Audit & Compliance
- All operations logged with full context
- Immutable audit trail for compliance operations
- Retention policy enforcement automated
- Regular compliance reports available via metrics

## Next Steps

1. **Implementation Phase**: Use this quickstart as foundation for development
2. **Contract Tests**: Implement OpenAPI contract validation tests
3. **Integration Testing**: Test with real cloud storage providers
4. **Performance Testing**: Validate 1000+ concurrent tenant operations
5. **Security Review**: Complete threat model validation and penetration testing

This quickstart provides the essential information needed to understand, deploy, and operate the Tenant Management Service within a document management system architecture.