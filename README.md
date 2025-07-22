# AI Error Analysis Buildkite Plugin

🤖 Automatically analyze build failures using state-of-the-art AI models to provide actionable insights and suggestions.

[![Build Status](https://badge.buildkite.com/your-pipeline-badge.svg)](https://buildkite.com/your-org/your-pipeline)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚨 Critical Security Notice

**NEVER store API keys in pipeline configuration.** This plugin requires external secret management for production use. API keys stored in pipeline settings are exposed via the Buildkite API and logs.

## Supported AI Providers

### Latest 2025 Models

| Provider | Model | Context Window | Key Features |
|----------|-------|----------------|--------------|
| **Anthropic** | `claude-opus-4-20250514` | 200K tokens | Best coding model (72.5% SWE-bench), extended thinking |
| **Anthropic** | `claude-sonnet-4-20250514` | 200K tokens | Balanced performance, hybrid reasoning |
| **OpenAI** | `gpt-4.1` | 1M tokens | Latest flagship, superior coding & instruction following |
| **OpenAI** | `gpt-4.1-mini` | 1M tokens | 83% cost reduction vs GPT-4o, beats GPT-4o in benchmarks |
| **Google** | `gemini-2.0-flash` | 1M tokens | Generally available, multimodal, native tools |
| **Google** | `gemini-2.0-pro-exp` | 2M tokens | Experimental, best coding performance |

### All Supported Models

| Provider | Models | Authentication | Notes |
|----------|--------|----------------|-------|
| **OpenAI** | `gpt-4.1`, `gpt-4.1-mini`, `gpt-4o`, `gpt-4o-mini` | Bearer token | GPT-4.1 series are the newest with 1M token context |
| **Anthropic** | `claude-opus-4-20250514`, `claude-sonnet-4-20250514`, `claude-3-5-sonnet-20241022`, `claude-3-5-haiku-20241022`, `claude-3-opus-20240229` | x-api-key header | Claude Opus 4 is the most capable model |
| **Google** | `gemini-2.0-flash`, `gemini-2.0-pro-exp`, `gemini-1.5-pro`, `gemini-1.5-flash` | API key parameter | Gemini 2.0 Flash is GA, 2.0 Pro is experimental |

## Quick Start

### For Local Development/Testing

If you're setting up the plugin locally or with Docker/OrbStack:

1. **Copy and configure `.env` file**:
```bash
cp .env.example .env
# Edit .env with your credentials:
# - BUILDKITE_AGENT_TOKEN
# - ANTHROPIC_API_KEY (or OPENAI_API_KEY, GOOGLE_API_KEY)
# - GITHUB_TOKEN (for private repos)
```

2. **Run with Docker**:
```bash
docker-compose -f docker-compose.orbstack.yml up -d --build
```

See [Environment Configuration](#environment-configuration-env) for detailed setup.

### 1. External Secret Management (Production)

**AWS Secrets Manager (Recommended)**
```yaml
steps:
  - label: "Tests"
    command: "npm test"
    plugins:
      - ./ai-error-analysis:
          provider: openai
          model: "gpt-4o-mini"
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
      - ./ai-error-analysis:
          provider: anthropic
          model: "claude-3-5-haiku-20241022"
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
      - ./ai-error-analysis:
          provider: gemini
          model: "gemini-1.5-flash"
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
      - ./ai-error-analysis:
          provider: openai
          model: "gpt-4o-mini"
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
      - ./ai-error-analysis:
          provider: anthropic
          model: "claude-3-5-sonnet-20241022"
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
model: "gpt-4o-mini"  # or "gpt-4.1", "gpt-4.1-mini", "gpt-4o"
secret_source:
  type: aws_secrets_manager
  secret_name: buildkite/openai-key
  region: us-east-1
max_tokens: 1000
temperature: 0.1
```

**Available Models**:
- `gpt-4.1`: Latest model with 1M token context window
- `gpt-4.1-mini`: Smaller, faster version of GPT-4.1
- `gpt-4o`: Multimodal flagship model
- `gpt-4o-mini`: Cost-effective option

### Anthropic Configuration

```yaml
provider: anthropic
model: "claude-opus-4-20250514"  # or other models below
secret_source:
  type: vault
  vault_path: secret/buildkite/claude-key
  vault_role: buildkite-ai
max_tokens: 1000
```

**Available Models**:
- `claude-opus-4-20250514`: Claude 4 Opus - Most capable model (best for complex tasks)
- `claude-sonnet-4-20250514`: Claude 4 Sonnet - Balanced performance
- `claude-3-5-sonnet-20241022`: Claude 3.5 Sonnet (previous generation)
- `claude-3-5-haiku-20241022`: Fast and cost-effective
- `claude-3-opus-20240229`: Claude 3 Opus (legacy)

### Google Gemini Configuration

```yaml
provider: gemini
model: "gemini-1.5-flash"  # or other models below
secret_source:
  type: gcp_secret_manager
  project_id: your-project
  secret_name: gemini-api-key
max_tokens: 1000
```

**Available Models**:
- `gemini-2.0-flash`: Latest GA model with 1M token context
- `gemini-2.0-pro-exp`: Experimental model with best coding performance
- `gemini-1.5-pro`: Production-ready balanced model
- `gemini-1.5-flash`: Fast and cost-effective

## Security Features

### Automatic Log Sanitization

The plugin automatically removes sensitive information before sending to AI:

- **API Keys**: `sk-*`, `AIza*`, bearer tokens
- **Secrets**: Environment variables containing `SECRET`, `TOKEN`, `KEY`, `PASSWORD`
- **URLs**: Credentials in database URLs and webhook endpoints
- **SSH Keys**: Private key blocks
- **Personal Data**: Email addresses, file paths with usernames

### Container Security (2025 Standards)

The plugin enforces the following security settings:

**Plugin-level security configuration:**
```yaml
security:
  run_as_non_root: true  # Enforced by the plugin
  allowed_domains:       # Restricts API calls to these domains
    - "api.openai.com"
    - "api.anthropic.com" 
    - "generativelanguage.googleapis.com"
```

**Recommended Buildkite Agent container security settings:**
```yaml
# docker-compose.yml or Kubernetes deployment
security_opt:
  - no-new-privileges:true
cap_drop:
  - ALL
read_only: true
user: "1000:1000"
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
      - ./ai-error-analysis:
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
      - ./ai-error-analysis:
          providers:
            - provider: openai
              model: "gpt-4o-mini"
              secret_source:
                type: aws_secrets_manager
                secret_name: buildkite/openai-key
            - provider: anthropic  
              model: "claude-3-5-haiku-20241022"
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
      - ./ai-error-analysis:
          provider: gemini
          model: "gemini-1.5-flash"  # Most cost-effective
          max_tokens: 500
          enable_caching: true
          cache_ttl: 3600
          secret_source:
            type: gcp_secret_manager
            secret_name: gemini-key
```

## Cost Optimization

### Approximate Costs

| Provider | Model | ~Cost/Analysis | Best For |
|----------|-------|---------------|----------|
| Google | gemini-1.5-flash | $0.001-0.003 | High volume, cost-sensitive |
| OpenAI | gpt-4o-mini | $0.005-0.015 | Balanced quality/cost |
| Anthropic | claude-3-5-haiku-20241022 | $0.008-0.020 | Fast Claude responses |
| Google | gemini-1.5-pro | $0.010-0.030 | Production workloads |
| Anthropic | claude-3-5-sonnet-20241022 | $0.015-0.045 | Balanced capability |
| Anthropic | claude-sonnet-4-20250514 | $0.020-0.050 | Enhanced reasoning |
| OpenAI | gpt-4o | $0.020-0.080 | Multimodal analysis |
| OpenAI | gpt-4.1 | $0.030-0.100 | Latest with 1M context |
| Anthropic | claude-opus-4-20250514 | $0.050-0.150 | Best coding & complex tasks |

### Cost Reduction Features
- **Caching**: Avoid duplicate analyses (60%+ savings)
- **Log truncation**: Send only relevant error context  
- **Rate limiting**: Prevent API quota exhaustion
- **Token limits**: Configurable max_tokens parameter

## Development

### Prerequisites
- Python 3.10+ (3.12 recommended)
- Docker for testing
- External secret management system
- GitHub personal access token (for private repos)

### Environment Configuration (.env)

The plugin requires environment variables to be configured. Copy `.env.example` to `.env` and update with your credentials:

```bash
cp .env.example .env
```

#### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `BUILDKITE_AGENT_TOKEN` | Your Buildkite agent token | `bkua_xxxxxxxxxxxxx` |
| `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` or `GOOGLE_API_KEY` | API key for your chosen AI provider | `sk-ant-api03-xxxxx` |

#### Optional Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AI_PROVIDER` | AI provider to use | `anthropic` |
| `AI_MODEL` | Specific model to use | Provider default |
| `AI_MAX_TOKENS` | Maximum tokens for analysis | `2000` |
| `AI_ENABLE_CACHING` | Cache analysis results | `true` |
| `AI_DEBUG` | Enable debug logging | `false` |
| `GITHUB_TOKEN` | GitHub personal access token for private repos | None |
| `BUILDKITE_AGENT_NAME` | Agent name | `orbstack-claude-agent` |
| `BUILDKITE_AGENT_TAGS` | Agent tags | `queue=default,os=linux,...` |

#### GitHub Access Token Setup

If your Buildkite pipelines need to clone private GitHub repositories:

1. **Generate a GitHub Personal Access Token**:
   - Go to https://github.com/settings/tokens
   - Click "Generate new token (classic)"
   - Give it a descriptive name (e.g., "Buildkite Agent")
   - Select the `repo` scope for private repository access
   - Click "Generate token"
   - Copy the token immediately (you won't see it again)

2. **Add to your `.env` file**:
   ```bash
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx
   ```

3. **Security Notes**:
   - Never commit `.env` files to version control
   - Add `.env` to your `.gitignore`
   - Rotate tokens regularly
   - Use minimal required scopes

#### Example `.env` File

```bash
# Buildkite Configuration
BUILDKITE_AGENT_TOKEN=bkua_1234567890abcdef

# AI Provider Configuration (choose one)
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
# OPENAI_API_KEY=sk-xxxxxxxxxxxxx
# GOOGLE_API_KEY=AIzaxxxxxxxxxxxxx

# Plugin Settings
AI_PROVIDER=anthropic
AI_MODEL=claude-opus-4-20250514
AI_MAX_TOKENS=2000
AI_ENABLE_CACHING=true
AI_DEBUG=false

# GitHub Access (for private repos)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# Agent Configuration
BUILDKITE_AGENT_NAME=my-ai-agent
BUILDKITE_AGENT_TAGS=queue=default,os=linux,ai-error-analysis=enabled
```

### Local Testing

1. **Clone and setup**:
```bash
git clone https://github.com/JustinD-HNL/ai-error-analysis-buildkite-plugin
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

### Docker/OrbStack Setup

For containerized deployment using Docker or OrbStack:

1. **Ensure `.env` file is configured** (see Environment Configuration above)

2. **Build and run with docker-compose**:
```bash
# For OrbStack users
docker-compose -f docker-compose.orbstack.yml up -d --build

# For standard Docker
docker-compose -f docker/docker-compose.yml up -d --build
```

3. **Verify agent is running**:
```bash
docker logs buildkite-agent-ai-analysis
```

4. **Important Notes**:
- The `.env` file is automatically loaded by docker-compose
- GitHub token is passed to the container for private repo access
- AI provider credentials are securely passed as environment variables
- Never include `.env` in Docker images or commits

### Testing Framework

```bash
# Run test scripts from testing directory
cd testing
./test-full-pipeline.sh

# Or use the simple test
./test-analysis.sh
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

**GitHub clone failures (private repos)**:
- Ensure `GITHUB_TOKEN` is set in your `.env` file
- Verify token has `repo` scope for private repositories
- Check token hasn't expired
- Test with: `curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user`

**Container not starting**:
- Check `.env` file exists and has valid `BUILDKITE_AGENT_TOKEN`
- Verify AI provider API key is set (ANTHROPIC_API_KEY, etc.)
- Check logs: `docker logs buildkite-agent-ai-analysis`

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
