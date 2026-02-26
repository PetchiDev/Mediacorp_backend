# Mediacorp Backend - Media Processing Infrastructure

A production-grade FastAPI backend designed for robust, high-availability media ingestion. This service provides advanced multipart upload capabilities, secure AWS S3 integration via STS Role Assumption, and strictly validated processing pipelines.

## 🏗️ Architecture Overview

The system follows a strict layered architecture to ensure separation of concerns and maintainability:

- **API Layer (`src/api`)**: Handles HTTP requests, versioning, and endpoint routing.
- **Service Layer (`src/services`)**: Contains core business logic, orchestration, and validation.
- **Repository Layer (`src/repositories`)**: Manages all database interactions using SQLAlchemy ORM.
- **Core Layer (`src/core`)**: Centralized configuration, logging, and security middleware.
- **Models & Schemas**: Data persistence definitions and Pydantic validation models.

## 📁 Folder Structure

```text
Mediacorp_Backend/
├── src/
│   ├── main.py           # Application entry point
│   ├── api/v1/           # Versioned REST endpoints
│   ├── core/             # Configuration & Security
│   ├── models/           # SQLAlchemy ORM models
│   ├── repositories/     # Data access layer
│   ├── schemas/          # Pydantic data validation
│   ├── services/         # Business logic & S3 integration
│   └── utils/            # Helper utilities and validators
├── tests/                # Comprehensive test suite
├── scripts/              # Infrastructure and utility scripts
└── .env                  # Environment configuration
```

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- AWS CLI configured with base credentials
- MFA Device for role assumption

### Setup Instructions

1. **Environment Initialization**:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Credential Configuration**:
   - Copy `.env.example` to `.env`.
   - Populate `BASE_AWS_ACCESS_KEY_ID` and `BASE_AWS_SECRET_ACCESS_KEY` with your permanent credentials.

3. **Assume IAM Role (MFA)**:
   ```powershell
   .\scripts\get_role_creds.ps1
   ```

4. **Run Development Server**:
   ```bash
   python -m uvicorn src.main:app --reload --port 8000
   ```

## 📡 API Reference (v1)

| Method | Endpoint | Description | Payload |
|--------|----------|-------------|---------|
| `POST` | `/api/v1/bulk-upload` | Initiate one or more uploads. Returns presigned URLs or Multipart IDs. | `BulkUploadRequest` |
| `GET`  | `/api/v1/{upload_id}/part/{num}` | Get a presigned URL for a specific part of a multipart upload. | - |
| `POST` | `/api/v1/{upload_id}/complete` | Finalize a multipart upload with part ETags. | `MultipartCompleteRequest` |
| `GET`  | `/health` | System health and status check. | - |

## 🧪 Testing

The project utilizes `pytest` for both unit and integration testing.

- **Run all tests**: `pytest`
- **Run with coverage**: `pytest --cov=src`
- **Integration Tests**: `python scripts/test_bulk_real.py` (Requires valid AWS session)

## 🛡️ Security Standards

- **Signature V4**: All S3 operations explicitly utilize AWS Signature Version 4 for regional compatibility.
- **STS Role Assumption**: Temporary credentials are used for all cloud interactions.
- **Input Validation**: Zero-trust approach with mandatory Pydantic schema validation for ALL requests.
- **CORS Hardening**: Strict header exposure (e.g., ETag) restricted to verified origins.
