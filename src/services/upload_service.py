from datetime import datetime
import hashlib
import uuid
from typing import Optional, Dict, Any

from src.repositories.upload_repository import UploadRepository
from src.services.s3_service import generate_presigned_url
from src.utils.validators import validate_file_type, validate_file_size
from src.core.config import settings
from src.core.logging import logger
from src.schemas.upload_schema import UploadRequest, UploadResponse, BulkUploadRequest, BulkUploadResponse

class UploadService:
    """Rule 3.2: Business logic for handling media uploads."""
    def __init__(self, repository: UploadRepository):
        self.repository = repository

    async def initiate_upload(self, request: UploadRequest) -> UploadResponse:
        """
        Orchestrate the upload initiation process:
        1. Validate file type and size.
        2. Generate unique upload ID and S3 object key.
        3. Generate presigned URL or initiate multipart upload.
        4. Create database records.
        """
        try:
            # 1. Validate
            category = validate_file_type(request.filename)
            validate_file_size(request.file_size, category)
            
            # 2. Generate identifiers
            upload_id = uuid.uuid4()
            timestamp = datetime.now().strftime("%Y%m%d")
            object_key = f"incoming/{timestamp}/{upload_id}/{request.filename}"
            
            # 3. S3 Integration
            presigned_result = await generate_presigned_url(
                bucket=settings.S3_BUCKET,
                object_key=object_key,
                file_size=request.file_size,
                content_type=request.content_type
            )
            
            # 4. Database Persistence
            metadata_hash = self._generate_metadata_hash(
                request.filename, request.file_size, request.content_type
            )
            
            # Create content record
            self.repository.create_content_record(
                content_id=upload_id,
                source_bucket=settings.S3_BUCKET,
                source_key=object_key,
                original_filename=request.filename,
                file_size_bytes=request.file_size,
                mime_type=request.content_type,
                metadata_hash=metadata_hash,
                processing_config=request.processing_config or {},
                status='pending'
            )
            
            # Initialize component statuses
            components = [
                'transcription', 'entity_extraction', 'sentiment_analysis',
                'visual_processing', 'postprocessing', 'scene_detection', 'person_tracking'
            ]
            for component in components:
                self.repository.create_component_status(content_id=upload_id, component=component)
            
            logger.info(f"Upload initiated successfully: {upload_id}")
            
            return UploadResponse(
                upload_id=str(upload_id),
                presigned_url=presigned_result,
                object_key=object_key,
                expires_in=settings.PRESIGNED_URL_EXPIRY
            )
            
        except ValueError as e:
            logger.warning(f"Validation error during upload initiation: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initiate upload: {e}", exc_info=True)
            raise

    async def initiate_bulk_upload(self, request: BulkUploadRequest) -> BulkUploadResponse:
        """
        Initiate multiple uploads in a batch.
        Currently processes sequentially and returns all results.
        """
        logger.info(f"Initiating bulk upload for {len(request.uploads)} files")
        results = []
        for upload_req in request.uploads:
            # We reuse the existing initiate_upload logic
            result = await self.initiate_upload(upload_req)
            results.append(result)
        
        return BulkUploadResponse(results=results)

    def _generate_metadata_hash(self, filename: str, size: int, mime_type: str) -> str:
        """Generate a hash for duplicate detection."""
        hash_input = f"{filename}:{size}:{mime_type}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
