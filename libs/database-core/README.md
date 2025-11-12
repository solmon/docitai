# database-core

Multi-database abstraction layer with TenantAwareBase model for Docitai DMS.

## Features

- **Multi-Database Support**: SQLModel abstraction for PostgreSQL and SQL Server
- **Tenant Isolation**: TenantAwareBase model enforcing tenant_id on all entities
- **Alembic Migrations**: Database schema management
- **Type Safety**: Full Pydantic integration

## Installation

```bash
uv pip install -e .
```

## Usage

```python
from database_core.base import TenantAwareBase
from sqlmodel import SQLModel, Field

class MyEntity(TenantAwareBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
```
