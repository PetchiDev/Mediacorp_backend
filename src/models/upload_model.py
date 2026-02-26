from sqlalchemy import Column, String, BigInteger, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.types import UUID
from sqlalchemy.sql import func
from src.core.database import Base
import uuid

class ContentInventory(Base):
    """
    SQLAlchemy model representing the master inventory of uploaded media.
    
    This table tracks the source identity of files on S3, their ingestion status, 
    and links to processing downstream.
    
    Attributes:
        content_id: Unique UUID for the content.
        source_bucket: S3 Bucket names where the raw file resides.
        source_key: S3 Key path for the raw file.
        status: Current ingestion state (pending, uploaded, etc).
        s3_upload_id: Optional tracking ID for S3 Multipart Uploads.
    """
    __tablename__ = "content_inventory"

    content_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_bucket = Column(String(255), nullable=False)
    source_key = Column(String(1024), nullable=False)
    processed_key = Column(String(1024))
    original_filename = Column(String(255))
    file_size_bytes = Column(BigInteger, nullable=False)
    mime_type = Column(String(64), nullable=False)
    checksum_sha256 = Column(String(64), unique=True)
    metadata_hash = Column(String(64), nullable=False)
    media_metadata = Column(JSON)
    processing_config = Column(JSON, nullable=False, default={})
    status = Column(String(50), nullable=False, server_default='pending')
    execution_arn = Column(String(255))
    entity_count = Column(Integer, server_default='0')
    s3_upload_id = Column(String(255))  # Added for multipart upload tracking
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))

    def __repr__(self):
        return f"<ContentInventory(id={self.content_id}, filename={self.original_filename})>"

class ComponentStatus(Base):
    """
    SQLAlchemy model for tracking granular processing states of media components.
    
    Each media upload generates multiple component records (e.g., transcription, 
    entity extraction) to track asynchronous workflow progress.
    
    Attributes:
        content_id: Foreign key to the master ContentInventory record.
        component: The unique name of the processing stage.
        status: The specific state of this component (pending, processing, failed, completed).
    """
    __tablename__ = "component_status"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("content_inventory.content_id"), nullable=False)
    component = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, server_default='pending')
    progress_percent = Column(Integer, server_default='0')
    error_code = Column(String(50))
    error_message = Column(String)
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    result_summary = Column(JSON)

    def __repr__(self):
        return f"<ComponentStatus(content_id={self.content_id}, component={self.component}, status={self.status})>"
