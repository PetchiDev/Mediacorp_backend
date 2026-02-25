import pytest
from unittest.mock import patch
from fastapi import status

def test_health_check(client):
    """Rule 12: Basic health check test."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy", "service": "upload-service"}

@patch("src.services.s3_service.s3_client.generate_presigned_url")
def test_create_upload_success(mock_s3, client):
    """Rule 12: Successful upload initiation test."""
    mock_s3.return_value = "https://mock-s3-url.com/presigned"
    
    upload_data = {
        "filename": "test_video.mp4",
        "file_size": 1024 * 1024,  # 1 MB
        "content_type": "video/mp4",
        "processing_config": {"watermark": True}
    }
    
    response = client.post("/api/v1/upload", json=upload_data)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "upload_id" in data
    assert data["presigned_url"] == "https://mock-s3-url.com/presigned"
    assert "incoming/" in data["object_key"]

def test_create_upload_invalid_type(client):
    """Rule 12: Error case - unsupported file type."""
    upload_data = {
        "filename": "malicious.exe",
        "file_size": 1024,
        "content_type": "application/octet-stream"
    }
    
    response = client.post("/api/v1/upload", json=upload_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Unsupported file type" in response.json()["detail"]

def test_create_upload_too_large(client):
    """Rule 12: Error case - file too large."""
    upload_data = {
        "filename": "huge_image.png",
        "file_size": 1 * 1024 * 1024 * 1024,  # 1 GB (Limit for image is 100MB)
        "content_type": "image/png"
    }
    
    response = client.post("/api/v1/upload", json=upload_data)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "File size exceeds limit" in response.json()["detail"]

@patch("src.services.s3_service.s3_client.generate_presigned_url")
def test_bulk_upload_success(mock_s3, client):
    """Test successful bulk upload initiation."""
    mock_s3.return_value = "http://mock-url"
    
    bulk_data = {
        "uploads": [
            {"filename": "v1.mp4", "file_size": 100, "content_type": "video/mp4"},
            {"filename": "v2.mp4", "file_size": 200, "content_type": "video/mp4"}
        ]
    }
    
    response = client.post("/api/v1/bulk-upload", json=bulk_data)
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["results"]) == 2

def test_bulk_upload_empty_list(client):
    """Test behavior with empty upload list."""
    # The schema requires a list, so we pass an empty list.
    response = client.post("/api/v1/bulk-upload", json={"uploads": []})
    assert response.status_code == status.HTTP_201_CREATED
    assert len(response.json()["results"]) == 0
