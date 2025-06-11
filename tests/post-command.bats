#!/usr/bin/env bats

load '/usr/local/lib/bats-support/load'
load '/usr/local/lib/bats-assert/load'
load '/usr/local/lib/bats-file/load'

# Setup and teardown
setup() {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN="true"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"
    export AI_ERROR_ANALYSIS_PLUGIN_DIR="$PWD"
    export AI_ERROR_ANALYSIS_INITIALIZED="true"
    export AI_ERROR_ANALYSIS_LOG_PREFIX="🤖 [AI Error Analysis]"
    
    # Create temporary directory for tests
    export TEST_TEMP_DIR=$(mktemp -d)
    export AI_ERROR_ANALYSIS_TEMP_DIR="$TEST_TEMP_DIR"
}

teardown() {
    if [[ -n "${TEST_TEMP_DIR:-}" ]] && [[ -d "${TEST_TEMP_DIR}" ]]; then
        rm -rf "${TEST_TEMP_DIR}"
    fi
}

@test "skips analysis when plugin not initialized" {
    unset AI_ERROR_ANALYSIS_INITIALIZED
    
    run hooks/post-command
    assert_success
    assert_output --partial "not properly initialized"
}

@test "skips analysis when explicitly disabled" {
    export AI_ERROR_ANALYSIS_SKIP="true"
    
    run hooks/post-command
    assert_success
    assert_output --partial "skipped for this branch"
}

@test "skips analysis on successful builds" {
    export BUILDKITE_COMMAND_EXIT_STATUS="0"
    
    run hooks/post-command
    assert_success
    assert_output --partial "command succeeded"
}

@test "triggers analysis on build failure" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_COMMAND="npm test"
    
    # Mock the Python scripts to succeed
    stub python3 \
        'lib/error_detector.py : echo "{\"error_detected\":true,\"exit_code\":1,\"patterns\":[],\"error_category\":\"test_failure\"}" > $TEST_TEMP_DIR/error_detection.json' \
        'lib/context_builder.py : echo "{\"build_info\":{},\"error_info\":{\"exit_code\":1}}" > $TEST_TEMP_DIR/context.json' \
        'lib/log_sanitizer.py * * : cp "$2" "$3"' \
        'lib/ai_providers.py * : echo "{\"provider\":\"mock\",\"analysis\":{\"root_cause\":\"test\",\"suggested_fixes\":[\"fix1\"]}}" > $TEST_TEMP_DIR/analysis_result.json' \
        'lib/report_generator.py * * * * : echo "<div>Mock analysis report</div>"'
    
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "Annotation created"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Starting error analysis"
    
    unstub python3
    unstub buildkite-agent
}

@test "handles error detection failure gracefully" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_COMMAND="npm test"
    
    stub python3 \
        'lib/error_detector.py : exit 1'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Error detection failed"
}

@test "handles context building failure gracefully" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_COMMAND="npm test"
    
    stub python3 \
        'lib/error_detector.py : echo "{\"error_detected\":true}" > $TEST_TEMP_DIR/error_detection.json' \
        'lib/context_builder.py : exit 1'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Context building failed"
}

@test "respects exit code configuration" {
    export BUILDKITE_COMMAND_EXIT_STATUS="42"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONDITIONS_EXIT_STATUS="[42,1]"
    
    stub python3 \
        'lib/error_detector.py : echo "{\"error_detected\":true}" > $TEST_TEMP_DIR/error_detection.json' \
        'lib/context_builder.py : echo "{\"build_info\":{}}" > $TEST_TEMP_DIR/context.json' \
        'lib/log_sanitizer.py * * : cp "$2" "$3"' \
        'lib/ai_providers.py * : echo "{\"provider\":\"mock\",\"analysis\":{}}" > $TEST_TEMP_DIR/analysis_result.json' \
        'lib/report_generator.py * * * * : echo "test"'
    
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "done"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "exit code 42 is in allowed list"
    
    unstub python3
    unstub buildkite-agent
}

@test "handles async execution mode" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_ASYNC_EXECUTION="true"
    
    run hooks/post-command
    assert_success
    assert_output --partial "Running analysis in background"
    assert_output --partial "build will continue"
}

@test "respects trigger mode configuration" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_TRIGGER="explicit"
    
    run hooks/post-command
    assert_success
    assert_output --partial "explicit mode requires manual trigger"
}

@test "always mode triggers on success" {
    export BUILDKITE_COMMAND_EXIT_STATUS="0"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_TRIGGER="always"
    
    stub python3 \
        'lib/error_detector.py : echo "{\"error_detected\":false}" > $TEST_TEMP_DIR/error_detection.json' \
        'lib/context_builder.py : echo "{\"build_info\":{}}" > $TEST_TEMP_DIR/context.json' \
        'lib/log_sanitizer.py * * : cp "$2" "$3"' \
        'lib/ai_providers.py * : echo "{\"provider\":\"mock\",\"analysis\":{}}" > $TEST_TEMP_DIR/analysis_result.json' \
        'lib/report_generator.py * * * * : echo "test"'
    
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "done"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Analysis triggered: always mode"
    
    unstub python3
    unstub buildkite-agent
}

@test "creates fallback annotation on analysis failure" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_MAX_RETRIES="1"
    
    stub python3 \
        'lib/error_detector.py : exit 1' \
        'lib/error_detector.py : exit 1'
    
    stub buildkite-agent \
        'annotate --style warning --context ai-error-analysis-fallback : echo "Fallback annotation created"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Analysis failed after 1 attempts"
    assert_output --partial "Fallback annotation created"
    
    unstub python3
    unstub buildkite-agent
}

@test "handles timeout configuration" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_TIMEOUT="5"
    
    # Mock a slow Python script
    stub timeout \
        '5 python3 lib/ai_providers.py * : exit 124'  # timeout exit code
    
    stub python3 \
        'lib/error_detector.py : echo "{\"error_detected\":true}" > $TEST_TEMP_DIR/error_detection.json' \
        'lib/context_builder.py : echo "{\"build_info\":{}}" > $TEST_TEMP_DIR/context.json' \
        'lib/log_sanitizer.py * * : cp "$2" "$3"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "timed out after 5 seconds"
    
    unstub timeout
    unstub python3
}

@test "generates artifacts when configured" {
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_OUTPUT_SAVE_AS_ARTIFACT="true"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_OUTPUT_ARTIFACT_PATH="test-report.json"
    
    stub python3 \
        'lib/error_detector.py : echo "{\"error_detected\":true}" > $TEST_TEMP_DIR/error_detection.json' \
        'lib/context_builder.py : echo "{\"build_info\":{}}" > $TEST_TEMP_DIR/context.json' \
        'lib/log_sanitizer.py * * : cp "$2" "$3"' \
        'lib/ai_providers.py * : echo "{\"provider\":\"mock\",\"analysis\":{}}" > $TEST_TEMP_DIR/analysis_result.json' \
        'lib/report_generator.py * * * * : echo "test"'
    
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "done"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Analysis saved as artifact: test-report.json"
    assert_file_exists "test-report.json"
    
    unstub python3
    unstub buildkite-agent
}