# Firebase Cloud Messaging CLI Tool

![fcm-project-icon](./images/firebase-fcm-icon.png)

A `shell-script`/`bash` command-line utility for sending push notifications via [Firebase Cloud Messaging (FCM)](https://firebase.google.com/docs/cloud-messaging/send/v1-api) **HTTP v1 API**.

## Features

- 🔐 **OAuth 2.0 Authentication** - Authenticate using Google Cloud service accounts
- 💾 **Token Caching** - Access tokens are cached locally to avoid regeneration on each call
- 📱 **Send Push Notifications** - Send data messages to specific device tokens
- 📦 **Custom JSON Payloads** - Send custom JSON payloads inline or from files
- ⚡ **Simple CLI Interface** - Easy-to-use command structure with helpful documentation

## Prerequisites

- [Google Cloud SDK (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and configured
- A Firebase project with Cloud Messaging enabled
- Service account JSON key file with FCM permissions
- Python 3 (for auto-extracting `client_email` from JSON key file and response formatting)

## Installation

1. Clone this repository:

   ```bash
   git clone <repository-url>
   cd firebase-cloud-message
   ```

2. Make the script executable:

   ```bash
   chmod +x scripts/fcm.sh
   ```

3. (Optional) Add to your PATH or create an alias:

   ```bash
   # Add to ~/.bashrc or ~/.zshrc
   alias fcm="/path/to/scripts/fcm.sh"
   ```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to your Firebase service account JSON key | Recommended |
| `FCM_TOKEN_CACHE_FILE` | Custom path for token cache file (default: `~/.fcm_access_token_cache`) | Optional |
| `FCM_TOKEN_TTL` | Token TTL in seconds (default: 3300 = 55 minutes) | Optional |

### Service Account Setup

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Navigate to **Project Settings** → **Service Accounts**
3. Click **Generate new private key**
4. Save the `.json` file securely
5. Set the environment variable:

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-firebase-key.json"
   ```

## Usage

### Commands

```bash
./scripts/fcm.sh <command> [options]
```

| Command | Description |
|---------|-------------|
| `auth` | Generate and cache an OAuth 2.0 access token |
| `access-token` | Alias for `auth` |
| `send` | Send a push notification to a device |
| `token` | Display the current cached access token (if valid) |
| `check-python` | Check if Python 3 is installed |
| `test` | Run unit tests |
| `help` | Show help message |

### Options

| Flag | Description |
|------|-------------|
| `-e EMAIL` | Service account email (optional - auto-extracted from JSON if not provided) |
| `-f FILE` | Path to the Firebase private key JSON file |
| `-t TOKEN` | FCM device token (required for `send` command) |
| `-p PROJECT` | Firebase Project ID (required for `send` command) |
| `-d DATA` | Custom JSON for the `data` field (inline string or `@file.json` path) |
| `-T TITLE` | Message title (default: "CLI Test Message") - ignored if `-d` is used |
| `-B BODY` | Message body - ignored if `-d` is used |
| `-r` | Force refresh the access token (ignore cache) |
| `-h` | Show help message |

### Examples

#### 1. Authenticate and Cache Access Token

```bash
# Auto-extract email from GOOGLE_APPLICATION_CREDENTIALS
./scripts/fcm.sh auth

# Or specify the credentials file explicitly (email auto-extracted)
./scripts/fcm.sh auth -f /path/to/firebase-private-key.json

# Or provide email manually (overrides auto-extraction)
./scripts/fcm.sh auth -e your-service@project.iam.gserviceaccount.com
```

#### 2. Send a Notification

```bash
# Basic send (uses cached token)
./scripts/fcm.sh send \
  -t "device_fcm_token_here" \
  -p "your-firebase-project-id"

# Send with custom message
./scripts/fcm.sh send \
  -t "device_fcm_token_here" \
  -p "your-firebase-project-id" \
  -T "Hello World" \
  -B "This is a test notification"
```

#### 3. Send with Custom Data Payload (`-d` flag)

```bash
# Inline JSON data payload
./scripts/fcm.sh send \
  -t "device_fcm_token_here" \
  -p "your-firebase-project-id" \
  -d '{"action": "open_article", "article_id": "12345", "category": "news"}'

# From a JSON file
./scripts/fcm.sh send \
  -t "device_fcm_token_here" \
  -p "your-firebase-project-id" \
  -d @payloads/custom-data.json
```

#### 4. Force Token Refresh (`-r` flag)

```bash
# Refresh token before sending
./scripts/fcm.sh send \
  -t "device_fcm_token_here" \
  -p "your-firebase-project-id" \
  -r
```

#### 5. View Cached Token

```bash
./scripts/fcm.sh token
```

## Token Caching

Access tokens are automatically cached to improve performance:

- **Default location**: `~/.fcm_access_token_cache`
- **Default TTL**: 55 minutes (Google OAuth tokens last 60 minutes)
- **Cache format**: First line is timestamp, second line is the token
- **Security**: Cache file is created with `600` permissions (owner read/write only)

The script automatically:

- Checks if a valid cached token exists before making API calls
- Generates a new token if the cache is expired or missing
- Refreshes the token when using the `-r` flag

## Message Payload Structure

### Default Payload

When using `-t`, `-T`, and `-B` flags, the script sends data messages with the following structure:

```json
{
  "message": {
    "token": "<fcm_device_token>",
    "data": {
      "push_from": "fcm",
      "title": "<message_title>",
      "body": "<message_body>",
      "custom_action": "update_service"
    }
  }
}
```

> **Note**: Data messages are handled by your app's message handler, not displayed automatically by the system.

### Custom Data Payload (`-d` flag)

Use the `-d` flag to provide a custom JSON object for the `data` field. The `-t` flag is still required.

1. **Inline JSON string:**

   ```bash
   ./scripts/fcm.sh send -t <token> -p my-project -d '{"key": "value", "action": "..."}'
   ```

2. **File reference (prefix with `@`):**

   ```bash
   ./scripts/fcm.sh send -t <token> -p my-project -d @path/to/data.json
   ```

#### Example: Custom Action Data

```json
{
  "action": "open_article",
  "article_id": "12345",
  "category": "technology",
  "priority": "high"
}
```

#### Example: Deep Link Data

```json
{
  "action": "deep_link",
  "url": "myapp://products/12345",
  "fallback_url": "https://example.com/products/12345"
}
```

#### Example: Sync Trigger

```json
{
  "action": "sync_data",
  "sync_type": "full",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

The script wraps your data payload in the FCM message structure:

```json
{
  "message": {
    "token": "<fcm_device_token>",
    "data": { /* your custom data here */ }
  }
}
```

> See [FCM HTTP v1 API Reference](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages) for all available options.

## Troubleshooting

### Common Issues

1. **"Service account email is required"**
   - Provide the `-e` flag with the email from your JSON key's `client_email` field

2. **"Firebase private key file not found"**
   - Set `GOOGLE_APPLICATION_CREDENTIALS` or use the `-f` flag

3. **"Python 3 is required but not found"**
   - Install Python 3 (`brew install python3` on macOS, `apt install python3` on Ubuntu)
   - Or provide the `-e` flag manually to skip auto-extraction

4. **"No valid cached token found"**
   - Run the `auth` command first to generate a token

5. **HTTP 401 Unauthorized**
   - Your token may have expired; use `-r` to force refresh
   - Verify your service account has FCM permissions

6. **HTTP 404 Not Found**
   - Check that your Project ID (`-p`) is correct

### Debug Tips

```bash
# Check if gcloud is authenticated
gcloud auth list

# Verify your credentials file
cat $GOOGLE_APPLICATION_CREDENTIALS | python3 -m json.tool

# Check cached token age
ls -la ~/.fcm_access_token_cache
```

## Testing

Unit tests are available for all core functions:

```bash
# Run all tests (using the test command)
./scripts/fcm.sh test

# Or run the test script directly
./scripts/tests/test_fcm.sh

# Run tests with code coverage (requires kcov)
./scripts/tests/test_fcm.sh --coverage
```

### Code Coverage

The test suite supports code coverage analysis using bash trace analysis:

```bash
# Run tests with coverage (terminal output - default)
./scripts/fcm.sh test --coverage

# Run tests with coverage (HTML report)
./scripts/fcm.sh test --coverage --output html

# Or run directly
./scripts/tests/test_fcm.sh --coverage
./scripts/tests/test_fcm.sh --coverage --output html
```

**Output formats:**

| Format | Description |
|--------|-------------|
| `terminal` (default) | Shows coverage percentage and generates text report |
| `html` | Generates beautiful HTML report with line-by-line coverage highlighting |

**Generated files:**

- `scripts/tests/coverage/coverage_report.txt` - Text coverage report
- `scripts/tests/coverage/index.html` - HTML summary page (with `--output html`)
- `scripts/tests/coverage/fcm.sh.html` - Line-by-line source coverage (with `--output html`)
- `scripts/tests/coverage/trace.log` - Raw trace log

**Example output:**

```bash
Running tests with code coverage...

Running coverage tests with tracing...

Coverage analysis complete!

  fcm.sh Coverage: 70% (191 lines executed)

  Coverage report: scripts/tests/coverage/coverage_report.txt
  HTML report: scripts/tests/coverage/index.html
  Trace log: scripts/tests/coverage/trace.log
```

> **Note**: Coverage uses bash's `set -x` tracing to track executed lines. Some code paths that require external services (gcloud, network) or specific system states (Python not installed) may not be fully covered in tests.

### Test Coverage

The test suite covers:

- **Logging functions** - `log_info`, `log_error`, `log_success`
- **Python detection** - `get_python_cmd`
- **Token caching** - `save_token_to_cache`, `get_cached_token`, `is_token_valid`
- **Argument parsing** - All command-line flags (`-e`, `-f`, `-t`, `-p`, `-d`, `-T`, `-B`, `-r`)
- **JSON payloads** - `build_default_data`, `build_message_payload`, `resolve_data_payload`, `validate_json`
- **Client email extraction** - `extract_client_email`
- **Usage output** - `print_usage`

### Example Output

```bash
=============================================================================
  FCM CLI Unit Tests
=============================================================================

▶ Running: log_info outputs correct format
  ✓ PASSED

▶ Running: parse_arguments sets command
  ✓ PASSED

...

=============================================================================

  All tests passed!

  Total:  38
  Passed: 38
  Failed: 0

=============================================================================
```

## CI/CD

### GitHub Actions

Unit tests run automatically on:
- Push to `shell-script-cli` branch
- Pull requests targeting `shell-script-cli` branch

The workflow is defined in `.github/workflows/test.yml`.

### Running Workflows Locally

You can test GitHub Actions workflows locally using [act](https://github.com/nektos/act) before pushing to the repository.

#### Prerequisites

1. **Install Docker** - `act` uses Docker to run workflows
   
   ```bash
   # macOS
   brew install --cask docker
   
   # Ubuntu/Debian
   sudo apt install docker.io
   ```

2. **Install act**

   ```bash
   # macOS
   brew install act
   
   # Linux (via curl)
   curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash
   ```

#### Running Workflows

```bash
# List available workflows and jobs
act -l

# Run the default push event (simulates push to branch)
act push

# Run a specific job
act -j test

# Dry-run mode (shows what would happen without executing)
act -n push

# Run with verbose output
act -v push

# Use a specific GitHub event (e.g., pull_request)
act pull_request
```

#### Example Output

```bash
$ act push
[Unit Tests/Run Unit Tests] 🚀  Start image=catthehacker/ubuntu:act-latest
[Unit Tests/Run Unit Tests]   🐳  docker pull catthehacker/ubuntu:act-latest
[Unit Tests/Run Unit Tests] ⭐  Run actions/checkout@v4
[Unit Tests/Run Unit Tests]   ✅  Success - actions/checkout@v4
[Unit Tests/Run Unit Tests] ⭐  Run Make scripts executable
[Unit Tests/Run Unit Tests]   ✅  Success - Make scripts executable
[Unit Tests/Run Unit Tests] ⭐  Run unit tests
[Unit Tests/Run Unit Tests]   ✅  Success - Run unit tests
[Unit Tests/Run Unit Tests] ⭐  Run coverage report
[Unit Tests/Run Unit Tests]   ✅  Success - Run coverage report
```

#### Troubleshooting

| Issue | Solution |
|-------|----------|
| Docker not running | Start Docker Desktop or run `sudo systemctl start docker` |
| Permission denied | Run `sudo act push` or add your user to the docker group |
| Slow first run | First run downloads Docker images (~1GB); subsequent runs are faster |
| Missing secrets | Use `act -s SECRET_NAME=value` for workflows that need secrets |

> **Tip**: Create an `.actrc` file in your project root to set default options:
> ```
> -P ubuntu-latest=catthehacker/ubuntu:act-latest
> ```

## Project Structure

```bash
firebase-cloud-message/
├── README.md
├── .github/
│   └── workflows/
│       └── test.yml            # GitHub Actions workflow
├── scripts/
│   ├── fcm.sh                  # Main CLI script
│   └── tests/
│       ├── test_lib.sh         # Test framework library
│       └── test_fcm.sh         # Unit tests
└── .gitignore
```

## License

MIT License - feel free to use and modify as needed.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## References

- [FCM HTTP v1 API Reference](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages)
- [Firebase Admin SDK: Initialize in non-Google environments](https://firebase.google.com/docs/admin/setup#initialize_the_sdk_in_non-google_environments)