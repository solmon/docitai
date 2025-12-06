# Infrastructure Setup

This directory contains Docker Compose configurations for local development and testing of the Docitai platform dependencies.

## Services

### PostgreSQL
- **Image**: `postgres:16-alpine`
- **Port**: `5432`
- **User**: `docitai`
- **Password**: `docitai-dev-password`
- **Database**: `docitai_dev`
- **Volume**: `postgres_data`

### MSSQL Server
- **Image**: `mcr.microsoft.com/mssql/server:2022-latest`
- **Port**: `1433`
- **SA Password**: `DocitaiDev@123`
- **Edition**: Developer
- **Volumes**:
  - `mssql_data` - Database files
  - `mssql_log` - Transaction logs
  - `mssql_backup` - Backup files

### PgAdmin (PostgreSQL Management UI)
- **Image**: `dpage/pgadmin4:latest`
- **Port**: `5050`
- **Email**: `admin@docitai.local`
- **Password**: `admin-password`
- **Access**: http://localhost:5050

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- At least 2GB of available RAM
- Port availability: 5432 (PostgreSQL), 1433 (MSSQL), 5050 (PgAdmin)

### Start Services
```bash
# From the repo root or infra directory
docker-compose -f infra/docker-compose.yml up -d

# View logs
docker-compose -f infra/docker-compose.yml logs -f

# Check service status
docker-compose -f infra/docker-compose.yml ps
```

### Stop Services
```bash
docker-compose -f infra/docker-compose.yml down
```

### Stop and Remove All Data
```bash
docker-compose -f infra/docker-compose.yml down -v
```

## Connection Strings

### PostgreSQL
```
postgresql://docitai:docitai-dev-password@localhost:5432/docitai_dev
```

### MSSQL Server
```
mssql+pyodbc://sa:DocitaiDev@123@localhost:1433/master?driver=ODBC+Driver+17+for+SQL+Server
```

Or with SQLAlchemy:
```
mssql+pymssql://sa:DocitaiDev@123@localhost:1433/master
```

## Environment Variables

Copy `.env.example` to `.env` to customize configuration:
```bash
cp infra/.env.example .env
```

## Health Checks

All services include health checks that can be monitored:

```bash
# Check PostgreSQL
docker-compose -f infra/docker-compose.yml exec postgres pg_isready -U docitai -d docitai_dev

# Check MSSQL
docker-compose -f infra/docker-compose.yml exec mssql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P 'DocitaiDev@123' -Q 'SELECT 1'
```

## Connecting from Application

### Using Environment Variables

Set these in your application `.env`:
```
DATABASE_URL=postgresql://docitai:docitai-dev-password@localhost:5432/docitai_dev
DATABASE_TYPE=postgresql
MSSQL_DATABASE_URL=mssql+pymssql://sa:DocitaiDev@123@localhost:1433/master
```

### Python Connection Example

**PostgreSQL:**
```python
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://docitai:docitai-dev-password@localhost:5432/docitai_dev"
)
```

**MSSQL:**
```python
from sqlalchemy import create_engine

engine = create_engine(
    "mssql+pymssql://sa:DocitaiDev@123@localhost:1433/master"
)
```

## Database Initialization

### PostgreSQL
After starting services, the database is automatically created and ready for migrations:

```bash
# Run Alembic migrations
alembic upgrade head
```

### MSSQL
Connect and create database if needed:

```sql
CREATE DATABASE docitai_dev;
GO
USE docitai_dev;
GO
```

## Troubleshooting

### PostgreSQL Won't Start
```bash
# Check logs
docker-compose -f infra/docker-compose.yml logs postgres

# Reset data
docker-compose -f infra/docker-compose.yml down -v
docker-compose -f infra/docker-compose.yml up -d postgres
```

### MSSQL Won't Start
- Requires at least 2GB RAM
- Check available disk space
- Verify port 1433 is not in use

```bash
# Check logs
docker-compose -f infra/docker-compose.yml logs mssql

# Reset data
docker-compose -f infra/docker-compose.yml down -v
docker-compose -f infra/docker-compose.yml up -d mssql
```

### Connection Refused
1. Ensure services are running: `docker-compose ps`
2. Verify correct port mappings
3. Check firewall rules
4. Wait for health checks to pass

### PgAdmin Access Issues
- Clear browser cache
- Try incognito/private mode
- Check port 5050 is accessible
- Restart pgadmin service: `docker-compose restart pgadmin`

## Development Workflow

1. **Start infrastructure:**
   ```bash
   docker-compose -f infra/docker-compose.yml up -d
   ```

2. **Wait for health checks:**
   ```bash
   docker-compose -f infra/docker-compose.yml ps
   ```

3. **Run application with database:**
   ```bash
   cd apps/tenant-service
   python -m uvicorn src.tenant_service.main:app --reload
   ```

4. **Access PgAdmin for PostgreSQL:**
   - http://localhost:5050
   - Add server with: `postgres:5432`

5. **Stop services when done:**
   ```bash
   docker-compose -f infra/docker-compose.yml down
   ```

## Tenant Service Deployment

### Using Docker Compose

```bash
# Start tenant service with PostgreSQL (production build)
docker compose -f infra/docker-compose.yml up tenant-service -d

# Start in development mode with hot reload
docker compose -f infra/docker-compose.yml --profile dev up tenant-service-dev -d

# Enable distributed tracing with Jaeger
docker compose -f infra/docker-compose.yml --profile tracing up tenant-service jaeger -d

# View service logs
docker compose -f infra/docker-compose.yml logs -f tenant-service
```

### Service Profiles

| Profile | Services | Description |
|---------|----------|-------------|
| (default) | postgres, mssql, tenant-service | Core services |
| `dev` | tenant-service-dev | Development with hot reload (port 8001) |
| `admin` | pgadmin | Database administration UI |
| `tracing` | jaeger | Distributed tracing |

### Kubernetes Deployment

See `k8s/` directory for Kubernetes manifests:

```bash
cd infra/k8s

# Update secrets before deployment
kubectl apply -f namespace.yaml
kubectl apply -f secret.yaml    # ⚠️ Update with real credentials
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f hpa.yaml
kubectl apply -f ingress.yaml
```

## Production Notes

⚠️ **These configurations are for development only.**

For production, ensure:
- Use strong, randomly generated passwords
- Enable SSL/TLS for connections
- Use external database services (managed PostgreSQL, Azure SQL)
- Implement proper backup strategies
- Use Docker secrets instead of environment variables
- Configure resource limits and requests
- Implement monitoring and alerting
- Use private container registries

## Additional Resources

- [PostgreSQL Docker Documentation](https://hub.docker.com/_/postgres)
- [MSSQL Docker Documentation](https://hub.docker.com/_/microsoft-mssql-server)
- [PgAdmin Documentation](https://www.pgadmin.org/docs/)
- [Docker Compose Reference](https://docs.docker.com/compose/compose-file/)
