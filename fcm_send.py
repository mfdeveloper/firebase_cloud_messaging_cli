#!/usr/bin/env python3
"""
Firebase Cloud Messaging (FCM) Notification Sender

This script programmatically sends FCM notifications using the Firebase Admin Python SDK.

Prerequisites:
    pip install -r requirements.txt

Credentials (one of the following is required):
    --credentials-key-file: CLI argument pointing to the service account JSON file (takes precedence)
    GOOGLE_APPLICATION_CREDENTIALS: Environment variable pointing to the service account JSON file

Usage:
    ./fcm_send.py --credentials-key-file /path/to/service-account.json --info
    ./fcm_send.py --token <FCM_TOKEN> --title "Hello" --body "World"
    ./fcm_send.py --token <FCM_TOKEN> --title "Hello" --body "World" --data '{"key": "value"}'
    ./fcm_send.py --info  # Display service account info and Firebase Admin SDK access token
    ./fcm_send.py --info-http  # Display service account info and Google OAuth2 access token for using with FCM HTTP API
    ./fcm_send.py --access-token  # Alias for --info
    ./fcm_send.py --access-token-http  # Alias for --info-http
    ./fcm_send.py --token <YOUR_FCM_TOKEN> \
        --title "Order Update" \
        --body "Your order has been shipped!" \
        --data '{"order_id": "12345", "action": "open_order"}'
    ./fcm_send.py --token <YOUR_FCM_TOKEN> --data-only '{"action": "sync", "resource_id": "123"}'
"""

import argparse
import json
import os
import sys
from typing import Optional
from enum import Enum

try:
    import firebase_admin
    from firebase_admin import credentials, messaging
except ImportError:
    print("Error: firebase-admin package not installed.")
    print("Are you using a virtual environment? (run: source venv/bin/activate)")
    print("If not, install it with: pip install -r requirements.txt")
    sys.exit(1)

class AccessTokenType(Enum):
    """
    Type of access token to retrieve.

    #### References

    - [python.org: enum — Support for enumerations](https://docs.python.org/3/library/enum.html)
    """
    FIREBASE_ADMIN = "firebase_admin"
    FCM_OAUTH_HTTP_API = "fcm_http_api"

