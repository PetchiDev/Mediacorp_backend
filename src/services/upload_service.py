from datetime import datetime
import hashlib
import uuid
from typing import Optional, Dict, Any

from src.repositories.upload_repository import UploadRepository
from src.utils.validators import validate_file_type, validate_file_size
from src.core.config import settings
from src.core.logging import logger
from src.schemas.upload_schema import (
    UploadRequest, UploadResponse, BulkUploadRequest, BulkUploadResponse,
    MultipartPartResponse, MultipartCompleteRequest
)
from src.services.s3_service import (
    generate_presigned_url, generate_part_presigned_url, complete_multipart_upload
)

class UploadService:
    """Rule 3.2: Business logic for handling media uploads."""
    def __init__(self, repository: UploadRepository):
        self.repository = repository

    async def initiate_upload(self, request: UploadRequest) -> UploadResponse:
        """
        Orchestrate the media upload initiation lifecycle.
        
        This method performs the following:
        1. Validates the file extension and size against production limits.
        2. Generates a unique content ID (UUID) and organized S3 object key.
        3. Decides and executes the upload protocol (Single PUT or Multipart).
        4. Persists the initial content metadata and processing states to the database.
        
        Args:
            request: Metadata for the file to be uploaded.
            
        Returns:
            UploadResponse containing S3 identifiers and presigned URLs.
            
        Raises:
            ValueError: If validation fails or processing limits are exceeded.
        """
        try:
            # 1. Validate
            category = validate_file_type(request.filename)
            validate_file_size(request.file_size, category)
            
            # 2. Generate identifiers
            upload_id = uuid.uuid4()
            timestamp = datetime.now().strftime("%Y%m%d")
            object_key = f"incoming/{timestamp}/{upload_id}/{request.filename}"
            
            # 3. S3 Integration (Check threshold)
            is_multipart = request.file_size >= 100 * 1024 * 1024
            
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
                status='pending',
                s3_upload_id=presigned_result if is_multipart else None
            )
            
            # Initialize component statuses
            components = [
                'transcription', 'entity_extraction', 'sentiment_analysis',
                'visual_processing', 'postprocessing', 'scene_detection', 'person_tracking'
            ]
            for component in components:
                self.repository.create_component_status(content_id=upload_id, component=component)
            
            logger.info(f"Upload initiated successfully: {upload_id} (Multipart: {is_multipart})")
            
            return UploadResponse(
                upload_id=str(upload_id),
                object_key=object_key,
                is_multipart=is_multipart,
                presigned_url=presigned_result if not is_multipart else None,
                s3_upload_id=presigned_result if is_multipart else None,
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
        Initiate multiple media uploads in a single transactional batch.
        
        Currently processes each upload sequentially to ensure database integrity 
        and returns a collection of initiation results.
        
        Args:
            request: Collection of upload requests.
            
        Returns:
            BulkUploadResponse containing individual UploadResponse objects.
        """
        logger.info(f"Initiating bulk upload for {len(request.uploads)} files")
        results = []
        for upload_req in request.uploads:
            # We reuse the existing initiate_upload logic
            result = await self.initiate_upload(upload_req)
            results.append(result)
        
        return BulkUploadResponse(results=results)

    async def get_multipart_part_url(self, upload_id: uuid.UUID, part_number: int) -> MultipartPartResponse:
        """
        Retrieve a presigned URL for a specific chunk (part) of a multipart upload.
        
        Args:
            upload_id: The UUID of the initiated upload.
            part_number: The part index (1-based) to generate a URL for.
            
        Returns:
            MultipartPartResponse with the presigned URL for the part.
            
        Raises:
            ValueError: If the upload session is non-existent or not a multipart type.
        """
        record = self.repository.get_content_by_id(upload_id)
        if not record or not record.s3_upload_id:
            raise ValueError(f"No active multipart upload found for {upload_id}")

        url = await generate_part_presigned_url(
            bucket=record.source_bucket,
            object_key=record.source_key,
            upload_id=record.s3_upload_id,
            part_number=part_number
        )
        
        return MultipartPartResponse(
            upload_id=str(upload_id),
            part_number=part_number,
            presigned_url=url
        )

    async def complete_multipart_upload(self, upload_id: uuid.UUID, request: MultipartCompleteRequest) -> Dict[str, Any]:
        """
        Finalize a multipart upload by merging all segments on S3.
        
        Updates the record status to 'uploaded' and prepares the system for 
        asynchronous processing pipelines.
        
        Args:
            upload_id: The UUID of the upload session.
            request: List of PartNumbers and ETags verified by the client.
            
        Returns:
            Success status and final S3 object location.
            
        Raises:
            ValueError: If the upload session is invalid.
        """
        record = self.repository.get_content_by_id(upload_id)
        if not record or not record.s3_upload_id:
            raise ValueError(f"No active multipart upload found for {upload_id}")

        # Map to S3 expected format
        parts_data = [part.model_dump() for part in request.parts]
        
        result = await complete_multipart_upload(
            bucket=record.source_bucket,
            object_key=record.source_key,
            upload_id=record.s3_upload_id,
            parts=parts_data
        )
        
        # Mark as pending for processing (or uploaded)
        self.repository.update_status(upload_id, 'uploaded')
        
        return {"status": "success", "detail": "Multipart upload completed", "location": result.get('Location')}

    def _generate_metadata_hash(self, filename: str, size: int, mime_type: str) -> str:
        """Generate a hash for duplicate detection."""
        hash_input = f"{filename}:{size}:{mime_type}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
