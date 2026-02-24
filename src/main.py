from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.v1.routes import v1_router
from src.core.config import settings
from src.core.database import Base, engine
from src.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Rule 9: Create tables in dev (In prod use Alembic)
    logger.info("Starting up: Creating database tables...")
    Base.metadata.create_all(bind=engine)
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Rule 15: CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rule 7: Versioned prefix
app.include_router(v1_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Rule 5: Health check endpoint."""
    return {"status": "healthy", "service": "upload-service"}

@app.get("/")
async def root():
    return {"message": "Welcome to Mediacorp Backend API"}
