# Tenant Service - Development Guide

## Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose
- uv (package manager)

### Setup

1. **Install dependencies:**
   ```bash
   bash ./setup.sh
   ```

2. **Activate virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Start infrastructure (MSSQL + PostgreSQL):**
   ```bash
   docker compose -f infra/docker-compose.yml up -d
   ```

4. **Run tenant service:**
   ```bash
   # Using poe task
   poe run_ts
   
   # Or directly with uvicorn
   python -m uvicorn tenant_service.main:app --host 0.0.0.0 --port 8000 --reload --app-dir apps/tenant-service/src
   ```

The service will be available at `http://localhost:8000`

## Environment Configuration

The tenant service uses environment variables defined in `.env` (git-ignored). 

**Template:** See `apps/tenant-service/.env.example`

### Key Variables

- `DB_DATABASE_TYPE`: `sqlserver` or `postgresql`
- `DB_DATABASE_URL`: Connection string
- `__OPEN_API__`: `true` to enable OpenAPI/Swagger UI
- `LOG_LEVEL`: `debug`, `info`, `warning`, `error`, or `critical`

### Example .env for MSSQL

```bash
DB_DATABASE_TYPE=sqlserver
DB_DATABASE_URL=mssql+pyodbc://sa:DocitaiDev@123@localhost:1433/docitai_dev?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
__OPEN_API__=true
LOG_LEVEL=info
```

## API Endpoints

### Health & Monitoring
- **Health Check (Liveness):** `GET /health`
- **Readiness Check:** `GET /health/ready`
- **Detailed Status:** `GET /health/detailed`
- **Prometheus Metrics:** `GET /metrics`
- **OpenAPI Schema:** `GET /openapi-json`
- **Swagger UI:** `GET /openapi` (when enabled)

### Tenant Management (Examples)
- **Create Tenant:** `POST /api/v1/tenants`
- **List Tenants:** `GET /api/v1/tenants`
- **Get Tenant:** `GET /api/v1/tenants/{tenant_id}`
- **Update Tenant:** `PUT /api/v1/tenants/{tenant_id}`

## VSCode Debug Profiles

Four debug configurations available in `.vscode/launch.json`:

1. **Tenant Service (FastAPI)** - Default SQLite dev setup
2. **Tenant Service (FastAPI with MSSQL)** - MSSQL Server backend
3. **Tenant Service Tests** - Run pytest suite
4. **Health Check Endpoint** - Service with health check verification

**To debug:** F5 or Run → Start Debugging, then select configuration

## Available Tasks

Use `Ctrl+Shift+P` → "Tasks: Run Task" or from `.vscode/tasks.json`:

- **Run Tenant Service** - Start service with hot reload
- **Test Tenant Service** - Run pytest tests
- **Lint Code** - Run ruff linter with fixes
- **Format Code** - Format with ruff
- **Type Check** - Run mypy type checking
- **Health Check** - Test `/health` endpoint
- **Metrics Endpoint** - Fetch Prometheus metrics
- **OpenAPI Schema** - Fetch OpenAPI specification
- **Docker Compose Up** - Start infrastructure
- **Docker Compose Down** - Stop infrastructure

## Database Configuration

### MSSQL Server
- **Container:** `docitai-mssql` on `localhost:1433`
- **User:** `sa`
- **Password:** `DocitaiDev@123`
- **Database:** `docitai_dev`
- **Driver:** ODBC Driver 18 for SQL Server

### PostgreSQL
- **Container:** `docitai-postgres` on `localhost:5432`
- **User:** `docitai`
- **Password:** `docitai-dev-password`
- **Database:** `docitai_dev`

### Managing Infrastructure

```bash
# Start services
docker compose -f infra/docker-compose.yml up -d

# Stop services
docker compose -f infra/docker-compose.yml down

# View logs
docker compose -f infra/docker-compose.yml logs -f mssql
docker compose -f infra/docker-compose.yml logs -f postgres

# Access MSSQL
docker exec -it docitai-mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P DocitaiDev@123

# Access PostgreSQL
docker exec -it docitai-postgres psql -U docitai -d docitai_dev
```

## Dependency Groups

Install specific database support with uv:

```bash
# MSSQL support
uv sync --group mssql

# PostgreSQL support
uv sync --group postgres

# Development tools
uv sync --group dev
```

## Testing

```bash
# Run all tests
pytest apps/tenant-service/tests/ -v

# Run specific test file
pytest apps/tenant-service/tests/unit/test_health_check.py -v

# Run with coverage
pytest apps/tenant-service/tests/ --cov=apps/tenant-service/src --cov-report=html

# Run in watch mode (requires pytest-watch)
ptw apps/tenant-service/tests/
```

## Code Quality

```bash
# Run all linters and formatters
poe lint
poe format

# Individual tools
ruff check --fix .
ruff format .
mypy apps/tenant-service/src libs/
pylint apps/tenant-service/src libs/
```

## Project Structure

```
├── apps/
│   └── tenant-service/          # Tenant microservice
│       ├── src/
│       │   └── tenant_service/
│       │       ├── main.py      # FastAPI app entry point
│       │       ├── config.py    # Settings & configuration
│       │       ├── api/v1/      # REST endpoints
│       │       ├── domain/      # Business logic
│       │       └── infrastructure/
│       └── tests/               # Unit & integration tests
├── libs/
│   ├── fastapi-core/            # Shared FastAPI foundation
│   │   └── fastapi_core/
│   │       ├── app_factory.py  # App creation factory
│   │       ├── config/         # Configuration management
│   │       ├── middlewares/    # Reusable middleware (including metrics)
│   │       └── metrics.py      # Prometheus metrics definitions
│   ├── database-core/           # Database abstraction layer
│   ├── storage-adapter/         # Cloud storage (S3, Azure, GCS)
│   ├── tenant-auth/             # JWT authentication
│   └── compliance-engine/       # Compliance & retention logic
└── infra/
    └── docker-compose.yml       # Local infrastructure
```

## Common Issues

### Service won't start
- Check `.env` file exists and LOG_LEVEL is lowercase
- Verify Docker containers are running: `docker compose -f infra/docker-compose.yml ps`
- Check logs: `tail -f tenant_service.log`

### OpenAPI endpoint returns 404
- Ensure `__OPEN_API__=true` in `.env`
- Restart service after changing `.env`

### MSSQL connection fails
- Verify `docitai-mssql` container is running: `docker ps | grep mssql`
- Check connection string in `.env` matches container settings
- Test connection: `docker exec docitai-mssql sqlcmd -S localhost -U sa -P DocitaiDev@123 -Q "SELECT 1"`

### Import errors in IDE
- Configure Python interpreter to use `.venv`
- Ensure workspace is opened as folder, not subfolder
- Reload VS Code window: `Cmd+Shift+P` → "Developer: Reload Window"

## Performance Monitoring

### Metrics
Access Prometheus metrics at `http://localhost:8000/metrics`

**Key metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency histogram
- `db_queries_total` - Database query count
- `auth_attempts_total` - Authentication attempts
- `cache_hits_total` - Cache hit rate

### Health Status
```bash
curl http://localhost:8000/health/detailed | python3 -m json.tool
```

## Further Reading

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)
- [Pydantic V2 Guide](https://docs.pydantic.dev/latest/)
- [Docker Compose Reference](https://docs.docker.com/compose/reference/)