class FCMClient:
    """Firebase Cloud Messaging client for sending notifications."""

    def __init__(self, credentials_key_file: Optional[str] = None):
        """
        Initialize the FCM client.
        
        Args:
            credentials_key_file: Optional path to the service account JSON file.
                                  If provided, takes precedence over GOOGLE_APPLICATION_CREDENTIALS.
        """
        self._credentials_key_file = credentials_key_file
        self._credentials_info: Optional[dict] = None
        self._initialized = False

    @property
    def credentials_path(self) -> str:
        """
        Get the path to the credentials file.
        
        Priority:
            1. `--credentials-key-file` CLI argument
            2. `GOOGLE_APPLICATION_CREDENTIALS` environment variable
        """
        # CLI argument takes precedence
        if self._credentials_key_file:
            creds_path = self._credentials_key_file
        else:
            creds_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

        if not creds_path:
            raise EnvironmentError(
                "No credentials provided. Please provide one of the following:\n"
                "  1. Use --credentials-key-file /path/to/service-account.json\n"
                "  2. Set environment variable: export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json"
            )

        if not os.path.exists(creds_path):
            raise FileNotFoundError(f"Credentials file not found: {creds_path}")

        return creds_path

    @property
    def credentials_info(self) -> Optional[dict]:
        """Load and return the service account credentials info."""
        if self._credentials_info is None:
            with open(self.credentials_path, "r") as f:
                self._credentials_info = json.load(f)
        return self._credentials_info

    @property
    def project_id(self) -> str:
        """Get the project ID from credentials."""
        if self.credentials_info:
            return self.credentials_info.get("project_id", "N/A")
        
        return ""

    @property
    def service_account_email(self) -> str:
        """Get the service account email from credentials."""
        if self.credentials_info:
            return self.credentials_info.get("client_email", "N/A")
        
        return ""

    def initialize(self) -> None:
        """
        Initialize the Firebase Admin SDK.
        
        If credentials_key_file was provided via CLI, it sets the environment variable
        so that Google Application Default Credentials (ADC) can find it.
        
        See: https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments
        """
        if not self._initialized and not firebase_admin._apps:
            # If CLI argument was provided, set the environment variable for ADC
            if self._credentials_key_file:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = self._credentials_key_file
            
            firebase_admin.initialize_app()
            self._initialized = True

    def get_access_token(self) -> str:
        """Get the current access token from Firebase Admin SDK."""
        self.initialize()
        cred = firebase_admin.get_app().credential
        access_token_info = cred.get_access_token()
        return access_token_info.access_token

    def get_access_token_http_api(self) -> str:
        """Get the current Google OAuth2 access token for using with FCM HTTP API."""
        self.initialize()

        certificate = credentials.Certificate(self.credentials_path)
        access_token_info = certificate.get_access_token()

        return access_token_info.access_token

    def show_info(self, access_token_type: AccessTokenType) -> None:
        """Display service account information and access token."""
        print("\n" + "=" * 60)
        print("Firebase Service Account Information")
        print("=" * 60)
        print(f"  PROJECT_ID:            {self.project_id}")
        print(f"  SERVICE_ACCOUNT_EMAIL: {self.service_account_email}")
        print(f"  CREDENTIALS_FILE:      {self.credentials_path}")
        print("=" * 60)

        try:
            if access_token_type == AccessTokenType.FCM_OAUTH_HTTP_API:
                access_token = self.get_access_token_http_api()
                print(f"\n  ACCESS_TOKEN (first 50 chars): {access_token[:50]}...")
            else:
                access_token = self.get_access_token()

            print(f"  ACCESS_TOKEN (full):\n{access_token}")
        except Exception as e:
            print(f"\n  Error retrieving access token: {e}")

        print("=" * 60 + "\n")

    def send_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[dict] = None,
        image_url: Optional[str] = None,
        dry_run: bool = False
    ) -> str:
        """
        Send an FCM notification to a specific device.

        Args:
            fcm_token: The FCM registration token of the target device
            title: Notification title
            body: Notification body
            data: Optional custom data payload (dict)
            image_url: Optional image URL for the notification
            dry_run: If True, validates message without sending

        Returns:
            The message ID from FCM

        Raises:
            messaging.UnregisteredError: If the token is not registered
            messaging.SenderIdMismatchError: If the token doesn't match sender ID
        """
        self.initialize()

        # Build the notification
        notification = messaging.Notification(
            title=title,
            body=body,
            image=image_url
        )

        # Build the message
        message = messaging.Message(
            notification=notification,
            token=fcm_token,
            data=data
        )

        response = messaging.send(message, dry_run=dry_run)
        return response

    def send_data_message(
        self,
        fcm_token: str,
        data: dict,
        dry_run: bool = False
    ) -> str:
        """
        Send a data-only FCM message to a specific device.

        Args:
            fcm_token: The FCM registration token of the target device
            data: Custom data payload (dict with string keys and values)
            dry_run: If True, validates message without sending

        Returns:
            The message ID from FCM
        """
        self.initialize()

        # Ensure all data values are strings (FCM requirement)
        string_data = {k: str(v) for k, v in data.items()}

        message = messaging.Message(
            data=string_data,
            token=fcm_token
        )

        response = messaging.send(message, dry_run=dry_run)
        return response


class CLIHandler:
    """Command-line interface handler for FCM operations."""

    def __init__(self):
        """Initialize the CLI handler, parse arguments, and create FCM client."""
        self.parser = self._create_parser()
        self.args = self.parser.parse_args()
        self.client = FCMClient(self.args.credentials_key_file)

    def _create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            description="Send Firebase Cloud Messaging notifications",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Using --credentials-key-file (takes precedence over environment variable)
  %(prog)s --credentials-key-file /path/to/service-account.json --info

  # Show service account info and access token
  %(prog)s --info
  %(prog)s --access-token

  # Show service account info and Google OAuth2 access token for FCM HTTP API
  %(prog)s --info-http
  %(prog)s --access-token-http

  # Send a simple notification
  %(prog)s --token <YOUR_FCM_TOKEN> --title "Hello" --body "World"

  # Send notification with custom data
  %(prog)s --token <YOUR_FCM_TOKEN> --title "Order Update" --body "Your order shipped" --data '{"order_id": "12345"}'

  # Send data-only message (no notification shown)
  %(prog)s --token <YOUR_FCM_TOKEN> --data-only '{"action": "sync", "id": "123"}'

  # Validate message without sending (dry run)
  %(prog)s --token <YOUR_FCM_TOKEN> --title "Test" --body "Test" --dry-run

