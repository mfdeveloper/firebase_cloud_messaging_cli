#!/bin/bash

# =============================================================================
# Firebase Cloud Messaging (FCM) CLI Tool
# =============================================================================
# A unified script to authenticate with Google Cloud and send FCM messages
# via the HTTP v1 API.
#
# Features:
#   - OAuth 2.0 access token generation with caching
#   - Token preservation to avoid regeneration on each call
#   - Send data messages to specific device tokens
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------
TOKEN_CACHE_FILE="${FCM_TOKEN_CACHE_FILE:-$HOME/.fcm_access_token_cache}"
TOKEN_TTL_SECONDS="${FCM_TOKEN_TTL:-3300}"  # 55 minutes (tokens last 60 min)

# -----------------------------------------------------------------------------
# Global Variables (populated by argument parsing)
# -----------------------------------------------------------------------------
SERVICE_ACCOUNT_EMAIL=""
KEY_FILE_PATH=""
FCM_TOKEN=""
PROJECT_ID=""
ACCESS_TOKEN=""
COMMAND=""
FORCE_REFRESH=false
MESSAGE_TITLE="CLI Test Message"
MESSAGE_BODY="This is a custom data payload from the command line!"
CUSTOM_PAYLOAD=""

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

print_usage() {
    cat << EOF
Firebase Cloud Messaging (FCM) CLI Tool

USAGE:
    $(basename "$0") <command> [options]

COMMANDS:
    auth          Generate and cache an OAuth 2.0 access token
    access-token  Alias for 'auth'
    send          Send a push notification to a device
    token         Display the current cached access token (if valid)
    check-python  Check if Python 3 is installed and available
    test          Run unit tests

OPTIONS:
    -e EMAIL    Service account email (from your firebase-private-key.json)
    -f FILE     Path to the Firebase private key JSON file
                (defaults to \$GOOGLE_APPLICATION_CREDENTIALS)
    -t TOKEN    FCM device token (required for 'send' command)
    -p PROJECT  Firebase Project ID (required for 'send' command)
    -d DATA     Custom JSON for the "data" field. Can be:
                - Inline JSON string: '{"key": "value", ...}'
                - Path to JSON file: @/path/to/data.json
                Note: When using -d, the -T and -B flags are ignored
    -T TITLE    Message title (default: "CLI Test Message")
    -B BODY     Message body (default: "This is a custom data payload...")
    -r          Force refresh the access token (ignore cache)
    -h          Show this help message

ENVIRONMENT VARIABLES:
    GOOGLE_APPLICATION_CREDENTIALS  Path to Firebase private key JSON
    FCM_TOKEN_CACHE_FILE            Custom path for token cache file
    FCM_TOKEN_TTL                   Token TTL in seconds (default: 3300)

EXAMPLES:
    # Authenticate and cache access token
    $(basename "$0") auth -e your-service@project.iam.gserviceaccount.com

    # Send a notification
    $(basename "$0") send -t <device_token> -p <project_id>

    # Send with custom message
    $(basename "$0") send -t <device_token> -p <project_id> -T "Hello" -B "World"

    # Send with custom data payload (inline JSON)
    $(basename "$0") send -t <device_token> -p <project_id> -d '{"action": "open_url", "url": "https://..."}'

    # Send with custom data payload (from file)
    $(basename "$0") send -t <device_token> -p <project_id> -d @data.json

    # Force token refresh before sending
    $(basename "$0") send -t <device_token> -p <project_id> -r

EOF
}

log_info() {
    echo "[INFO] $1"
}

log_error() {
    echo "[ERROR] $1" >&2
}

log_success() {
    echo "[SUCCESS] $1"
}

# -----------------------------------------------------------------------------
# Argument Parsing
# -----------------------------------------------------------------------------

