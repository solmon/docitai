# Quickstart: Multitenant DMS (Developer)

This quickstart demonstrates the basic developer flow to run contract checks and a minimal upload/download smoke test.

Prerequisites:
- Node.js 20+, pnpm
- PostgreSQL running and accessible via DATABASE_URL
- OpenSearch running for search index (optional for smoke test)

Steps:
1. Install dependencies

2. Generate Prisma client and run migrations (from repo root)

3. Run contract validation against `contracts/openapi.yaml`

4. Run a smoke script to perform:
   - create tenant
   - create user
   - create folder
   - upload small file
   - confirm metadata saved and audit event created

This quickstart is intentionally minimal; implementation repository will expand these steps into runnable scripts.
# Quickstart — Multitenant DMS (Dev)

Date: 2025-09-11

This quickstart describes how to spin up the service locally for development and run the minimal contract tests, including frontend setup (Next.js + Radix UI + Tailwind + shadcn).

Prereqs: Node 18+, pnpm, Docker (for PostgreSQL), Redis (optional)

1. Install dependencies

```bash
pnpm install
```

2. Start Postgres (Dev)

```bash
docker run --name dms-postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15
```

3. Backend migrations

```bash
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
pnpm --filter backend prisma migrate dev
```

4. Frontend setup (Next.js + Tailwind + Radix UI + shadcn)

```bash
cd frontend
pnpm create next-app . --ts --eslint
pnpm install tailwindcss postcss autoprefixer
pnpm dlx tailwindcss init -p
# Install UI libs
pnpm add @radix-ui/react-primitive @radix-ui/react-popover @radix-ui/react-dialog
pnpm add @shadcn/ui # (replace with actual shadcn package name used in this repo)
pnpm add chart.js react-chartjs-2
```

5. Run contract tests (they should fail initially)

```bash
pnpm test:contract
```

6. Start backend

```bash
pnpm --filter backend start:dev
```

7. Start frontend

```bash
cd frontend
pnpm dev
```

Docker quickstart (local dev):

1. Start local infra

```bash
docker compose -f infra/docker-compose.dms.yml up -d
```

2. Set DATABASE_URL e.g.:

```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/docitai_dev"
```

3. From `backend/` run:

```bash
pnpm --filter backend prisma:generate
pnpm --filter backend prisma:migrate
```

4. Run contract tests (from repo root)

```bash
pnpm test:contract
```

Note: contract tests are intended to fail until the backend implementation is available at `http://localhost:3000`.
