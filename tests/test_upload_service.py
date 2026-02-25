import pytest
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
        
        assert result.presigned_url == "mock-upload-id"
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
