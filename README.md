# Firebase Cloud Messaging (FCM) Notification Sender

![fcm-icon](./images/firebase-fcm-icon.png)

A Python CLI tool for sending [Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android) notifications using the **[Firebase Admin SDK](https://firebase.google.com/docs/admin/setup#add-sdk).**

[![PyPI version](https://badge.fury.io/py/fcm-send.svg)](https://badge.fury.io/py/fcm-send)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

### Using Poetry (Recommended)

This project uses [Poetry](https://python-poetry.org/) for dependency management and packaging.

**Add to your project:**

```bash
poetry add fcm-send
```

**Install globally:**

```bash
pipx install fcm-send
```

### Using pip

```bash
pip install fcm-send
```

### Using pipx (Isolated CLI)

[pipx](https://pipx.pypa.io/) installs the CLI in an isolated environment, avoiding dependency conflicts:

```bash
# Install pipx if you don't have it
pip install pipx
# macOS: Using brew
brew install pipx
pipx ensurepath

# Install fcm-send
pipx install fcm-send
```

### From Source (Development)

```bash
git clone https://github.com/mfdeveloper/firebase_cloud_messaging_cli.git
cd firebase_cloud_messaging_cli

# Install with Poetry (recommended)
poetry install

# Run the CLI
poetry run fcm-send --version
```

## Features

- **Send push notifications** with title, body, and optional custom data
- **Send data-only messages** (silent notifications for background processing)
- **Display service account info** and retrieve the access token
- **Dry-run mode** to validate messages without sending
- **Image support** for rich notifications

## Prerequisites

### 1. Install [Poetry](https://python-poetry.org/docs/#installation)

If you don't have Poetry installed:

```bash
# macOS / Linux
curl -sSL https://install.python-poetry.org | python3 -

# Alternatively, create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# And using pipx
pipx install poetry
```

> **Note:** After installation, ensure Poetry is in your PATH. See [Poetry Installation](https://python-poetry.org/docs/#installation).

### 2. Set Up the Project

```bash
cd <project-root>

# Install dependencies (creates .venv automatically)
poetry install

# Activate the virtual environment
poetry shell
```

> **Note:** Poetry automatically creates a `.venv` folder in your project (configured in `poetry.toml`).

### 3. Firebase Service Account

To authenticate a service account and authorize it to access Firebase services, you must generate a
`service-account.json` private key file in **JSON** format.

**To generate and obtain one: a private key file for your service account:**

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Select your project
3. Open **Project Settings** > [Service Accounts](https://console.firebase.google.com/project/_/settings/serviceaccounts/adminsdk).
4. Click **Generate New Private Key**, then confirm by clicking **Generate Key**.
5. Securely store the `.json` file containing the key.

> For more details, see the Firebase documentation page: [Initialize the SDK in non-Google environments](https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments)

### Environment Setup

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

### Running with Poetry

Before running commands, ensure you're in the Poetry environment:

```bash
cd <project-root>

# Option 1: Activate shell
poetry shell
fcm-send --info

# Option 2: Run directly with "poetry run"
poetry run fcm-send --info
```

> **Note:** Using a code editor (such as [VSCode](https://code.visualstudio.com) or [Cursor](https://cursor.com)) a Python Virtual Environment can be loaded automatically using [.vscode/settings.json](./.vscode/settings.json) configurations.
> Open this folder as `${workspaceFolder}` and `settings.json` file mentioned above would be loaded!

---

### Pass Google Credentials `.json` file

```bash
# Using CLI argument (takes precedence)
fcm-send --credentials-key-file ~/my-service-account.json --info

# Using environment variable
export GOOGLE_APPLICATION_CREDENTIALS=~/my-service-account.json
fcm-send --info

# Combining with other commands
fcm-send --credentials-key-file ~/sa.json --token FCM_TOKEN --title "Hi" --body "Test"
```

### Show Service Account Info & Access Token

Display project details and retrieve the current **Firebase Admin SDK** access token:

```bash
fcm-send --info
# Or use --access-token alias
fcm-send --access-token
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
fcm-send --info-http
# Or use --access-token-http alias
fcm-send --access-token-http
```

### Send a Simple Notification

```bash
fcm-send --token YOUR_FCM_TOKEN --title "Hello" --body "World"
```

### Send Notification with Custom Data Payload

```bash
fcm-send --token YOUR_FCM_TOKEN \
  --title "Order Update" \
  --body "Your order has been shipped!" \
  --data '{"order_id": "12345", "action": "open_order"}'
```

### Send Notification with Image

```bash
fcm-send --token YOUR_FCM_TOKEN \
  --title "Check this out" \
  --body "New feature available!" \
  --image "https://example.com/image.png"
```

### Send Data-Only Message (Silent/Background)

Data-only messages don't show a visible notification but are delivered to your app for background processing:

```bash
fcm-send --token YOUR_FCM_TOKEN \
  --data-only '{"action": "sync", "resource_id": "123"}'
```

### Validate Message Without Sending (Dry Run)

Test your message configuration without actually sending it:

```bash
fcm-send --token YOUR_FCM_TOKEN \
  --title "Test" \
  --body "This is a test" \
  --dry-run
```

### Using as a Python Library

You can also use `fcm-send` as a library in your **Python** code:

```python
from fcm_send import FCMClient

# Initialize client with credentials file
client = FCMClient("/path/to/service-account.json")

# Send a notification
response = client.send_notification(
    fcm_token="device_fcm_token",
    title="Hello",
    body="World",
    data={"key": "value"}  # optional
)
print(f"Message ID: {response}")

# Send a data-only message
response = client.send_data_message(
    fcm_token="device_fcm_token",
    data={"action": "sync", "id": "123"}
)
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

## Development

### Package Structure

```
firebase-cloud-messaging/
├── src/
│   └── fcm_send/
│       ├── __init__.py      # Package exports (FCMClient, main, etc.)
│       ├── __main__.py      # Enables `python -m fcm_send`
│       ├── __version__.py   # Version from pyproject.toml ✨
│       ├── client.py        # FCMClient class
│       ├── cli.py           # CLIHandler and main() entry point
│       └── py.typed         # PEP 561 marker for type checking
├── tests/                   # Test suite (58 tests)
├── pyproject.toml           # Poetry configuration
├── poetry.toml              # Poetry settings (in-project venv)
├── poetry.lock              # Locked dependencies
├── LICENSE                  # MIT License
└── README.md                # This file
```

### Installation for Development

#### Using Poetry (Recommended)

```bash
git clone https://github.com/mfdeveloper/firebase_cloud_messaging_cli.git
cd firebase_cloud_messaging_cli

# Install all dependencies (creates .venv automatically)
poetry install

# Activate the virtual environment
poetry shell

# Or run commands directly
poetry run fcm-send --version
poetry run pytest
```

#### Using pip (Alternative)

```bash
git clone https://github.com/mfdeveloper/firebase_cloud_messaging_cli.git
cd firebase_cloud_messaging_cli

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install from requirements.txt
pip install -r requirements.txt

# Or install the package in editable mode
pip install -e .
```

### Unit Testing

The project includes a comprehensive test suite with **58 unit tests** achieving **97% code coverage**.

```bash
# Run all tests
poetry run pytest

# Run with coverage terminal report
poetry run pytest --cov=src/fcm_send --cov-report=term-missing

# Run tests with coverage (HTML report)
poetry run pytest --cov=src/fcm_send --cov-report=html
```

For detailed testing documentation, including test breakdown, fixtures, and mocking strategy, see:

📄 **[tests/README.md](./tests/README.md)**

## Code Linting

This project uses [Pylint](https://pylint.readthedocs.io/) for static code analysis. The configuration is defined in `.pylintrc`.

### Running Pylint

```bash
# Lint source package only
poetry run pylint src/fcm_send/

# Lint source package and tests
poetry run pylint src/fcm_send/ tests/

# Lint tests only
poetry run pylint tests/
```

### Configuration

The `.pylintrc` file includes project-specific settings:

- **Max line length:** 120 characters
- **Extended test names:** Supports long descriptive test method names
- **Disabled rules:** Common pytest patterns (unused fixtures, redefined outer names) and CLI patterns (broad exception catching)

To check your current score:

```bash
# Output: Your code has been rated at X.XX/10
poetry run pylint src/fcm_send/ tests/
```

## Publishing to PyPI

This project uses **Poetry** for building and publishing packages.

### 1. Update Version

Update the version in `pyproject.toml`:

```toml
[tool.poetry]
version = "0.2.0"
```

Or use Poetry's version command:

```bash
# Bump patch version (0.1.0 → 0.1.1)
poetry version patch

# Bump minor version (0.1.0 → 0.2.0)
poetry version minor

# Bump major version (0.1.0 → 1.0.0)
poetry version major
```

### 2. Build the Package

```bash
# Build both sdist and wheel
poetry build
```

This creates distribution files in the `dist/` directory:
- `dist/fcm_send-0.1.0.tar.gz` (source distribution)
- `dist/fcm_send-0.1.0-py3-none-any.whl` (wheel)

### 3. Upload to Test PyPI (Recommended First)

Test your package on [Test PyPI](https://test.pypi.org) before publishing to the real PyPI.

#### Option A: Using GitHub Actions (Recommended)

This project includes a GitHub Actions workflow for automated publishing to TestPyPI.

**Triggers:**
- **Manual**: Go to Actions → **"Publish to TestPyPI"** → **"Run workflow"**
- **Automatic**: Push a version tag (e.g., `git tag v0.1.0 && git push --tags`)

**One-time Setup:**
1. Create a [TestPyPI account](https://test.pypi.org/account/register/)
2. Generate an API token at [TestPyPI API Tokens](https://test.pypi.org/manage/account/#api-tokens)
3. Add the token as a GitHub secret:
   - Go to your repository **Settings** → **Secrets and variables** → **Actions**
   - Create a new secret named `TEST_PYPI_API_TOKEN` with your token

#### Option B: Manual Upload with Poetry

```bash
# Configure TestPyPI repository
poetry config repositories.testpypi https://test.pypi.org/legacy/

# Set your TestPyPI token
poetry config pypi-token.testpypi pypi-XXXXXXXXXXXX

# Publish to TestPyPI
poetry publish --repository testpypi

# Alternatively, you can use regular "Twine" for publishing
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  fcm-send
```

> **Note**: The `--extra-index-url` is needed because TestPyPI doesn't have all dependencies (like [`firebase-admin`](https://firebase.google.com/docs/admin/setup#add-sdk)), so it falls back to the real PyPI for those.

### 4. Upload to PyPI

Once verified on TestPyPI, publish to the official PyPI.

#### Option A: Using GitHub Actions (Recommended)

This project includes a GitHub Actions workflow for automated publishing to PyPI.

**Trigger:**
- Push a `pypi-*` tag:
  ```bash
  git tag -a pypi-0.1.0 -m "Release version 0.1.0"
  git push origin pypi-0.1.0
  ```

**One-time Setup:**
1. Create a [PyPI account](https://pypi.org/account/register/)
2. Generate an API token at [PyPI API Tokens](https://pypi.org/manage/account/#api-tokens)
3. Add the token as a GitHub secret:
   - Go to your repository **Settings** → **Secrets and variables** → **Actions**
   - Create a new secret named `PYPI_API_TOKEN` with your token

#### Option B: Manual Upload with Poetry

```bash
# Set your PyPI token
poetry config pypi-token.pypi pypi-XXXXXXXXXXXX

# Publish to PyPI
poetry publish

# Alternatively, you can use regular "Twine" for publishing
twine upload dist/*
```

### 5. After Publishing

Users can install your package with:

```bash
poetry add fcm-send
# or
pip install fcm-send
```

## Poetry Commands Reference

| Command                     | Description                                    |
|-----------------------------|------------------------------------------------|
| `poetry install`            | Install all dependencies                       |
| `poetry install --extras dev` | Install with dev dependencies                |
| `poetry shell`              | Activate the virtual environment               |
| `poetry run <cmd>`          | Run a command in the virtual environment       |
| `poetry add <pkg>`          | Add a dependency                               |
| `poetry add --group dev <pkg>` | Add a dev dependency                        |
| `poetry remove <pkg>`       | Remove a dependency                            |
| `poetry update`             | Update dependencies to latest versions         |
| `poetry lock`               | Update poetry.lock without installing          |
| `poetry build`              | Build sdist and wheel                          |
| `poetry publish`            | Publish to PyPI                                |
| `poetry version <rule>`     | Bump version (patch, minor, major)             |
| `poetry show`               | Show installed packages                        |
| `poetry env info`           | Show virtualenv info                           |

## References

- [Poetry Documentation](https://python-poetry.org/docs/)
- [FCM: Retrieve the current registration token](https://firebase.google.com/docs/cloud-messaging/get-started?platform=android#retrieve-the-current-registration-token)
- [Firebase Admin SDK: Initialize in non-Google environments](https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments)
