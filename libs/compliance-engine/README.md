# compliance-engine

Retention policy enforcement, compliance scheduling, and audit trail management for document lifecycle.

## Features

- **Policy Engine**: Retention policy rule evaluation
- **Scheduled Enforcement**: Background task scheduling with APScheduler
- **Audit Trails**: Comprehensive compliance operation logging
- **Conflict Resolution**: Tenant vs folder policy resolution

## Installation

```bash
uv pip install -e .
```

## Usage

Retention policies are configured per tenant and folder with automatic enforcement scheduling.
