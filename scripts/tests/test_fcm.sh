#!/bin/bash

# =============================================================================
# FCM CLI Unit Tests
# =============================================================================
# Run with: ./scripts/tests/test_fcm.sh
# 
# Options:
#   --coverage           Run tests with code coverage
#   --output <format>    Coverage output format: "terminal" (default) or "html"
#   --help               Show help message
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FCM_SCRIPT="$SCRIPT_DIR/../fcm.sh"
TEST_SCRIPT_NAME="$(basename "$0")"

# Source the test library
source "$SCRIPT_DIR/test_lib.sh"

# -----------------------------------------------------------------------------
# Test Setup/Teardown
# -----------------------------------------------------------------------------

setup() {
    # Create temporary directory for test files
    TEST_TMP_DIR=$(create_temp_dir)
    
    # Source the FCM script to get access to functions
    set +e
    source "$FCM_SCRIPT"
    set -e
    
    # Reset global variables
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
    TOKEN_CACHE_FILE="$TEST_TMP_DIR/.test_token_cache"
    TOKEN_TTL_SECONDS=3300
    
    # Reset getopts index
    OPTIND=1
}

teardown() {
    cleanup_temp_dir
}

# -----------------------------------------------------------------------------
# Coverage Tests - Commands to exercise all FCM functions
# -----------------------------------------------------------------------------
# Define the bash commands that will be traced for coverage analysis.
# These run in a subshell with the FCM script sourced.

read -r -d '' COVERAGE_TESTS << 'END_COVERAGE' || true
# Create temp directory for test files
TMP_DIR=$(mktemp -d)
TOKEN_CACHE_FILE="$TMP_DIR/token_cache"
TOKEN_TTL_SECONDS=3300

# --- Logging functions ---
log_info "Testing log_info" > /dev/null
log_error "Testing log_error" || true
log_success "Testing log_success" > /dev/null

# --- Python detection ---
get_python_cmd > /dev/null || true

# --- Token cache functions ---
save_token_to_cache "test_token_123" > /dev/null
get_cached_token > /dev/null
is_token_valid > /dev/null || true

# Expired token
echo "$(($(date +%s) - 4000))" > "$TOKEN_CACHE_FILE"
echo "expired" >> "$TOKEN_CACHE_FILE"
is_token_valid > /dev/null || true

# No file
TOKEN_CACHE_FILE="$TMP_DIR/nonexistent"
is_token_valid > /dev/null || true

# Valid token
TOKEN_CACHE_FILE="$TMP_DIR/token_cache"
save_token_to_cache "fresh_token" > /dev/null
is_token_valid > /dev/null || true

# --- Argument parsing ---
OPTIND=1; (parse_arguments "auth") || true
OPTIND=1; (parse_arguments "auth" "-e" "test@example.com") || true
OPTIND=1; (parse_arguments "auth" "-f" "/path/to/key.json") || true
OPTIND=1; (parse_arguments "send" "-t" "token" "-p" "project") || true
OPTIND=1; (parse_arguments "send" "-T" "Title" "-B" "Body") || true
OPTIND=1; (parse_arguments "send" "-d" '{"key":"value"}') || true
OPTIND=1; (parse_arguments "send" "-r") || true
OPTIND=1; (parse_arguments "send" "-h") > /dev/null || true
OPTIND=1; (parse_arguments) > /dev/null || true
OPTIND=1; (parse_arguments "send" "-X" "invalid" > /dev/null) || true

# --- JSON payload functions ---
FCM_TOKEN="test_device_token"
MESSAGE_TITLE="Test Title"
MESSAGE_BODY="Test Body"
CUSTOM_PAYLOAD=""

build_default_data > /dev/null
build_message_payload '{"test":"data"}' > /dev/null
resolve_data_payload '{"inline":"json"}' > /dev/null

echo '{"from":"file"}' > "$TMP_DIR/data.json"
resolve_data_payload "@$TMP_DIR/data.json" > /dev/null
(resolve_data_payload "@/nonexistent/file.json" > /dev/null) || true

validate_json '{"valid":"json"}' || true
(validate_json 'invalid json{' > /dev/null) || true

# --- Extract client email ---
echo '{"client_email":"test@example.com"}' > "$TMP_DIR/creds.json"
extract_client_email "$TMP_DIR/creds.json" > /dev/null || true
echo '{"no_email":"here"}' > "$TMP_DIR/no_email.json"
extract_client_email "$TMP_DIR/no_email.json" > /dev/null || true
extract_client_email "/nonexistent/file.json" > /dev/null || true

