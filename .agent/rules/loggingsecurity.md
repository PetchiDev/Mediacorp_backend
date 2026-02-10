---
trigger: always_on
---

# 11. LOGGING RULES
# ═══════════════════════════════════════════════════════════════════════════════

- Use centralized logger from `app.core.logging`
- Import: `from app.core.logging import logger`
- NEVER use `print()` — always `logger.info()`, `logger.error()`, etc.

Log levels:
- `logger.debug()`   → Detailed dev info
- `logger.info()`    → Request entry, successful operations
- `logger.warning()` → Resource not found, non-critical issues
- `logger.error()`   → Exceptions, failures (include exc_info=True)

Format: Include timestamp, level, module, function, line number, message

# ═══════════════════════════════════════════════════════════════════════════════
# 12. TESTING RULES
# ═══════════════════════════════════════════════════════════════════════════════

- Use pytest with FastAPI's TestClient
- Test DB: in-memory SQLite or separate test.db
- Override `get_db` dependency for test isolation
- Use `@pytest.fixture(autouse=True)` for DB setup/teardown
- Every resource MUST have:
  - API tests: test all CRUD endpoints + error cases (404, 400)
  - Service tests: test business logic with mocked repository

Test naming: `test_<action>_<resource>` → `test_create_media`, `test_get_media_not_found`

Minimum test coverage per resource:
- test_create_<resource>
- test_list_<resource>
- test_get_<resource>_by_id
- test_get_<resource>_not_found (404)
- test_update_<resource>
- test_delete_<resource>
- test_health_check (once, globally)

# ═══════════════════════════════════════════════════════════════════════════════
# 13. CODE STYLE & QUALITY RULES
# ═══════════════════════════════════════════════════════════════════════════════

- Type hints on ALL function parameters and return types
- Docstrings on all classes and public functions
- Max line length: 88 characters (Black formatter standard)
- Use f-strings for string formatting
- Use `Optional[]` for nullable parameters
- Use `List[]`, `Dict[]` from typing (Python 3.11+: use built-in)
- Use absolute imports: `from app.core.config import settings`
- NEVER use wildcard imports: `from module import *`
- Group imports: stdlib → third-party → local (separated by blank line)
- Use trailing commas in multi-line function calls/dicts
- Comments should explain WHY, not WHAT

# ═══════════════════════════════════════════════════════════════════════════════
# 14. WHEN ADDING A NEW RESOURCE (CHECKLIST)
# ═══════════════════════════════════════════════════════════════════════════════

When asked to add a new resource (e.g., "add products"), create ALL of these:

1. ✅ `app/models/<resource>_model.py`       → SQLAlchemy model
2. ✅ `app/schemas/<resource>_schema.py`      → Pydantic schemas (Base, Create, Update, Response)
3. ✅ `app/repositories/<resource>_repository.py` → CRUD database operations
4. ✅ `app/services/<resource>_service.py`     → Business logic
5. ✅ `app/api/v1/endpoints/<resource>.py`     → API endpoints with router
6. ✅ Update `app/api/v1/routes.py`            → Register new router
7. ✅ `tests/test_<resource>_api.py`           → Full CRUD tests
8. ✅ Update `README.md`                       → Add new endpoints to API table

NEVER create partial resources. Always create the full stack.

# ═══════════════════════════════════════════════════════════════════════════════
# 15. SECURITY RULES
# ═══════════════════════════════════════════════════════════════════════════════

- NEVER hardcode passwords, API keys, or secrets
- NEVER log sensitive data (passwords, tokens, personal info)
- NEVER commit `.env` files to git
- Use CORS middleware with specific origins in production (not "*")
- Validate and sanitize all user inputs via Pydantic schemas
- Use parameterized queries (SQLAlchemy ORM handles this)
- Set proper response headers via middleware
- Use HTTPS in production

# ═══════════════════════════════════════════════════════════════════════════════
# 16. RESPONSE FORMAT RULES
# ═══════════════════════════════════════════════════════════════════════════════

- Always use `response_model` in endpoint decorators
- Always set proper `status_code` for each endpoint
- List endpoints should support `skip` and `limit` query params
- Error responses MUST use: `{"detail": "error message"}`
- Successful DELETE returns 204 with no body
- Successful POST returns 201 with created resource

# ═══════════════════════════════════════════════════════════════════════════════
# 17. GIT & DOCUMENTATION RULES
# ═══════════════════════════════════════════════════════════════════════════════

- `.gitignore` must exclude: __pycache__, .env, *.db, venv/, .idea/, .vscode/
- `README.md` MUST include:
  - Project description
  - Folder structure diagram
  - Setup instructions (venv, install, .env, run)
  - API endpoint table (method, path, description)
  - Example curl requests and responses
  - How to run tests
- Update README whenever new endpoints are added

# ═══════════════════════════════════════════════════════════════════════════════
# 18. WHAT TO NEVER DO (ANTI-PATTERNS)
# ═══════════════════════════════════════════════════════════════════════════════

❌ NEVER put business logic in endpoints
❌ NEVER put DB queries in services
❌ NEVER put HTTP handling in repositories
❌ NEVER use the same class as both DB model and API schema
❌ NEVER use global mutable state
❌ NEVER use `print()` — use logger
❌ NEVER hardcode config values
❌ NEVER skip type hints
❌ NEVER create a file without adding it to proper directory
❌ NEVER write a function longer than 30 lines — break it down
❌ NEVER import from a higher layer (repository should not import service)
❌ NEVER return SQLAlchemy model directly without response_model
❌ NEVER use `from x import *`
❌ NEVER leave dead code or commented-out code
❌ NEVER write tests that depend on execution order
