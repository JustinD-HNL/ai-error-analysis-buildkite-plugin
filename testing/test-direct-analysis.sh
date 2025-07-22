#!/bin/bash
set -euo pipefail

echo "Testing direct AI analysis..."

# Create test context
cat > /tmp/test-context.json << 'EOF'
{
  "build_info": {
    "build_id": "test-123",
    "build_number": "123",
    "pipeline_name": "Test Pipeline",
    "step_key": "test-postgres",
    "pipeline": "test-pipeline",
    "branch": "main",
    "command": "psql -h nonexistent.postgres.server -U testuser -d testdb -c 'SELECT 1'",
    "exit_status": 1
  },
  "error_info": {
    "exit_code": 1,
    "command": "psql -h nonexistent.postgres.server -U testuser -d testdb -c 'SELECT 1'",
    "error_category": "general_failure"
  },
  "git_info": {
    "branch": "main",
    "commit": "abc123def456",
    "author": "Test User"
  },
  "pipeline_info": {
    "pipeline": "test-pipeline",
    "pipeline_name": "Test Pipeline"
  },
  "log_excerpt": "Testing database connection... psql: error: connection to server at nonexistent.postgres.server (192.168.1.100), port 5432 failed: Connection refused Is the server running on that host and accepting TCP/IP connections? psql: error: could not connect to server: No such file or directory Is the server running locally and accepting connections on Unix domain socket /var/run/postgresql/.s.PGSQL.5432? Error: Database connection failed FATAL: Unable to establish connection to PostgreSQL server"
}
EOF

# Copy to container and run analysis
docker cp /tmp/test-context.json buildkite-agent-ai-analysis:/tmp/test-context.json

docker exec buildkite-agent-ai-analysis bash -c "
  # Set up environment
  export AI_ERROR_ANALYSIS_API_KEY=\$ANTHROPIC_API_KEY
  export AI_DEBUG=true
  
  cd /buildkite/plugins/ai-error-analysis
  
  # Run analysis
  python3 lib/analyze.py \
    --provider anthropic \
    --model claude-3-opus-20240229 \
    --max-tokens 1000 \
    --input /tmp/test-context.json \
    --output /tmp/test-analysis-result.json
  
  echo '--- Analysis Result ---'
  cat /tmp/test-analysis-result.json | jq '.'
"