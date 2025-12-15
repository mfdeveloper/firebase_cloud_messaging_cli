"""
Pytest configuration and shared fixtures for FCM tests.
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_service_account_data():
    """Sample service account JSON data."""
    return {
        "type": "service_account",
        "project_id": "test-project-123",
        "private_key_id": "abc123",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIBOgIBAAJBALRiMLAHudeSA\n-----END RSA PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk@test-project-123.iam.gserviceaccount.com",
        "client_id": "123456789",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk"
    }


@pytest.fixture
def temp_credentials_file(mock_service_account_data):
    """Create a temporary credentials file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(mock_service_account_data, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def mock_firebase_admin():
    """Mock the firebase_admin module."""
    with patch('fcm_send.client.firebase_admin') as mock_admin:
        # Mock _apps to simulate uninitialized state
        mock_admin._apps = {}
        
        # Mock initialize_app
        mock_admin.initialize_app = MagicMock()
        
        # Mock get_app and credential
        mock_app = MagicMock()
        mock_credential = MagicMock()
        mock_access_token = MagicMock()
        mock_access_token.access_token = "mock_access_token_12345"
        mock_credential.get_access_token.return_value = mock_access_token
        mock_app.credential = mock_credential
        mock_admin.get_app.return_value = mock_app
        
        yield mock_admin


@pytest.fixture
def mock_messaging():
    """Mock the firebase_admin.messaging module."""
    with patch('fcm_send.client.messaging') as mock_msg:
        # Mock send to return a message ID
        mock_msg.send.return_value = "projects/test-project/messages/mock_message_id_123"
        
        # Mock Notification and Message classes
        mock_msg.Notification = MagicMock()
        mock_msg.Message = MagicMock()
        
        # Mock error classes
        mock_msg.UnregisteredError = type('UnregisteredError', (Exception,), {})
        mock_msg.SenderIdMismatchError = type('SenderIdMismatchError', (Exception,), {})
        
        yield mock_msg


@pytest.fixture
def mock_credentials():
    """Mock the firebase_admin.credentials module."""
    with patch('fcm_send.client.credentials') as mock_creds:
        mock_certificate = MagicMock()
        mock_access_token = MagicMock()
        mock_access_token.access_token = "mock_http_access_token_67890"
        mock_certificate.get_access_token.return_value = mock_access_token
        mock_creds.Certificate.return_value = mock_certificate
        
        yield mock_creds


@pytest.fixture
def mock_cli_messaging():
    """Mock the firebase_admin.messaging module for CLI tests."""
    with patch('fcm_send.cli.messaging') as mock_msg:
        # Mock send to return a message ID
        mock_msg.send.return_value = "projects/test-project/messages/mock_message_id_123"
        
        # Mock Notification and Message classes
        mock_msg.Notification = MagicMock()
        mock_msg.Message = MagicMock()
        
        # Mock error classes
        mock_msg.UnregisteredError = type('UnregisteredError', (Exception,), {})
        mock_msg.SenderIdMismatchError = type('SenderIdMismatchError', (Exception,), {})
        
        yield mock_msg


@pytest.fixture
def clean_environment():
    """Ensure clean environment for each test."""
    # Save original env
    original_env = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Remove env var if exists
    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    
    yield
    
    # Restore original env
    if original_env:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_env
    elif "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
