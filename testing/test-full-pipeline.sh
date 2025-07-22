#!/bin/bash
set -euo pipefail

echo "Testing full AI analysis pipeline..."

# Clear any existing cache
docker exec buildkite-agent-ai-analysis find /buildkite/builds -name ".ai-error-analysis-cache" -type d -exec rm -rf {} \; 2>/dev/null || true

# Create test log file
cat > /tmp/buildkite.log << 'EOF'
~~~ Running step
Testing database connection...
psql: error: connection to server at "nonexistent.postgres.server" (192.168.1.100), port 5432 failed: Connection refused
    Is the server running on that host and accepting TCP/IP connections?
psql: error: could not connect to server: No such file or directory
    Is the server running locally and accepting
    connections on Unix domain socket "/var/run/postgresql/.s.PGSQL.5432"?
Error: Database connection failed
FATAL: Unable to establish connection to PostgreSQL server
Additional error context:
- Connection timeout after 30 seconds
- No route to host
- Previous connection attempt at 2025-07-22 10:30:00 UTC also failed
EOF

# Copy to container
docker cp /tmp/buildkite.log buildkite-agent-ai-analysis:/tmp/buildkite.log.host

# Set up unique build ID to avoid cache
export BUILDKITE_BUILD_ID="test-full-$(date +%s)"

# Run the full pipeline
docker exec \
  -e BUILDKITE_COMMAND_EXIT_STATUS="1" \
  -e BUILDKITE_COMMAND="psql -h nonexistent.postgres.server -U testuser -d testdb -c 'SELECT 1'" \
  -e BUILDKITE_BUILD_ID="$BUILDKITE_BUILD_ID" \
  -e BUILDKITE_BUILD_NUMBER="456" \
  -e BUILDKITE_PIPELINE_SLUG="production-pipeline" \
  -e BUILDKITE_PIPELINE_NAME="Production Database Pipeline" \
  -e BUILDKITE_STEP_KEY="db-migration" \
  -e BUILDKITE_BRANCH="main" \
  -e BUILDKITE_COMMIT="def789abc123" \
  -e BUILDKITE_BUILD_AUTHOR="John Doe" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER="anthropic" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL="claude-3-opus-20240229" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG="false" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ENABLE_CACHING="false" \
  buildkite-agent-ai-analysis bash -c "
    # Copy test log
    cp /tmp/buildkite.log.host /tmp/buildkite.log
    
    # Source the .env file
    if [ -f /buildkite/plugins/ai-error-analysis/.env ]; then
      export \$(grep -v '^#' /buildkite/plugins/ai-error-analysis/.env | xargs)
    fi
    
    # Run the post-command hook
    cd /buildkite/plugins/ai-error-analysis
    ./hooks/post-command 2>&1
    
    echo ''
    echo '=== Generated Markdown Report ==='
    find /tmp -name 'report.md' -mmin -1 -exec cat {} \; 2>/dev/null || echo 'No report found'
  "