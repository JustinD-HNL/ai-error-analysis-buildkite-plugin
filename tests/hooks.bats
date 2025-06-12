#!/usr/bin/env bats
# AI Error Analysis Buildkite Plugin - Integration Tests (2025)

load '/usr/local/lib/bats-support/load'
load '/usr/local/lib/bats-assert/load'
load '/usr/local/lib/bats-file/load'

setup() {
    export PLUGIN_DIR="$PWD"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG="true"
    
    # Mock Buildkite environment
    export BUILDKITE_BUILD_ID="test-build-123"
    export BUILDKITE_BUILD_NUMBER="42"
    export BUILDKITE_PIPELINE_SLUG="test-pipeline"
    export BUILDKITE_STEP_KEY="test-step"
    export BUILDKITE_BRANCH="main"
    export BUILDKITE_COMMIT="abc123def456"
    export BUILDKITE_COMMAND="npm test"
    export BUILDKITE_COMMAND_EXIT_STATUS="1"
    
    # Test configuration
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER="openai"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL="GPT-4o mini"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MAX_TOKENS="1000"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ENABLE_CACHING="true"
    
    # External secret configuration (mock)
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_TYPE="env_var"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_API_KEY_ENV="OPENAI_API_KEY"
    export OPENAI_API_KEY="sk-test-key-for-testing"
    
    # Create temp directory
    export TEST_TEMP_DIR=$(mktemp -d)
}

teardown() {
    if [[ -n "${TEST_TEMP_DIR:-}" ]] && [[ -d "${TEST_TEMP_DIR}" ]]; then
        rm -rf "${TEST_TEMP_DIR}"
    fi
}

@test "environment hook validates Python 3.10+" {
    # Mock Python version check
    stub python3 \
        '--version : echo "Python 3.12.0"' \
        '-c "import sys; print(\".\".join(map(str, sys.version_info[:2])))" : echo "3.12"'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    
    run hooks/environment
    assert_success
    assert_output --partial "Python 3.12 detected"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "environment hook fails with old Python" {
    # Mock old Python version
    stub python3 \
        '--version : echo "Python 3.9.0"' \
        '-c "import sys; print(\".\".join(map(str, sys.version_info[:2])))" : echo "3.9"'
    
    run hooks/environment
    assert_failure
    assert_output --partial "Python 3.10 or later is required"
    
    unstub python3
}

@test "environment hook validates supported AI providers" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER="unsupported_provider"
    
    stub python3 \
        '--version : echo "Python 3.12.0"' \
        '-c "import sys; print(\".\".join(map(str, sys.version_info[:2])))" : echo "3.12"'
    
    run hooks/environment
    assert_failure
    assert_output --partial "Unsupported provider"
    
    unstub python3
}

@test "environment hook validates 2025 model names" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL="gpt-4.1"  # Invalid 2025 model
    
    stub python3 \
        '--version : echo "Python 3.12.0"' \
        '-c "import sys; print(\".\".join(map(str, sys.version_info[:2])))" : echo "3.12"'
    
    stub curl '--version : echo "curl 7.68.0"'
    stub jq '--version : echo "jq-1.6"'
    
    run hooks/environment
    assert_failure
    assert_output --partial "Invalid model name"
    
    unstub python3
    unstub curl
    unstub jq
}

@test "post-command skips analysis on success" {
    export BUILDKITE_COMMAND_EXIT_STATUS="0"
    
    run hooks/post-command
    assert_success
    assert_output --partial "Command succeeded, skipping analysis"
}

@test "post-command requires provider configuration" {
    unset BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER
    
    run hooks/post-command
    assert_failure
    assert_output --partial "AI provider not specified"
}

@test "post-command validates provider" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER="invalid_provider"
    
    run hooks/post-command
    assert_failure
    assert_output --partial "Unsupported provider: invalid_provider"
}

