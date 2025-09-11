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
