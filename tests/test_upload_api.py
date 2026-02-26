import pytest
import uuid
from unittest.mock import patch, MagicMock
from fastapi import status

def test_health_check(client):
    """Rule 12: Basic health check test."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy", "service": "upload-service"}

@patch("src.services.s3_service.get_s3_client")
def test_bulk_upload_success(mock_s3_client_getter, client):
    """Test successful bulk upload initiation."""
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "http://mock-url"
    mock_s3_client_getter.return_value = mock_s3
    
    bulk_data = {
        "uploads": [
            {"filename": "v1.mp4", "file_size": 100, "content_type": "video/mp4"},
            {"filename": "v2.mp4", "file_size": 200, "content_type": "video/mp4"}
        ]
    }
    
    response = client.post("/api/v1/bulk-upload", json=bulk_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert len(data["results"]) == 2
    assert data["results"][0]["presigned_url"] == "http://mock-url"

def test_bulk_upload_validation_error(client):
    """Test behavior with invalid input data (missing fields)."""
    response = client.post("/api/v1/bulk-upload", json={"uploads": [{"filename": "v.mp4"}]})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@patch("src.services.upload_service.UploadService.get_multipart_part_url")
def test_get_part_url_success(mock_get_url, client):
    """Test obtaining a part presigned URL via API."""
    upload_id = str(uuid.uuid4())
    mock_get_url.return_value = MagicMock(
        upload_id=upload_id,
        part_number=1,
        presigned_url="http://part-url"
    )
    
    response = client.get(f"/api/v1/{upload_id}/part/1")
    assert response.status_code == 200
    assert response.json()["presigned_url"] == "http://part-url"

def test_get_part_url_invalid_uuid(client):
    """Test that invalid UUID format returns 422."""
    response = client.get("/api/v1/not-a-uuid/part/1")
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@patch("src.services.upload_service.UploadService.complete_multipart_upload")
def test_complete_upload_success(mock_complete, client):
    """Test successful multipart completion via API."""
    upload_id = str(uuid.uuid4())
    mock_complete.return_value = {"status": "success", "location": "http://s3-location"}
    
    complete_data = {
        "parts": [{"PartNumber": 1, "ETag": "etag-123"}]
    }
    
    response = client.post(f"/api/v1/{upload_id}/complete", json=complete_data)
    assert response.status_code == 200
    assert response.json()["location"] == "http://s3-location"