parse_arguments() {
    # First argument should be the command
    if [[ $# -lt 1 ]]; then
        print_usage
        exit 1
    fi

    COMMAND="$1"
    shift

    # Parse remaining flags
    while getopts "e:f:t:p:d:T:B:rh" flag; do
        case "${flag}" in
            e) SERVICE_ACCOUNT_EMAIL="${OPTARG}" ;;
            f) KEY_FILE_PATH="${OPTARG}" ;;
            t) FCM_TOKEN="${OPTARG}" ;;
            p) PROJECT_ID="${OPTARG}" ;;
            d) CUSTOM_PAYLOAD="${OPTARG}" ;;
            T) MESSAGE_TITLE="${OPTARG}" ;;
            B) MESSAGE_BODY="${OPTARG}" ;;
            r) FORCE_REFRESH=true ;;
            h) print_usage; exit 0 ;;
            *) print_usage; exit 1 ;;
        esac
    done

    # Set defaults from environment if not provided
    if [[ -z "$KEY_FILE_PATH" ]]; then
        KEY_FILE_PATH="$GOOGLE_APPLICATION_CREDENTIALS"
    fi
}

# -----------------------------------------------------------------------------
# Token Management Functions
# -----------------------------------------------------------------------------

is_token_valid() {
    # Check if cache file exists
    if [[ ! -f "$TOKEN_CACHE_FILE" ]]; then
        return 1
    fi

    # Read cached token and timestamp
    local cached_timestamp
    cached_timestamp=$(head -n 1 "$TOKEN_CACHE_FILE" 2>/dev/null)
    
    if [[ -z "$cached_timestamp" ]]; then
        return 1
    fi

    # Check if token has expired
    local current_time
    current_time=$(date +%s)
    local elapsed=$((current_time - cached_timestamp))

    if [[ $elapsed -ge $TOKEN_TTL_SECONDS ]]; then
        log_info "Cached token has expired (${elapsed}s old)"
        return 1
    fi

    log_info "Using cached token (${elapsed}s old, valid for $((TOKEN_TTL_SECONDS - elapsed))s more)"
    return 0
}

get_cached_token() {
    if [[ -f "$TOKEN_CACHE_FILE" ]]; then
        # Token is on the second line
        sed -n '2p' "$TOKEN_CACHE_FILE"
    fi
}

save_token_to_cache() {
    local token="$1"
    local timestamp
    timestamp=$(date +%s)
    
    # Save timestamp on first line, token on second line
    echo "$timestamp" > "$TOKEN_CACHE_FILE"
    echo "$token" >> "$TOKEN_CACHE_FILE"
    chmod 600 "$TOKEN_CACHE_FILE"
    
    log_info "Token cached at: $TOKEN_CACHE_FILE"
}

get_python_cmd() {
    # Check for python3 first (preferred), then fall back to python
    if command -v python3 &> /dev/null; then
        echo "python3"
    elif command -v python &> /dev/null; then
        # Verify it's Python 3.x
        if python -c "import sys; sys.exit(0 if sys.version_info[0] >= 3 else 1)" 2>/dev/null; then
            echo "python"
        else
            return 1
        fi
    else
        return 1
    fi
}

extract_client_email() {
    local json_file="$1"
    
    if [[ ! -f "$json_file" ]]; then
        return 1
    fi
    
    # Find available Python command
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -z "$python_cmd" ]]; then
        log_error "Python 3 is required but not found"
        log_error "Please install Python 3 or provide -e flag manually"
        return 1
    fi
    
    # Extract client_email using Python
    "$python_cmd" -c "
import json
import sys
try:
    with open('$json_file', 'r') as f:
        data = json.load(f)
        print(data.get('client_email', ''))
except:
    sys.exit(1)
" 2>/dev/null
}