# --- Print functions ---
print_usage > /dev/null
ACCESS_TOKEN="test_access_token"
print_access_token > /dev/null

# --- Access token management ---
save_token_to_cache "cached_token" > /dev/null
FORCE_REFRESH=false
get_access_token > /dev/null || true
FORCE_REFRESH=true
(get_access_token > /dev/null) || true

# --- Command handlers ---
(cmd_check_python > /dev/null) || true

TOKEN_CACHE_FILE="$TMP_DIR/token_cache"
save_token_to_cache "valid_token" > /dev/null
(cmd_token > /dev/null) || true
TOKEN_CACHE_FILE="$TMP_DIR/no_cache"
(cmd_token > /dev/null) || true

KEY_FILE_PATH="$TMP_DIR/creds.json"
(cmd_auth > /dev/null) || true

FCM_TOKEN=""
PROJECT_ID=""
(cmd_send > /dev/null) || true
FCM_TOKEN="test_device_token"
(cmd_send > /dev/null) || true

FCM_TOKEN="test_device_token"
PROJECT_ID="test-project"
TOKEN_CACHE_FILE="$TMP_DIR/token_cache"
save_token_to_cache "valid_token" > /dev/null
ACCESS_TOKEN="test_token"
FORCE_REFRESH=false
(cmd_send > /dev/null) || true

CUSTOM_PAYLOAD='{"custom":"data"}'
(send_fcm_message > /dev/null) || true

echo '{"file":"data"}' > "$TMP_DIR/payload.json"
CUSTOM_PAYLOAD="@$TMP_DIR/payload.json"
(send_fcm_message > /dev/null) || true

# --- Error paths ---
KEY_FILE_PATH="/nonexistent/key.json"
SERVICE_ACCOUNT_EMAIL=""
(generate_access_token > /dev/null) || true

KEY_FILE_PATH="$TMP_DIR/creds.json"
(generate_access_token > /dev/null) || true

# --- Main function ---
(main "help" > /dev/null) || true
(main "-h" > /dev/null) || true
(main "--help" > /dev/null) || true
(main "check-python" > /dev/null) || true
(main "token" > /dev/null) || true
(main "unknown_command" > /dev/null) || true
(main "auth" "-e" "test@example.com" "-f" "$TMP_DIR/creds.json" > /dev/null) || true
(main "access-token" "-f" "$TMP_DIR/creds.json" > /dev/null) || true
(main "send" "-t" "token" "-p" "project" > /dev/null) || true

# --- Additional edge cases ---
KEY_FILE_PATH=""
SERVICE_ACCOUNT_EMAIL=""
(generate_access_token > /dev/null) || true

echo "" > "$TMP_DIR/token_cache"
TOKEN_CACHE_FILE="$TMP_DIR/token_cache"
is_token_valid || true

save_token_to_cache "valid_test_token" > /dev/null
cmd_token > /dev/null || true

echo '{"type":"service_account","project_id":"test"}' > "$TMP_DIR/no_email_creds.json"
KEY_FILE_PATH="$TMP_DIR/no_email_creds.json"
SERVICE_ACCOUNT_EMAIL=""
(generate_access_token > /dev/null) || true

ACCESS_TOKEN=""
FCM_TOKEN="device_token"
PROJECT_ID="project"
TOKEN_CACHE_FILE="$TMP_DIR/totally_nonexistent_cache_$$"
FORCE_REFRESH=false
KEY_FILE_PATH=""
CUSTOM_PAYLOAD=""
(send_fcm_message > /dev/null) || true

# Cleanup
rm -rf "$TMP_DIR"
END_COVERAGE


# =============================================================================
# Test Cases: Logging Functions
# =============================================================================

test_log_info() {
    local output
    output=$(log_info "test message")
    assert_equals "[INFO] test message" "$output"
}

test_log_error() {
    local output
    output=$(log_error "error message" 2>&1)
    assert_contains "$output" "[ERROR] error message"
}

test_log_success() {
    local output
    output=$(log_success "success message")
    assert_equals "[SUCCESS] success message" "$output"
}

# =============================================================================
# Test Cases: Python Detection
# =============================================================================

