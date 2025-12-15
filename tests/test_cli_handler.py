"""
Unit tests for CLIHandler class.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

from fcm_send import CLIHandler, FCMClient, AccessTokenType


class TestCLIHandlerParser:
    """Tests for CLIHandler argument parser."""

    def test_parser_has_credentials_key_file_arg(self):
        """Test that parser includes --credentials-key-file argument."""
        with patch.object(sys, 'argv', ['fcm_send']):
            handler = CLIHandler()
            
            # Check that the argument was parsed (will be None if not provided)
            assert hasattr(handler.args, 'credentials_key_file')

    def test_parser_has_info_arg(self):
        """Test that parser includes --info argument."""
        with patch.object(sys, 'argv', ['fcm_send', '--info']):
            with patch.object(CLIHandler, 'run'):  # Prevent actual run
                handler = CLIHandler()
                assert handler.args.info is True

    def test_parser_has_token_arg(self):
        """Test that parser includes --token argument."""
        with patch.object(sys, 'argv', ['fcm_send', '--token', 'test_token']):
            handler = CLIHandler()
            assert handler.args.token == 'test_token'

    def test_parser_has_title_and_body_args(self):
        """Test that parser includes --title and --body arguments."""
        with patch.object(sys, 'argv', ['fcm_send', '--title', 'Test', '--body', 'Body']):
            handler = CLIHandler()
            assert handler.args.title == 'Test'
            assert handler.args.body == 'Body'

    def test_parser_has_data_arg(self):
        """Test that parser includes --data argument."""
        with patch.object(sys, 'argv', ['fcm_send', '--data', '{"key": "value"}']):
            handler = CLIHandler()
            assert handler.args.data == '{"key": "value"}'

    def test_parser_has_data_only_arg(self):
        """Test that parser includes --data-only argument."""
        with patch.object(sys, 'argv', ['fcm_send', '--data-only', '{"action": "sync"}']):
            handler = CLIHandler()
            assert handler.args.data_only == '{"action": "sync"}'

    def test_parser_has_dry_run_arg(self):
        """Test that parser includes --dry-run argument."""
        with patch.object(sys, 'argv', ['fcm_send', '--dry-run']):
            handler = CLIHandler()
            assert handler.args.dry_run is True

    def test_parser_has_image_arg(self):
        """Test that parser includes --image argument."""
        with patch.object(sys, 'argv', ['fcm_send', '--image', 'https://example.com/img.png']):
            handler = CLIHandler()
            assert handler.args.image == 'https://example.com/img.png'


class TestCLIHandlerRun:
    """Tests for CLIHandler run method."""

    def test_run_shows_help_when_no_args(self, capsys):
        """Test that help is shown when no arguments provided."""
        with patch.object(sys, 'argv', ['fcm_send']):
            handler = CLIHandler()
            handler.run()
            
            captured = capsys.readouterr()
            assert 'usage:' in captured.out.lower() or 'Firebase Cloud Messaging' in captured.out

    def test_run_calls_handle_info_for_info_flag(self, temp_credentials_file, clean_environment):
        """Test that --info flag calls handle_info."""
        with patch.object(sys, 'argv', ['fcm_send', '--credentials-key-file', temp_credentials_file, '--info']):
            handler = CLIHandler()
            handler.handle_info = MagicMock()
            
            handler.run()
            
            handler.handle_info.assert_called_once_with()

    def test_run_calls_handle_info_for_access_token_flag(self, temp_credentials_file, clean_environment):
        """Test that --access-token flag calls handle_info."""
        with patch.object(sys, 'argv', ['fcm_send', '--credentials-key-file', temp_credentials_file, '--access-token']):
            handler = CLIHandler()
            handler.handle_info = MagicMock()
            
            handler.run()
            
            handler.handle_info.assert_called_once()

    def test_run_calls_handle_info_http_for_info_http_flag(self, temp_credentials_file, clean_environment):
        """Test that --info-http flag calls handle_info with HTTP token type."""
        with patch.object(sys, 'argv', ['fcm_send', '--credentials-key-file', temp_credentials_file, '--info-http']):
            handler = CLIHandler()
            handler.handle_info = MagicMock()
            
            handler.run()
            
            handler.handle_info.assert_called_once_with(AccessTokenType.FCM_OAUTH_HTTP_API)

    def test_run_calls_handle_notification(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test that notification flags call handle_notification."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--title', 'Test',
            '--body', 'Body'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.handle_notification = MagicMock()
                    
                    handler.run()
                    
                    handler.handle_notification.assert_called_once()

    def test_run_calls_handle_data_only(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test that --data-only flag calls handle_data_only."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--data-only', '{"action": "sync"}'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.handle_data_only = MagicMock()
                    
                    handler.run()
                    
                    handler.handle_data_only.assert_called_once()


class TestCLIHandlerHandleInfo:
    """Tests for CLIHandler handle_info method."""

    def test_handle_info_calls_client_show_info(
        self, temp_credentials_file, mock_firebase_admin, mock_credentials, clean_environment
    ):
        """Test that handle_info calls client.show_info."""
        with patch.object(sys, 'argv', ['fcm_send', '--credentials-key-file', temp_credentials_file]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.credentials', mock_credentials):
                    handler = CLIHandler()
                    handler.client.show_info = MagicMock()
                    
                    handler.handle_info()
                    
                    handler.client.show_info.assert_called_once_with(AccessTokenType.FIREBASE_ADMIN)

    def test_handle_info_with_http_token_type(
        self, temp_credentials_file, mock_firebase_admin, mock_credentials, clean_environment
    ):
        """Test that handle_info passes correct token type."""
        with patch.object(sys, 'argv', ['fcm_send', '--credentials-key-file', temp_credentials_file]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.credentials', mock_credentials):
                    handler = CLIHandler()
                    handler.client.show_info = MagicMock()
                    
                    handler.handle_info(AccessTokenType.FCM_OAUTH_HTTP_API)
                    
                    handler.client.show_info.assert_called_once_with(AccessTokenType.FCM_OAUTH_HTTP_API)

    def test_handle_info_exits_on_error(self, clean_environment):
        """Test that handle_info exits on EnvironmentError."""
        with patch.object(sys, 'argv', ['fcm_send']):
            handler = CLIHandler()
            handler.client.show_info = MagicMock(side_effect=EnvironmentError("Test error"))
            
            with pytest.raises(SystemExit) as exc_info:
                handler.handle_info()
            
            assert exc_info.value.code == 1


class TestCLIHandlerHandleNotification:
    """Tests for CLIHandler handle_notification method."""

    def test_handle_notification_success(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, capsys, clean_environment
    ):
        """Test successful notification handling."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--title', 'Test',
            '--body', 'Body'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.handle_notification(handler.args)
                    
                    captured = capsys.readouterr()
                    assert '✓' in captured.out
                    assert 'successfully' in captured.out.lower()

    def test_handle_notification_with_data(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test notification handling with custom data."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--title', 'Test',
            '--body', 'Body',
            '--data', '{"key": "value"}'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.client.send_notification = MagicMock(return_value="msg_id")
                    
                    handler.handle_notification(handler.args)
                    
                    call_kwargs = handler.client.send_notification.call_args.kwargs
                    assert call_kwargs['data'] == {'key': 'value'}

    def test_handle_notification_invalid_json_exits(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test that invalid JSON in --data exits with error."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--title', 'Test',
            '--body', 'Body',
            '--data', 'invalid json'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    
                    with pytest.raises(SystemExit) as exc_info:
                        handler.handle_notification(handler.args)
                    
                    assert exc_info.value.code == 1

    def test_handle_notification_dry_run(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, capsys, clean_environment
    ):
        """Test notification dry run mode."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--title', 'Test',
            '--body', 'Body',
            '--dry-run'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.handle_notification(handler.args)
                    
                    captured = capsys.readouterr()
                    assert 'Dry run' in captured.out


class TestCLIHandlerHandleDataOnly:
    """Tests for CLIHandler handle_data_only method."""

    def test_handle_data_only_success(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, capsys, clean_environment
    ):
        """Test successful data-only message handling."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--data-only', '{"action": "sync"}'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.handle_data_only(handler.args)
                    
                    captured = capsys.readouterr()
                    assert '✓' in captured.out
                    assert 'successfully' in captured.out.lower()

    def test_handle_data_only_invalid_json_exits(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test that invalid JSON in --data-only exits with error."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--data-only', 'not valid json'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    
                    with pytest.raises(SystemExit) as exc_info:
                        handler.handle_data_only(handler.args)
                    
                    assert exc_info.value.code == 1

    def test_handle_data_only_dry_run(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, capsys, clean_environment
    ):
        """Test data-only dry run mode."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--data-only', '{"action": "sync"}',
            '--dry-run'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    handler = CLIHandler()
                    handler.handle_data_only(handler.args)
                    
                    captured = capsys.readouterr()
                    assert 'Dry run' in captured.out

    def test_handle_data_only_send_error_exits(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
    ):
        """Test that send error in data-only exits with error."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--data-only', '{"action": "sync"}'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    # Make send_data_message raise an exception
                    mock_messaging.send.side_effect = Exception("Network error")
                    
                    handler = CLIHandler()
                    
                    with pytest.raises(SystemExit) as exc_info:
                        handler.handle_data_only(handler.args)
                    
                    assert exc_info.value.code == 1


class TestCLIHandlerNotificationErrors:
    """Tests for CLIHandler notification error handling."""

    def test_handle_notification_unregistered_error(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, mock_cli_messaging, capsys, clean_environment
    ):
        """Test handling of UnregisteredError."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'invalid_token',
            '--title', 'Test',
            '--body', 'Body'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    with patch('fcm_send.cli.messaging', mock_cli_messaging):
                        # Make send raise UnregisteredError
                        mock_messaging.send.side_effect = mock_cli_messaging.UnregisteredError("Token not registered")
                        
                        handler = CLIHandler()
                        
                        with pytest.raises(SystemExit) as exc_info:
                            handler.handle_notification(handler.args)
                        
                        assert exc_info.value.code == 1
                        captured = capsys.readouterr()
                        assert "not registered" in captured.out.lower()

    def test_handle_notification_sender_id_mismatch_error(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, mock_cli_messaging, capsys, clean_environment
    ):
        """Test handling of SenderIdMismatchError."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'wrong_project_token',
            '--title', 'Test',
            '--body', 'Body'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    with patch('fcm_send.cli.messaging', mock_cli_messaging):
                        # Make send raise SenderIdMismatchError
                        mock_messaging.send.side_effect = mock_cli_messaging.SenderIdMismatchError("Sender ID mismatch")
                        
                        handler = CLIHandler()
                        
                        with pytest.raises(SystemExit) as exc_info:
                            handler.handle_notification(handler.args)
                        
                        assert exc_info.value.code == 1
                        captured = capsys.readouterr()
                        assert "sender ID" in captured.out.lower() or "wrong project" in captured.out.lower()

    def test_handle_notification_generic_error(
        self, temp_credentials_file, mock_firebase_admin, mock_messaging, capsys, clean_environment
    ):
        """Test handling of generic exceptions."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token',
            '--title', 'Test',
            '--body', 'Body'
        ]):
            with patch('fcm_send.client.firebase_admin', mock_firebase_admin):
                with patch('fcm_send.client.messaging', mock_messaging):
                    # Make send raise a generic exception
                    mock_messaging.send.side_effect = Exception("Network timeout")
                    
                    handler = CLIHandler()
                    
                    with pytest.raises(SystemExit) as exc_info:
                        handler.handle_notification(handler.args)
                    
                    assert exc_info.value.code == 1
                    captured = capsys.readouterr()
                    assert "Error sending notification" in captured.out


class TestCLIHandlerParserErrors:
    """Tests for CLIHandler parser error handling."""

    def test_run_requires_token_for_data_only(self, temp_credentials_file, clean_environment):
        """Test that --data-only requires --token."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--data-only', '{"action": "sync"}'
            # Missing --token
        ]):
            handler = CLIHandler()
            
            with pytest.raises(SystemExit) as exc_info:
                handler.run()
            
            # argparse exits with code 2 for errors
            assert exc_info.value.code == 2

    def test_run_requires_title_and_body_for_notification(self, temp_credentials_file, clean_environment):
        """Test that notification requires --title and --body."""
        with patch.object(sys, 'argv', [
            'fcm_send',
            '--credentials-key-file', temp_credentials_file,
            '--token', 'test_token'
            # Missing --title and --body
        ]):
            handler = CLIHandler()
            
            with pytest.raises(SystemExit) as exc_info:
                handler.run()
            
            # argparse exits with code 2 for errors
            assert exc_info.value.code == 2


class TestMainFunction:
    """Tests for main() entry point."""

    def test_main_creates_cli_handler_and_runs(self, capsys):
        """Test that main() creates CLIHandler and calls run()."""
        from fcm_send import main
        
        with patch.object(sys, 'argv', ['fcm_send']):
            main()
            
            captured = capsys.readouterr()
            # Should print help when no args
            assert 'usage:' in captured.out.lower() or 'Firebase Cloud Messaging' in captured.out
