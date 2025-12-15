# FCM Notification Sender - Test Suite

Unit tests for the FCM Notification Sender script using pytest with mocked Firebase Admin SDK.

## Directory Structure

```
tests/
├── README.md              # This file
├── __init__.py            # Package marker
├── conftest.py            # Shared fixtures and pytest configuration
├── test_fcm_client.py     # Tests for FCMClient class
└── test_cli_handler.py    # Tests for CLIHandler class
```

## Test Coverage Summary

| File | Tests | Description |
|------|-------|-------------|
| `test_fcm_client.py` | 27 | Tests for the `FCMClient` class |
| `test_cli_handler.py` | 31 | Tests for the `CLIHandler` class |
| **Total** | **58** | |

### Code Coverage

| Module | Coverage |
|--------|----------|
| `src/fcm_send/` | 97% |
| `test_fcm_client.py` | 100% |
| `test_cli_handler.py` | 100% |

## Tests Breakdown

### `test_fcm_client.py` (27 tests)

#### `TestFCMClientCredentials` (5 tests)
- `test_credentials_path_from_cli_argument` - CLI argument takes precedence
- `test_credentials_path_from_environment` - Environment variable fallback
- `test_credentials_path_cli_takes_precedence` - Priority verification
- `test_credentials_path_missing_raises_error` - Error when no credentials
- `test_credentials_path_file_not_found` - Error for non-existent file

#### `TestFCMClientCredentialsInfo` (6 tests)
- `test_credentials_info_loads_json` - JSON file loading
- `test_credentials_info_cached` - Caching behavior
- `test_project_id` - Project ID extraction
- `test_service_account_email` - Service account email extraction
- `test_project_id_returns_empty_when_credentials_info_none` - Empty string fallback
- `test_service_account_email_returns_empty_when_credentials_info_none` - Empty string fallback

#### `TestFCMClientInitialize` (2 tests)
- `test_initialize_sets_env_var_when_cli_arg_provided` - Environment variable setup
- `test_initialize_only_once` - Single initialization guarantee

#### `TestFCMClientAccessToken` (2 tests)
- `test_get_access_token` - Firebase Admin SDK token retrieval
- `test_get_access_token_http_api` - OAuth2 HTTP API token retrieval

#### `TestFCMClientSendNotification` (4 tests)
- `test_send_notification_success` - Successful notification
- `test_send_notification_with_data` - Notification with custom data
- `test_send_notification_with_image` - Notification with image URL
- `test_send_notification_dry_run` - Dry run mode

#### `TestFCMClientSendDataMessage` (3 tests)
- `test_send_data_message_success` - Successful data-only message
- `test_send_data_message_converts_values_to_strings` - Value type conversion
- `test_send_data_message_dry_run` - Dry run mode

#### `TestFCMClientShowInfo` (3 tests)
- `test_show_info_firebase_admin_token` - Display Firebase Admin SDK token
- `test_show_info_http_api_token` - Display HTTP API OAuth2 token
- `test_show_info_handles_token_retrieval_error` - Error handling for token retrieval

#### `TestAccessTokenType` (2 tests)
- `test_firebase_admin_type` - Enum value verification
- `test_fcm_http_api_type` - Enum value verification

### `test_cli_handler.py` (31 tests)

#### `TestCLIHandlerParser` (8 tests)
- `test_parser_has_credentials_key_file_arg`
- `test_parser_has_info_arg`
- `test_parser_has_token_arg`
- `test_parser_has_title_and_body_args`
- `test_parser_has_data_arg`
- `test_parser_has_data_only_arg`
- `test_parser_has_dry_run_arg`
- `test_parser_has_image_arg`

#### `TestCLIHandlerRun` (6 tests)
- `test_run_shows_help_when_no_args`
- `test_run_calls_handle_info_for_info_flag`
- `test_run_calls_handle_info_for_access_token_flag`
- `test_run_calls_handle_info_http_for_info_http_flag`
- `test_run_calls_handle_notification`
- `test_run_calls_handle_data_only`

#### `TestCLIHandlerHandleInfo` (3 tests)
- `test_handle_info_calls_client_show_info`
- `test_handle_info_with_http_token_type`
- `test_handle_info_exits_on_error`

#### `TestCLIHandlerHandleNotification` (4 tests)
- `test_handle_notification_success`
- `test_handle_notification_with_data`
- `test_handle_notification_invalid_json_exits`
- `test_handle_notification_dry_run`

#### `TestCLIHandlerHandleDataOnly` (4 tests)
- `test_handle_data_only_success`
- `test_handle_data_only_invalid_json_exits`
- `test_handle_data_only_dry_run`
- `test_handle_data_only_send_error_exits`

#### `TestCLIHandlerNotificationErrors` (3 tests)
- `test_handle_notification_unregistered_error` - UnregisteredError handling
- `test_handle_notification_sender_id_mismatch_error` - SenderIdMismatchError handling
- `test_handle_notification_generic_error` - Generic exception handling

#### `TestCLIHandlerParserErrors` (2 tests)
- `test_run_requires_token_for_data_only` - Token required validation
- `test_run_requires_title_and_body_for_notification` - Title/body required validation