Credentials (one of the following is required):
  --credentials-key-file          Path to Firebase service account JSON file (CLI argument, takes precedence)
  GOOGLE_APPLICATION_CREDENTIALS  Path to Firebase service account JSON file (environment variable)
            """
        )

        parser.add_argument(
            "--credentials-key-file",
            metavar="PATH",
            dest="credentials_key_file",
            help="Path to Firebase service account JSON file (takes precedence over GOOGLE_APPLICATION_CREDENTIALS)"
        )

        parser.add_argument(
            "--info",
            action="store_true",
            help="Display service account info and Firebase Admin SDK access token"
        )

        parser.add_argument(
            "--access-token",
            action="store_true",
            help="Display service account info and Firebase Admin SDK access token"
        )

        parser.add_argument(
            "--info-http",
            action="store_true",
            help="Display service account info and Google OAuth2 access token for using with FCM HTTP API"
        )

        parser.add_argument(
            "--access-token-http",
            action="store_true",
            help="Display service account info and Google OAuth2 access token for using with FCM HTTP API"
        )

        parser.add_argument(
            "--token",
            metavar="FCM_TOKEN",
            help="FCM registration token of the target device"
        )

        parser.add_argument(
            "--title",
            help="Notification title"
        )

        parser.add_argument(
            "--body",
            help="Notification body"
        )

        parser.add_argument(
            "--data",
            metavar="JSON",
            help="Custom data payload as JSON string (e.g., '{\"key\": \"value\"}')"
        )

        parser.add_argument(
            "--data-only",
            metavar="JSON",
            dest="data_only",
            help="Send data-only message (no notification) with JSON payload"
        )

        parser.add_argument(
            "--image",
            metavar="URL",
            help="Image URL for the notification"
        )

        parser.add_argument(
            "--dry-run",
            action="store_true",
            dest="dry_run",
            help="Validate the message without actually sending it"
        )

        return parser

    def handle_info(self, access_token_type: AccessTokenType = AccessTokenType.FIREBASE_ADMIN) -> None:
        """Handle the --info command."""
        try:
            self.client.show_info(access_token_type)
        except (EnvironmentError, FileNotFoundError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    def handle_data_only(self, args) -> None:
        """Handle the --data-only command."""
        try:
            data = json.loads(args.data_only)
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in --data-only: {e}")
            sys.exit(1)

        try:
            response = self.client.send_data_message(args.token, data, args.dry_run)
            if args.dry_run:
                print("\n✓ Dry run successful! Data message is valid.")
                print(f"  Message ID (dry run): {response}")
            else:
                print("\n✓ Data message sent successfully!")
                print(f"  Message ID: {response}")
        except Exception as e:
            print(f"\n✗ Error sending data message: {e}")
            sys.exit(1)

    def handle_notification(self, args) -> None:
        """Handle the notification command."""
        data = None
        if args.data:
            try:
                data = json.loads(args.data)
                # Ensure all values are strings
                data = {k: str(v) for k, v in data.items()}
            except json.JSONDecodeError as e:
                print(f"Error: Invalid JSON in --data: {e}")
                sys.exit(1)

        try:
            response = self.client.send_notification(
                fcm_token=args.token,
                title=args.title,
                body=args.body,
                data=data,
                image_url=args.image,
                dry_run=args.dry_run
            )
            if args.dry_run:
                print("\n✓ Dry run successful! Message is valid.")
                print(f"  Message ID (dry run): {response}")
            else:
                print("\n✓ Notification sent successfully!")
                print(f"  Message ID: {response}")
        except messaging.UnregisteredError:
            print("\n✗ Error: The FCM token is not registered (device may have uninstalled the app)")
            sys.exit(1)
        except messaging.SenderIdMismatchError:
            print("\n✗ Error: The FCM token does not match the sender ID (wrong project?)")
            sys.exit(1)
        except Exception as e:
            print(f"\n✗ Error sending notification: {e}")
            sys.exit(1)

    def run(self) -> None:
        """Run the CLI application."""
        # Show info mode with Firebase Admin SDK access token
        if self.args.info or self.args.access_token:
            self.handle_info()
            return

        # Show info mode with Google OAuth2 (HTTP) access token
        if self.args.info_http or self.args.access_token_http:
            self.handle_info(AccessTokenType.FCM_OAUTH_HTTP_API)
            return

        # Data-only message mode
        if self.args.data_only:
            if not self.args.token:
                self.parser.error("--token is required for sending messages")
            self.handle_data_only(self.args)
            return

        # Regular notification mode
        if self.args.token:
            if not self.args.title or not self.args.body:
                self.parser.error("--title and --body are required for notifications")
            self.handle_notification(self.args)
            return

        # No valid action specified
        self.parser.print_help()


def main():
    """Main entry point."""
    cli = CLIHandler()
    cli.run()

if __name__ == "__main__":
    main()
