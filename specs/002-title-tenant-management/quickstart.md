# Quickstart — Tenant Management Service (MVP)

This quickstart explains how to run the service locally (developer flow) and demonstrates basic API calls using the generated contract.

Assumptions
- Service implemented as a NestJS microservice (per constitution). Uses Postgres + Prisma for persistence.

Run locally (developer)

1. Install dependencies (from repo root)

```bash
pnpm install
```

2. Start Postgres (local developer db) — ensure env vars set in `.env`

3. Run migrations (Prisma)

```bash
pnpm prisma migrate dev --name init
```

4. Start the service

```bash
pnpm --filter tenant-service start:dev
```

Example API calls (using OpenAPI contract)

Create tenant (Super Admin)

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"name":"District 42","storage_config":{"storage_type":"s3","location_identifier":"arn:aws:s3:::customer-bucket","provision":false}}' \
  http://localhost:3000/tenants
```

List tenants

```bash
curl http://localhost:3000/tenants
```

Create retention policy for container

```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"duration_days":3650,"action":"archive","legal_hold":false}' \
  http://localhost:3000/tenants/{tenantId}/containers/{containerId}/retention
```

Notes
- This quickstart assumes the tenant-service is available via `tenant-service` package in monorepo. Implementation must follow the OpenAPI contract in `specs/002-title-tenant-management/contracts/openapi.yaml`.
