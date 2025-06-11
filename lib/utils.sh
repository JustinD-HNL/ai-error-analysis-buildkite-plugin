#!/bin/bash
# AI Error Analysis Buildkite Plugin - Utility Functions
# Common utility functions used across plugin hooks

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*" >&2
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $*"
}

log_debug() {
    if [[ "${AI_ERROR_ANALYSIS_DEBUG:-false}" == "true" ]]; then
        echo -e "${PURPLE}[DEBUG]${NC} $*" >&2
    fi
}

# Performance timing
start_timer() {
    local timer_name="${1:-default}"
    export "AI_TIMER_${timer_name}=$(date +%s%N)"
}

end_timer() {
    local timer_name="${1:-default}"
    local start_var="AI_TIMER_${timer_name}"
    local start_time="${!start_var}"
    
    if [[ -n "${start_time}" ]]; then
        local end_time=$(date +%s%N)
        local duration=$(( (end_time - start_time) / 1000000 )) # Convert to milliseconds
        echo "${duration}"
    else
        echo "0"
    fi
}

# Configuration helpers
get_config_value() {
    local config_key="$1"
    local default_value="${2:-}"
    local env_var="BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_${config_key}"
    
    echo "${!env_var:-${default_value}}"
}

get_config_bool() {
    local config_key="$1"
    local default_value="${2:-false}"
    local value
    value=$(get_config_value "${config_key}" "${default_value}")
    
    case "${value,,}" in
        true|yes|1|on)
            echo "true"
            ;;
        *)
            echo "false"
            ;;
    esac
}

get_config_int() {
    local config_key="$1"
    local default_value="${2:-0}"
    local value
    value=$(get_config_value "${config_key}" "${default_value}")
    
    # Validate that it's a number
    if [[ "${value}" =~ ^[0-9]+$ ]]; then
        echo "${value}"
    else
        echo "${default_value}"
    fi
}

# File operations
ensure_directory() {
    local dir_path="$1"
    local permissions="${2:-755}"
    
    if [[ ! -d "${dir_path}" ]]; then
        mkdir -p "${dir_path}"
        chmod "${permissions}" "${dir_path}"
    fi
}

safe_remove() {
    local file_path="$1"
    
    if [[ -e "${file_path}" ]]; then
        rm -rf "${file_path}"
    fi
}

create_temp_file() {
    local prefix="${1:-ai-error-analysis}"
    local suffix="${2:-.tmp}"
    
    mktemp "/tmp/${prefix}-XXXXXX${suffix}"
}

create_temp_dir() {
    local prefix="${1:-ai-error-analysis}"
    
    mktemp -d "/tmp/${prefix}-XXXXXX"
}

# JSON operations
json_get() {
    local json_file="$1"
    local key_path="$2"
    local default_value="${3:-null}"
    
    if [[ -f "${json_file}" ]] && command -v jq >/dev/null 2>&1; then
        jq -r "${key_path} // \"${default_value}\"" "${json_file}" 2>/dev/null || echo "${default_value}"
    else
        echo "${default_value}"
    fi
}

json_set() {
    local json_file="$1"
    local key_path="$2"
    local value="$3"
    local temp_file
    
    temp_file=$(create_temp_file "json" ".json")
    
    if [[ -f "${json_file}" ]] && command -v jq >/dev/null 2>&1; then
        jq "${key_path} = \"${value}\"" "${json_file}" > "${temp_file}" && mv "${temp_file}" "${json_file}"
    else
        echo "{\"${key_path//./\":{\"}\": \"${value}\"}" > "${json_file}"
    fi
}

# Network operations
check_url_reachable() {
    local url="$1"
    local timeout="${2:-10}"
    
    if command -v curl >/dev/null 2>&1; then
        curl --silent --head --fail --max-time "${timeout}" "${url}" >/dev/null 2>&1
    elif command -v wget >/dev/null 2>&1; then
        wget --quiet --spider --timeout="${timeout}" "${url}" >/dev/null 2>&1
    else
        return 1
    fi
}