@test "post-command handles AWS Secrets Manager" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_TYPE="aws_secrets_manager"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_SECRET_NAME="buildkite/openai-key"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_REGION="us-east-1"
    
    # Mock AWS CLI
    stub aws \
        'secretsmanager get-secret-value --secret-id buildkite/openai-key --region us-east-1 --query SecretString --output text : echo "sk-test-secret-key"'
    
    # Mock Python analysis components
    stub python3 \
        'lib/sanitizer.py * * : echo "Log sanitization completed" && touch "$2"' \
        'lib/analyze.py --provider openai --model "GPT-4o mini" --max-tokens 1000 --input * --output * : echo "AI analysis completed" && echo "{\"provider\":\"openai\",\"analysis\":{\"root_cause\":\"test\"}}" > "$8"' \
        'lib/report.py * : echo "<div>Test report</div>"'
    
    # Mock buildkite-agent
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "Annotation created"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Retrieving API key from AWS Secrets Manager"
    assert_output --partial "Analysis completed successfully"
    
    unstub aws
    unstub python3
    unstub buildkite-agent
}

@test "post-command handles Vault secrets" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_TYPE="vault"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_VAULT_PATH="secret/buildkite/openai"
    
    # Mock Vault CLI
    stub vault \
        'kv get -mount=secret -field=api_key secret/buildkite/openai : echo "sk-vault-secret-key"'
    
    # Mock Python components
    stub python3 \
        'lib/sanitizer.py * * : echo "Log sanitization completed" && touch "$2"' \
        'lib/analyze.py --provider openai --model "GPT-4o mini" --max-tokens 1000 --input * --output * : echo "AI analysis completed" && echo "{\"provider\":\"openai\",\"analysis\":{\"root_cause\":\"test\"}}" > "$8"' \
        'lib/report.py * : echo "<div>Test report</div>"'
    
    # Mock buildkite-agent
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "Annotation created"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Retrieving API key from HashiCorp Vault"
    assert_output --partial "Analysis completed successfully"
    
    unstub vault
    unstub python3
    unstub buildkite-agent
}

@test "post-command handles GCP Secret Manager" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_TYPE="gcp_secret_manager"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_PROJECT_ID="test-project"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECRET_SOURCE_SECRET_NAME="openai-key"
    
    # Mock gcloud CLI
    stub gcloud \
        'secrets versions access latest --secret=openai-key --project=test-project : echo "sk-gcp-secret-key"'
    
    # Mock Python components
    stub python3 \
        'lib/sanitizer.py * * : echo "Log sanitization completed" && touch "$2"' \
        'lib/analyze.py --provider openai --model "GPT-4o mini" --max-tokens 1000 --input * --output * : echo "AI analysis completed" && echo "{\"provider\":\"openai\",\"analysis\":{\"root_cause\":\"test\"}}" > "$8"' \
        'lib/report.py * : echo "<div>Test report</div>"'
    
    # Mock buildkite-agent
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "Annotation created"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Retrieving API key from Google Secret Manager"
    assert_output --partial "Analysis completed successfully"
    
    unstub gcloud
    unstub python3
    unstub buildkite-agent
}

@test "post-command handles analysis failure gracefully" {
    # Mock Python analysis to fail
    stub python3 \
        'lib/sanitizer.py * * : echo "Log sanitization completed" && touch "$2"' \
        'lib/analyze.py --provider openai --model "GPT-4o mini" --max-tokens 1000 --input * --output * : echo "AI analysis failed" && exit 1'
    
    # Mock buildkite-agent for fallback annotation
    stub buildkite-agent \
        'annotate --style warning --context ai-error-analysis-fallback : echo "Fallback annotation created"'
    
    run hooks/post-command
    assert_success  # Should not fail the build
    assert_output --partial "AI analysis failed"
    assert_output --partial "Fallback annotation created"
    
    unstub python3
    unstub buildkite-agent
}

@test "post-command enforces container security" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_RUN_AS_NON_ROOT="true"
    
    # Mock running as root (UID 0)
    stub id '-u : echo "0"'
    
    run hooks/post-command
    assert_failure
    assert_output --partial "Security violation: Running as root user not allowed"
    
    unstub id
}

@test "post-command validates configuration values" {
    # Test injection attempt in provider name
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER="openai; rm -rf /"
    
    run hooks/post-command
    assert_failure
    assert_output --partial "Invalid characters in configuration"
}