generate_access_token() {
    # Validate key file first (needed for auto-extraction)
    if [[ ! -f "$KEY_FILE_PATH" ]]; then
        log_error "Firebase private key file not found: '$KEY_FILE_PATH'"
        log_error "Set GOOGLE_APPLICATION_CREDENTIALS or use -f flag"
        exit 1
    fi

    # Auto-extract client_email if not provided
    if [[ -z "$SERVICE_ACCOUNT_EMAIL" ]]; then
        log_info "Extracting client_email from credentials file..."
        SERVICE_ACCOUNT_EMAIL=$(extract_client_email "$KEY_FILE_PATH")
        
        if [[ -z "$SERVICE_ACCOUNT_EMAIL" ]]; then
            log_error "Could not extract client_email from: $KEY_FILE_PATH"
            log_error "Please provide it manually with the -e flag"
            exit 1
        fi
        
        log_info "Found client_email: $SERVICE_ACCOUNT_EMAIL"
    fi

    log_info "Using credentials file: $KEY_FILE_PATH"
    log_info "Authenticating service account: $SERVICE_ACCOUNT_EMAIL"

    # Authenticate the service account
    if ! gcloud auth activate-service-account "$SERVICE_ACCOUNT_EMAIL" \
        --key-file="$KEY_FILE_PATH" 2>/dev/null; then
        log_error "Failed to authenticate service account"
        exit 1
    fi

    # Generate the OAuth 2.0 access token
    local token
    token=$(gcloud auth print-access-token \
        --scopes="https://www.googleapis.com/auth/firebase.messaging" 2>/dev/null)

    if [[ -z "$token" ]]; then
        log_error "Failed to generate access token"
        exit 1
    fi

    # Cache the token
    save_token_to_cache "$token"
    
    ACCESS_TOKEN="$token"
    log_success "Access token generated successfully"
}

get_access_token() {
    # Check if we should use cached token
    if [[ "$FORCE_REFRESH" == false ]] && is_token_valid; then
        ACCESS_TOKEN=$(get_cached_token)
        if [[ -n "$ACCESS_TOKEN" ]]; then
            return 0
        fi
    fi

    # Generate new token
    generate_access_token
}

print_access_token() {
    if [[ -n "$ACCESS_TOKEN" ]]; then
        echo ""
        echo "═══════════════════════════════════════════════════════════════════"
        echo "ACCESS TOKEN:"
        echo "═══════════════════════════════════════════════════════════════════"
        echo "$ACCESS_TOKEN"
        echo "═══════════════════════════════════════════════════════════════════"
        echo ""
    fi
}

# -----------------------------------------------------------------------------
# FCM HTTP Request Functions
# -----------------------------------------------------------------------------

resolve_data_payload() {
    local input="$1"
    
    # Check if input starts with @ (file reference)
    if [[ "$input" == @* ]]; then
        local file_path="${input:1}"  # Remove the @ prefix
        
        if [[ ! -f "$file_path" ]]; then
            log_error "Data file not found: $file_path"
            exit 1
        fi
        
        cat "$file_path"
    else
        # Return inline JSON as-is
        echo "$input"
    fi
}

validate_json() {
    local json="$1"
    local field_name="${2:-JSON}"
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -z "$python_cmd" ]]; then
        log_info "Python 3 not found, skipping JSON validation"
        return 0
    fi
    
    if ! echo "$json" | "$python_cmd" -m json.tool > /dev/null 2>&1; then
        log_error "Invalid $field_name payload"
        log_error "Please check your JSON syntax"
        exit 1
    fi
}

build_default_data() {
    cat << EOF
{
    "push_from": "fcm",
    "title": "$MESSAGE_TITLE",
    "body": "$MESSAGE_BODY",
    "custom_action": "update_service"
}
EOF
}

build_message_payload() {
    local data_json="$1"
    
    cat << EOF
{
    "message": {
        "token": "$FCM_TOKEN",
        "data": $data_json
    }
}
EOF
}

