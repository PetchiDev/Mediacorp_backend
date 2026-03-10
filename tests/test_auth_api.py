import pytest
from fastapi.testclient import TestClient
from src.main import app
from src.core.config import settings

client = TestClient(app)

def test_admin_access_success():
    # Simulate API Gateway forwarding 'mdm-admins'
    response = client.get(
        "/api/v1/auth-test/admin-only",
        headers={settings.COGNITO_GROUPS_HEADER: "mdm-admins"}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome, Admin!", "status": "Success"}

def test_admin_access_denied_for_editor():
    # Editor trying to access admin-only endpoint
    response = client.get(
        "/api/v1/auth-test/admin-only",
        headers={settings.COGNITO_GROUPS_HEADER: "mdm-editors"}
    )
    assert response.status_code == 403
    assert "User does not have required permissions" in response.json()["detail"]

def test_editor_access_success():
    response = client.get(
        "/api/v1/auth-test/editor-admin",
        headers={settings.COGNITO_GROUPS_HEADER: "mdm-editors"}
    )
    assert response.status_code == 200
    assert "Welcome, Editor or Admin!" in response.json()["message"]

def test_multiple_groups_access():
    # User with multiple groups
    response = client.get(
        "/api/v1/auth-test/admin-only",
        headers={settings.COGNITO_GROUPS_HEADER: "mdm-viewers, mdm-admins"}
    )
    assert response.status_code == 200

def test_missing_header_denied():
    response = client.get("/api/v1/auth-test/admin-only")
    assert response.status_code == 403
    assert "User groups not found in request headers" in response.json()["detail"]
