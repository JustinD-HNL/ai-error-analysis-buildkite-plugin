# Configuration Guide

Complete configuration reference for the AI Error Analysis Buildkite Plugin.

## Table of Contents

- [Basic Configuration](#basic-configuration)
- [AI Provider Configuration](#ai-provider-configuration)
- [Secret Management](#secret-management)
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
          # Specify AI provider
          provider: openai
          
          # Use specific model (optional)
          model: gpt-4o
          
          # Basic parameters
          max_tokens: 1000
          temperature: 0.1
```

## AI Provider Configuration

### Single Provider (Simple)

```yaml
provider: openai              # Required: openai, anthropic, or gemini
model: gpt-4o-mini           # Optional: Uses provider default if not specified
api_key_env: OPENAI_API_KEY  # Optional: Default is {PROVIDER}_API_KEY
max_tokens: 1000             # Optional: Default 1000 (min: 100, max: 4000)
temperature: 0.1             # Optional: Default 0.1 (min: 0.0, max: 2.0)
```

### Multiple Providers with Fallback

```yaml
# Use providers array instead of provider
providers:
  - provider: openai
    model: gpt-4o-mini
    priority: 1              # Lower number = higher priority
  - provider: anthropic
    model: claude-3-haiku-20240307
    priority: 2
  - provider: gemini
    model: gemini-1.5-flash
    priority: 3

fallback_strategy: priority  # priority (default), round_robin, or fail_fast
```

### Supported Providers

| Provider | Example Models | Default API Key Env | Notes |
|----------|----------------|-------------------|-------|
| **openai** | `gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo` | `OPENAI_API_KEY` | Most popular, good balance |
| **anthropic** | `claude-3-haiku-20240307`, `claude-3-sonnet-20240229`, `claude-3-opus-20240229` | `ANTHROPIC_API_KEY` | Excellent reasoning |
| **gemini** | `gemini-1.5-flash`, `gemini-1.5-pro` | `GEMINI_API_KEY` | Fast and cost-effective |

### Caching Configuration

```yaml
enable_caching: true    # Default: true - Enable prompt caching for cost savings
cache_ttl: 3600        # Default: 3600 seconds (1 hour) - Cache time-to-live
```

## Secret Management

### Environment Variable (Default)

By default, the plugin looks for API keys in environment variables:

```yaml
provider: openai
api_key_env: OPENAI_API_KEY  # Default: {PROVIDER}_API_KEY
```

### External Secret Management (Production)

For production environments, use external secret management:

```yaml
secret_source:
  type: aws_secrets_manager  # or vault, gcp_secret_manager, env_var
  
  # AWS Secrets Manager
  secret_name: buildkite/ai-api-keys
  region: us-east-1          # Default: us-east-1
```

### Supported Secret Sources

#### AWS Secrets Manager

```yaml
secret_source:
  type: aws_secrets_manager
  secret_name: buildkite/ai-api-keys
  region: us-west-2
```

#### HashiCorp Vault

```yaml
secret_source:
  type: vault
  vault_path: secret/buildkite/api-key
  vault_role: buildkite-agent
  vault_addr: https://vault.example.com  # Optional: uses VAULT_ADDR env var
```

#### Google Cloud Secret Manager

```yaml
secret_source:
  type: gcp_secret_manager
  project_id: my-project-123
  secret_name: ai-api-key
```

### Multiple Providers with Different Secrets

```yaml
providers:
  - provider: openai
    priority: 1
    secret_source:
      type: aws_secrets_manager
      secret_name: openai-api-key
  - provider: anthropic
    priority: 2
    secret_source:
      type: vault
      vault_path: secret/anthropic/key
```

## Context Configuration

### Basic Context

```yaml
context:
  max_log_lines: 500              # Number of log lines to analyze (default: 500)
  include_env_vars: false         # Include environment variables (default: false - security risk)
  include_git_info: true          # Include git branch, commit, author (default: true)
  custom_context: "Additional context for AI analysis"
```

### Advanced Context

```yaml
context:
  max_log_lines: 1000            # Min: 50, Max: 2000
  include_env_vars: false        # Keep false for security
  include_git_info: true
  custom_context: |
    This is a Node.js microservice that:
    - Connects to PostgreSQL database
    - Uses Redis for caching
    - Deployed via Docker containers
    - Critical for payment processing
```

**Note:** The `custom_context` field is limited to 1000 characters.

## Security Configuration

### Basic Security Settings

```yaml
security:
  sanitize_logs: true           # Enable log sanitization (default: true)
  redact_secrets: true          # Automatically redact secrets (default: true)
  run_as_non_root: true        # Enforce non-root container execution (default: true)
```

### Advanced Security Features

```yaml
security:
  sanitize_logs: true
  redact_secrets: true
  allowed_domains:              # Restrict API calls to these domains
    - api.openai.com
    - api.anthropic.com
    - generativelanguage.googleapis.com
  run_as_non_root: true
  enable_thinking_mode: false   # Claude Opus 4 thinking mode (default: false)
  enable_deep_think: false      # Gemini Pro Deep Think mode (default: false)
```

### Domain Allowlist

By default, the plugin restricts API calls to known AI provider domains:

```yaml
security:
  allowed_domains:
    - api.openai.com
    - api.anthropic.com
    - generativelanguage.googleapis.com
    # Add custom proxy domains if needed:
    - your-proxy.example.com
```

## Output Configuration

### Basic Output

```yaml
output:
  style: error                  # error (default), warning, info, success
  include_confidence: true      # Include AI confidence score (default: true)
  save_artifact: false         # Save detailed analysis as artifact (default: false)
```

### Advanced Output

```yaml
output:
  style: warning
  include_confidence: true
  save_artifact: true
  artifact_path: ai-analysis.json  # Default: ai-analysis.json
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
  timeout_seconds: 120          # Analysis timeout (default: 120, max: 600)
  retry_attempts: 3            # Retry attempts on failure (default: 3, max: 5)
  rate_limit_rpm: 30           # Rate limit requests/minute (default: 30, max: 100)
  async_execution: false       # Run analysis asynchronously (default: false)
```

### Advanced Performance

```yaml
performance:
  timeout_seconds: 300
  retry_attempts: 5
  rate_limit_rpm: 50
  async_execution: true        # Don't block build
```

### Cost Optimization

```yaml
# Enable caching to reduce API calls
enable_caching: true           # Default: true
cache_ttl: 7200               # 2 hours (max: 86400 = 24 hours)

# Use faster, cheaper models
provider: gemini
model: gemini-1.5-flash       # Very cost-effective

# Reduce context size
context:
  max_log_lines: 300          # Reduce from default 500
```

## Advanced Configuration

### Debug and Dry Run

```yaml
debug: true                    # Enable debug logging (default: false)
dry_run: false                # Test configuration without calling AI APIs (default: false)
```

### Complete Example with All Options

```yaml
steps:
  - label: "🧪 Run Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Single provider configuration
          provider: openai
          model: gpt-4o-mini
          max_tokens: 1500
          temperature: 0.1
          
          # Caching
          enable_caching: true
          cache_ttl: 3600
          
          # Secret management
          secret_source:
            type: aws_secrets_manager
            secret_name: buildkite/openai-key
            region: us-east-1
          
          # Context
          context:
            max_log_lines: 750
            include_env_vars: false
            include_git_info: true
            custom_context: "Node.js service with PostgreSQL"
          
          # Security
          security:
            sanitize_logs: true
            redact_secrets: true
            run_as_non_root: true
          
          # Output
          output:
            style: error
            include_confidence: true
            save_artifact: true
            artifact_path: ai-analysis.json
          
          # Performance
          performance:
            timeout_seconds: 180
            retry_attempts: 3
            rate_limit_rpm: 30
            async_execution: false
          
          # Debug
          debug: false
          dry_run: false
```

### Multi-Provider Example

```yaml
steps:
  - label: "🧪 Run Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Multiple providers with fallback
          providers:
            - provider: openai
              model: gpt-4o-mini
              priority: 1
              secret_source:
                type: aws_secrets_manager
                secret_name: openai-key
            - provider: anthropic
              model: claude-3-haiku-20240307
              priority: 2
              secret_source:
                type: vault
                vault_path: secret/anthropic/key
            - provider: gemini
              model: gemini-1.5-flash
              priority: 3
          
          fallback_strategy: priority
          
          # Rest of configuration...
```

## Environment Variables

### API Key Variables

By default, the plugin looks for API keys in these environment variables:

| Provider | Default Environment Variable | Example |
|----------|---------------------------|---------|
| `openai` | `OPENAI_API_KEY` | `sk-proj-abc123...` |
| `anthropic` | `ANTHROPIC_API_KEY` | `sk-ant-abc123...` |
| `gemini` | `GEMINI_API_KEY` | `AIza123...` |

You can override the environment variable name using `api_key_env`:

```yaml
provider: openai
api_key_env: MY_CUSTOM_OPENAI_KEY
```

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
| `BUILDKITE_BUILD_URL` | Link to build |
| `BUILDKITE_JOB_ID` | Job identification |

## Troubleshooting

### Common Issues

1. **No analysis triggered**
   - Check that the command actually failed (exit code non-zero)
   - Verify API keys are set correctly
   - Enable debug mode to see detailed logs

2. **Analysis too slow**
   ```yaml
   # Reduce context and timeout
   context:
     max_log_lines: 200
   performance:
     timeout_seconds: 60
   ```

3. **API costs too high**
   ```yaml
   # Enable caching and use cheaper models
   provider: gemini
   model: gemini-1.5-flash
   enable_caching: true
   cache_ttl: 7200
   ```

### Testing Configuration

Use dry run mode to test configuration without making API calls:

```yaml
debug: true
dry_run: true
```

This will validate your configuration and show what would be sent to the AI provider.

## Configuration Reference

### Top-Level Properties

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `provider` | string | - | AI provider: `openai`, `anthropic`, or `gemini` (required unless using `providers`) |
| `providers` | array | - | Multiple AI providers with fallback (alternative to `provider`) |
| `model` | string | - | Specific AI model to use (optional, uses provider default) |
| `api_key_env` | string | `{PROVIDER}_API_KEY` | Environment variable containing the API key |
| `max_tokens` | integer | 1000 | Maximum tokens for AI response (100-4000) |
| `temperature` | number | 0.1 | AI model temperature (0.0-2.0) |
| `enable_caching` | boolean | true | Enable prompt caching for cost savings |
| `cache_ttl` | integer | 3600 | Cache time-to-live in seconds (300-86400) |
| `secret_source` | object | - | External secret management configuration |
| `fallback_strategy` | string | `priority` | Strategy when primary provider fails: `priority`, `round_robin`, `fail_fast` |
| `context` | object | - | Build context configuration |
| `output` | object | - | Output and reporting configuration |
| `performance` | object | - | Performance and reliability settings |
| `security` | object | - | Security settings |
| `debug` | boolean | false | Enable debug logging |
| `dry_run` | boolean | false | Test configuration without calling AI APIs |

### Context Object

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `include_env_vars` | boolean | false | Include environment variables (security risk) |
| `include_git_info` | boolean | true | Include git branch, commit, and author info |
| `max_log_lines` | integer | 500 | Maximum log lines to analyze (50-2000) |
| `custom_context` | string | - | Custom context to include (max 1000 chars) |

### Security Object

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `sanitize_logs` | boolean | true | Enable log sanitization before AI analysis |
| `redact_secrets` | boolean | true | Automatically redact secrets from logs |
| `allowed_domains` | array | See schema | Allowed domains for API calls |
| `run_as_non_root` | boolean | true | Enforce non-root container execution |
| `enable_thinking_mode` | boolean | false | Enable extended thinking mode (Claude Opus 4) |
| `enable_deep_think` | boolean | false | Enable Deep Think mode (Gemini Pro) |

### Output Object

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `style` | string | `error` | Buildkite annotation style: `error`, `warning`, `info`, `success` |
| `include_confidence` | boolean | true | Include AI confidence score in output |
| `save_artifact` | boolean | false | Save detailed analysis as build artifact |
| `artifact_path` | string | `ai-analysis.json` | Path for analysis artifact |

### Performance Object

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `timeout_seconds` | integer | 120 | Analysis timeout in seconds (30-600) |
| `retry_attempts` | integer | 3 | Number of retry attempts on failure (1-5) |
| `rate_limit_rpm` | integer | 30 | Rate limit requests per minute (1-100) |
| `async_execution` | boolean | false | Run analysis asynchronously (don't block build) |

### Secret Source Object

| Property | Type | Description |
|----------|------|-------------|
| `type` | string | Type of secret management: `aws_secrets_manager`, `vault`, `gcp_secret_manager`, `env_var` |
| `secret_name` | string | AWS Secrets Manager secret name |
| `region` | string | AWS region (default: us-east-1) |
| `vault_path` | string | Vault secret path |
| `vault_role` | string | Vault AppRole for authentication |
| `vault_addr` | string | Vault server address |
| `project_id` | string | GCP project ID for Secret Manager |

### Provider Object (for `providers` array)

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `provider` | string | - | Provider name: `openai`, `anthropic`, or `gemini` (required) |
| `model` | string | - | Specific model to use |
| `priority` | integer | 1 | Priority for fallback (1-10, lower = higher priority) |
| `secret_source` | object | - | Provider-specific secret configuration |