send_fcm_message() {
    # Validate required parameters
    if [[ -z "$FCM_TOKEN" ]]; then
        log_error "FCM device token is required (-t flag)"
        exit 1
    fi

    if [[ -z "$PROJECT_ID" ]]; then
        log_error "Firebase Project ID is required (-p flag)"
        exit 1
    fi

    # Build data payload
    local data_json
    
    if [[ -n "$CUSTOM_PAYLOAD" ]]; then
        log_info "Using custom data payload"
        data_json=$(resolve_data_payload "$CUSTOM_PAYLOAD")
        validate_json "$data_json" "data"
    else
        data_json=$(build_default_data)
    fi

    # Build the full message payload
    local payload
    payload=$(build_message_payload "$data_json")

    # Get or generate access token
    get_access_token

    if [[ -z "$ACCESS_TOKEN" ]]; then
        log_error "No access token available. Run 'auth' command first."
        exit 1
    fi

    local url="https://fcm.googleapis.com/v1/projects/${PROJECT_ID}/messages:send"

    log_info "Sending FCM message to project: $PROJECT_ID"
    log_info "Target device token: ${FCM_TOKEN:0:20}..."

    # Show payload preview (first 200 chars)
    log_info "Payload preview: ${payload:0:200}..."

    # Send the request
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" -X POST \
        -H "Authorization: Bearer $ACCESS_TOKEN" \
        -H "Content-Type: application/json" \
        "$url" \
        -d "$payload")

    # Extract HTTP status code (last line)
    http_code=$(echo "$response" | tail -n 1)
    # Extract response body (all but last line)
    response=$(echo "$response" | sed '$d')

    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "FCM RESPONSE (HTTP $http_code):"
    echo "═══════════════════════════════════════════════════════════════════"
    local python_cmd
    python_cmd=$(get_python_cmd)
    if [[ -n "$python_cmd" ]]; then
        echo "$response" | "$python_cmd" -m json.tool 2>/dev/null || echo "$response"
    else
        echo "$response"
    fi
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""

    if [[ "$http_code" == "200" ]]; then
        log_success "Message sent successfully!"
    else
        log_error "Failed to send message (HTTP $http_code)"
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Command Handlers
# -----------------------------------------------------------------------------

cmd_auth() {
    log_info "Generating new access token..."
    FORCE_REFRESH=true
    get_access_token
    print_access_token
}

cmd_send() {
    send_fcm_message
}

cmd_token() {
    if is_token_valid; then
        ACCESS_TOKEN=$(get_cached_token)
        print_access_token
    else
        log_error "No valid cached token found. Run 'auth' command first."
        exit 1
    fi
}

cmd_check_python() {
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -n "$python_cmd" ]]; then
        local python_version
        python_version=$("$python_cmd" --version 2>&1)
        local python_path
        python_path=$(command -v "$python_cmd")
        
        log_success "Python 3 is installed"
        echo ""
        echo "  Command:  $python_cmd"
        echo "  Version:  $python_version"
        echo "  Path:     $python_path"
        echo ""
        exit 0
    else
        log_error "Python 3 is not installed or not found in PATH"
        echo ""
        echo "  Install Python 3:"
        echo "    macOS:   brew install python3"
        echo "    Ubuntu:  sudo apt install python3"
        echo "    Fedora:  sudo dnf install python3"
        echo ""
        exit 1
    fi
}

cmd_test() {
    local script_dir
    script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    local test_script="$script_dir/tests/test_fcm.sh"
    
    if [[ ! -f "$test_script" ]]; then
        log_error "Test script not found: $test_script"
        exit 1
    fi
    
    exec "$test_script" "$@"
}

# -----------------------------------------------------------------------------
# Main Entry Point
# -----------------------------------------------------------------------------

main() {
    # For 'test' command, pass all remaining args directly without parsing
    if [[ "${1:-}" == "test" ]]; then
        shift
        cmd_test "$@"
        return
    fi
    
    parse_arguments "$@"

    case "$COMMAND" in
        auth|access-token)
            cmd_auth
            ;;
        send)
            cmd_send
            ;;
        token)
            cmd_token
            ;;
        check-python)
            cmd_check_python
            ;;
        help|-h|--help)
            print_usage
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            print_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments (only when executed, not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi

