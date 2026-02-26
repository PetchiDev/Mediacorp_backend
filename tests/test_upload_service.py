import pytest
import uuid
from unittest.mock import patch, MagicMock, AsyncMock
from src.services.upload_service import UploadService
from src.schemas.upload_schema import UploadRequest, BulkUploadRequest, UploadResponse
from src.repositories.upload_repository import UploadRepository

@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=UploadRepository)
    return repo

@pytest.fixture
def service(mock_repo):
    return UploadService(repository=mock_repo)

@pytest.mark.asyncio
async def test_initiate_upload_small_file_calls_presigned(service, mock_repo):
    """Test that files < 100MB use generate_presigned_url."""
    request = UploadRequest(
        filename="small.mp4",
        file_size=50 * 1024 * 1024, # 50MB
        content_type="video/mp4"
    )
    
    with patch("src.services.upload_service.generate_presigned_url", new_callable=AsyncMock) as mock_gen_url:
        mock_gen_url.return_value = "http://mock-url"
        
        result = await service.initiate_upload(request)
        
        assert result.presigned_url == "http://mock-url"
        mock_gen_url.assert_called_once()
        assert mock_repo.create_content_record.called

@pytest.mark.asyncio
async def test_initiate_upload_large_file_calls_multipart(service, mock_repo):
    """Test that files >= 100MB use initiate_multipart_upload."""
    request = UploadRequest(
        filename="large.mp4",
        file_size=150 * 1024 * 1024, # 150MB
        content_type="video/mp4"
    )
    
    with patch("src.services.upload_service.generate_presigned_url", new_callable=AsyncMock) as mock_gen_url:
        mock_gen_url.return_value = "mock-upload-id"
        
        result = await service.initiate_upload(request)
        
        assert result.is_multipart is True
        assert result.s3_upload_id == "mock-upload-id"
        assert result.presigned_url is None
        mock_gen_url.assert_called_once()
        assert mock_repo.create_content_record.called

@pytest.mark.asyncio
async def test_initiate_bulk_upload_multiple_files(service):
    """Test bulk upload initiation with mixed file sizes."""
    bulk_request = BulkUploadRequest(uploads=[
        UploadRequest(filename="f1.mp4", file_size=10, content_type="video/mp4"),
        UploadRequest(filename="f2.mp4", file_size=200*1024*1024, content_type="video/mp4")
    ])
    
    # We need to return a valid UploadResponse object so BulkUploadResponse schema can validate it
    mock_response = UploadResponse(
        upload_id="test-id",
        presigned_url="http://mock-url",
        object_key="incoming/test/key",
        expires_in=3600
    )
    
    with patch.object(service, 'initiate_upload', new_callable=AsyncMock) as mock_init:
        mock_init.return_value = mock_response
        
        response = await service.initiate_bulk_upload(bulk_request)
        
        assert len(response.results) == 2
        assert mock_init.call_count == 2
        assert response.results[0].upload_id == "test-id"

@pytest.mark.asyncio
async def test_get_multipart_part_url_success(service, mock_repo):
    """Test obtaining a presigned URL for a part."""
    upload_id = uuid.uuid4()
    mock_record = MagicMock()
    mock_record.s3_upload_id = "s3-id-123"
    mock_record.source_bucket = "bucket"
    mock_record.source_key = "key"
    mock_repo.get_content_by_id.return_value = mock_record
    
    with patch("src.services.upload_service.generate_part_presigned_url", new_callable=AsyncMock) as mock_gen_url:
        mock_gen_url.return_value = "http://part-url"
        
        result = await service.get_multipart_part_url(upload_id, 1)
        
        assert result.presigned_url == "http://part-url"
        assert result.part_number == 1

@pytest.mark.asyncio
async def test_get_multipart_part_url_not_found(service, mock_repo):
    """Test that requesting a part URL for a non-existent upload ID fails."""
    mock_repo.get_content_by_id.return_value = None
    with pytest.raises(ValueError, match="No active multipart upload found"):
        await service.get_multipart_part_url(uuid.uuid4(), 1)

@pytest.mark.asyncio
async def test_complete_multipart_upload_success(service, mock_repo):
    """Test finalizing a multipart upload."""
    upload_id = uuid.uuid4()
    mock_record = MagicMock()
    mock_record.s3_upload_id = "s3-id-123"
    mock_repo.get_content_by_id.return_value = mock_record
    
    from src.schemas.upload_schema import MultipartCompleteRequest, MultipartCompletePart
    request = MultipartCompleteRequest(parts=[MultipartCompletePart(PartNumber=1, ETag="test-etag")])
    
    with patch("src.services.upload_service.complete_multipart_upload", new_callable=AsyncMock) as mock_complete:
        mock_complete.return_value = {"Location": "http://final-location"}
        
        result = await service.complete_multipart_upload(upload_id, request)
        
        assert result["status"] == "success"
        mock_repo.update_status.assert_called_with(upload_id, "uploaded")

@pytest.mark.asyncio
async def test_upload_validation_invalid_type(service):
    """Test that invalid file extensions are rejected."""
    request = UploadRequest(filename="test.exe", file_size=1024, content_type="application/octet-stream")
    with pytest.raises(ValueError, match="Unsupported file type"):
        await service.initiate_upload(request)

@pytest.mark.asyncio
async def test_upload_validation_exceeds_size(service):
    """Test that files exceeding category size limits are rejected."""
    # Video limit is 10GB, let's try 11GB
    request = UploadRequest(filename="huge.mp4", file_size=11 * 1024 * 1024 * 1024, content_type="video/mp4")
    with pytest.raises(ValueError, match="File size exceeds limit"):
        await service.initiate_upload(request)