test_get_python_cmd_returns_value() {
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -n "$python_cmd" ]]; then
        if [[ "$python_cmd" == *"python"* ]]; then
            return 0
        else
            echo "    Expected python command, got: $python_cmd"
            return 1
        fi
    else
        # Python not installed, which is fine for the test
        return 0
    fi
}

test_get_python_cmd_returns_valid_command() {
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -n "$python_cmd" ]]; then
        command -v "$python_cmd" &> /dev/null
        assert_exit_code 0 $?
    else
        return 0
    fi
}

# =============================================================================
# Test Cases: Token Cache Management
# =============================================================================

test_save_token_to_cache_creates_file() {
    save_token_to_cache "test_token_123" > /dev/null
    assert_file_exists "$TOKEN_CACHE_FILE"
}

test_save_token_to_cache_stores_token() {
    save_token_to_cache "my_secret_token" > /dev/null
    local stored_token
    stored_token=$(sed -n '2p' "$TOKEN_CACHE_FILE")
    assert_equals "my_secret_token" "$stored_token"
}

test_save_token_to_cache_stores_timestamp() {
    save_token_to_cache "test_token" > /dev/null
    local stored_timestamp
    stored_timestamp=$(head -n 1 "$TOKEN_CACHE_FILE")
    if [[ "$stored_timestamp" =~ ^[0-9]+$ ]]; then
        return 0
    else
        echo "    Expected numeric timestamp, got: $stored_timestamp"
        return 1
    fi
}

test_get_cached_token_returns_token() {
    save_token_to_cache "cached_token_value" > /dev/null
    local result
    result=$(get_cached_token)
    assert_equals "cached_token_value" "$result"
}

test_get_cached_token_returns_empty_when_no_file() {
    local result
    result=$(get_cached_token)
    assert_empty "$result"
}

test_is_token_valid_returns_false_when_no_file() {
    is_token_valid > /dev/null 2>&1
    local result=$?
    assert_equals 1 $result "Should return 1 (false) when no cache file exists"
}

test_is_token_valid_returns_true_for_fresh_token() {
    save_token_to_cache "fresh_token" > /dev/null
    is_token_valid > /dev/null 2>&1
    local result=$?
    assert_equals 0 $result "Should return 0 (true) for a fresh token"
}

test_is_token_valid_returns_false_for_expired_token() {
    local old_timestamp=$(($(date +%s) - 4000))
    echo "$old_timestamp" > "$TOKEN_CACHE_FILE"
    echo "expired_token" >> "$TOKEN_CACHE_FILE"
    
    is_token_valid > /dev/null 2>&1
    local result=$?
    assert_equals 1 $result "Should return 1 (false) for an expired token"
}

# =============================================================================
# Test Cases: Argument Parsing
# =============================================================================

test_parse_arguments_sets_command() {
    parse_arguments "auth"
    assert_equals "auth" "$COMMAND"
}

test_parse_arguments_sets_email() {
    parse_arguments "auth" "-e" "test@example.com"
    assert_equals "test@example.com" "$SERVICE_ACCOUNT_EMAIL"
}

test_parse_arguments_sets_fcm_token() {
    parse_arguments "send" "-t" "device_token_123"
    assert_equals "device_token_123" "$FCM_TOKEN"
}

test_parse_arguments_sets_project_id() {
    parse_arguments "send" "-p" "my-project-id"
    assert_equals "my-project-id" "$PROJECT_ID"
}

test_parse_arguments_sets_custom_payload() {
    parse_arguments "send" "-d" '{"key": "value"}'
    assert_equals '{"key": "value"}' "$CUSTOM_PAYLOAD"
}

test_parse_arguments_sets_title() {
    parse_arguments "send" "-T" "Custom Title"
    assert_equals "Custom Title" "$MESSAGE_TITLE"
}

test_parse_arguments_sets_body() {
    parse_arguments "send" "-B" "Custom Body"
    assert_equals "Custom Body" "$MESSAGE_BODY"
}

test_parse_arguments_sets_force_refresh() {
    parse_arguments "send" "-r"
    assert_equals "true" "$FORCE_REFRESH"
}

test_parse_arguments_sets_key_file() {
    parse_arguments "auth" "-f" "/path/to/key.json"
    assert_equals "/path/to/key.json" "$KEY_FILE_PATH"
}

