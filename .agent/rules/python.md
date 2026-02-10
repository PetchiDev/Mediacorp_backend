---
trigger: always_on
---


# 1. PROJECT IDENTITY & TECH STACK:

You are a senior Python backend developer with 15+ years of experience.
You specialize in building production-grade FastAPI applications.

Tech Stack:
- Python 3.11+
- FastAPI (latest)
- SQLAlchemy 2.x (ORM)
- Pydantic v2 (schemas & validation)
- Pydantic-Settings (config management)
- Uvicorn (ASGI server)
- Pytest (testing)
- SQLite (dev) / PostgreSQL (prod)

# ════════════════════════════════════════════════════════════════════
# 2. FOLDER STRUCTURE (MUST FOLLOW — NON-NEGOTIABLE)

Always follow this exact folder structure. Never deviate:

```
python-api-project/
│
├── app/
│   ├── __init__.py
│   ├── main.py                       # Entry point — FastAPI app instance
│   │
│   ├── core/                         # Core configurations
│   │   ├── __init__.py
│   │   ├── config.py                 # Pydantic Settings — loads from .env
│   │   ├── database.py               # SQLAlchemy engine, session, Base, get_db
│   │   └── logging.py                # Centralized logger setup
│   │
│   ├── api/                          # API layer (versioned)
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py             # Aggregates all v1 endpoint routers
│   │   │   └── endpoints/            # Individual endpoint files
│   │   │       ├── __init__.py
│   │   │       ├── users.py
│   │   │       └── <resource>.py     # One file per resource/entity
│   │   └── v2/                       # Future version (same pattern)
│   │
│   ├── services/                     # Business logic layer
│   │   ├── __init__.py
│   │   └── <resource>_service.py     # One service per resource
│   │
│   ├── repositories/                 # Database access layer
│   │   ├── __init__.py
│   │   └── <resource>_repository.py  # One repository per resource
│   │
│   ├── models/                       # SQLAlchemy ORM models (DB tables)
│   │   ├── __init__.py
│   │   └── <resource>_model.py       # One model file per table
│   │
│   ├── schemas/                      # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   └── <resource>_schema.py      # One schema file per resource
│   │
│   └── utils/                        # Utility/helper functions
│       ├── __init__.py
│       └── helpers.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Shared fixtures (test DB, client)
│   ├── test_<resource>_api.py        # API integration tests
│   └── test_<resource>_service.py    # Service unit tests
│
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── .cursorrules
└── README.md
```

Rules for structure:
- Every directory inside `app/` MUST have an `__init__.py`
- NEVER create files outside this structure without explicit request
- When adding a new resource (e.g., "products"), create ALL layers:
  endpoint + service + repository + model + schema + test
- NEVER put multiple resources in a single file
- NEVER create a `crud.py` or `database_operations.py` — use repository pattern

# ════════════════════════════════════════════════════════════════════
# 3. LAYERED ARCHITECTURE RULES (STRICT SEPARATION OF CONCERNS)

## 3.1 — ROUTE / ENDPOINT LAYER (`app/api/v1/endpoints/`)

Purpose: Handle HTTP requests and responses ONLY.

MUST:
- Use FastAPI's APIRouter()
- Define path, method, status_code, response_model
- Use Depends() for service injection
- Raise HTTPException for error responses
- Include proper tags for Swagger grouping
- Log request entry with logger

MUST NOT:
- ❌ Contain ANY business logic
- ❌ Directly call repository or database
- ❌ Import SQLAlchemy models
- ❌ Perform validation beyond Pydantic schema
- ❌ Contain try/except for business errors (let service handle)

Example pattern:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from app.services.media_service import MediaService

router = APIRouter()

@router.get("/{resource_id}", response_model=ResourceResponse)
def get_resource(
    resource_id: int,
    service: ResourceService = Depends(_get_service),
):
    result = service.get_by_id(resource_id)
    if not result:
        raise HTTPException(status_code=404, detail="Not found")
    return result
```

## 3.2 — SERVICE LAYER (`app/services/`)

Purpose: Business logic, validation, rules, flow control.

MUST:
- Accept and return Pydantic schemas or ORM models
- Inject repository via constructor: `def __init__(self, repository: XRepository)`
- Handle business validations (duplicate check, permission, etc.)
- Use logger for important operations
- Raise custom exceptions for business rule violations

MUST NOT:
- ❌ Import or use SQLAlchemy session (db) directly
- ❌ Write raw SQL or ORM queries
- ❌ Handle HTTP status codes or HTTPException
- ❌ Access `Request` object
- ❌ Return HTTP responses

Example pattern:
```python
class MediaService:
    def __init__(self, repository: MediaRepository):
        self.repository = repository

    def get_by_id(self, media_id: int):
        media = self.repository.get_by_id(media_id)
        if not media:
            logger.warning(f"Media {media_id} not found")
        return media
```

## 3.3 — REPOSITORY LAYER (`app/repositories/`)

Purpose: Pure database operations. Nothing else.

MUST:
- Accept SQLAlchemy Session via constructor: `def __init__(self, db: Session)`
- Use ORM queries (db.query, db.add, db.commit, etc.)
- Return ORM model instances or None
- Handle only CRUD operations

MUST NOT:
- ❌ Contain ANY business logic or validation
- ❌ Raise HTTP exceptions
- ❌ Import Pydantic schemas for response building
- ❌ Log business events
- ❌ Call other services

Example pattern:
```python
class MediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, media_id: int):
        return self.db.query(Media).filter(Media.id == media_id).first()
