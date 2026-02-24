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
    presigned_url: str
    object_key: str
    expires_in: int = 3600

    model_config = ConfigDict(from_attributes=True)

class BulkUploadRequest(BaseModel):
    """Schema for bulk upload initiation."""
    uploads: list[UploadRequest] = Field(..., description="List of file upload requests")

class BulkUploadResponse(BaseModel):
    """Schema for bulk upload response."""
    results: list[UploadResponse]
