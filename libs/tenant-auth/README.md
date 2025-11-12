# tenant-auth

JWT-based authentication and RBAC middleware for multi-tenant applications.

## Features

- **JWT Validation**: Token extraction and validation
- **RBAC Support**: Role-based access control with hierarchical roles
- **Tenant Context**: Automatic tenant context injection
- **Permission Decorators**: Endpoint-level authorization

## Installation

```bash
uv pip install -e .
```

## Supported Roles

- System Admin
- Tenant Admin
- Folder Manager
