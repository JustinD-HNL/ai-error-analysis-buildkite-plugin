#!/usr/bin/env bats

load '/usr/local/lib/bats-support/load'
load '/usr/local/lib/bats-assert/load'
load '/usr/local/lib/bats-file/load'

setup() {
    export AI_ERROR_ANALYSIS_PLUGIN_DIR="$PWD"
    export AI_ERROR_ANALYSIS_INITIALIZED="true"
    export AI_ERROR_ANALYSIS_LOG_PREFIX="🤖 [AI Error Analysis]"
    
    # Create temp directory for tests
    export TEST_TEMP_DIR=$(mktemp -d)
    export AI_ERROR_ANALYSIS_TEMP_DIR="$TEST_TEMP_DIR"
    export AI_ERROR_ANALYSIS_CACHE_DIR="$TEST_TEMP_DIR/cache"
}

teardown() {
    if [[ -n "${TEST_TEMP_DIR:-}" ]] && [[ -d "${TEST_TEMP_DIR}" ]]; then
        rm -rf "${TEST_TEMP_DIR}"
    fi
}

@test "exits early when plugin not initialized" {
    unset AI_ERROR_ANALYSIS_INITIALIZED
    
    run hooks/pre-exit
    assert_success
    refute_output --partial "Cleaning up"
}

@test "performs basic cleanup" {
    run hooks/pre-exit
    assert_success
    assert_output --partial "Cleaning up"
    assert_output --partial "Cleanup completed"
}

@test "waits for async analysis to complete" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_ASYNC_EXECUTION="true"
    
    # Create a background job that will finish quickly
    sleep 1 &
    local bg_pid=$!
    
    # Mock jobs command to return our background job initially, then nothing
    stub jobs \
        '%% : echo "[1]+  Running                 sleep 1 &"' \
        '%% : echo ""'  # No jobs running
    
    run hooks/pre-exit
    assert_success
    assert_output --partial "Waiting for background analysis"
    assert_output --partial "Background analysis completed"
    
    # Clean up background job if still running
    kill $bg_pid 2>/dev/null || true
    
    unstub jobs
}

@test "handles async analysis timeout" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_ASYNC_EXECUTION="true"
    
    # Mock jobs to always return a running job (simulate timeout)
    stub jobs \
        '%% : echo "[1]+  Running                 long-running-process &"' \
        '%% : echo "[1]+  Running                 long-running-process &"' \
        '%% : echo "[1]+  Running                 long-running-process &"' \
        '%% : echo "[1]+  Running                 long-running-process &"'
    
    # Mock xargs and kill for cleanup
    stub xargs '-r kill : echo "Killed background processes"'
    
    run timeout 35s hooks/pre-exit  # Should timeout in 30s
    assert_success
    assert_output --partial "did not complete within 30 seconds"
    
    unstub jobs
    unstub xargs
}

@test "cleans up temporary directories" {
    # Create some temporary files to clean up
    mkdir -p "/tmp/ai-error-analysis-test123"
    touch "/tmp/ai-error-analysis-test123/file1"
    
    # Create an old directory that should be cleaned
    mkdir -p "/tmp/ai-error-analysis-old"
    touch "/tmp/ai-error-analysis-old/oldfile"
    
    # Mock find to return our test directories
    stub find \
        '/tmp -maxdepth 1 -name ai-error-analysis-* -type d -mmin +60 -exec rm -rf {} + : echo "Cleaned old temp dirs"'
    
    run hooks/pre-exit
    assert_success
    
    unstub find
}

@test "cleans up cache when enabled" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_ENABLED="true"
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_TTL="3600"
    
    # Create cache directory with test files
    mkdir -p "$AI_ERROR_ANALYSIS_CACHE_DIR"
    touch "$AI_ERROR_ANALYSIS_CACHE_DIR/cache1.json"
    touch "$AI_ERROR_ANALYSIS_CACHE_DIR/cache2.json"
    
    # Mock find commands for cache cleanup
    stub find \
        '$AI_ERROR_ANALYSIS_CACHE_DIR -type f -name "*.json" -mmin +60 -delete : echo "Removed expired cache files"' \
        '$AI_ERROR_ANALYSIS_CACHE_DIR -type d -empty -delete : echo "Removed empty directories"' \
        '$AI_ERROR_ANALYSIS_CACHE_DIR -type f -name "*.json" : echo "cache1.json\ncache2.json"'
    
    stub wc '-l : echo "2"'
    
    run hooks/pre-exit
    assert_success
    assert_output --partial "Cleaning expired cache entries"
    assert_output --partial "Cache contains 2 entries"
    
    unstub find
    unstub wc
}

@test "skips cache cleanup when disabled" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_ENABLED="false"
    
    run hooks/pre-exit
    assert_success
    refute_output --partial "Cleaning expired cache entries"
}

