#!/usr/bin/env bats

load '/usr/local/lib/bats-support/load'
load '/usr/local/lib/bats-assert/load'
load '/usr/local/lib/bats-file/load'

setup() {
    export AI_ERROR_ANALYSIS_PLUGIN_DIR="$PWD"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN="true"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="false"
    
    # Create temp directory for tests
    export TEST_TEMP_DIR=$(mktemp -d)
}

teardown() {
    if [[ -n "${TEST_TEMP_DIR:-}" ]] && [[ -d "${TEST_TEMP_DIR}" ]]; then
        rm -rf "${TEST_TEMP_DIR}"
    fi
}

@test "validates Python 3 is available" {
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "Python 3.9 detected"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "fails when Python is too old" {
    stub python3 \
        '--version : echo "Python 2.7.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".2.7"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : false'
    
    run hooks/environment
    assert_failure
    assert_output --partial "Python 2.7 found, but Python 3.7 or later is required"
    
    unstub python3
}

@test "fails when required commands are missing" {
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true'
    
    stub curl '--version : echo "curl 7.68.0"'
    # jq is missing (not stubbed)
    
    run hooks/environment
    assert_failure
    assert_output --partial "Required command 'jq' not found"
    
    unstub python3
    unstub curl
}

@test "validates AI provider configuration in non-dry-run mode" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN="false"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_AI_PROVIDERS='[{"name":"openai","model":"gpt-4o-mini"}]'
    export OPENAI_API_KEY="test-key"
    
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true' \
        '-c "
import json
import os
import sys

try:
    providers = json.loads('\''[{\"name\":\"openai\",\"model\":\"gpt-4o-mini\"}]'\'')
    if not isinstance(providers, list):
        providers = [providers]
    
    missing_keys = []
    for provider in providers:
        name = provider.get('\''name'\'', '\'\'\'').lower()
        api_key_env = provider.get('\''api_key_env'\'', f'\''{name.upper()}_API_KEY'\'')
        
        if api_key_env not in os.environ:
            missing_keys.append(f'\''{name}: {api_key_env}'\'')
    
    if missing_keys:
        print('\''❌ Missing API keys for providers:'\'')
        for key in missing_keys:
            print(f'\''  - {key}'\'')
        print('\''Please set the required environment variables.'\'')
        sys.exit(1)
    else:
        print('\''✅ All required API keys found'\'')
        
except json.JSONDecodeError as e:
    print(f'\''❌ Invalid AI providers configuration: {e}'\'')
    sys.exit(1)
except Exception as e:
    print(f'\''❌ Error validating AI providers: {e}'\'')
    sys.exit(1)
 : echo "✅ All required API keys found"'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "All required API keys found"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "skips API key validation in dry-run mode" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN="true"
    
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "Dry run mode enabled - skipping API key validation"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "handles branch restrictions correctly" {
    export BUILDKITE_BRANCH="feature/test"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONDITIONS_BRANCHES='["main","develop"]'
    
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true' \
        '-c "
import json
import sys

allowed = json.loads('\''[\"main\",\"develop\"]'\'')
current_branch = '\''feature/test'\''

if not allowed or current_branch in allowed:
    print(f'\''✅ Branch \"{current_branch}\" is allowed for AI analysis'\'')
else:
    print(f'\''ℹ️ Branch \"{current_branch}\" not in allowed list: {allowed}'\'')
    print('\''Skipping AI error analysis for this branch'\'')
    # Set flag to skip analysis but don'\''t fail the build
    sys.exit(42)  # Special exit code to indicate skip
 : exit 42'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "not in allowed list"
    # Should set skip flag
    
    unstub python3
    unstub curl
    unstub jq
}

@test "sets up cache directory when enabled" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_ENABLED="true"
    export BUILDKITE_BUILD_PATH="$TEST_TEMP_DIR"
    
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "Caching enabled at"
    assert_dir_exists "$TEST_TEMP_DIR/.ai-error-analysis-cache"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "installs Python dependencies when missing" {
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true' \
        '-c "import requests" : exit 1' \
        '-m pip install --user requests : echo "Installing requests..."'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "Installing required Python packages"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "provides debug information when enabled" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"
    
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true' \
        '--version : echo "Python 3.9.0 (default, Jan 1 2023, 00:00:00)"'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    stub whoami ': echo "testuser"'
    stub pwd ': echo "/test/directory"'
    stub df '-h . : echo "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   50G   50G  50% /"'
    stub free '-h : echo "              total        used        free      shared  buff/cache   available\nMem:           16Gi       8Gi       4Gi       1Gi       4Gi       6Gi"'
    stub python3 'lib/health_check.py : echo "{\"overall_status\":\"pass\"}"'
    
    run hooks/environment
    assert_success
    assert_output --partial "Debug Information"
    assert_output --partial "Python version:"
    assert_output --partial "Current user:"
    
    unstub python3
    unstub curl
    unstub jq
    unstub whoami
    unstub pwd
    unstub df
    unstub free
}

@test "fails when health check fails" {
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true' \
        'lib/health_check.py : exit 1'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    
    run hooks/environment
    assert_failure
    assert_output --partial "Health check failed"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "handles missing Python gracefully" {
    # python3 command not available
    run hooks/environment
    assert_failure
    assert_output --partial "Python 3 is required but not found"
}

@test "validates JSON configuration" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_AI_PROVIDERS='invalid-json'
    
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\" + \".\".join(map(str, sys.version_info[:2])))" : echo ".3.9"' \
        '-c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)" : true' \
        '-c "
import json
import os
import sys

try:
    providers = json.loads('\''invalid-json'\'')
    # ... rest of validation
except json.JSONDecodeError as e:
    print(f'\''❌ Invalid AI providers configuration: {e}'\'')
    sys.exit(1)
 : echo "❌ Invalid AI providers configuration: Expecting value: line 1 column 1 (char 0)" && exit 1'
    
    run hooks/environment
    assert_failure
    assert_output --partial "Invalid AI providers configuration"
    
    unstub python3
}