#### `TestMainFunction` (1 test)
- `test_main_creates_cli_handler_and_runs` - Main entry point test

## Running the Tests

### Prerequisites

1. Activate the virtual environment:

```bash
cd scripts/firebase-notifications
source venv/bin/activate
```

2. Ensure test dependencies are installed:

```bash
pip install -r requirements.txt
```

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
# Terminal report
pytest --cov=. --cov-report=term-missing

# HTML report (generates htmlcov/ directory)
pytest --cov=. --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_fcm_client.py
pytest tests/test_cli_handler.py
```

### Run Specific Test Class

```bash
pytest tests/test_fcm_client.py::TestFCMClientCredentials
pytest tests/test_cli_handler.py::TestCLIHandlerParser
```

### Run Specific Test

```bash
pytest tests/test_fcm_client.py::TestFCMClientCredentials::test_credentials_path_from_cli_argument
```

### Run Tests Matching Pattern

```bash
# Run all tests with "notification" in the name
pytest -k "notification"

# Run all tests with "dry_run" in the name
pytest -k "dry_run"
```

## Fixtures

The test suite uses the following shared fixtures defined in `conftest.py`:

| Fixture | Description |
|---------|-------------|
| `mock_service_account_data` | Sample service account JSON data |
| `temp_credentials_file` | Temporary credentials file for testing |
| `mock_firebase_admin` | Mocked `firebase_admin` module |
| `mock_messaging` | Mocked `firebase_admin.messaging` module |
| `mock_credentials` | Mocked `firebase_admin.credentials` module |
| `clean_environment` | Ensures clean environment variables |

## Mocking Strategy

The tests mock the Firebase Admin SDK at the module level to avoid:

1. **Network calls** - No actual FCM API requests are made
2. **Authentication** - No real service account credentials needed
3. **External dependencies** - Tests run in isolation

### Example Mock Usage

```python
def test_send_notification_success(
    self, temp_credentials_file, mock_firebase_admin, mock_messaging, clean_environment
):
    """Test sending a notification successfully."""
    with patch('fcm_send.firebase_admin', mock_firebase_admin):
        with patch('fcm_send.messaging', mock_messaging):
            client = FCMClient(credentials_key_file=temp_credentials_file)
            
            response = client.send_notification(
                fcm_token="test_fcm_token",
                title="Test Title",
                body="Test Body"
            )
            
            assert response == "projects/test-project/messages/mock_message_id_123"
```

## Adding New Tests

1. Create test methods following the naming convention `test_<description>`
2. Group related tests in classes prefixed with `Test`
3. Use existing fixtures from `conftest.py` or create new ones as needed
4. Mock external dependencies (Firebase Admin SDK) appropriately

## GitHub Actions Workflow

The project includes a GitHub Actions workflow (`.github/workflows/tests.yml`) that automatically runs tests on:

- Push to `main` or `master` branches
- Pull requests targeting `main` or `master`
- Manual trigger via workflow dispatch

### Workflow Jobs

| Job | Description |
|-----|-------------|
| `test` | Runs pytest with coverage across Python 3.9-3.13 |
| `lint` | Runs pylint with minimum score threshold of 8.0 |

### Running the Workflow Locally

You can run the GitHub Actions workflow locally using [act](https://github.com/nektos/act), a tool that runs your workflows in Docker containers.

#### Prerequisites

1. **Install Docker** - Required for running containers
   - macOS: `brew install --cask docker`
   - Linux: Follow [Docker installation guide](https://docs.docker.com/engine/install/)

2. **Install act**
   ```bash
   # macOS
   brew install act

   # Linux (via curl)
   curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

#### Running Workflows Locally

```bash
# Navigate to project root
cd /path/to/firebase-cloud-message

# Run the entire workflow (all jobs)
act

# Run only the test job
act -j test

# Run only the lint job
act -j lint

# Run with a specific Python version (uses medium Ubuntu image)
act -P ubuntu-latest=catthehacker/ubuntu:act-latest

# Dry run (list actions without executing)
act -n

# Run workflow on push event (default)
act push

# Run workflow on pull_request event
act pull_request

# Run with verbose output for debugging
act -v
```

#### First Run Notes

On the first run, `act` will prompt you to select a Docker image size:

- **Micro** (~200MB) - Minimal, may lack some tools
- **Medium** (~500MB) - Recommended for most workflows
- **Large** (~17GB) - Full GitHub Actions environment

For this project, the **Medium** image is recommended.

#### Troubleshooting act

| Issue | Solution |
|-------|----------|
| Docker not running | Start Docker Desktop or the Docker daemon |
| Permission denied | Run with `sudo` or add user to docker group |
| Image pull fails | Check internet connection and Docker Hub access |
| Python version not available | Use `-P ubuntu-latest=catthehacker/ubuntu:act-latest` |

#### Example: Running Tests Locally

```bash
# Quick test run (single Python version)
act -j test --matrix python-version:3.12

# Full matrix test (all Python versions)
act -j test
```