@test "post-command handles timeout correctly" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_TIMEOUT_SECONDS="5"
    
    # Mock slow Python analysis
    stub timeout \
        '5 python3 lib/analyze.py --provider openai --model "GPT-4o mini" --max-tokens 1000 --input * --output * : sleep 10'
    
    stub python3 \
        'lib/sanitizer.py * * : echo "Log sanitization completed" && touch "$2"'
    
    run hooks/post-command
    assert_success  # Should handle timeout gracefully
    assert_output --partial "Analysis timed out"
    
    unstub timeout
    unstub python3
}

@test "post-command creates artifact when configured" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_OUTPUT_SAVE_ARTIFACT="true"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_OUTPUT_ARTIFACT_PATH="test-analysis.json"
    
    # Mock Python components
    stub python3 \
        'lib/sanitizer.py * * : echo "Log sanitization completed" && touch "$2"' \
        'lib/analyze.py --provider openai --model "GPT-4o mini" --max-tokens 1000 --input * --output * : echo "AI analysis completed" && echo "{\"provider\":\"openai\",\"analysis\":{\"root_cause\":\"test\"}}" > "$8"' \
        'lib/report.py * : echo "<div>Test report</div>"'
    
    stub buildkite-agent \
        'annotate --style error --context ai-error-analysis : echo "Annotation created"'
    
    run hooks/post-command
    assert_success
    assert_output --partial "Analysis saved as artifact: test-analysis.json"
    assert_file_exists "test-analysis.json"
    
    unstub python3
    unstub buildkite-agent
}

@test "log sanitizer removes 2025 API key patterns" {
    # Create test input with 2025 API key patterns
    echo '{
        "log_excerpt": "Using API key sk-proj-abc123T3BlbkFJdef456 for OpenAI access",
        "build_info": {"command": "export ANTHROPIC_API_KEY=sk-ant-api03-xyz789"}
    }' > "${TEST_TEMP_DIR}/test_input.json"
    
    run python3 lib/sanitizer.py "${TEST_TEMP_DIR}/test_input.json" "${TEST_TEMP_DIR}/test_output.json"
    assert_success
    assert_output --partial "Sanitization complete"
    
    # Verify API keys were redacted
    run cat "${TEST_TEMP_DIR}/test_output.json"
    refute_output --partial "sk-proj-abc123T3BlbkFJdef456"
    refute_output --partial "sk-ant-api03-xyz789"
    assert_output --partial "[REDACTED_OPENAI_KEY]"
    assert_output --partial "[REDACTED_ANTHROPIC_KEY]"
}

@test "analysis engine validates 2025 model names" {
    echo '{"build_info": {"command": "npm test", "exit_status": 1}, "log_excerpt": "Test failed"}' > "${TEST_TEMP_DIR}/context.json"
    
    # Test with invalid 2025 model name
    run python3 lib/analyze.py --provider openai --model "gpt-4.1" --input "${TEST_TEMP_DIR}/context.json" --output "${TEST_TEMP_DIR}/result.json"
    assert_failure
    assert_output --partial "Unsupported model"
}

@test "analysis engine maps legacy model names to 2025 standards" {
    echo '{"build_info": {"command": "npm test", "exit_status": 1}, "log_excerpt": "Test failed"}' > "${TEST_TEMP_DIR}/context.json"
    
    # Mock successful API call for legacy model name
    export AI_ERROR_ANALYSIS_API_KEY="sk-test-key"
    
    # This would require mocking the HTTP request, which is complex in BATS
    # In practice, this test would verify the model name mapping in unit tests
    skip "Model name mapping tested in Python unit tests"
}

# Helper function to mock buildkite-agent command
mock_buildkite_agent() {
    export PATH="${TEST_TEMP_DIR}/bin:${PATH}"
    mkdir -p "${TEST_TEMP_DIR}/bin"
    
    cat > "${TEST_TEMP_DIR}/bin/buildkite-agent" << 'EOF'
#!/bin/bash
echo "Mock buildkite-agent called with: $*" >&2
case "$1" in
    "annotate")
        echo "Mock annotation created" >&2
        ;;
    *)
        echo "Unknown buildkite-agent command: $1" >&2
        exit 1
        ;;
esac
EOF
    
    chmod +x "${TEST_TEMP_DIR}/bin/buildkite-agent"
}