from fastapi import APIRouter
from src.api.v1.endpoints import upload, auth_test

v1_router = APIRouter()

# Register endpoint routers
v1_router.include_router(upload.router, tags=["Upload"])
v1_router.include_router(auth_test.router, prefix="/auth-test", tags=["Auth Test"])
