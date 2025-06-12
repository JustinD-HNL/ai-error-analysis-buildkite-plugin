# AI Error Analysis Buildkite Plugin

🤖 Automatically analyze build failures using state-of-the-art AI models to provide actionable insights and suggestions.

[![Build Status](https://badge.buildkite.com/your-pipeline-badge.svg)](https://buildkite.com/your-org/your-pipeline)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚨 Critical Security Notice

**NEVER store API keys in pipeline configuration.** This plugin requires external secret management for production use. API keys stored in pipeline settings are exposed via the Buildkite API and logs.

## Supported AI Providers (2025 Models)

| Provider | Models | Authentication | Notes |
|----------|--------|----------------|-------|
| **OpenAI** | `GPT-4o`, `GPT-4o mini`, `GPT-4o nano` | Bearer token | Latest models with improved reasoning |
| **Anthropic** | `Claude 3.5 Haiku`, `Claude Sonnet 4`, `Claude Opus 4` | x-api-key header | Extended thinking mode available |
| **Google** | `Gemini 2.0 Flash`, `Gemini 2.5 Pro` | API key parameter | Deep Think mode for complex analysis |

## Quick Start

### 1. External Secret Management (Required)

**AWS Secrets Manager (Recommended)**
```yaml
steps:
  - label: "Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: openai
          model: "GPT-4o mini"
          secret_source:
            type: aws_secrets_manager
            secret_name: buildkite/ai-error-analysis/openai-key
            region: us-east-1
```

**HashiCorp Vault**
```yaml
steps:
  - label: "Tests" 
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: anthropic
          model: "Claude 3.5 Haiku"
          secret_source:
            type: vault
            vault_path: secret/buildkite/anthropic-key
            vault_role: buildkite-ai-analysis
```

**Google Secret Manager**
```yaml
steps:
  - label: "Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: gemini
          model: "Gemini 2.0 Flash"
          secret_source:
            type: gcp_secret_manager
            project_id: your-project
            secret_name: buildkite-gemini-key
```

### 2. Environment Variables (Less Secure Fallback)

⚠️ **Not recommended for production**

```bash
# Set in agent environment, NOT in pipeline
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_API_KEY_ENV="OPENAI_API_KEY"
export OPENAI_API_KEY="your-api-key-here"
```

## Configuration

### Basic Configuration

```yaml
steps:
  - command: "pytest tests/"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: openai
          model: "GPT-4o mini"
          max_tokens: 1000
          enable_caching: true
          secret_source:
            type: aws_secrets_manager
            secret_name: buildkite/openai-key
```

### Advanced Configuration

```yaml
steps:
  - command: "cargo test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: anthropic
          model: "Claude Sonnet 4"
          max_tokens: 2000
          enable_caching: true
          temperature: 0.1
          
          # External secret management
          secret_source:
            type: vault
            vault_path: secret/buildkite/claude-key
            vault_addr: https://vault.company.com
            vault_role: buildkite-ai
          
          # Context configuration
          context:
            include_env_vars: false
            include_git_info: true
            max_log_lines: 500
            custom_context: "Rust application with async/await patterns"
          
          # Output configuration
          output:
            style: error
            include_confidence: true
            save_artifact: true
            artifact_path: "reports/ai-analysis.json"
          
          # Performance tuning
          performance:
            timeout_seconds: 120
            retry_attempts: 3
            rate_limit_rpm: 30
          
          # Security settings
          security:
            sanitize_logs: true
            redact_secrets: true
            allowed_domains: ["api.anthropic.com"]
```

## Environment Variables

Environment variables follow the pattern: `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_<PROPERTY>`

⚠️ **Critical**: The plugin name comes from the repository folder name, not the plugin.yml name field.

### Examples

| Configuration | Environment Variable |
|---------------|---------------------|
| `provider: openai` | `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER=openai` |
| `max_tokens: 1500` | `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MAX_TOKENS=1500` |
| `enable_caching: false` | `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ENABLE_CACHING=false` |

## AI Provider Setup

### OpenAI Configuration

```yaml
provider: openai
model: "GPT-4o mini"  # or "GPT-4o", "GPT-4o nano"
secret_source:
  type: aws_secrets_manager
  secret_name: buildkite/openai-key
  region: us-east-1
max_tokens: 1000
temperature: 0.1
```

**Available Models (2025)**:
- `GPT-4o`: Latest flagship model ($3/$10 per 1M tokens)
- `GPT-4o mini`: Cost-effective option ($0.15/$0.60 per 1M tokens)  
- `GPT-4o nano`: Ultra-fast responses ($0.05/$0.20 per 1M tokens)

### Anthropic Configuration

```yaml
provider: anthropic
model: "Claude 3.5 Haiku"  # or "Claude Sonnet 4", "Claude Opus 4"
secret_source:
  type: vault
  vault_path: secret/buildkite/claude-key
  vault_role: buildkite-ai
max_tokens: 1000
enable_thinking_mode: true  # For Opus 4
```

**Available Models (2025)**:
- `Claude Opus 4`: Flagship with extended thinking ($15/$75 per 1M tokens)
- `Claude Sonnet 4`: Balanced performance ($3/$15 per 1M tokens)
- `Claude 3.5 Haiku`: Fast and cost-effective ($0.25/$1.25 per 1M tokens)

### Google Gemini Configuration

```yaml
provider: gemini
model: "Gemini 2.0 Flash"  # or "Gemini 2.5 Pro"
secret_source:
  type: gcp_secret_manager
  project_id: your-project
  secret_name: gemini-api-key
max_tokens: 1000
enable_deep_think: true  # For Pro models
```

**Available Models (2025)**:
- `Gemini 2.5 Pro`: Premium with Deep Think capability
- `Gemini 2.0 Flash`: Optimized for speed and cost

## Security Features

### Automatic Log Sanitization

The plugin automatically removes sensitive information before sending to AI:

- **API Keys**: `sk-*`, `AIza*`, bearer tokens
- **Secrets**: Environment variables containing `SECRET`, `TOKEN`, `KEY`, `PASSWORD`
- **URLs**: Credentials in database URLs and webhook endpoints
- **SSH Keys**: Private key blocks
- **Personal Data**: Email addresses, file paths with usernames

### Container Security (2025 Standards)

```yaml
security:
  container:
    run_as_non_root: true
    user_id: 1000
    group_id: 1000
    read_only_root_fs: true
    drop_capabilities: ["ALL"]
    security_opts: ["no-new-privileges:true"]
  
  network:
    allowed_domains: 
      - "api.openai.com"
      - "api.anthropic.com" 
      - "generativelanguage.googleapis.com"
```

### External Secret Management Examples

**AWS Secrets Manager with IAM Role**
```bash
# hooks/environment
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id buildkite/ai-error-analysis/openai \
  --query SecretString --output text \
  --region us-east-1)
```

**HashiCorp Vault with AppRole**
```bash
# hooks/environment  
export VAULT_TOKEN=$(vault write -field=token \
  auth/approle/login \
  role_id="$VAULT_ROLE_ID" \
  secret_id="$VAULT_SECRET_ID")

export ANTHROPIC_API_KEY=$(vault kv get \
  -mount=secret -field=api_key \
  buildkite/anthropic)
```

## Examples

### Zero Configuration
```yaml
steps:
  - command: "make test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: openai
          secret_source:
            type: aws_secrets_manager
            secret_name: buildkite/openai-key
```

### Multi-Provider Fallback
```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          providers:
            - provider: openai
              model: "GPT-4o mini"
              secret_source:
                type: aws_secrets_manager
                secret_name: buildkite/openai-key
            - provider: anthropic  
              model: "Claude 3.5 Haiku"
              secret_source:
                type: vault
                vault_path: secret/buildkite/claude-key
          fallback_strategy: priority
```

### Cost-Optimized Configuration
```yaml
steps:
  - command: "pytest"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          provider: gemini
          model: "Gemini 2.0 Flash"  # Most cost-effective
          max_tokens: 500
          enable_caching: true
          cache_ttl: 3600
          secret_source:
            type: gcp_secret_manager
            secret_name: gemini-key
```

## Cost Optimization

### Approximate Costs (2025 Pricing)

| Provider | Model | ~Cost/Analysis | Best For |
|----------|-------|---------------|----------|
| Google | Gemini 2.0 Flash | $0.001-0.003 | High volume, cost-sensitive |
| OpenAI | GPT-4o nano | $0.002-0.005 | Fast responses |
| OpenAI | GPT-4o mini | $0.005-0.015 | Balanced quality/cost |
| Anthropic | Claude 3.5 Haiku | $0.008-0.020 | Complex reasoning |
| OpenAI | GPT-4o | $0.020-0.080 | Premium quality |

### Cost Reduction Features
- **Caching**: Avoid duplicate analyses (60%+ savings)
- **Log truncation**: Send only relevant error context
- **Rate limiting**: Prevent API quota exhaustion
- **Batch processing**: Analyze multiple errors together

## Development

### Prerequisites
- Python 3.10+ (3.12 recommended)
- Docker for testing
- External secret management system

### Local Testing

1. **Clone and setup**:
```bash
git clone https://github.com/your-org/ai-error-analysis-buildkite-plugin
cd ai-error-analysis-buildkite-plugin
pip install -r requirements.txt
```

2. **Configure secrets**:
```bash
# AWS Secrets Manager
aws secretsmanager create-secret \
  --name buildkite/ai-error-analysis/openai \
  --secret-string '{"api_key":"your-key-here"}'

# Or use environment variables for testing only
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_API_KEY_ENV="OPENAI_API_KEY"
export OPENAI_API_KEY="your-test-key"
```

3. **Test with sample failure**:
```bash
export BUILDKITE_COMMAND_EXIT_STATUS="1"
export BUILDKITE_COMMAND="npm test"
./hooks/post-command
```

### Testing Framework

```bash
# Python unit tests
pytest tests/ --cov=lib --cov-report=term --cov-fail-under=80

# Security scanning
bandit -r lib/

# Hook integration tests  
bats tests/hooks.bats

# Type checking
mypy lib/ --strict
```

## Troubleshooting

### Common Issues

**No analysis generated**:
```bash
# Check plugin initialization
echo $BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER

# Verify secret access
aws secretsmanager get-secret-value --secret-id buildkite/openai-key

# Enable debug mode
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG=true
```

**API errors**:
- Verify correct 2025 model names
- Check API key permissions and quotas
- Ensure network access to AI provider endpoints
- Review rate limiting configuration

**Security warnings**:
- Never store secrets in pipeline configuration
- Use external secret management in production
- Regularly rotate API keys
- Monitor for secret exposure in logs

### Health Check

```bash
python3 lib/health_check.py
```

Validates:
- ✅ External secret access
- ✅ AI provider connectivity  
- ✅ Log sanitization effectiveness
- ✅ Container security configuration
- ✅ Rate limiting setup

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Security-First AI-Powered DevOps Intelligence for Buildkite**