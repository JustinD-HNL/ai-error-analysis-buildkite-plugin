#!/bin/bash
set -euo pipefail

echo "Testing AI Error Analysis with PostgreSQL connection error..."

# Create test log file
TEST_LOG="/tmp/buildkite.log"
cat > "$TEST_LOG" << 'EOF'
~~~ Running step
Testing database connection...
psql: error: connection to server at "nonexistent.postgres.server" (192.168.1.100), port 5432 failed: Connection refused
    Is the server running on that host and accepting TCP/IP connections?
psql: error: could not connect to server: No such file or directory
    Is the server running locally and accepting
    connections on Unix domain socket "/var/run/postgresql/.s.PGSQL.5432"?
Error: Database connection failed
FATAL: Unable to establish connection to PostgreSQL server
EOF

# Set up environment variables
export BUILDKITE_COMMAND_EXIT_STATUS=1
export BUILDKITE_COMMAND="psql -h nonexistent.postgres.server -U testuser -d testdb -c 'SELECT 1'"
export BUILDKITE_BUILD_ID="test-$(date +%s)-$$"
export BUILDKITE_BUILD_NUMBER="123"
export BUILDKITE_PIPELINE_SLUG="test-pipeline"
export BUILDKITE_PIPELINE_NAME="Test Pipeline"
export BUILDKITE_STEP_KEY="test-postgres"
export BUILDKITE_BRANCH="main"
export BUILDKITE_COMMIT="abc123def456"
export BUILDKITE_BUILD_AUTHOR="Test User"

# Run inside container
docker exec -e BUILDKITE_COMMAND_EXIT_STATUS="$BUILDKITE_COMMAND_EXIT_STATUS" \
  -e BUILDKITE_COMMAND="$BUILDKITE_COMMAND" \
  -e BUILDKITE_BUILD_ID="$BUILDKITE_BUILD_ID" \
  -e BUILDKITE_BUILD_NUMBER="$BUILDKITE_BUILD_NUMBER" \
  -e BUILDKITE_PIPELINE_SLUG="$BUILDKITE_PIPELINE_SLUG" \
  -e BUILDKITE_PIPELINE_NAME="$BUILDKITE_PIPELINE_NAME" \
  -e BUILDKITE_STEP_KEY="$BUILDKITE_STEP_KEY" \
  -e BUILDKITE_BRANCH="$BUILDKITE_BRANCH" \
  -e BUILDKITE_COMMIT="$BUILDKITE_COMMIT" \
  -e BUILDKITE_BUILD_AUTHOR="$BUILDKITE_BUILD_AUTHOR" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER="anthropic" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL="claude-3-opus-20240229" \
  -e BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG="true" \
  buildkite-agent-ai-analysis bash -c "
    # Copy test log
    cp /tmp/buildkite.log.host /tmp/buildkite.log
    
    # Source the .env file to get debug mode
    if [ -f /buildkite/plugins/ai-error-analysis/.env ]; then
      export \$(grep -v '^#' /buildkite/plugins/ai-error-analysis/.env | xargs)
    fi
    
    # Run the post-command hook
    cd /buildkite/plugins/ai-error-analysis
    ./hooks/post-command 2>&1
  "