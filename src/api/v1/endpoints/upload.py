from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.schemas.upload_schema import UploadRequest, UploadResponse, BulkUploadRequest, BulkUploadResponse
from src.services.upload_service import UploadService
from src.repositories.upload_repository import UploadRepository
from src.core.database import get_db
from src.core.logging import logger

router = APIRouter()

def _get_upload_service(db: Session = Depends(get_db)) -> UploadService:
    """Rule 4: Dependency injection for UploadService."""
    return UploadService(repository=UploadRepository(db))

@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def create_upload(
    request: UploadRequest,
    service: UploadService = Depends(_get_upload_service)
):
    """
    Rule 3.1: Endpoint for initiating a media upload.
    Returns a presigned URL for S3 and an internal upload ID.
    """
    logger.info(f"Received upload request for file: {request.filename}")
    try:
        return await service.initiate_upload(request)
    except ValueError as e:
        # Business logic/validation error
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        # System failure
        logger.error(f"Unexpected error in upload endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate upload due to internal error"
        )

@router.post("/bulk-upload", response_model=BulkUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_upload(
    request: BulkUploadRequest,
    service: UploadService = Depends(_get_upload_service)
):
    """
    Endpoint for initiating multiple media uploads at once.
    Returns a list of presigned URLs and upload IDs.
    """
    logger.info(f"Received bulk upload request for {len(request.uploads)} files")
    try:
        return await service.initiate_bulk_upload(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in bulk upload endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal Server Error: {str(e)}"
        )
