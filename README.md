# Mediacorp Backend

Professional Python Backend for Mediacorp.

## Project Structure

- `src/api`: API endpoints and routers.
- `src/core`: Configuration, logging, and security.
- `src/db`: Database connection and session management.
- `src/models`: SQLAlchemy database models.
- `src/schemas`: Pydantic validation schemas.
- `src/services`: Business logic.
- `src/utils`: Helper functions.
- `tests`: Unit and integration tests.
- `migrations`: Alembic database migrations.

## Getting Started

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   copy .env.example .env
   ```

4. Run the application:
   ```bash
   uvicorn src.main:app --reload
   ```
## API Documentation

| Method | Path | Description | Response |
|--------|------|-------------|----------|
| GET | `/health` | Service health check | `{"status": "healthy", ...}` |
| POST | `/api/v1/upload` | Initiate media upload (get presigned URL) | `UploadResponse` |

### Example Request
```bash
curl -X POST "http://localhost:8000/api/v1/upload" \
     -H "Content-Type: application/json" \
     -d '{
           "filename": "my_video.mp4",
           "file_size": 1048576,
           "content_type": "video/mp4"
         }'
```
