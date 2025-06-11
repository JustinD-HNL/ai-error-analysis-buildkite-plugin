# AI Error Analysis Buildkite Plugin

🤖 Automatically analyze build failures using state-of-the-art AI models to provide actionable insights and suggestions.

This plugin integrates with multiple AI providers (OpenAI GPT-4.1, Claude Opus 4, Gemini 2.5) to analyze build errors and provide intelligent suggestions for resolution, helping developers fix issues faster and learn from failures.

[![Build Status](https://badge.buildkite.com/your-pipeline-badge.svg)](https://buildkite.com/your-org/your-pipeline)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

### Supported Providers (2025 Models)

| Provider | Models | API Key Env | Notes |
|----------|--------|-------------|-------|
| **OpenAI** | `gpt-4.1`, `o4-mini`, `gpt-4o-mini` (legacy) | `OPENAI_API_KEY` | Latest reasoning models, 1M context |
| **Claude** | `claude-opus-4`, `claude-sonnet-4` | `ANTHROPIC_API_KEY` | Extended thinking, excellent reasoning |
| **Gemini** | `gemini-2.5-pro`, `gemini-2.5-flash` | `GOOGLE_API_KEY` | Deep Think mode, multimodal support |

## 🚨 Security Notice

**CRITICAL**: Never store API keys in Buildkite pipeline configuration. Use external secret management services like AWS Secrets Manager, HashiCorp Vault, or Google Secret Manager. API keys in pipeline settings are exposed via the API and logs.

## Features

### 🔍 **Intelligent Error Detection**
- Automatic pattern recognition for compilation errors, test failures, dependency issues, and more
- Context-aware analysis using pipeline metadata and git information  
- Support for multiple error categories with confidence scoring

### 🤖 **Latest AI Provider Support**
- **OpenAI GPT-4.1** and **o4-mini** (2025 models)
- **Anthropic Claude Opus 4** and **Sonnet 4** with extended thinking
- **Google Gemini 2.5 Pro** and **2.5 Flash** with multimodal capabilities
- Automatic fallback between providers with exponential backoff
- Batch API support for 50% cost savings on non-critical analysis

### 🔒 **Enterprise Security**
- External secret management integration (AWS, Vault, GCP)
- Comprehensive log sanitization before AI analysis
- Automatic redaction of secrets, tokens, passwords, and sensitive data
- Container security with non-root execution and capability dropping
- Command injection prevention and input validation

### 📊 **Rich Output & Reporting**
- Beautiful HTML annotations in Buildkite with confidence scores
- Structured JSON reports for programmatic consumption
- Markdown reports for documentation
- Optional artifact generation for detailed analysis

### ⚡ **Performance Optimized**
- Intelligent caching to avoid redundant API calls (54% build time reduction)
- Configurable timeouts (60s standard, 300s for reasoning models)
- Async execution options to not block builds
- Smart context truncation to fit AI model limits
- Batch processing for cost optimization

### 🛠 **Flexible Configuration**
- Zero-config defaults that work out of the box
- Extensive customization options for enterprise users
- Branch-specific analysis controls
- Custom prompts for different error types

## Quick Start

### 1. Add to Your Pipeline

```yaml
steps:
  - label: "Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0: ~
```

### 2. Configure Secret Management (Required)

**Option A: AWS Secrets Manager**
```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          ai_providers:
            - name: openai
              model: gpt-4.1
              secret_source:
                type: aws_secrets_manager
                name: buildkite/openai-api-key
                region: us-east-1
```

**Option B: HashiCorp Vault**
```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          ai_providers:
            - name: openai
              model: gpt-4.1
              secret_source:
                type: vault
                vault_path: secret/buildkite/openai-api-key
```

**Option C: Environment Variable (Less Secure)**
```bash
# Set in your agent environment, NOT in pipeline
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Watch the Magic ✨

When your build fails, the plugin will automatically:
1. Detect the error patterns
2. Gather relevant context
3. Sanitize logs for security
4. Analyze with AI
5. Create a beautiful annotation with suggestions

## Environment Variables

### Critical Security Note
Environment variables follow the pattern: `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_<PROPERTY>`

**The plugin name comes from the repository folder name**, not the `plugin.yml` name field. For a plugin at `your-org/ai-error-analysis-buildkite-plugin`, variables use `AI_ERROR_ANALYSIS`.

### Examples

| Configuration | Environment Variable |
|---------------|---------------------|
| `trigger: auto` | `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_TRIGGER=auto` |
| `performance.timeout: 120` | `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_TIMEOUT=120` |
| `advanced.debug_mode: true` | `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE=true` |

## Configuration

### Basic Configuration

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          # AI Provider Configuration
          ai_providers:
            - name: openai
              model: gpt-4.1
              secret_source:
                type: aws_secrets_manager
                name: buildkite/openai-api-key
          
          # When to trigger analysis
          trigger: auto  # auto, explicit, always
          
          # Error conditions
          conditions:
            exit_status: [1, 2, 125, 126, 127, 128, 130]
            branches: ["main", "develop"]  # empty = all branches
```

### Advanced Configuration with Security

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          # Multiple AI providers with fallback
          ai_providers:
            - name: openai
              model: gpt-4.1
              secret_source:
                type: aws_secrets_manager
                name: buildkite/openai-api-key
                region: us-east-1
              max_tokens: 1000
              timeout: 60
              use_batch_api: false  # Set true for non-critical analysis
            - name: claude
              model: claude-opus-4
              secret_source:
                type: vault
                vault_path: secret/buildkite/claude-api-key
              max_tokens: 1000
              timeout: 300  # Extended for reasoning models
          
          # Fallback strategy with retry configuration
          performance:
            fallback_strategy: priority
            timeout: 120
            async_execution: false
            cache_enabled: true
            cache_ttl: 3600
            retry_config:
              max_attempts: 3
              initial_delay: 2
              max_delay: 60
          
          # Context gathering
          context:
            log_lines: 500
            include_environment: true
            include_pipeline_info: true
            include_git_info: true
            custom_context: "Additional context for AI analysis"
          
          # Enhanced Security & Privacy
          redaction:
            enable_builtin_patterns: true
            custom_patterns:
              - "(?i)company[_-]?secret[\\s]*[=:]+[\\s]*[^\\s]+"
              - "(?i)internal[_-]?token[\\s]*[=:]+[\\s]*[^\\s]+"
            redact_file_paths: true
            redact_urls: true
          
          # Output configuration  
          output:
            annotation_style: error
            annotation_context: ai-error-analysis
            include_confidence: true
            save_as_artifact: true
            artifact_path: ai-analysis-report.json
          
          # Advanced security options
          advanced:
            debug_mode: false
            dry_run: false
            input_validation:
              enabled: true
              max_log_size_mb: 50
              allowed_commands: []  # Whitelist specific commands
            security:
              enable_command_validation: true
              container_security:
                run_as_non_root: true
                drop_capabilities: ["ALL"]
                add_capabilities: []
                no_new_privileges: true
            custom_prompts:
              compilation_error: "Focus on compilation issues and syntax errors"
              test_failure: "Analyze test failures and assertion errors"
              deployment_error: "Focus on deployment and infrastructure issues"
              security_error: "Analyze security-related errors with special attention"
```

## AI Provider Configuration

### OpenAI Setup (2025 Models)

```yaml
ai_providers:
  - name: openai
    model: gpt-4.1  # or gpt-4o-mini, o4-mini
    secret_source:
      type: aws_secrets_manager
      name: buildkite/openai-api-key
    max_tokens: 1000
    timeout: 60
    use_batch_api: false  # Enable for 50% cost savings on non-critical analysis
```

**Available Models:**
- `gpt-4.1`: Latest flagship model with 1M token context ($2.50/$10 per 1M tokens)
- `gpt-4o-mini`: Cost-effective general purpose ($0.15/$0.60 per 1M tokens)
- `o4-mini`: Reasoning model for complex analysis ($0.15/$0.60 per 1M tokens)

### Anthropic Claude Setup (2025 Models)

```yaml
ai_providers:
  - name: claude
    model: claude-opus-4  # or claude-sonnet-4
    secret_source:
      type: vault
      vault_path: secret/buildkite/claude-api-key
    max_tokens: 1000
    timeout: 300  # Extended for thinking capabilities
    use_batch_api: true  # Recommended for 50% savings
```

**Available Models:**
- `claude-opus-4`: Latest flagship with extended thinking ($15/$75 per 1M tokens)
- `claude-sonnet-4`: Balanced performance and cost ($3/$15 per 1M tokens)

### Google Gemini Setup (2025 Models)

```yaml
ai_providers:
  - name: gemini
    model: gemini-2.5-pro  # or gemini-2.5-flash
    secret_source:
      type: gcp_secret_manager
      name: buildkite-gemini-api-key
    max_tokens: 1000
    timeout: 60
```

**Available Models:**
- `gemini-2.5-pro`: Flagship model with Deep Think capability
- `gemini-2.5-flash`: Fast and cost-effective (64% price reduction in 2025)

## Examples

### Zero Configuration (Recommended)

Just add the plugin and configure secret management:

```yaml
steps:
  - command: "make test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          ai_providers:
            - name: openai
              model: gpt-4o-mini
              secret_source:
                type: aws_secrets_manager
                name: buildkite/openai-api-key
```

### Branch-Specific Analysis

Only analyze failures on important branches:

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          conditions:
            branches: ["main", "develop", "release/*"]
          ai_providers:
            - name: openai
              model: gpt-4.1
              secret_source:
                type: aws_secrets_manager
                name: buildkite/openai-api-key
```

### Cost-Optimized Configuration

Use batch APIs and efficient models:

```yaml
steps:
  - command: "cargo test"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          ai_providers:
            - name: gemini
              model: gemini-2.5-flash  # Most cost-effective
              use_batch_api: true
            - name: openai  
              model: gpt-4o-mini       # Fallback
              use_batch_api: true
          performance:
            fallback_strategy: priority
            cache_enabled: true
            cache_ttl: 7200  # Longer caching
```

### Enterprise Security Configuration

Maximum security for sensitive environments:

```yaml
steps:
  - command: "pytest"
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          ai_providers:
            - name: claude
              model: claude-sonnet-4
              secret_source:
                type: vault
                vault_path: secret/buildkite/claude-api-key
          
          redaction:
            enable_builtin_patterns: true
            custom_patterns:
              # Company-specific secrets
              - "(?i)acmecorp[_-]?api[_-]?key[\\s]*[=:]+[\\s]*[^\\s]+"
              - "(?i)internal[_-]?webhook[\\s]*[=:]+[\\s]*[^\\s]+"
              
              # Database connections
              - "postgresql://[^\\s]+"
              - "mongodb://[^\\s]+"
              - "redis://[^\\s]+"
          
          advanced:
            input_validation:
              enabled: true
              max_log_size_mb: 25
              allowed_commands: ["npm", "mvn", "gradle", "python"]
            security:
              enable_command_validation: true
              container_security:
                run_as_non_root: true
                drop_capabilities: ["ALL"]
                no_new_privileges: true
```

### Async Analysis

Run analysis in background to not block builds:

```yaml
steps:
  - command: "docker build ."
    plugins:
      - your-org/ai-error-analysis-buildkite-plugin#v1.0.0:
          performance:
            async_execution: true
            timeout: 300  # Longer timeout for complex analysis
          ai_providers:
            - name: openai
              model: gpt-4.1
              secret_source:
                type: aws_secrets_manager
                name: buildkite/openai-api-key
```

## Security & Privacy

The plugin implements multiple layers of security protection:

### Automatic Redaction
- **Built-in patterns**: Automatically detects and redacts passwords, tokens, API keys, SSH keys, etc.
- **File paths**: Removes user-specific paths like `/home/username/` 
- **URLs**: Redacts credentials in URLs
- **Email addresses**: Partially masks email addresses

### External Secret Management
Supports integration with enterprise secret management:

- **AWS Secrets Manager**: Recommended for AWS environments
- **HashiCorp Vault**: Enterprise-grade secret management
- **Google Secret Manager**: For GCP environments
- **Environment Variables**: Fallback option (less secure)

### Container Security
- **Non-root execution**: All containers run as non-root user
- **Capability dropping**: Removes unnecessary Linux capabilities
- **Security scanning**: Integrated vulnerability scanning
- **AppArmor/seccomp**: Security profiles enforced

### What Gets Sent to AI
- **Sanitized log excerpts** (with secrets removed)
- **Error patterns and categories** 
- **Basic build metadata** (pipeline name, branch, commit hash)
- **Safe environment variables** (no secrets)

### What Never Gets Sent
- **Raw logs** (always sanitized first)
- **Environment variables** containing secrets
- **File contents** (only log output)
- **Sensitive build artifacts**

## Error Types Detected

The plugin automatically detects and categorizes various error types:

| Category | Examples | Confidence |
|----------|----------|------------|
| **Compilation** | Syntax errors, missing imports, type errors | High |
| **Test Failure** | Assertion failures, test timeouts, setup errors | High |
| **Dependency** | Package not found, version conflicts, resolution errors | High |
| **Network** | Connection timeouts, DNS failures, certificate errors | Medium |
| **Permission** | Access denied, file permissions, authentication | High |
| **Memory** | Out of memory, segmentation faults, allocation failures | High |
| **Timeout** | Build timeouts, test timeouts, deployment timeouts | Medium |
| **Configuration** | Missing config files, invalid syntax, environment issues | Medium |
| **Security** | Certificate errors, permission denied, authentication failures | High |

## Performance

### Optimization Tips

1. **Use Caching**: Enable caching to avoid repeated analysis of similar errors
2. **Batch APIs**: Enable for non-critical analysis (50% cost savings)
3. **Choose Efficient Models**: Use mini/flash variants for speed and cost
4. **Async Execution**: Enable for non-blocking analysis
5. **Branch Filtering**: Only analyze important branches

### Performance Metrics

The plugin tracks and reports:
- Analysis duration
- API tokens consumed  
- Cache hit rates (54% improvement reported)
- Provider response times
- Memory and disk usage

## API Costs (2025 Pricing)

Approximate costs per analysis (USD):

| Provider | Model | ~Cost/Analysis | Notes |
|----------|-------|---------------|-------|
| OpenAI | gpt-4o-mini | $0.001-0.005 | Most cost-effective |
| OpenAI | gpt-4.1 | $0.01-0.05 | Premium quality |
| Claude | claude-sonnet-4 | $0.005-0.02 | Excellent reasoning |
| Claude | claude-opus-4 | $0.02-0.08 | Flagship model |
| Gemini | gemini-2.5-flash | $0.0005-0.002 | Most economical |
| Gemini | gemini-2.5-pro | $0.002-0.01 | Premium multimodal |

*Costs depend on context size and response length. Batch APIs provide 50% savings.*

### Cost Optimization
- Enable caching to avoid duplicate analyses
- Use batch APIs for non-critical analysis
- Choose appropriate models for your use case
- Set reasonable rate limits and timeouts

## Development

### Local Testing

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/ai-error-analysis-buildkite-plugin
cd ai-error-analysis-buildkite-plugin
```

2. **Set up environment**:
```bash
# Configure secret management (recommended)
aws secretsmanager create-secret \
  --name buildkite/openai-api-key \
  --secret-string '{"api_key":"your-key"}'

export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"
```

3. **Run tests**:
```bash
docker-compose run --rm tests
```

4. **Test with sample failure**:
```bash
# Simulate a build failure
export BUILDKITE_COMMAND_EXIT_STATUS="1"
export BUILDKITE_COMMAND="npm test"
./hooks/post-command
```

## Troubleshooting

### Common Issues

#### Plugin Not Running
```bash
# Check plugin is properly installed
ls -la .buildkite/plugins/

# Verify environment variables (corrected pattern)
env | grep BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS

# Check permissions
ls -la hooks/
```

#### Secret Management Issues  
```bash
# Verify AWS Secrets Manager access
aws secretsmanager get-secret-value --secret-id buildkite/openai-api-key

# Test Vault connectivity
vault kv get secret/buildkite/openai-api-key

# Check container security
docker run --user 1000:1000 --cap-drop=ALL --security-opt=no-new-privileges:true your-image
```

#### No Analysis Generated
```bash
# Enable debug mode
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"

# Check error detection
python3 lib/error_detector.py

# Verify exit code triggers analysis
echo "Exit code: $BUILDKITE_COMMAND_EXIT_STATUS"
```

### Health Check

Run comprehensive health check:

```bash
python3 lib/health_check.py
```

Validates:
- ✅ Python version compatibility
- ✅ Required system commands
- ✅ Plugin file integrity
- ✅ File permissions
- ✅ Secret management configuration
- ✅ AI provider connectivity
- ✅ Cache setup
- ✅ Container security
- ✅ Input validation

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📚 **Documentation**: [Plugin Docs](https://github.com/your-org/ai-error-analysis-buildkite-plugin/docs)
- 💬 **Community**: [Buildkite Community](https://community.buildkite.com/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/ai-error-analysis-buildkite-plugin/issues)
- 📧 **Enterprise**: Contact your Buildkite representative

---

**Made with ❤️ for the Buildkite community**