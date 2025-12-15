"""
CLI module - handles command-line interface for FCM operations.
"""

import argparse
import json
import sys

from firebase_admin import messaging

from fcm_send.__version__ import __version__
from fcm_send.client import FCMClient, AccessTokenType


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
            "--version",
            action="version",
            version=f"%(prog)s {__version__}"
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

