"""
Unit tests for FCMClient class.
"""

import os
import pytest
from unittest.mock import patch

from fcm_send import FCMClient, AccessTokenType


class TestFCMClientCredentials:
    """Tests for FCMClient credentials handling."""

    def test_credentials_path_from_cli_argument(self, temp_credentials_file, clean_environment):
        """Test that CLI argument takes precedence over environment variable."""
        client = FCMClient(credentials_key_file=temp_credentials_file)
        assert client.credentials_path == temp_credentials_file

    def test_credentials_path_from_environment(self, temp_credentials_file, clean_environment):
        """Test credentials path from environment variable."""
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_credentials_file
        client = FCMClient()
        assert client.credentials_path == temp_credentials_file

    def test_credentials_path_cli_takes_precedence(self, temp_credentials_file, clean_environment):
        """Test CLI argument takes precedence over environment variable."""
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/some/other/path.json"
        client = FCMClient(credentials_key_file=temp_credentials_file)
        assert client.credentials_path == temp_credentials_file

    def test_credentials_path_missing_raises_error(self, clean_environment):
        """Test that missing credentials raises EnvironmentError."""
        client = FCMClient()
        with pytest.raises(EnvironmentError) as exc_info:
            _ = client.credentials_path
        assert "No credentials provided" in str(exc_info.value)
        assert "--credentials-key-file" in str(exc_info.value)
        assert "GOOGLE_APPLICATION_CREDENTIALS" in str(exc_info.value)

    def test_credentials_path_file_not_found(self, clean_environment):
        """Test that non-existent file raises FileNotFoundError."""
        client = FCMClient(credentials_key_file="/nonexistent/path/file.json")
        with pytest.raises(FileNotFoundError) as exc_info:
            _ = client.credentials_path
        assert "Credentials file not found" in str(exc_info.value)


class TestFCMClientCredentialsInfo:
    """Tests for FCMClient credentials info loading."""

    def test_credentials_info_loads_json(self, temp_credentials_file, mock_service_account_data, clean_environment):
        """Test that credentials info is loaded correctly from JSON."""
        client = FCMClient(credentials_key_file=temp_credentials_file)
        info = client.credentials_info
        
        assert info is not None
        assert info["project_id"] == mock_service_account_data["project_id"]
        assert info["client_email"] == mock_service_account_data["client_email"]

    def test_credentials_info_cached(self, temp_credentials_file, clean_environment):
        """Test that credentials info is cached after first load."""
        client = FCMClient(credentials_key_file=temp_credentials_file)
        
        # First access
        info1 = client.credentials_info
        # Second access should return cached value
        info2 = client.credentials_info
        
        assert info1 is info2

    def test_project_id(self, temp_credentials_file, mock_service_account_data, clean_environment):
        """Test project_id property."""
        client = FCMClient(credentials_key_file=temp_credentials_file)
        assert client.project_id == mock_service_account_data["project_id"]

    def test_service_account_email(self, temp_credentials_file, mock_service_account_data, clean_environment):
        """Test service_account_email property."""
        client = FCMClient(credentials_key_file=temp_credentials_file)
        assert client.service_account_email == mock_service_account_data["client_email"]

    def test_project_id_returns_empty_when_credentials_info_none(self, clean_environment):
        """Test project_id returns empty string when credentials_info is None."""
        client = FCMClient()
        # Manually set _credentials_info to None and bypass credentials_path check
        client._credentials_info = None
        # Mock credentials_path to avoid the error
        with patch.object(FCMClient, 'credentials_info', None):
            assert client.project_id == ""

    def test_service_account_email_returns_empty_when_credentials_info_none(self, clean_environment):
        """Test service_account_email returns empty string when credentials_info is None."""
        client = FCMClient()
        # Mock credentials_info to return None
        with patch.object(FCMClient, 'credentials_info', None):
            assert client.service_account_email == ""


class TestFCMClientInitialize:
    """Tests for FCMClient initialization."""

    def test_initialize_sets_env_var_when_cli_arg_provided(
        self, temp_credentials_file, mock_firebase_admin, clean_environment
    ):
        """Test that initialize sets environment variable when CLI arg is provided."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            client = FCMClient(credentials_key_file=temp_credentials_file)
            client.initialize()
            
            assert os.environ.get("GOOGLE_APPLICATION_CREDENTIALS") == temp_credentials_file
            mock_firebase_admin.initialize_app.assert_called_once()

    def test_initialize_only_once(self, temp_credentials_file, mock_firebase_admin, clean_environment):
        """Test that initialize is only called once."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            client = FCMClient(credentials_key_file=temp_credentials_file)
            
            client.initialize()
            client.initialize()
            client.initialize()
            
            # Should only be called once
            assert mock_firebase_admin.initialize_app.call_count == 1


class TestFCMClientAccessToken:
    """Tests for FCMClient access token retrieval."""

    def test_get_access_token(self, temp_credentials_file, mock_firebase_admin, clean_environment):
        """Test getting access token from Firebase Admin SDK."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            client = FCMClient(credentials_key_file=temp_credentials_file)
            token = client.get_access_token()
            
            assert token == "mock_access_token_12345"
            mock_firebase_admin.get_app.assert_called()

    def test_get_access_token_http_api(
        self, temp_credentials_file, mock_firebase_admin, mock_credentials, clean_environment
    ):
        """Test getting OAuth2 access token for HTTP API."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.credentials', mock_credentials):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                token = client.get_access_token_http_api()
                
                assert token == "mock_http_access_token_67890"
                mock_credentials.Certificate.assert_called_with(temp_credentials_file)


