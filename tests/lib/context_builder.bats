#!/usr/bin/env bats

load '/usr/local/lib/bats-support/load'
load '/usr/local/lib/bats-assert/load'
load '/usr/local/lib/bats-file/load'

setup() {
    export AI_ERROR_ANALYSIS_PLUGIN_DIR="$PWD"
    export PYTHONPATH="$PWD/lib"
    
    # Create test environment
    export BUILDKITE_BUILD_ID="test-build-123"
    export BUILDKITE_BUILD_NUMBER="42"
    export BUILDKITE_JOB_ID="test-job-456"
    export BUILDKITE_STEP_KEY="test-step"
    export BUILDKITE_COMMAND="npm test"
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_PIPELINE_SLUG="test-pipeline"
    export BUILDKITE_BRANCH="main"
    export BUILDKITE_COMMIT="abc123"
    
    # Test temp directory
    export TEST_TEMP_DIR=$(mktemp -d)
}

teardown() {
    if [[ -n "${TEST_TEMP_DIR:-}" ]] && [[ -d "${TEST_TEMP_DIR}" ]]; then
        rm -rf "${TEST_TEMP_DIR}"
    fi
}

@test "context builder produces valid JSON output" {
    run python3 lib/context_builder.py
    assert_success
    
    # Verify it's valid JSON
    echo "$output" | jq . > /dev/null
}

@test "context builder includes basic build information" {
    run python3 lib/context_builder.py
    assert_success
    
    # Check for required fields
    echo "$output" | jq -e '.build_info.build_id' > /dev/null
    echo "$output" | jq -e '.build_info.job_id' > /dev/null
    echo "$output" | jq -e '.build_info.step_key' > /dev/null
}

@test "context builder includes error information" {
    run python3 lib/context_builder.py
    assert_success
    
    # Check error info
    echo "$output" | jq -e '.error_info.exit_code' > /dev/null
    echo "$output" | jq -e '.error_info.command' > /dev/null
    
    # Verify exit code is correct
    local exit_code=$(echo "$output" | jq -r '.error_info.exit_code')
    assert_equal "$exit_code" "1"
}

@test "context builder includes git information when available" {
    run python3 lib/context_builder.py
    assert_success
    
    # Check git info
    echo "$output" | jq -e '.git_info.branch' > /dev/null
    echo "$output" | jq -e '.git_info.commit' > /dev/null
    
    # Verify values
    local branch=$(echo "$output" | jq -r '.git_info.branch')
    assert_equal "$branch" "main"
}

@test "context builder handles missing environment variables gracefully" {
    # Remove some environment variables
    unset BUILDKITE_BRANCH
    unset BUILDKITE_COMMIT
    
    run python3 lib/context_builder.py
    assert_success
    
    # Should still produce valid JSON with unknown values
    local branch=$(echo "$output" | jq -r '.git_info.branch')
    assert_equal "$branch" "unknown"
}

@test "context builder respects configuration flags" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_INCLUDE_ENVIRONMENT="false"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_INCLUDE_GIT_INFO="false"
    
    run python3 lib/context_builder.py
    assert_success
    
    # Environment should be empty when disabled
    local env_keys=$(echo "$output" | jq -r '.environment | keys | length')
    assert_equal "$env_keys" "0"
    
    # Git info should be empty when disabled
    local git_keys=$(echo "$output" | jq -r '.git_info | keys | length')
    assert_equal "$git_keys" "0"
}

@test "context builder includes log excerpt" {
    run python3 lib/context_builder.py
    assert_success
    
    # Should have log_excerpt field
    echo "$output" | jq -e '.log_excerpt' > /dev/null
    
    # Log excerpt should be a string
    local log_type=$(echo "$output" | jq -r '.log_excerpt | type')
    assert_equal "$log_type" "string"
}

@test "context builder includes metadata" {
    run python3 lib/context_builder.py
    assert_success
    
    # Check metadata
    echo "$output" | jq -e '.context_metadata.context_version' > /dev/null
    echo "$output" | jq -e '.context_metadata.extraction_time' > /dev/null
    echo "$output" | jq -e '.context_metadata.builder_version' > /dev/null
}

@test "context builder limits log excerpt size" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_LOG_LINES="10"
    
    run python3 lib/context_builder.py
    assert_success
    
    # Log excerpt should be limited in size
    local log_content=$(echo "$output" | jq -r '.log_excerpt')
    local char_count=${#log_content}
    
    # Should be reasonable size (less than 15000 chars for 10 lines)
    [[ $char_count -lt 15000 ]]
}

@test "context builder handles custom context" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_CUSTOM_CONTEXT="This is custom context for testing"
    
    run python3 lib/context_builder.py
    assert_success
    
    # Should include custom context
    local custom=$(echo "$output" | jq -r '.custom_context')
    assert_equal "$custom" "This is custom context for testing"
}

@test "context builder sanitizes sensitive information" {
    export TEST_SECRET="secret-value-123"
    export TEST_PASSWORD="password-456"
    
    run python3 lib/context_builder.py
    assert_success
    
    # Sensitive values should not appear in output
    refute_output --partial "secret-value-123"
    refute_output --partial "password-456"
}

@test "context builder handles errors gracefully" {
    # Stub python to fail on certain operations
    stub git 'diff --stat HEAD~1 HEAD : exit 1'
    
    run python3 lib/context_builder.py
    assert_success
    
    # Should still produce valid JSON even with git errors
    echo "$output" | jq . > /dev/null
    
    unstub git
}

@test "context builder produces consistent output structure" {
    run python3 lib/context_builder.py
    assert_success
    
    # Verify all expected top-level keys exist
    local expected_keys=(
        "build_info"
        "error_info" 
        "log_excerpt"
        "environment"
        "pipeline_info"
        "git_info"
        "timing_info"
        "custom_context"
        "context_metadata"
    )
    
    for key in "${expected_keys[@]}"; do
        echo "$output" | jq -e ".${key}" > /dev/null
    done
}