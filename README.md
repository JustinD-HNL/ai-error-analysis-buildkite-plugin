# AI Error Analysis Buildkite Plugin

🤖 Automatically analyze build failures using AI models to provide actionable insights and suggestions.

This plugin integrates with multiple AI providers (OpenAI, Claude, Gemini) to analyze build errors and provide intelligent suggestions for resolution, helping developers fix issues faster and learn from failures.

[![Build Status](https://badge.buildkite.com/your-pipeline-badge.svg)](https://buildkite.com/your-org/your-pipeline)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

### 🔍 **Intelligent Error Detection**
- Automatic pattern recognition for compilation errors, test failures, dependency issues, and more
- Context-aware analysis using pipeline metadata and git information  
- Support for multiple error categories with confidence scoring

### 🤖 **Multi-AI Provider Support**
- **OpenAI GPT** (GPT-4o, GPT-4o-mini, GPT-3.5-turbo)
- **Anthropic Claude** (Claude-3-Haiku, Claude-3-Sonnet, Claude-3-Opus)
- **Google Gemini** (Gemini-1.5-Flash, Gemini-1.5-Pro)
- Automatic fallback between providers
- Configurable model selection and parameters

### 🔒 **Security-First Design**
- Comprehensive log sanitization before AI analysis
- Automatic redaction of secrets, tokens, and sensitive data
- Configurable custom redaction patterns
- No storage of sensitive information

### 📊 **Rich Output & Reporting**
- Beautiful HTML annotations in Buildkite with confidence scores
- Structured JSON reports for programmatic consumption
- Markdown reports for documentation
- Optional artifact generation for detailed analysis

### ⚡ **Performance Optimized**
- Intelligent caching to avoid redundant API calls
- Configurable timeouts and rate limiting
- Async execution options to not block builds
- Smart context truncation to fit AI model limits

### 🛠 **Flexible Configuration**
- Zero-config defaults that work out of the box
- Extensive customization options for advanced users
- Branch-specific analysis controls
- Custom prompts for different error types

## Quick Start

### 1. Add to Your Pipeline

```yaml
steps:
  - label: "Tests"
    command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0: ~
```

### 2. Set API Key

Set your AI provider API key as an environment variable:

```bash
# For OpenAI (default)
export OPENAI_API_KEY="your-api-key-here"

# For Claude
export ANTHROPIC_API_KEY="your-api-key-here"

# For Gemini
export GOOGLE_API_KEY="your-api-key-here"
```

### 3. Watch the Magic ✨

When your build fails, the plugin will automatically:
1. Detect the error patterns
2. Gather relevant context
3. Sanitize logs for security
4. Analyze with AI
5. Create a beautiful annotation with suggestions

## Configuration

### Basic Configuration

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # AI Provider Configuration
          ai_providers:
            - name: openai
              model: gpt-4o-mini
              api_key_env: OPENAI_API_KEY
          
          # When to trigger analysis
          trigger: auto  # auto, explicit, always
          
          # Error conditions
          conditions:
            exit_status: [1, 2, 125, 126, 127, 128, 130]
            branches: ["main", "develop"]  # empty = all branches
```

### Advanced Configuration

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          # Multiple AI providers with fallback
          ai_providers:
            - name: openai
              model: gpt-4o-mini
              api_key_env: OPENAI_API_KEY
              max_tokens: 1000
              timeout: 60
            - name: claude
              model: claude-3-haiku-20240307
              api_key_env: ANTHROPIC_API_KEY
              max_tokens: 1000
          
          # Fallback strategy
          performance:
            fallback_strategy: priority  # round_robin, priority, fail_fast
            timeout: 120
            async_execution: false
            cache_enabled: true
            cache_ttl: 3600
          
          # Context gathering
          context:
            log_lines: 500
            include_environment: true
            include_pipeline_info: true
            include_git_info: true
            custom_context: "Additional context for AI analysis"
          
          # Security & Privacy
          redaction:
            custom_patterns:
              - "(?i)internal[_-]?token[\\s]*[=:]+[\\s]*[^\\s]+"
              - "(?i)company[_-]?secret[\\s]*[=:]+[\\s]*[^\\s]+"
            redact_file_paths: true
            redact_urls: true
          
          # Output configuration  
          output:
            annotation_style: error  # error, warning, info, success
            annotation_context: ai-error-analysis
            include_confidence: true
            save_as_artifact: true
            artifact_path: ai-analysis-report.json
          
          # Advanced options
          advanced:
            debug_mode: false
            dry_run: false
            max_retries: 3
            custom_prompts:
              compilation_error: "Focus on compilation issues and syntax errors"
              test_failure: "Analyze test failures and assertion errors"
              deployment_error: "Focus on deployment and infrastructure issues"
```

## AI Provider Configuration

### OpenAI Setup

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

```yaml
ai_providers:
  - name: openai
    model: gpt-4o-mini  # or gpt-4o, gpt-3.5-turbo
    api_key_env: OPENAI_API_KEY
    max_tokens: 1000
    timeout: 60
```

### Anthropic Claude Setup

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

```yaml
ai_providers:
  - name: claude
    model: claude-3-haiku-20240307  # or claude-3-sonnet-20240229, claude-3-opus-20240229
    api_key_env: ANTHROPIC_API_KEY
    max_tokens: 1000
    timeout: 60
```

### Google Gemini Setup

```bash
export GOOGLE_API_KEY="your-key-here"
```

```yaml
ai_providers:
  - name: gemini
    model: gemini-1.5-flash  # or gemini-1.5-pro
    api_key_env: GOOGLE_API_KEY
    max_tokens: 1000
    timeout: 60
```

## Examples

### Zero Configuration (Recommended)

Just add the plugin and set an API key:

```yaml
steps:
  - command: "make test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0: ~
```

### Branch-Specific Analysis

Only analyze failures on important branches:

```yaml
steps:
  - command: "npm test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          conditions:
            branches: ["main", "develop", "release/*"]
```

### Multiple Providers with Fallback

Use multiple AI providers for reliability:

```yaml
steps:
  - command: "cargo test"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          ai_providers:
            - name: openai
              model: gpt-4o-mini
            - name: claude  
              model: claude-3-haiku-20240307
          performance:
            fallback_strategy: priority
```

### Custom Error Types

Configure custom prompts for specific error types:

```yaml
steps:
  - command: "pytest"
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          advanced:
            custom_prompts:
              test_failure: |
                Analyze this Python test failure. Focus on:
                1. Assertion errors and expected vs actual values
                2. Import errors and dependency issues  
                3. Environment setup problems
                4. Suggest specific pytest flags or configurations
```

### Async Analysis

Run analysis in background to not block builds:

```yaml
steps:
  - command: "docker build ."
    plugins:
      - your-org/ai-error-analysis#v1.0.0:
          performance:
            async_execution: true
            timeout: 300  # Longer timeout for complex analysis
```

## Security & Privacy

The plugin takes security seriously and implements multiple layers of protection:

### Automatic Redaction
- **Built-in patterns**: Automatically detects and redacts passwords, tokens, API keys, SSH keys, etc.
- **File paths**: Removes user-specific paths like `/home/username/` 
- **URLs**: Redacts credentials in URLs
- **Email addresses**: Partially masks email addresses

### Custom Redaction
Add your own patterns for organization-specific secrets:

```yaml
redaction:
  custom_patterns:
    - "(?i)company[_-]?secret[\\s]*[=:]+[\\s]*[^\\s]+"
    - "(?i)internal[_-]?api[\\s]*[=:]+[\\s]*[^\\s]+"
```

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

## Output Examples

### HTML Annotation
![Example HTML Annotation](docs/images/annotation-example.png)

The plugin creates rich HTML annotations with:
- 🔍 **Root cause analysis**
- 💡 **Numbered suggested fixes**
- 📊 **Confidence scores and metrics**
- 📋 **Error details and context**
- 🏗️ **Collapsible build context**

### JSON Report
```json
{
  "ai_analysis": {
    "provider": "openai",
    "model": "gpt-4o-mini",
    "root_cause": "Test failed due to assertion error in user authentication test",
    "suggested_fixes": [
      "Update the test data to match the new authentication flow",
      "Check if the API endpoint URL has changed",
      "Verify that test environment variables are set correctly"
    ],
    "confidence": 85,
    "severity": "medium"
  },
  "build_context": {
    "pipeline": "web-app-tests",
    "branch": "feature/auth-update", 
    "exit_code": 1
  },
  "performance_metrics": {
    "analysis_time": "3.2s",
    "tokens_used": 245,
    "cached": false
  }
}
```

## Caching

The plugin implements intelligent caching to avoid redundant API calls:

### How Caching Works
1. **Context Analysis**: Creates a fingerprint of the error context
2. **Pattern Matching**: Matches similar errors across builds
3. **Smart Invalidation**: Expires cache entries based on time and relevance
4. **Performance**: Reduces API costs and analysis time

### Cache Configuration
```yaml
performance:
  cache_enabled: true
  cache_ttl: 3600  # 1 hour
```

### Cache Statistics
View cache performance:
```bash
python3 lib/cache_manager.py stats
```

## Development

### Local Testing

1. **Clone the repository**:
```bash
git clone https://github.com/your-org/ai-error-analysis-buildkite-plugin
cd ai-error-analysis-buildkite-plugin
```

2. **Set up environment**:
```bash
export OPENAI_API_KEY="your-key"
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

### Testing Framework

The plugin uses [BATS](https://github.com/bats-core/bats-core) for testing:

```bash
# Run all tests
docker-compose run --rm tests

# Run specific test file
docker-compose run --rm tests tests/post-command.bats

# Run with debug output
docker-compose run --rm tests --verbose-run tests/
```

### Plugin Development

Key files and their purposes:

```
ai-error-analysis-buildkite-plugin/
├── plugin.yml                    # Plugin configuration schema
├── hooks/
│   ├── environment              # Setup and validation
│   ├── post-command             # Main error analysis logic  
│   └── pre-exit                 # Cleanup
├── lib/
│   ├── error_detector.py        # Log parsing and pattern recognition
│   ├── ai_providers.py          # Multi-provider AI integration
│   ├── context_builder.py       # Safe context extraction
│   ├── log_sanitizer.py         # Security and redaction
│   ├── report_generator.py      # Output formatting
│   ├── cache_manager.py         # Result caching
│   ├── health_check.py          # System health validation
│   └── utils.sh                 # Common shell utilities
└── tests/                       # Comprehensive test suite
```

## Troubleshooting

### Common Issues

#### Plugin Not Running
```bash
# Check plugin is properly installed
ls -la .buildkite/plugins/

# Verify environment variables
env | grep BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS

# Check permissions
ls -la hooks/
```

#### API Key Issues  
```bash
# Verify API key is set
echo $OPENAI_API_KEY

# Test API connectivity  
python3 lib/health_check.py
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

### Debug Mode

Enable comprehensive debugging:

```yaml
plugins:
  - your-org/ai-error-analysis#v1.0.0:
      advanced:
        debug_mode: true
```

This provides:
- Detailed execution logs
- API request/response information  
- Context extraction details
- Performance metrics

### Dry Run Mode

Test configuration without making API calls:

```yaml
plugins:
  - your-org/ai-error-analysis#v1.0.0:
      advanced:
        dry_run: true
```

### Health Check

Run comprehensive health check:

```bash
python3 lib/health_check.py
```

Checks:
- ✅ Python version compatibility
- ✅ Required system commands
- ✅ Plugin file integrity
- ✅ File permissions
- ✅ Environment variables
- ✅ AI provider configuration
- ✅ Cache setup
- ✅ Network connectivity
- ✅ Disk space and memory

## Performance

### Optimization Tips

1. **Use Caching**: Enable caching to avoid repeated analysis of similar errors
2. **Limit Context**: Reduce `log_lines` for faster analysis
3. **Choose Faster Models**: Use `gpt-4o-mini` or `claude-3-haiku` for speed
4. **Async Execution**: Enable for non-blocking analysis
5. **Branch Filtering**: Only analyze important branches

### Performance Metrics

The plugin tracks and reports:
- Analysis duration
- API tokens consumed  
- Cache hit rates
- Provider response times
- Memory and disk usage

## API Costs

Approximate costs per analysis (USD):

| Provider | Model | ~Cost/Analysis | Notes |
|----------|-------|---------------|-------|
| OpenAI | GPT-4o-mini | $0.001-0.005 | Recommended for cost |
| OpenAI | GPT-4o | $0.01-0.05 | Best quality |
| Claude | Claude-3-Haiku | $0.001-0.005 | Fast and cheap |
| Claude | Claude-3-Sonnet | $0.005-0.02 | Balanced |
| Gemini | Gemini-1.5-Flash | $0.0005-0.002 | Most economical |

*Costs depend on context size and response length*

### Cost Optimization
- Enable caching to avoid duplicate analyses
- Use smaller context windows for simple errors
- Choose appropriate models for your use case
- Set reasonable rate limits

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Issues and Feature Requests

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/your-org/ai-error-analysis-buildkite-plugin/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/your-org/ai-error-analysis-buildkite-plugin/discussions)
- 📖 **Documentation**: Improvements always welcome

### Development Setup

1. Fork and clone the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

## Support

- 📚 **Documentation**: [Plugin Docs](https://github.com/your-org/ai-error-analysis-buildkite-plugin/docs)
- 💬 **Community**: [Buildkite Community](https://community.buildkite.com/)
- 🐛 **Issues**: [GitHub Issues](https://github.com/your-org/ai-error-analysis-buildkite-plugin/issues)
- 📧 **Enterprise**: Contact your Buildkite representative

---

**Made with ❤️ for the Buildkite community**