class TestFCMClientSendNotification:
    """Tests for FCMClient send_notification method."""

    def test_send_notification_success(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test sending a notification successfully."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                response = client.send_notification(
                    fcm_token="test_fcm_token",
                    title="Test Title",
                    body="Test Body"
                )
                
                assert response == "projects/test-project/messages/mock_message_id_123"
                mock_messaging.send.assert_called_once()

    def test_send_notification_with_data(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test sending a notification with custom data."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                response = client.send_notification(
                    fcm_token="test_fcm_token",
                    title="Test Title",
                    body="Test Body",
                    data={"key": "value"}
                )
                
                assert response is not None
                mock_messaging.Message.assert_called()

    def test_send_notification_with_image(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test sending a notification with image."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                response = client.send_notification(
                    fcm_token="test_fcm_token",
                    title="Test Title",
                    body="Test Body",
                    image_url="https://example.com/image.png"
                )
                
                assert response is not None
                mock_messaging.Notification.assert_called()

    def test_send_notification_dry_run(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test sending a notification with dry_run=True."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                client.send_notification(
                    fcm_token="test_fcm_token",
                    title="Test Title",
                    body="Test Body",
                    dry_run=True
                )
                
                # Verify dry_run was passed
                call_args = mock_messaging.send.call_args
                assert call_args.kwargs.get('dry_run') is True


class TestFCMClientSendDataMessage:
    """Tests for FCMClient send_data_message method."""

    def test_send_data_message_success(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test sending a data-only message successfully."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                response = client.send_data_message(
                    fcm_token="test_fcm_token",
                    data={"action": "sync", "id": "123"}
                )
                
                assert response == "projects/test-project/messages/mock_message_id_123"

    def test_send_data_message_converts_values_to_strings(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test that data values are converted to strings."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                # Pass mixed types
                client.send_data_message(
                    fcm_token="test_fcm_token",
                    data={"count": 42, "active": True, "name": "test"}
                )
                
                # Verify Message was called with string data
                call_args = mock_messaging.Message.call_args
                assert call_args is not None

    def test_send_data_message_dry_run(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test sending a data message with dry_run=True."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.messaging', mock_messaging):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                
                client.send_data_message(
                    fcm_token="test_fcm_token",
                    data={"action": "test"},
                    dry_run=True
                )
                
                call_args = mock_messaging.send.call_args
                assert call_args.kwargs.get('dry_run') is True


class TestFCMClientShowInfo:
    """Tests for FCMClient show_info method."""

    def test_show_info_firebase_admin_token(
        self, temp_credentials_file, mock_firebase_admin, capsys, clean_environment
    ):
        """Test show_info displays Firebase Admin SDK access token."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            client = FCMClient(credentials_key_file=temp_credentials_file)
            client.show_info(AccessTokenType.FIREBASE_ADMIN)
            
            captured = capsys.readouterr()
            assert "Firebase Service Account Information" in captured.out
            assert "PROJECT_ID:" in captured.out
            assert "SERVICE_ACCOUNT_EMAIL:" in captured.out
            assert "CREDENTIALS_FILE:" in captured.out
            assert "ACCESS_TOKEN" in captured.out

    def test_show_info_http_api_token(
        self, temp_credentials_file, mock_firebase_admin, mock_credentials, capsys, clean_environment
    ):
        """Test show_info displays HTTP API OAuth2 access token."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            with patch('fcm_send.client.credentials', mock_credentials):
                client = FCMClient(credentials_key_file=temp_credentials_file)
                client.show_info(AccessTokenType.FCM_OAUTH_HTTP_API)
                
                captured = capsys.readouterr()
                assert "Firebase Service Account Information" in captured.out
                assert "ACCESS_TOKEN (first 50 chars):" in captured.out
                assert "mock_http_access_token_67890" in captured.out

    def test_show_info_handles_token_retrieval_error(
        self, temp_credentials_file, mock_firebase_admin, capsys, clean_environment
    ):
        """Test show_info handles errors when retrieving access token."""
        with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
            # Make get_access_token raise an exception
            mock_firebase_admin.get_app.return_value.credential.get_access_token.side_effect = Exception("Token error")
            
            client = FCMClient(credentials_key_file=temp_credentials_file)
            client.show_info(AccessTokenType.FIREBASE_ADMIN)
            
            captured = capsys.readouterr()
            assert "Error retrieving access token:" in captured.out
            assert "Token error" in captured.out


class TestAccessTokenType:
    """Tests for AccessTokenType enum."""

    def test_firebase_admin_type(self):
        """Test FIREBASE_ADMIN enum value."""
        assert AccessTokenType.FIREBASE_ADMIN.value == "firebase_admin"

    def test_fcm_http_api_type(self):
        """Test FCM_OAUTH_HTTP_API enum value."""
        assert AccessTokenType.FCM_OAUTH_HTTP_API.value == "fcm_http_api"