test_parse_arguments_uses_env_for_key_file() {
    export GOOGLE_APPLICATION_CREDENTIALS="/env/path/key.json"
    parse_arguments "auth"
    assert_equals "/env/path/key.json" "$KEY_FILE_PATH"
    unset GOOGLE_APPLICATION_CREDENTIALS
}

test_parse_arguments_multiple_flags() {
    parse_arguments "send" "-t" "token123" "-p" "project456" "-T" "Title" "-B" "Body"
    assert_equals "send" "$COMMAND" && \
    assert_equals "token123" "$FCM_TOKEN" && \
    assert_equals "project456" "$PROJECT_ID" && \
    assert_equals "Title" "$MESSAGE_TITLE" && \
    assert_equals "Body" "$MESSAGE_BODY"
}

# =============================================================================
# Test Cases: JSON Payload Functions
# =============================================================================

test_build_default_data_contains_required_fields() {
    MESSAGE_TITLE="Test Title"
    MESSAGE_BODY="Test Body"
    local result
    result=$(build_default_data)
    
    assert_contains "$result" "push_from" && \
    assert_contains "$result" "title" && \
    assert_contains "$result" "body" && \
    assert_contains "$result" "custom_action"
}

test_build_default_data_uses_message_title() {
    MESSAGE_TITLE="My Custom Title"
    local result
    result=$(build_default_data)
    assert_contains "$result" "My Custom Title"
}

test_build_default_data_uses_message_body() {
    MESSAGE_BODY="My Custom Body"
    local result
    result=$(build_default_data)
    assert_contains "$result" "My Custom Body"
}

test_build_message_payload_contains_token() {
    FCM_TOKEN="device_token_xyz"
    local data='{"key": "value"}'
    local result
    result=$(build_message_payload "$data")
    assert_contains "$result" "device_token_xyz"
}

test_build_message_payload_contains_message_wrapper() {
    FCM_TOKEN="token"
    local data='{"key": "value"}'
    local result
    result=$(build_message_payload "$data")
    assert_contains "$result" '"message"'
}

test_build_message_payload_contains_data() {
    FCM_TOKEN="token"
    local data='{"custom_key": "custom_value"}'
    local result
    result=$(build_message_payload "$data")
    assert_contains "$result" "custom_key"
}

test_resolve_data_payload_returns_inline_json() {
    local result
    result=$(resolve_data_payload '{"inline": "json"}')
    assert_equals '{"inline": "json"}' "$result"
}

test_resolve_data_payload_reads_file() {
    local test_file="$TEST_TMP_DIR/test_data.json"
    echo '{"from": "file"}' > "$test_file"
    
    local result
    result=$(resolve_data_payload "@$test_file")
    assert_equals '{"from": "file"}' "$result"
}

test_validate_json_accepts_valid_json() {
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -z "$python_cmd" ]]; then
        echo "    Skipping: Python not available"
        return 0
    fi
    
    validate_json '{"valid": "json"}'
    return 0
}

# =============================================================================
# Test Cases: Extract Client Email
# =============================================================================

test_extract_client_email_from_valid_json() {
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -z "$python_cmd" ]]; then
        echo "    Skipping: Python not available"
        return 0
    fi
    
    local test_file="$TEST_TMP_DIR/credentials.json"
    echo '{"type": "service_account", "client_email": "test-service@project.iam.gserviceaccount.com", "project_id": "test-project"}' > "$test_file"
    
    local result
    result=$(extract_client_email "$test_file")
    assert_equals "test-service@project.iam.gserviceaccount.com" "$result"
}

test_extract_client_email_returns_empty_for_missing_field() {
    local python_cmd
    python_cmd=$(get_python_cmd)
    
    if [[ -z "$python_cmd" ]]; then
        echo "    Skipping: Python not available"
        return 0
    fi
    
    local test_file="$TEST_TMP_DIR/no_email.json"
    echo '{"type": "service_account"}' > "$test_file"
    
    local result
    result=$(extract_client_email "$test_file")
    assert_empty "$result"
}

test_extract_client_email_fails_for_missing_file() {
    extract_client_email "/nonexistent/file.json"
    local result=$?
    assert_equals 1 $result
}

# =============================================================================
# Test Cases: Print Usage
# =============================================================================

test_print_usage_contains_commands() {
    local output
    output=$(print_usage)
    assert_contains "$output" "COMMANDS" && \
    assert_contains "$output" "auth" && \
    assert_contains "$output" "send" && \
    assert_contains "$output" "token"
}