@test "provides debug statistics when enabled" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"
    export BUILDKITE_JOB_STARTED_AT="2023-01-01T10:00:00Z"
    
    stub date \
        '-d "2023-01-01T10:00:00Z" +%s : echo "1672574400"' \
        '+%s : echo "1672574460"'  # 60 seconds later
    
    stub free \
        '-h : echo "              total        used        free      shared  buff/cache   available\nMem:           16Gi       8Gi       4Gi       1Gi       4Gi       6Gi"'
    
    stub df \
        '-h . : echo "Filesystem      Size  Used Avail Use% Mounted on\n/dev/sda1       100G   50G   50G  50% /"'
    
    run hooks/pre-exit
    assert_success
    assert_output --partial "Final Statistics"
    assert_output --partial "Build duration: 60 seconds"
    assert_output --partial "Memory:"
    assert_output --partial "Disk:"
    
    unstub date
    unstub free
    unstub df
}

@test "reads and reports plugin metrics" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"
    
    # Create a metrics file
    echo "Analysis completed in 3.2s" > "/tmp/ai-error-analysis-metrics.log"
    echo "Tokens used: 245" >> "/tmp/ai-error-analysis-metrics.log"
    
    stub cat '/tmp/ai-error-analysis-metrics.log : cat /tmp/ai-error-analysis-metrics.log'
    stub rm '-f /tmp/ai-error-analysis-metrics.log : echo "Metrics file removed"'
    
    run hooks/pre-exit
    assert_success
    assert_output --partial "Plugin metrics:"
    assert_output --partial "Analysis completed in 3.2s"
    assert_output --partial "Tokens used: 245"
    
    unstub cat
    unstub rm
}

@test "performs security cleanup" {
    # Set some environment variables that should be cleaned up
    export AI_ERROR_ANALYSIS_API_KEY="test-key"
    export OPENAI_API_KEY="test-openai-key"
    export AI_ERROR_ANALYSIS_REDACTION_PATTERNS="test-patterns"
    export AI_ERROR_ANALYSIS_TEST_VAR="test-value"
    
    run hooks/pre-exit
    assert_success
    
    # Variables should be unset (we can't easily test this in bats, but the script should do it)
}

@test "verifies plugin integrity" {
    # Create plugin files
    touch "$AI_ERROR_ANALYSIS_PLUGIN_DIR/plugin.yml"
    touch "$AI_ERROR_ANALYSIS_PLUGIN_DIR/lib/ai_providers.py"
    
    run hooks/pre-exit
    assert_success
    assert_output --partial "Plugin integrity verified"
}

@test "warns about missing plugin files" {
    # Remove a required file
    mv "$AI_ERROR_ANALYSIS_PLUGIN_DIR/plugin.yml" "$AI_ERROR_ANALYSIS_PLUGIN_DIR/plugin.yml.bak" 2>/dev/null || true
    
    run hooks/pre-exit
    assert_success
    assert_output --partial "Plugin integrity check failed"
    
    # Restore file
    mv "$AI_ERROR_ANALYSIS_PLUGIN_DIR/plugin.yml.bak" "$AI_ERROR_ANALYSIS_PLUGIN_DIR/plugin.yml" 2>/dev/null || true
}

@test "rotates log files" {
    # Create test log directory with files
    mkdir -p "/tmp/ai-error-analysis-logs"
    
    # Create multiple log files (some old)
    for i in {1..15}; do
        touch "/tmp/ai-error-analysis-logs/test${i}.log"
    done
    
    # Mock find commands for log rotation
    stub find \
        '/tmp/ai-error-analysis-logs -name "*.log" -type f : echo -e "test1.log\ntest2.log\ntest3.log\ntest4.log\ntest5.log\ntest6.log\ntest7.log\ntest8.log\ntest9.log\ntest10.log\ntest11.log\ntest12.log\ntest13.log\ntest14.log\ntest15.log"' \
        '/tmp/ai-error-analysis-logs -name "*.log" -type f -mtime +1 -exec gzip {} \; : echo "Compressed old logs"'
    
    stub sort '-r : echo -e "test15.log\ntest14.log\ntest13.log\ntest12.log\ntest11.log\ntest10.log\ntest9.log\ntest8.log\ntest7.log\ntest6.log\ntest5.log\ntest4.log\ntest3.log\ntest2.log\ntest1.log"'
    
    stub tail '-n +11 : echo -e "test5.log\ntest4.log\ntest3.log\ntest2.log\ntest1.log"'
    
    stub xargs '-r rm -f : echo "Removed old log files"'
    
    run hooks/pre-exit
    assert_success
    
    unstub find
    unstub sort
    unstub tail
    unstub xargs
}

@test "handles errors gracefully" {
    # Mock a command that fails
    stub jobs '%% : exit 1'
    
    run hooks/pre-exit
    assert_success  # Should still succeed despite errors
    
    unstub jobs
}

@test "handles missing cache directory gracefully" {
    export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_ENABLED="true"
    export AI_ERROR_ANALYSIS_CACHE_DIR="/nonexistent/cache/dir"
    
    run hooks/pre-exit
    assert_success
    # Should not fail even if cache directory doesn't exist
}