"""
Firebase Cloud Messaging (FCM) Notification Sender

A Python CLI tool and library for sending FCM notifications using the Firebase Admin SDK.

Example usage as a library:
    from fcm_send import FCMClient
    
    client = FCMClient("/path/to/service-account.json")
    response = client.send_notification(
        fcm_token="device_token",
        title="Hello",
        body="World"
    )
"""

# Import version first (no dependencies)
from fcm_send.__version__ import __version__

# Import submodules so they can be accessed for patching
from fcm_send import client
from fcm_send import cli

# Import public API
from fcm_send.client import FCMClient, AccessTokenType
from fcm_send.cli import CLIHandler, main

__all__ = ["FCMClient", "AccessTokenType", "CLIHandler", "main", "__version__", "client", "cli"]

