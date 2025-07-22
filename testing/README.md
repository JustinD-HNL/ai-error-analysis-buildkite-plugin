# Testing Scripts and Pipelines

This directory contains various test scripts and pipeline configurations for testing the AI Error Analysis Buildkite Plugin.

## Test Scripts

### `test-analysis.sh`
Basic test script that simulates a PostgreSQL connection error and runs the plugin analysis.

**Usage:**
```bash
./test-analysis.sh
```

### `test-direct-analysis.sh`
Directly tests the Python analysis module without going through the full plugin pipeline. Useful for debugging AI provider responses.

**Usage:**
```bash
./test-direct-analysis.sh
```

### `test-full-pipeline.sh`
Comprehensive test that runs the entire plugin pipeline including:
- Log collection
- Sanitization
- AI analysis
- Report generation

**Usage:**
```bash
./test-full-pipeline.sh
```

## Test Pipeline YAML Files

### Basic Tests

- `simple-test-pipeline.yml` - Minimal test pipeline with a failing command
- `test-pipeline-simple.yml` - Another simple test configuration
- `working-test-pipeline.yml` - Known working pipeline configuration

### Advanced Tests

- `test-claude-pipeline.yml` - Specific test for Claude/Anthropic provider
- `test-pipeline-with-plugin.yml` - Full plugin configuration example
- `test-pipeline-final.yml` - Production-like pipeline configuration
- `no-checkout-test-pipeline.yml` - Pipeline without repository checkout (for testing)

## Running Tests

### Local Testing with Docker

1. Ensure Docker is running and the agent container is up:
```bash
docker compose -f docker-compose.orbstack.yml up -d
```

2. Run a test script:
```bash
cd testing
./test-full-pipeline.sh
```

### Buildkite Pipeline Testing

1. Create a new pipeline in Buildkite
2. Upload one of the test YAML files:
```bash
buildkite-agent pipeline upload testing/test-pipeline-final.yml
```

### Environment Setup

Before running tests, ensure you have:
- `.env` file configured with API keys
- Docker or OrbStack installed
- Buildkite agent running (for pipeline tests)

## Test Scenarios Covered

1. **PostgreSQL Connection Errors** - Database connectivity issues
2. **Build Failures** - Generic command failures
3. **Compilation Errors** - Code build failures
4. **Network Timeouts** - Connection timeout scenarios
5. **Permission Errors** - File access issues

## Debugging Tips

- Enable debug mode: `export AI_DEBUG=true`
- Check container logs: `docker logs buildkite-agent-ai-analysis`
- Clear cache before testing: `docker exec buildkite-agent-ai-analysis find /buildkite/builds -name ".ai-error-analysis-cache" -type d -exec rm -rf {} \;`