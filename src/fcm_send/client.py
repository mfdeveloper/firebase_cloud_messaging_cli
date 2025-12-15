"""
FCM Client module - handles Firebase Cloud Messaging operations.
"""

import json
import os
from enum import Enum
from typing import Optional

import firebase_admin
from firebase_admin import credentials, messaging


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