# Process management
is_process_running() {
    local pid="$1"
    
    if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

wait_for_process() {
    local pid="$1"
    local timeout="${2:-30}"
    local interval="${3:-1}"
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        if ! is_process_running "${pid}"; then
            return 0
        fi
        
        sleep "${interval}"
        elapsed=$((elapsed + interval))
    done
    
    return 1
}

kill_process_tree() {
    local pid="$1"
    local signal="${2:-TERM}"
    
    if is_process_running "${pid}"; then
        # Kill child processes first
        pkill -"${signal}" -P "${pid}" 2>/dev/null || true
        
        # Kill the main process
        kill -"${signal}" "${pid}" 2>/dev/null || true
        
        # Wait a bit and force kill if necessary
        if [[ "${signal}" == "TERM" ]]; then
            sleep 2
            if is_process_running "${pid}"; then
                kill -KILL "${pid}" 2>/dev/null || true
            fi
        fi
    fi
}

# String operations
trim_whitespace() {
    local string="$1"
    
    # Remove leading whitespace
    string="${string#"${string%%[![:space:]]*}"}"
    
    # Remove trailing whitespace
    string="${string%"${string##*[![:space:]]}"}"
    
    echo "${string}"
}

url_encode() {
    local string="$1"
    
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import urllib.parse; print(urllib.parse.quote('${string}'))"
    else
        # Fallback: basic URL encoding
        echo "${string}" | sed 's/ /%20/g; s/!/%21/g; s/"/%22/g; s/#/%23/g; s/\$/%24/g; s/&/%26/g; s/'\''/%27/g; s/(/%28/g; s/)/%29/g; s/*/%2A/g; s/+/%2B/g; s/,/%2C/g; s/\//%2F/g; s/:/%3A/g; s/;/%3B/g; s/</%3C/g; s/=/%3D/g; s/>/%3E/g; s/?/%3F/g; s/@/%40/g; s/\[/%5B/g; s/\\/%5C/g; s/\]/%5D/g; s/\^/%5E/g; s/`/%60/g; s/{/%7B/g; s/|/%7C/g; s/}/%7D/g; s/~/%7E/g'
    fi
}

base64_encode() {
    local string="$1"
    
    echo -n "${string}" | base64 -w 0
}

base64_decode() {
    local encoded_string="$1"
    
    echo "${encoded_string}" | base64 -d
}

# Environment validation
validate_environment() {
    local required_vars=("$@")
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            missing_vars+=("${var}")
        fi
    done
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        return 1
    fi
    
    return 0
}

# Retry logic
retry_command() {
    local max_attempts="$1"
    local delay="$2"
    shift 2
    local command=("$@")
    
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        log_debug "Attempt ${attempt}/${max_attempts}: ${command[*]}"
        
        if "${command[@]}"; then
            return 0
        fi
        
        if [[ $attempt -lt $max_attempts ]]; then
            log_warn "Command failed, retrying in ${delay} seconds..."
            sleep "${delay}"
            
            # Exponential backoff
            delay=$((delay * 2))
        fi
        
        attempt=$((attempt + 1))
    done
    
    log_error "Command failed after ${max_attempts} attempts: ${command[*]}"
    return 1
}

# Hash functions
sha256_hash() {
    local input="$1"
    
    if command -v sha256sum >/dev/null 2>&1; then
        echo -n "${input}" | sha256sum | cut -d' ' -f1
    elif command -v shasum >/dev/null 2>&1; then
        echo -n "${input}" | shasum -a 256 | cut -d' ' -f1
    else
        # Fallback: use Python
        python3 -c "import hashlib; print(hashlib.sha256('${input}'.encode()).hexdigest())"
    fi
}

md5_hash() {
    local input="$1"
    
    if command -v md5sum >/dev/null 2>&1; then
        echo -n "${input}" | md5sum | cut -d' ' -f1
    elif command -v md5 >/dev/null 2>&1; then
        echo -n "${input}" | md5 -r | cut -d' ' -f1
    else
        # Fallback: use Python
        python3 -c "import hashlib; print(hashlib.md5('${input}'.encode()).hexdigest())"
    fi
}

# Lock file operations
acquire_lock() {
    local lock_file="$1"
    local timeout="${2:-10}"
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        if (set -C; echo $$ > "${lock_file}") 2>/dev/null; then
            return 0
        fi
        
        # Check if the process holding the lock is still running
        if [[ -f "${lock_file}" ]]; then
            local lock_pid
            lock_pid=$(cat "${lock_file}" 2>/dev/null)
            
            if [[ -n "${lock_pid}" ]] && ! is_process_running "${lock_pid}"; then
                log_warn "Removing stale lock file: ${lock_file}"
                rm -f "${lock_file}"
                continue
            fi
        fi
        
        sleep 1
        elapsed=$((elapsed + 1))
    done
    
    return 1
}

release_lock() {
    local lock_file="$1"
    
    if [[ -f "${lock_file}" ]]; then
        local lock_pid
        lock_pid=$(cat "${lock_file}" 2>/dev/null)
        
        if [[ "${lock_pid}" == "$$" ]]; then
            rm -f "${lock_file}"
        fi
    fi
}

# System information
get_system_info() {
    local info_type="$1"
    
    case "${info_type}" in
        "os")
            uname -s
            ;;
        "arch")
            uname -m
            ;;
        "kernel")
            uname -r
            ;;
        "hostname")
            hostname
            ;;
        "user")
            whoami
            ;;
        "home")
            echo "${HOME}"
            ;;
        "shell")
            echo "${SHELL}"
            ;;
        "pwd")
            pwd
            ;;
        *)
            echo "unknown"
            ;;
    esac
}

# Plugin-specific helpers
get_plugin_version() {
    local plugin_dir="${AI_ERROR_ANALYSIS_PLUGIN_DIR:-}"
    
    if [[ -f "${plugin_dir}/plugin.yml" ]]; then
        # Try to extract version from plugin.yml if it exists
        grep -E "^version:" "${plugin_dir}/plugin.yml" 2>/dev/null | sed 's/version:[[:space:]]*//' || echo "unknown"
    else
        echo "unknown"
    fi
}

is_buildkite_environment() {
    [[ -n "${BUILDKITE:-}" ]] || [[ -n "${BUILDKITE_AGENT_NAME:-}" ]]
}

get_buildkite_build_url() {
    echo "${BUILDKITE_BUILD_URL:-}"
}

get_buildkite_step_url() {
    local build_url="${BUILDKITE_BUILD_URL:-}"
    local step_id="${BUILDKITE_STEP_ID:-}"
    
    if [[ -n "${build_url}" ]] && [[ -n "${step_id}" ]]; then
        echo "${build_url}#${step_id}"
    else
        echo ""
    fi
}

# Error handling
setup_error_handling() {
    set -euo pipefail
    
    # Set up trap for cleanup
    trap 'cleanup_on_error $? $LINENO' ERR
}

cleanup_on_error() {
    local exit_code="$1"
    local line_number="$2"
    
    log_error "Script failed with exit code ${exit_code} at line ${line_number}"
    
    # Call cleanup function if it exists
    if declare -f cleanup >/dev/null 2>&1; then
        cleanup
    fi
    
    exit "${exit_code}"
}

# Performance monitoring
start_performance_monitor() {
    local interval="${1:-5}"
    local output_file="${2:-/tmp/ai-error-analysis-perf.log}"
    
    {
        while true; do
            echo "$(date '+%Y-%m-%d %H:%M:%S') - $(ps -o pid,ppid,pcpu,pmem,cmd --pid=$$ --no-headers)" >> "${output_file}"
            sleep "${interval}"
        done
    } &
    
    echo $!
}

stop_performance_monitor() {
    local monitor_pid="$1"
    
    if is_process_running "${monitor_pid}"; then
        kill "${monitor_pid}" 2>/dev/null || true
    fi
}

# Export functions for use in other scripts
export -f log_info log_warn log_error log_success log_debug
export -f start_timer end_timer
export -f get_config_value get_config_bool get_config_int
export -f ensure_directory safe_remove create_temp_file create_temp_dir
export -f json_get json_set
export -f check_url_reachable
export -f is_process_running wait_for_process kill_process_tree
export -f trim_whitespace url_encode base64_encode base64_decode
export -f validate_environment
export -f retry_command
export -f sha256_hash md5_hash
export -f acquire_lock release_lock
export -f get_system_info
export -f get_plugin_version is_buildkite_environment get_buildkite_build_url get_buildkite_step_url
export -f setup_error_handling cleanup_on_error
export -f start_performance_monitor stop_performance_monitor