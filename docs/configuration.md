# Configuration Guide

Complete configuration reference for the AI Error Analysis Buildkite Plugin.

## Table of Contents

- [Basic Configuration](#basic-configuration)
- [AI Provider Configuration](#ai-provider-configuration)
- [Trigger Configuration](#trigger-configuration)
- [Context Configuration](#context-configuration)
- [Security Configuration](#security-configuration)
- [Output Configuration](#output-configuration)
- [Performance Configuration](#performance-configuration)
- [Advanced Configuration](#advanced-configuration)
- [Environment Variables](#environment-variables)

## Basic Configuration

### Zero Configuration (Recommended)

The plugin works out of the box with minimal setup:

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0: ~
```

Just set your AI provider API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Basic Configuration

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Use different AI model
          ai_providers:
            - name: openai
              model: gpt-4o
          
          # Only analyze failures on main branch
          conditions:
            branches: ["main"]
```

## AI Provider Configuration

### Single Provider

```yaml
ai_providers:
  - name: openai
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY  # Default: {PROVIDER}_API_KEY
    max_tokens: 1000             # Default: 1000
    timeout: 60                  # Default: 60 seconds
```

### Multiple Providers with Fallback

```yaml
ai_providers:
  - name: openai
    model: gpt-4o-mini
    api_key_env: OPENAI_API_KEY
  - name: claude
    model: claude-3-haiku-20240307
    api_key_env: ANTHROPIC_API_KEY
  - name: gemini
    model: gemini-1.5-flash
    api_key_env: GOOGLE_API_KEY

performance:
  fallback_strategy: priority  # priority, round_robin, fail_fast
```

### Supported Providers

| Provider | Models | API Key Env | Notes |
|----------|--------|-------------|-------|
| **OpenAI** | `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo` | `OPENAI_API_KEY` | Most popular, good balance |
| **Claude** | `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`, `claude-3-opus-20240229` | `ANTHROPIC_API_KEY` | Excellent reasoning |
| **Gemini** | `gemini-1.5-flash`, `gemini-1.5-pro` | `GOOGLE_API_KEY` | Fast and cost-effective |

### Custom Endpoints

```yaml
ai_providers:
  - name: openai
    model: gpt-4o-mini
    endpoint: https://your-proxy.example.com/v1/chat/completions
    api_key_env: CUSTOM_API_KEY
```

## Trigger Configuration

### Trigger Modes

```yaml
trigger: auto  # auto (default), explicit, always
```

- **`auto`**: Analyze only on command failures (recommended)
- **`explicit`**: Only analyze when explicitly configured
- **`always`**: Analyze all commands, regardless of success/failure

### Conditions

```yaml
conditions:
  # Exit codes that trigger analysis
  exit_status: [1, 2, 125, 126, 127, 128, 130]
  
  # Branches to analyze (empty = all branches)
  branches: ["main", "develop", "release/*"]
  
  # Log patterns that trigger analysis
  patterns: ["ERROR", "FAILED", "Exception", "fatal:", "panic:"]
```

### Advanced Triggering

```yaml
# Only analyze critical branches
conditions:
  branches: ["main", "production"]
  exit_status: [1, 2]

# Custom error patterns
conditions:
  patterns:
    - "BUILD FAILED"
    - "Test suite failed"
    - "Compilation error"
```

## Context Configuration

### Basic Context

```yaml
context:
  log_lines: 500                    # Number of log lines to analyze
  include_environment: true         # Include safe environment variables
  include_pipeline_info: true       # Include pipeline metadata
  include_git_info: true           # Include git information
  custom_context: "Additional context for AI analysis"
```

### Advanced Context

```yaml
context:
  log_lines: 1000
  include_environment: true
  include_pipeline_info: true
  include_git_info: true
  custom_context: |
    This is a Node.js microservice that:
    - Connects to PostgreSQL database
    - Uses Redis for caching
    - Deployed via Docker containers
    - Critical for payment processing
```

## Security Configuration

### Basic Redaction

```yaml
redaction:
  redact_file_paths: true    # Redact user paths
  redact_urls: true          # Redact credentials in URLs
```

### Custom Redaction Patterns

```yaml
redaction:
  redact_file_paths: true
  redact_urls: true
  custom_patterns:
    - "(?i)company[_-]?secret[\\s]*[=:]+[\\s]*[^\\s]+"
    - "(?i)internal[_-]?token[\\s]*[=:]+[\\s]*[^\\s]+"
    - "(?i)database[_-]?url[\\s]*[=:]+[\\s]*[^\\s]+"
```

### Security Best Practices

```yaml
redaction:
  custom_patterns:
    # Organization-specific secrets
    - "(?i)acme[_-]?api[_-]?key[\\s]*[=:]+[\\s]*[^\\s]+"
    - "(?i)internal[_-]?webhook[\\s]*[=:]+[\\s]*[^\\s]+"
    
    # Database connections
    - "mongodb://[^\\s]+"
    - "redis://[^\\s]+"
    
    # Custom tokens
    - "Bearer [a-zA-Z0-9._-]+"
    - "token=[a-zA-Z0-9._-]+"
```

## Output Configuration

### Basic Output

```yaml
output:
  annotation_style: error        # error, warning, info, success
  annotation_context: ai-error-analysis
  include_confidence: true
```

### Advanced Output

```yaml
output:
  annotation_style: warning
  annotation_context: custom-ai-analysis
  include_confidence: true
  save_as_artifact: true
  artifact_path: analysis-reports/error-analysis.json
```

### Annotation Styles

| Style | Use Case | Color |
|-------|----------|--------|
| `error` | Build failures (default) | Red |
| `warning` | Non-critical issues | Orange |
| `info` | Informational analysis | Blue |
| `success` | Fixed issues | Green |

## Performance Configuration

### Basic Performance

```yaml
performance:
  timeout: 120                  # Total analysis timeout (seconds)
  async_execution: false        # Run analysis in background
  cache_enabled: true          # Enable result caching
  cache_ttl: 3600             # Cache time-to-live (seconds)
```

### Advanced Performance

```yaml
performance:
  timeout: 300
  async_execution: true
  cache_enabled: true
  cache_ttl: 7200
  fallback_strategy: priority
```

### Cost Optimization

```yaml
performance:
  # Enable caching to reduce API calls
  cache_enabled: true
  cache_ttl: 3600
  
  # Use faster, cheaper models
ai_providers:
  - name: openai
    model: gpt-4o-mini          # Cheaper than gpt-4o
  - name: gemini
    model: gemini-1.5-flash     # Very cost-effective

context:
  log_lines: 300               # Reduce context size
```

## Advanced Configuration

### Debug Mode

```yaml
advanced:
  debug_mode: true             # Enable detailed logging
  dry_run: false              # Test without API calls
  max_retries: 3              # Retry attempts on failure
```

### Custom Prompts

```yaml
advanced:
  custom_prompts:
    default: |
      You are a senior DevOps engineer. Analyze this build failure and provide:
      1. Root cause analysis
      2. Step-by-step fix instructions
      3. Prevention strategies
    
    compilation_error: |
      Focus on compilation issues. Analyze:
      1. Syntax errors and missing imports
      2. Dependency version conflicts
      3. Configuration issues
    
    test_failure: |
      Focus on test failures. Analyze:
      1. Assertion failures and test logic
      2. Environment setup issues
      3. Data dependencies
    
    deployment_error: |
      Focus on deployment issues. Analyze:
      1. Infrastructure problems
      2. Permission and access issues
      3. Network connectivity
```

### Rate Limiting

```yaml
advanced:
  rate_limit:
    requests_per_minute: 30
    burst_limit: 10
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | `sk-proj-abc123...` |
| `ANTHROPIC_API_KEY` | Claude API key | `sk-ant-abc123...` |
| `GOOGLE_API_KEY` | Gemini API key | `AIza123...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_ERROR_ANALYSIS_CACHE_DIR` | Cache directory | `/tmp/ai-error-analysis-cache` |
| `AI_ERROR_ANALYSIS_TEMP_DIR` | Temporary files | `/tmp/ai-error-analysis-temp` |
| `AI_ERROR_ANALYSIS_DEBUG` | Debug logging | `false` |

### Buildkite Variables Used

The plugin automatically uses these Buildkite environment variables:

| Variable | Purpose |
|----------|---------|
| `BUILDKITE_COMMAND_EXIT_STATUS` | Detect failures |
| `BUILDKITE_COMMAND` | Command that failed |
| `BUILDKITE_BUILD_ID` | Build identification |
| `BUILDKITE_PIPELINE_SLUG` | Pipeline context |
| `BUILDKITE_BRANCH` | Git branch |
| `BUILDKITE_COMMIT` | Git commit hash |
| `BUILDKITE_BUILD_AUTHOR` | Commit author |

## Complete Example

```yaml
steps:
  - label: "🧪 Run Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Multiple AI providers
          ai_providers:
            - name: openai
              model: gpt-4o-mini
              max_tokens: 1000
            - name: claude
              model: claude-3-haiku-20240307
              max_tokens: 1000
          
          # Trigger conditions
          trigger: auto
          conditions:
            exit_status: [1, 2]
            branches: ["main", "develop"]
          
          # Context gathering
          context:
            log_lines: 500
            include_environment: true
            include_pipeline_info: true
            include_git_info: true
            custom_context: "Node.js service with PostgreSQL"
          
          # Security
          redaction:
            redact_file_paths: true
            redact_urls: true
            custom_patterns:
              - "(?i)database[_-]?url[\\s]*[=:]+[\\s]*[^\\s]+"
          
          # Output
          output:
            annotation_style: error
            include_confidence: true
            save_as_artifact: true
            artifact_path: "reports/ai-analysis.json"
          
          # Performance
          performance:
            timeout: 120
            cache_enabled: true
            cache_ttl: 3600
            fallback_strategy: priority
          
          # Advanced
          advanced:
            debug_mode: false
            max_retries: 3
            custom_prompts:
              test_failure: |
                Analyze this test failure in a Node.js application.
                Focus on common issues like async/await problems,
                database connections, and environment setup.
```

## Troubleshooting Configuration

### Common Issues

1. **No analysis triggered**
   ```yaml
   # Check exit status configuration
   conditions:
     exit_status: [1, 2, 125, 126, 127, 128, 130]
   ```

2. **Analysis too slow**
   ```yaml
   # Reduce context and enable async
   context:
     log_lines: 200
   performance:
     async_execution: true
   ```

3. **API costs too high**
   ```yaml
   # Enable caching and use cheaper models
   ai_providers:
     - name: gemini
       model: gemini-1.5-flash
   performance:
     cache_enabled: true
   ```

### Validation

Use dry run mode to test configuration:

```yaml
advanced:
  dry_run: true
  debug_mode: true
```