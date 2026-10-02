# VanSure Multi-Tenant School Transportation SaaS Platform

A secure, scalable, maintainable backend for managing school and college van transportation.

## Technology Stack

- **Python**: 3.12+
- **FastAPI**: REST APIs, validation, OpenAPI documentation
- **PostgreSQL**: Primary relational database with PostGIS for geospatial data
- **SQLAlchemy 2.x**: Async ORM with typed models
- **Alembic**: Database migrations
- **Pydantic v2**: Request/response validation
- **Redis**: Caching, rate limiting, job coordination
- **Celery**: Background jobs, scheduled tasks
- **WebSockets**: Real-time GPS updates
- **MQTT**: IoT device integration (Eclipse Mosquitto)
- **JWT**: Secure authentication with Argon2id password hashing
- **Docker**: Containerization

## Quick Start

```bash
# 1. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies
uv pip install --group dev --group lint

# 3. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 4. Start PostgreSQL and Redis
docker-compose up -d postgres redis

# 5. Run migrations
alembic upgrade head

# 6. Seed initial data
python -m app.scripts.seed_data

# 7. Start the development server
uvicorn app.main:app --reload --port 8000

# 8. Run tests
pytest app/tests -v
```

## API Documentation

The OpenAPI specification is available at:
- **Development**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc

## Project Structure

```
app/
├── main.py                    # Application entry point
├── core/                      # Core infrastructure
│   ├── config.py             # Application configuration
│   ├── security.py           # Security utilities
│   ├── tenant_context.py     # Tenant context management
│   ├── permissions.py        # RBAC permissions
│   ├── middleware.py         # FastAPI middleware
│   └── exceptions.py         # Custom exceptions
├── api/
│   └── v1/
│       ├── router.py         # Main API router
│       └── endpoints/        # Endpoint handlers
├── modules/                  # Domain modules
│   ├── identity/           # Authentication and authorization
│   ├── schools/            # School/tenant management
│   ├── students/           # Student records
│   ├── fleet/              # Vehicles and drivers
│   ├── routes/             # Route planning
│   ├── trips/              # Trip management
│   └── ...
├── infrastructure/         # External dependencies
│   ├── database/           # SQLAlchemy models
│   ├── cache/              # Redis client
│   ├── queue/              # Celery configuration
│   └── messaging/          # Notification providers
├── workers/                # Celery tasks
├── schemas/                # Pydantic schemas
├── tests/                  # Test suite
└── migrations/             # Alembic migrations
```

## Multi-Tenancy

VanSure uses shared database, shared schema tenancy:

- Every tenant-owned table has a `school_id` column
- Tenant context is resolved from authenticated user
- PostgreSQL Row-Level Security (RLS) provides defense-in-depth
- Cross-tenant access is prohibited by design

## Authentication & Authorization

### Roles
1. **SUPER_ADMIN** - Platform super admin
2. **SCHOOL_OWNER** - School owner/owner
3. **SCHOOL_ADMIN** - School administrator
4. **TRANSPORT_MANAGER** - Transport manager
5. **DRIVER** - Bus driver
6. **PARENT** - Parent/Guardian
7. **STUDENT** - Student (read-only)
8. **FLEET_STAFF** - Fleet maintenance
9. **ACCOUNTANT** - School accountant

### JWT Flow
1. User logs in with email/password
2. Server returns short-lived access token (15 min) + refresh token (7 days)
3. On refresh, old refresh token is invalidated, new one issued
4. Logout revokes all tokens server-side

## Environment Variables

See `.env.example` for all configuration options.

## Docker

```bash
# Build and run all services
docker-compose up --build

# Run tests in container
docker-compose run --rm app pytest
```

## Development

### Code Quality

```bash
# Lint and format
ruff check app/
ruff format app/

# Type checking
mypy app/

# Pre-commit hooks
pre-commit run --all-files
```

### Testing

```bash
# Unit tests
pytest app/tests/unit -v

# Integration tests
pytest app/tests/integration -v

# API tests
pytest app/tests/api -v

# Security tests
pytest app/tests/security -v

# Full test suite
pytest --cov=app --cov-report=html
```

## Deployment

See `deploy/` directory for:
- Docker production configuration
- Kubernetes manifests
- Backup/restore scripts

## License

MIT