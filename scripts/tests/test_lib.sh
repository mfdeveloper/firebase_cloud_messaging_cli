#!/bin/bash

# =============================================================================
# Bash Test Library
# =============================================================================
# A lightweight testing framework for bash scripts with code coverage support.
#
# Features:
#   - Colorful test output
#   - Assertion functions
#   - Setup/teardown hooks
#   - Code coverage with terminal and HTML output
#
# Usage:
#   source test_lib.sh
#   # Define test functions
#   # Call run_test for each test
#   # Call print_test_summary at the end
# =============================================================================

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

SCRIPT_DIR="${SCRIPT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}"
COVERAGE_DIR="${COVERAGE_DIR:-$SCRIPT_DIR/coverage}"
TEST_TMP_DIR=""

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Coverage settings
RUN_COVERAGE=false
COVERAGE_OUTPUT="terminal"  # "terminal" or "html"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Command Line Arguments
# -----------------------------------------------------------------------------

show_test_help() {
    local script_name="${TEST_SCRIPT_NAME:-$(basename "$0")}"
    cat << EOF
Bash Test Runner

USAGE:
    $script_name [options]

OPTIONS:
    --coverage           Run tests with code coverage
    --output <format>    Coverage output format: "terminal" (default) or "html"
    --help               Show this help message

EXAMPLES:
    # Run tests normally
    $script_name

    # Run tests with coverage (terminal output)
    $script_name --coverage

    # Run tests with coverage (HTML report)
    $script_name --coverage --output html

EOF
}

parse_test_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --coverage)
                RUN_COVERAGE=true
                shift
                ;;
            --output)
                if [[ -n "$2" && "$2" != --* ]]; then
                    COVERAGE_OUTPUT="$2"
                    shift 2
                else
                    echo -e "${RED}Error: --output requires an argument (terminal or html)${NC}"
                    exit 1
                fi
                ;;
            --help|-h)
                show_test_help
                exit 0
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                show_test_help
                exit 1
                ;;
        esac
    done
}

# -----------------------------------------------------------------------------
# Assertion Functions
# -----------------------------------------------------------------------------

assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"
    
    if [[ "$expected" == "$actual" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed${NC}"
        echo "      Expected: '$expected'"
        echo "      Actual:   '$actual'"
        [[ -n "$message" ]] && echo "      Message:  $message"
        return 1
    fi
}

assert_not_equals() {
    local unexpected="$1"
    local actual="$2"
    local message="${3:-}"
    
    if [[ "$unexpected" != "$actual" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed${NC}"
        echo "      Expected NOT: '$unexpected'"
        echo "      Actual:       '$actual'"
        [[ -n "$message" ]] && echo "      Message:  $message"
        return 1
    fi
}

assert_not_empty() {
    local value="$1"
    local message="${2:-}"
    
    if [[ -n "$value" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: value is empty${NC}"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_empty() {
    local value="$1"
    local message="${2:-}"
    
    if [[ -z "$value" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: expected empty, got '$value'${NC}"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_true() {
    local condition="$1"
    local message="${2:-}"
    
    if [[ "$condition" == "true" || "$condition" == "1" || "$condition" == "0" ]]; then
        # If it's a string "true"/"1" or exit code 0
        if [[ "$condition" == "true" || "$condition" == "1" || "$condition" -eq 0 ]]; then
            return 0
        fi
    fi
    
    echo -e "    ${RED}✗ Assertion failed: expected true${NC}"
    [[ -n "$message" ]] && echo "      Message: $message"
    return 1
}

assert_false() {
    local condition="$1"
    local message="${2:-}"
    
    if [[ "$condition" == "false" || "$condition" == "0" || "$condition" != "0" ]]; then
        if [[ "$condition" == "false" || "$condition" == "0" || "$condition" -ne 0 ]]; then
            return 0
        fi
    fi
    
    echo -e "    ${RED}✗ Assertion failed: expected false${NC}"
    [[ -n "$message" ]] && echo "      Message: $message"
    return 1
}

assert_file_exists() {
    local file="$1"
    local message="${2:-}"
    
    if [[ -f "$file" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: file does not exist: $file${NC}"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_file_not_exists() {
    local file="$1"
    local message="${2:-}"
    
    if [[ ! -f "$file" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: file exists but shouldn't: $file${NC}"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_dir_exists() {
    local dir="$1"
    local message="${2:-}"
    
    if [[ -d "$dir" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: directory does not exist: $dir${NC}"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"
    
    if [[ "$haystack" == *"$needle"* ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: string does not contain expected substring${NC}"
        echo "      Looking for: '$needle'"
        echo "      In string:   '$haystack'"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-}"
    
    if [[ "$haystack" != *"$needle"* ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: string contains unexpected substring${NC}"
        echo "      Should NOT contain: '$needle'"
        echo "      In string:          '$haystack'"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_matches() {
    local string="$1"
    local pattern="$2"
    local message="${3:-}"
    
    if [[ "$string" =~ $pattern ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: string does not match pattern${NC}"
        echo "      Pattern: '$pattern'"
        echo "      String:  '$string'"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

assert_exit_code() {
    local expected="$1"
    local actual="$2"
    local message="${3:-}"
    
    if [[ "$expected" == "$actual" ]]; then
        return 0
    else
        echo -e "    ${RED}✗ Assertion failed: wrong exit code${NC}"
        echo "      Expected: $expected"
        echo "      Actual:   $actual"
        [[ -n "$message" ]] && echo "      Message: $message"
        return 1
    fi
}

# -----------------------------------------------------------------------------
# Test Runner
# -----------------------------------------------------------------------------

run_test() {
    local test_name="$1"
    local test_function="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${BLUE}▶${NC} Running: $test_name"
    
    # Call setup if defined
    if declare -f setup > /dev/null; then
        setup
    fi
    
    set +e
    "$test_function"
    local result=$?
    set -e
    
    # Call teardown if defined
    if declare -f teardown > /dev/null; then
        teardown
    fi
    
    if [[ $result -eq 0 ]]; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "  ${GREEN}✓ PASSED${NC}"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        echo -e "  ${RED}✗ FAILED${NC}"
    fi
    
    echo ""
}

skip_test() {
    local test_name="$1"
    local reason="${2:-}"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${BLUE}▶${NC} Running: $test_name"
    echo -e "  ${YELLOW}⊘ SKIPPED${NC}${reason:+ - $reason}"
    echo ""
}

print_test_header() {
    local title="${1:-Unit Tests}"
    echo ""
    echo "============================================================================="
    echo "  $title"
    echo "============================================================================="
    echo ""
}

print_test_summary() {
    echo "============================================================================="
    echo ""
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "  ${GREEN}All tests passed!${NC}"
    else
        echo -e "  ${RED}Some tests failed!${NC}"
    fi
    echo ""
    echo -e "  Total:  $TESTS_RUN"
    echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
    if [[ $TESTS_FAILED -gt 0 ]]; then
        echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
    else
        echo -e "  ${PURPLE}Failed: $TESTS_FAILED${NC}"
    fi
    echo ""
    echo "============================================================================="
    echo ""
}

# -----------------------------------------------------------------------------
# Coverage Support
# -----------------------------------------------------------------------------

# Main coverage function - runs coverage and then the test suite
#
# Usage:
#   run_with_coverage <target_script> [test_runner_script]
#
# The coverage test content should be defined in COVERAGE_TESTS variable before calling.
# This variable should contain bash commands that exercise the functions to test.
#
# Example:
#   COVERAGE_TESTS='
#   # Test logging
#   log_info "test" > /dev/null
#   log_error "test" || true
#   
#   # Test with subshells for functions that may exit
#   (some_function_that_exits) || true
#   '
#   run_with_coverage "$MY_SCRIPT"
#
run_with_coverage() {
    local target_script="$1"
    local test_runner_script="${2:-$0}"
    
    if [[ ! -f "$target_script" ]]; then
        echo -e "${RED}Error: Target script not found: $target_script${NC}"
        return 1
    fi
    
    if [[ -z "$COVERAGE_TESTS" ]]; then
        echo -e "${RED}Error: COVERAGE_TESTS variable is not defined${NC}"
        echo "Define COVERAGE_TESTS with the bash commands to exercise your functions."
        return 1
    fi
    
    echo -e "${BLUE}Running tests with code coverage...${NC}"
    echo ""
    
    # Clean previous coverage data
    rm -rf "$COVERAGE_DIR"
    mkdir -p "$COVERAGE_DIR"
    
    local trace_file="$COVERAGE_DIR/trace.log"
    local coverage_report="$COVERAGE_DIR/coverage_report.txt"
    local target_basename
    target_basename=$(basename "$target_script")
    
    # Create coverage test script
    local cov_script="$COVERAGE_DIR/.coverage_test.sh"
    
    cat > "$cov_script" << COVERAGE_HEADER
#!/bin/bash
set +e
export PS4='+ \${BASH_SOURCE[0]##*/}:\${LINENO}: '
exec 2>"$trace_file"
set -x
source "$target_script"
COVERAGE_HEADER

    # Append the coverage test content
    echo "$COVERAGE_TESTS" >> "$cov_script"
    chmod +x "$cov_script"
    
    echo "Running coverage tests with tracing..."
    
    # Run the coverage script
    bash "$cov_script" > /dev/null 2>/dev/null || true
    
    # Parse and display results
    _process_coverage_results "$target_script" "$target_basename" "$trace_file" "$coverage_report"
    
    # Clean up
    rm -f "$cov_script"
    
    # Run full test suite
    echo ""
    echo -e "${BLUE}Running full test suite...${NC}"
    echo ""
    COVERAGE_ALREADY_RUN=1 "$test_runner_script"
    
    exit $?
}

# Process coverage results from trace file
_process_coverage_results() {
    local target_script="$1"
    local target_basename="$2"
    local trace_file="$3"
    local coverage_report="$4"
    
    if [[ ! -f "$trace_file" ]]; then
        echo -e "${YELLOW}Warning: No trace file generated${NC}"
        return
    fi
    
    local covered_lines
    covered_lines=$(grep -oE "${target_basename}:[0-9]+" "$trace_file" 2>/dev/null | cut -d: -f2 | sort -u | wc -l | tr -d ' ')
    
    local total_lines
    total_lines=$(grep -c -E '^\s*(if|then|else|elif|fi|for|while|do|done|case|esac|local|return|exit|echo|shift|export|[a-zA-Z_][a-zA-Z0-9_]*=|\[\[|\]\]|;;|[a-zA-Z_][a-zA-Z0-9_]*\s+[^(])' "$target_script" 2>/dev/null || echo "0")
    
    local percent=0
    if [[ "$total_lines" -gt 0 ]]; then
        percent=$((covered_lines * 100 / total_lines))
    fi
    
    if [[ $percent -gt 100 ]]; then
        percent=100
    fi
    
    echo ""
    echo -e "${GREEN}Coverage analysis complete!${NC}"
    echo ""
    if [[ $percent -ge 70 ]]; then
        echo -e "  ${target_basename} Coverage: ${GREEN}${percent}%${NC} ($covered_lines lines executed)"
    elif [[ $percent -ge 40 ]]; then
        echo -e "  ${target_basename} Coverage: ${YELLOW}${percent}%${NC} ($covered_lines lines executed)"
    else
        echo -e "  ${target_basename} Coverage: ${RED}${percent}%${NC} ($covered_lines lines executed)"
    fi
    echo ""
    
    # Get list of covered lines
    local covered_list
    covered_list=$(grep -oE "${target_basename}:[0-9]+" "$trace_file" 2>/dev/null | cut -d: -f2 | sort -u -n)
    
    # Generate text report
    {
        echo "Coverage Report: $target_basename"
        echo "================================"
        echo "Generated: $(date)"
        echo ""
        echo "Coverage: ${percent}% ($covered_lines lines executed)"
        echo ""
        echo "Lines executed:"
        echo ""
        echo "$covered_list" | while read line; do
            local code
            code=$(sed -n "${line}p" "$target_script" | head -c 80)
            printf "  %4d: %s\n" "$line" "$code"
        done
    } > "$coverage_report"
    
    # Generate HTML report if requested
    if [[ "$COVERAGE_OUTPUT" == "html" ]]; then
        generate_html_coverage_report "$target_script" "$target_basename" "$percent" "$covered_lines" "$covered_list"
    fi
    
    echo "  Coverage report: $coverage_report"
    if [[ "$COVERAGE_OUTPUT" == "html" ]]; then
        echo "  HTML report: $COVERAGE_DIR/index.html"
    fi
    echo "  Trace log: $trace_file"
    echo ""
    
    # Open HTML report in browser if requested
    if [[ "$COVERAGE_OUTPUT" == "html" ]]; then
        if command -v open &> /dev/null; then
            echo -e "${BLUE}Opening HTML coverage report in browser...${NC}"
            open "$COVERAGE_DIR/index.html"
        elif command -v xdg-open &> /dev/null; then
            echo -e "${BLUE}Opening HTML coverage report in browser...${NC}"
            xdg-open "$COVERAGE_DIR/index.html"
        fi
    fi
}

generate_html_coverage_report() {
    local target_script="$1"
    local target_basename="$2"
    local percent="$3"
    local covered_lines="$4"
    local covered_list="$5"
    local html_file="$COVERAGE_DIR/index.html"
    local source_html="$COVERAGE_DIR/${target_basename}.html"
    
    # Save covered lines to a temp file for lookup
    local covered_file="$COVERAGE_DIR/.covered_lines"
    echo "$covered_list" > "$covered_file"
    
    # Determine color based on percentage
    local color_class
    if [[ $percent -ge 70 ]]; then
        color_class="high"
    elif [[ $percent -ge 40 ]]; then
        color_class="medium"
    else
        color_class="low"
    fi
    
    # Generate main index.html
    cat > "$html_file" << 'HTML_HEADER'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Coverage Report</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent: #e94560;
            --success: #00d26a;
            --warning: #ffc107;
            --danger: #e94560;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'JetBrains Mono', 'Fira Code', 'Monaco', monospace;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 2rem;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        header { text-align: center; margin-bottom: 3rem; }
        h1 {
            font-size: 2.5rem;
            background: linear-gradient(90deg, var(--accent), #ff6b6b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }
        .subtitle { color: var(--text-secondary); font-size: 0.9rem; }
        .coverage-card {
            background: var(--bg-secondary);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        .coverage-meter { display: flex; align-items: center; gap: 2rem; flex-wrap: wrap; }
        .percentage { font-size: 4rem; font-weight: bold; }
        .percentage.high { color: var(--success); }
        .percentage.medium { color: var(--warning); }
        .percentage.low { color: var(--danger); }
        .progress-container { flex: 1; min-width: 200px; }
        .progress-bar {
            height: 24px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 0.5rem;
        }
        .progress-fill { height: 100%; border-radius: 12px; transition: width 0.5s ease; }
        .progress-fill.high { background: linear-gradient(90deg, var(--success), #00ff88); }
        .progress-fill.medium { background: linear-gradient(90deg, var(--warning), #ffdb4d); }
        .progress-fill.low { background: linear-gradient(90deg, var(--danger), #ff6b6b); }
        .stats { display: flex; gap: 2rem; color: var(--text-secondary); }
        .stat-item { display: flex; gap: 0.5rem; }
        .file-link {
            display: inline-block;
            margin-top: 1.5rem;
            padding: 0.75rem 1.5rem;
            background: var(--accent);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .file-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(233, 69, 96, 0.4);
        }
        footer { text-align: center; margin-top: 3rem; color: var(--text-secondary); font-size: 0.85rem; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Coverage Report</h1>
            <p class="subtitle">Code Coverage Analysis</p>
        </header>
        <div class="coverage-card">
            <div class="coverage-meter">
HTML_HEADER

    cat >> "$html_file" << HTML_PERCENT
                <div class="percentage ${color_class}">${percent}%</div>
                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill ${color_class}" style="width: ${percent}%"></div>
                    </div>
                    <div class="stats">
                        <div class="stat-item"><span>✓</span><span>${covered_lines} lines covered</span></div>
                        <div class="stat-item"><span>📁</span><span>${target_basename}</span></div>
                    </div>
                </div>
            </div>
            <a href="${target_basename}.html" class="file-link">📄 View Source Coverage</a>
        </div>
        <footer>
            <p>Generated on $(date)</p>
        </footer>
    </div>
</body>
</html>
HTML_PERCENT

    # Generate source file coverage view
    cat > "$source_html" << 'SOURCE_HEADER'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Source Coverage</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --text-primary: #eaeaea;
            --text-secondary: #666;
            --line-covered: rgba(0, 210, 106, 0.15);
            --line-uncovered: rgba(233, 69, 96, 0.15);
            --border-covered: #00d26a;
            --border-uncovered: #e94560;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'JetBrains Mono', 'Fira Code', monospace;
            background: var(--bg-primary);
            color: var(--text-primary);
            font-size: 13px;
            line-height: 1.5;
        }
        .header {
            position: sticky;
            top: 0;
            background: var(--bg-secondary);
            padding: 1rem 2rem;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
        }
        .header a { color: #e94560; text-decoration: none; }
        .code-container { padding: 1rem 0; }
        .line { display: flex; padding: 0 1rem; }
        .line.covered { background: var(--line-covered); border-left: 3px solid var(--border-covered); }
        .line.uncovered { background: var(--line-uncovered); border-left: 3px solid var(--border-uncovered); }
        .line.neutral { border-left: 3px solid transparent; }
        .line-num { width: 50px; text-align: right; padding-right: 1rem; color: var(--text-secondary); user-select: none; }
        .line-code { flex: 1; white-space: pre; overflow-x: auto; }
        .comment { color: #6a9955; }
    </style>
</head>
<body>
SOURCE_HEADER

    echo "    <div class=\"header\">" >> "$source_html"
    echo "        <span>📄 ${target_basename}</span>" >> "$source_html"
    echo "        <a href=\"index.html\">← Back to Summary</a>" >> "$source_html"
    echo "    </div>" >> "$source_html"
    echo "    <div class=\"code-container\">" >> "$source_html"

    # Process each line of source file
    local line_num=0
    while IFS= read -r code_line || [[ -n "$code_line" ]]; do
        line_num=$((line_num + 1))
        
        local escaped_line
        escaped_line=$(echo "$code_line" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/>/\&gt;/g')
        
        local line_class="neutral"
        if grep -qx "$line_num" "$covered_file" 2>/dev/null; then
            line_class="covered"
        elif echo "$code_line" | grep -qE '^\s*[^#[:space:]]'; then
            line_class="uncovered"
        fi
        
        if [[ "$escaped_line" =~ ^[[:space:]]*# ]]; then
            escaped_line="<span class=\"comment\">$escaped_line</span>"
        fi
        
        echo "        <div class=\"line $line_class\"><span class=\"line-num\">$line_num</span><span class=\"line-code\">$escaped_line</span></div>" >> "$source_html"
    done < "$target_script"
    
    rm -f "$covered_file"

    cat >> "$source_html" << 'SOURCE_FOOTER'
    </div>
</body>
</html>
SOURCE_FOOTER
}

# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

create_temp_dir() {
    local prefix="${1:-test_tmp}"
    TEST_TMP_DIR="$SCRIPT_DIR/.${prefix}_$$"
    mkdir -p "$TEST_TMP_DIR"
    echo "$TEST_TMP_DIR"
}

cleanup_temp_dir() {
    if [[ -n "$TEST_TMP_DIR" && -d "$TEST_TMP_DIR" ]]; then
        rm -rf "$TEST_TMP_DIR"
    fi
}

cleanup_all_temp_dirs() {
    rm -rf "$SCRIPT_DIR/.test_tmp_"* 2>/dev/null || true
}