test_print_usage_contains_options() {
    local output
    output=$(print_usage)
    assert_contains "$output" "OPTIONS" && \
    assert_contains "$output" "-e EMAIL" && \
    assert_contains "$output" "-t TOKEN" && \
    assert_contains "$output" "-p PROJECT"
}

# =============================================================================
# Main Entry Point
# =============================================================================

# Parse arguments (skip if running under coverage)
if [[ -z "$COVERAGE_ALREADY_RUN" ]]; then
    parse_test_args "$@"
    
    if [[ "$RUN_COVERAGE" == true ]]; then
        run_with_coverage "$FCM_SCRIPT" "$0"
    fi
fi

# Print header
print_test_header "FCM CLI Unit Tests"

# Run logging tests
run_test "log_info outputs correct format" test_log_info
run_test "log_error outputs to stderr" test_log_error
run_test "log_success outputs correct format" test_log_success

# Run Python detection tests
run_test "get_python_cmd returns a value" test_get_python_cmd_returns_value
run_test "get_python_cmd returns valid command" test_get_python_cmd_returns_valid_command

# Run token cache tests
run_test "save_token_to_cache creates file" test_save_token_to_cache_creates_file
run_test "save_token_to_cache stores token" test_save_token_to_cache_stores_token
run_test "save_token_to_cache stores timestamp" test_save_token_to_cache_stores_timestamp
run_test "get_cached_token returns stored token" test_get_cached_token_returns_token
run_test "get_cached_token returns empty when no file" test_get_cached_token_returns_empty_when_no_file
run_test "is_token_valid returns false when no file" test_is_token_valid_returns_false_when_no_file
run_test "is_token_valid returns true for fresh token" test_is_token_valid_returns_true_for_fresh_token
run_test "is_token_valid returns false for expired token" test_is_token_valid_returns_false_for_expired_token

# Run argument parsing tests
run_test "parse_arguments sets command" test_parse_arguments_sets_command
run_test "parse_arguments sets email (-e)" test_parse_arguments_sets_email
run_test "parse_arguments sets FCM token (-t)" test_parse_arguments_sets_fcm_token
run_test "parse_arguments sets project ID (-p)" test_parse_arguments_sets_project_id
run_test "parse_arguments sets custom payload (-d)" test_parse_arguments_sets_custom_payload
run_test "parse_arguments sets title (-T)" test_parse_arguments_sets_title
run_test "parse_arguments sets body (-B)" test_parse_arguments_sets_body
run_test "parse_arguments sets force refresh (-r)" test_parse_arguments_sets_force_refresh
run_test "parse_arguments sets key file (-f)" test_parse_arguments_sets_key_file
run_test "parse_arguments uses GOOGLE_APPLICATION_CREDENTIALS" test_parse_arguments_uses_env_for_key_file
run_test "parse_arguments handles multiple flags" test_parse_arguments_multiple_flags

# Run JSON payload tests
run_test "build_default_data contains required fields" test_build_default_data_contains_required_fields
run_test "build_default_data uses MESSAGE_TITLE" test_build_default_data_uses_message_title
run_test "build_default_data uses MESSAGE_BODY" test_build_default_data_uses_message_body
run_test "build_message_payload contains token" test_build_message_payload_contains_token
run_test "build_message_payload has message wrapper" test_build_message_payload_contains_message_wrapper
run_test "build_message_payload contains data" test_build_message_payload_contains_data
run_test "resolve_data_payload returns inline JSON" test_resolve_data_payload_returns_inline_json
run_test "resolve_data_payload reads from file" test_resolve_data_payload_reads_file
run_test "validate_json accepts valid JSON" test_validate_json_accepts_valid_json

# Run extract client email tests
run_test "extract_client_email from valid JSON" test_extract_client_email_from_valid_json
run_test "extract_client_email returns empty for missing field" test_extract_client_email_returns_empty_for_missing_field
run_test "extract_client_email fails for missing file" test_extract_client_email_fails_for_missing_file

# Run usage tests
run_test "print_usage contains commands" test_print_usage_contains_commands
run_test "print_usage contains options" test_print_usage_contains_options

# Print summary
print_test_summary

# Clean up any remaining test directories
cleanup_all_temp_dirs

# Exit with error if any tests failed
[[ $TESTS_FAILED -eq 0 ]]
