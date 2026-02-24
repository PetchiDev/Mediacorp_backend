from fastapi import APIRouter
from src.api.v1.endpoints import upload

v1_router = APIRouter()

# Register endpoint routers
v1_router.include_router(upload.router, tags=["Upload"])
