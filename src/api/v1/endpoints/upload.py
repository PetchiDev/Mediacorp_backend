from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.schemas.upload_schema import (
    UploadRequest, UploadResponse, BulkUploadRequest, BulkUploadResponse,
    MultipartPartResponse, MultipartCompleteRequest
)
from src.services.upload_service import UploadService
from src.repositories.upload_repository import UploadRepository
from src.core.database import get_db
from src.core.logging import logger
import uuid

router = APIRouter()

def _get_upload_service(db: Session = Depends(get_db)) -> UploadService:
    """Rule 4: Dependency injection for UploadService."""
    return UploadService(repository=UploadRepository(db))

@router.post("/bulk-upload", response_model=BulkUploadResponse, status_code=status.HTTP_201_CREATED)
async def create_bulk_upload(
    request: BulkUploadRequest,
    service: UploadService = Depends(_get_upload_service)
):
    """
    Initiate multiple media uploads in a single batch.
    
    This endpoint validates the file metadata and returns either a direct presigned URL 
    (for files < 100MB) or an S3 Multipart Upload ID (for files >= 100MB).
    
    Args:
        request: BulkUploadRequest containing metadata for multiple files.
        service: Injected UploadService.
        
    Returns:
        BulkUploadResponse with initiation results for each file.
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

@router.get("/{upload_id}/part/{part_number}", response_model=MultipartPartResponse)
async def get_multipart_part_url(
    upload_id: uuid.UUID,
    part_number: int,
    service: UploadService = Depends(_get_upload_service)
):
    """
    Generate a presigned URL for a specific part of a multipart upload.
    
    Args:
        upload_id: The unique identifier of the initiated upload.
        part_number: The sequence number of the part to be uploaded (1-10000).
        service: Injected UploadService.
        
    Returns:
        MultipartPartResponse containing the presigned URL for the part.
    """
    try:
        return await service.get_multipart_part_url(upload_id, part_number)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in part URL endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{upload_id}/complete", status_code=status.HTTP_200_OK)
async def complete_multipart_upload_endpoint(
    upload_id: uuid.UUID,
    request: MultipartCompleteRequest,
    service: UploadService = Depends(_get_upload_service)
):
    """
    Finalize an S3 multipart upload.
    
    This endpoint stitches together all uploaded parts using their ETags.
    
    Args:
        upload_id: The unique identifier of the initiated upload.
        request: MultipartCompleteRequest containing the list of Part numbers and ETags.
        service: Injected UploadService.
        
    Returns:
        A success message and the final S3 location of the object.
    """
    try:
        return await service.complete_multipart_upload(upload_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in completion endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
