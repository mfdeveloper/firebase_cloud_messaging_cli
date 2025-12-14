# FCM Notification Sender

![fcm-icon](./images/firebase-fcm-icon.png)

A Python CLI tool for sending[Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android) notifications using the **[Firebase Admin SDK](https://firebase.google.com/docs/admin/setup#add-sdk).**

## Features

- **Send push notifications** with title, body, and optional custom data
- **Send data-only messages** (silent notifications for background processing)
- **Display service account info** and retrieve the access token
- **Dry-run mode** to validate messages without sending
- **Image support** for rich notifications

## Prerequisites

### 1. Set Up Virtual Environment

```bash
# Navigate to the firebase-notifications directory
cd scripts/firebase-notifications

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> **Note:** Always activate the virtual environment before running the script.

### 2. Firebase Service Account

To authenticate a service account and authorize it to access Firebase services, you must generate a
`service-account.json` private key file in **JSON** format.

**To generate and obtain one: a private key file for your service account:**

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Open **Project Settings** > [Service Accounts](https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk).
4. Click **Generate New Private Key**, then confirm by clicking **Generate Key**.
5. Securely store the `.json` file containing the key.

> For more details, see the Firebase documentation page: [Initialize the SDK in non-Google environments](https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments)

### 3. Environment Setup

Set the credentials environment variable pointing to your service account JSON file:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-service-account.json
```

> **Tip:** Add this to your `~/.zshrc` or `~/.bashrc` for persistence.

## External Variables Reference

| Variable                         | Description                                                          |
|----------------------------------|----------------------------------------------------------------------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Environment variable pointing to the service account `.json` file    |
| `ACCESS_TOKEN`                   | Temporary Firebase access token (retrieved automatically by the SDK) |
| `FCM_TOKEN`                      | Device FCM registration token (obtained from mobile app)             |
| `SERVICE_ACCOUNT_EMAIL`          | The `client_email` field from the credentials JSON                   |
| `PROJECT_ID`                     | The `project_id` field from the credentials JSON                     |

## Usage

### Activate Virtual Environment

Before running any commands, activate the virtual environment:

```bash
cd scripts/firebase-notifications
source venv/bin/activate
```

To deactivate when done:

```bash
deactivate
```

**Alternative:** Run directly without activating:

```bash
scripts/firebase-notifications/venv/bin/python scripts/firebase-notifications/fcm_send.py.py --info
```

> **Note:** Using a code editor (such as [VSCode](https://code.visualstudio.com) or [Cursor](https://cursor.com)) a Python Virtual Environment can be loaded automatically using [.vscode/settings.json](./.vscode/settings.json) configurations.
> Open this folder as `${workspaceFolder}` and `settings.json` file mentioned above would be loaded!
---

### Pass Google Credentials `.json` file

```bash
# Using CLI argument (takes precedence)
./fcm_send.py --credentials-key-file ~/my-service-account.json --info

# Using environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/my-service-account.json
./fcm_send.py --info

# Combining with other commands
./fcm_send.py --credentials-key-file ~/sa.json --token FCM_TOKEN --title "Hi" --body "Test"
```

### Show Service Account Info & Access Token

Display project details and retrieve the current **Firebase Admin SDK** access token:

```bash
./fcm_send.py --info
# Or use --access-token alias
./fcm_send.py --access-token
```

**Output:**

```bash
============================================================
Firebase Service Account Information
============================================================
  PROJECT_ID:            your-project-id
  SERVICE_ACCOUNT_EMAIL: firebase-adminsdk@your-project.iam.gserviceaccount.com
  CREDENTIALS_FILE:      /path/to/service-account.json
============================================================

  ACCESS_TOKEN (first 50 chars): ya29.c.c0ASRK0GYQ...
  ACCESS_TOKEN (full):
  ya29.c.c0ASRK0GYQ...
============================================================
```

Alternatively, display project details with current **Google OAuth2 access token for using with FCM HTTP API** access token. You can use it to perform a `curl` or any other way for HTTP requests on FCM API:

```bash
./fcm_send.py --info-http
# Or use --access-token-http alias
./fcm_send.py --access-token-http
```

### Send a Simple Notification

```bash
./fcm_send.py --token YOUR_FCM_TOKEN --title "Hello" --body "World"
```

### Send Notification with Custom Data Payload

```bash
./fcm_send.py --token YOUR_FCM_TOKEN \
  --title "Order Update" \
  --body "Your order has been shipped!" \
  --data '{"order_id": "12345", "action": "open_order"}'
```

### Send Notification with Image

```bash
./fcm_send.py --token YOUR_FCM_TOKEN \
  --title "Check this out" \
  --body "New feature available!" \
  --image "https://example.com/image.png"
```

### Send Data-Only Message (Silent/Background)

Data-only messages don't show a visible notification but are delivered to your app for background processing:

```bash
./fcm_send.py --token YOUR_FCM_TOKEN \
  --data-only '{"action": "sync", "resource_id": "123"}'
```

### Validate Message Without Sending (Dry Run)

Test your message configuration without actually sending it:

```bash
./fcm_send.py --token YOUR_FCM_TOKEN \
  --title "Test" \
  --body "This is a test" \
  --dry-run
```

## CLI Options Reference

| Option                   | Description                                                                                                |
|--------------------------|------------------------------------------------------------------------------------------------------------|
| `--credentials-key-file` | Path to Firebase service account `.json` file (CLI argument, takes over `$GOOGLE_APPLICATION_CREDENTIALS)` |
| `--info`                 | Display service account info and access token                                                              |
| `--info-http`            | Display service account info and **Google OAuth2** access token for **FCM HTTP API**                       |
| `--access-token`         | Alias for `--info`                                                                                         |
| `--access-token-http`    | Alias for `--info-http`                                                                                    |
| `--token <FCM_TOKEN>`    | FCM registration token of the target device                                                                |
| `--title TEXT`           | Notification title                                                                                         |
| `--body TEXT`            | Notification body                                                                                          |
| `--data <JSON>`          | Custom data payload as JSON string (e.g `--data '{"action": "sync" }'`)                                    |
| `--data-only <JSON>`     | Send data-only message (no visible notification)                                                           |
| `--image URL`            | Image URL for rich notifications                                                                           |
| `--dry-run`              | Validate message without sending                                                                           |

## Getting the FCM Token from Your App

To send notifications, you need the FCM registration token from your mobile app. In Android:

```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        Log.d("FCM", "Token: $token")
    }
}
```

> **Reference:** [FCM: Retrieve the current registration token](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android#retrieve-the-current-registration-token)

## Troubleshooting

### "GOOGLE_APPLICATION_CREDENTIALS environment variable not set"

Make sure you've exported the environment variable:

```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

> **Reference:** [Firebase Admin SDK: Initialize in non-Google environments](https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments)

### "The FCM token is not registered"

This error occurs when:

- The app has been uninstalled from the device
- The token has expired or been rotated
- The token was generated for a different Firebase project

### "The FCM token does not match the sender ID"

The FCM token was generated for a different Firebase project. Make sure you're using:

- The correct service account JSON for your project
- An FCM token generated by an app configured with the same Firebase project

## Class Structure

The script is organized into two main classes:

### `FCMClient`

Handles all Firebase operations:

- `credentials_path` - Get credentials file path from environment
- `credentials_info` - Load/cache credentials JSON
- `project_id` - Get project ID from credentials
- `service_account_email` - Get service account email
- `initialize()` - Initialize Firebase Admin SDK
- `get_access_token()` - Retrieve current access token
- `show_info()` - Display service account information
- `send_notification()` - Send FCM notification
- `send_data_message()` - Send data-only message

### `CLIHandler`

Handles command-line interface:

- `create_parser()` - Configure argument parser
- `handle_info()` - Process `--info` command
- `handle_data_only()` - Process `--data-only` command
- `handle_notification()` - Process notification command
- `run()` - Main CLI execution logic

## Unit testing

The project includes a comprehensive test suite with **58 unit tests** achieving **97% code coverage** on the main script.

### Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage terminal report
pytest --cov=. --cov-report=term-missing

# Alternatively, run tests with coverage (HTML report)
pytest --cov=. --cov-report=html
```

For detailed testing documentation, including test breakdown, fixtures, and mocking strategy, see:

📄 **[tests/README.md](./tests/README.md)**

## Code Linting

This project uses [Pylint](https://pylint.readthedocs.io/) for static code analysis. The configuration is defined in `.pylintrc`.

### Running Pylint

```bash
# Activate virtual environment
source venv/bin/activate

# Lint main script only
pylint fcm_send.py

# Lint main script and tests
pylint fcm_send.py tests/

# Lint tests only
pylint tests/
```

### Configuration

The `.pylintrc` file includes project-specific settings:

- **Max line length:** 120 characters
- **Extended test names:** Supports long descriptive test method names
- **Disabled rules:** Common pytest patterns (unused fixtures, redefined outer names) and CLI patterns (broad exception catching)

To check your current score:

```bash
# Output: Your code has been rated at X.XX/10
pylint fcm_send.py tests/
```

## References

- [FCM: Retrieve the current registration token](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android#retrieve-the-current-registration-token)
- [Firebase Admin SDK: Initialize in non-Google environments](https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments)