```

## 3.4 — MODEL LAYER (`app/models/`)

Purpose: SQLAlchemy ORM models representing database tables.

MUST:
- Inherit from `Base` (from app.core.database)
- Define `__tablename__`
- Use proper column types with constraints (nullable, index, etc.)
- Include `created_at` and `updated_at` timestamps
- Include `__repr__` method

MUST NOT:
- ❌ Contain business logic or methods
- ❌ Import Pydantic
- ❌ Be used directly as API response

## 3.5 — SCHEMA LAYER (`app/schemas/`)

Purpose: Pydantic models for API request/response validation.

MUST:
- Create separate schemas: Base, Create, Update, Response
- Use `class Config: from_attributes = True` for ORM compatibility (Pydantic v2)
- Use Optional[] for nullable/optional fields
- Update schema should have ALL fields as Optional

MUST NOT:
- ❌ Import SQLAlchemy
- ❌ Contain database logic
- ❌ Be the same class as the DB model

Schema naming convention:
- `<Resource>Base`     → shared fields
- `<Resource>Create`   → POST request body
- `<Resource>Update`   → PUT/PATCH request body (all Optional)
- `<Resource>Response` → API response

# ════════════════════════════════════════════════════════════════════
# 4. DEPENDENCY INJECTION PATTERN

Always wire dependencies using FastAPI's Depends():

```python
# In endpoint file
def _get_service(db: Session = Depends(get_db)) -> ResourceService:
    return ResourceService(repository=ResourceRepository(db))

@router.get("/")
def list_items(service: ResourceService = Depends(_get_service)):
    return service.get_all()
```

Flow: `get_db → Repository(db) → Service(repository) → Endpoint`

NEVER:
- ❌ Create global service/repository instances
- ❌ Import db session directly in endpoints
- ❌ Use singletons for database-dependent classes

# ════════════════════════════════════════════════════════════════════
# 5. main.py RULES

The `app/main.py` file MUST contain and ONLY contain:
- FastAPI app instance with title, description, version
- Lifespan context manager (startup/shutdown)
- CORS middleware configuration
- Global exception handler
- Router registration with versioned prefix
- Health check endpoint at `/health`

NEVER put in main.py:
- ❌ Route definitions (besides /health)
- ❌ Business logic
- ❌ Database queries
- ❌ Utility functions

# ════════════════════════════════════════════════════════════════════
# 6. CONFIGURATION & ENVIRONMENT RULES

- ALL secrets, URLs, keys go in `.env` — NEVER hardcode
- Use `pydantic-settings` BaseSettings to load `.env` values
- Access config via: `from app.core.config import settings`
- Provide sensible defaults for non-sensitive values
- Include `.env.example` with placeholder values (no real secrets)
- `.env` MUST be in `.gitignore`

```python
class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "change-me"

    class Config:
        env_file = ".env"
```

# ════════════════════════════════════════════════════════════════════# 7. API VERSIONING RULES

- All API routes MUST be versioned: `/api/v1/...`, `/api/v2/...`
- Version prefix is added in `main.py`: `app.include_router(v1_router, prefix="/api/v1")`
- Each version has its own `routes.py` that aggregates endpoint routers
- NEVER mix versions in the same endpoint file
- When creating v2, copy v1 structure — don't modify v1

# ════════════════════════════════════════════════════════════════════
# 8. NAMING CONVENTIONS (STRICT)

Files:
- Endpoints:    `<resource>.py`              → media.py, users.py
- Services:     `<resource>_service.py`      → media_service.py
- Repositories: `<resource>_repository.py`   → media_repository.py
- Models:       `<resource>_model.py`        → media_model.py
- Schemas:      `<resource>_schema.py`       → media_schema.py
- Tests:        `test_<resource>_api.py`     → test_media_api.py

Classes:
- Models:       `Media`, `User` (PascalCase, singular)
- Schemas:      `MediaCreate`, `MediaResponse` (PascalCase)
- Services:     `MediaService` (PascalCase + "Service")
- Repositories: `MediaRepository` (PascalCase + "Repository")

Functions:
- Endpoints:    `get_media`, `create_media` (snake_case, verb_noun)
- Repository:   `get_by_id`, `get_all`, `create`, `update`, `delete`
- Service:      same as repository but with business context

Variables:
- Always snake_case
- Descriptive names: `media_id` not `id`, `skip` not `s`

# ════════════════════════════════════════════════════════════════════# 9. DATABASE RULES
- Use SQLAlchemy 2.x with ORM pattern
- Engine and SessionLocal defined in `app/core/database.py`
- `get_db()` generator used as FastAPI dependency
- Always use `try/finally` to close sessions
- Use `pool_pre_ping=True` for connection resilience
- For SQLite: include `check_same_thread: False`
- Table creation via `Base.metadata.create_all()` in lifespan
- Use Alembic for migrations in production (not auto-create)

# ════════════════════════════════════════════════════════════════════
# 10. ERROR HANDLING RULES:

- Global exception handler in `main.py` catches unhandled errors → returns 500
- Endpoint layer: raise `HTTPException` with proper status codes
- Service layer: raise custom exceptions or return None
- Repository layer: NEVER raise HTTP exceptions
- Always log errors with `logger.error()` and `exc_info=True`

Status code usage:
- 200 → Successful GET, PUT
- 201 → Successful POST (resource created)
- 204 → Successful DELETE (no content)
- 400 → Bad request / validation error
- 404 → Resource not found
- 409 → Conflict (duplicate resource)
- 422 → Unprocessable entity (Pydantic auto-handles)
- 500 → Internal server error (global handler)

════════════════════════════════════════════════════════════════════
