from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from uuid import UUID

class UploadRequest(BaseModel):
    """Rule 3.5: Request schema for initiating an upload."""
    filename: str = Field(..., description="The name of the file to be uploaded")
    file_size: int = Field(..., description="The size of the file in bytes")
    content_type: str = Field(..., description="The MIME type of the file")
    processing_config: Optional[Dict[str, Any]] = Field(default={}, description="Optional processing configuration")

class UploadResponse(BaseModel):
    """Rule 3.5: Response schema for upload initiation."""
    upload_id: str
    object_key: str
    is_multipart: bool = False
    presigned_url: Optional[str] = None  # Valid if is_multipart is False
    s3_upload_id: Optional[str] = None   # Valid if is_multipart is True (S3's UploadId)
    expires_in: int = 3600

    model_config = ConfigDict(from_attributes=True)

class BulkUploadRequest(BaseModel):
    """Schema for bulk upload initiation."""
    uploads: list[UploadRequest] = Field(..., description="List of file upload requests")

class BulkUploadResponse(BaseModel):
    """Schema for bulk upload response."""
    results: list[UploadResponse]

class MultipartPartResponse(BaseModel):
    """Schema for a single part's presigned URL."""
    upload_id: str
    part_number: int
    presigned_url: str

class MultipartCompletePart(BaseModel):
    """Schema for a part's completion data (ETag)."""
    PartNumber: int
    ETag: str

class MultipartCompleteRequest(BaseModel):
    """Schema for completing a multipart upload."""
    parts: list[MultipartCompletePart]
