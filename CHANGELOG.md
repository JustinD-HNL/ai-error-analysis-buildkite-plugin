# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for Claude Opus 4 (claude-opus-4-20250514) - the most capable coding model
- Support for Claude Sonnet 4 (claude-sonnet-4-20250514)
- Support for OpenAI GPT-4.1 and GPT-4.1-mini with 1M token context window
- Support for Google Gemini 2.0 Flash and Pro models
- Enhanced AI prompts for better GitHub authentication error detection
- Improved checkout hook with GitHub token authentication support
- Command output capture for better error analysis
- Debug mode for troubleshooting authentication issues

### Changed
- Updated AI analysis prompts to be more specific about common errors
- Improved error categorization and root cause detection
- Enhanced security settings in docker-compose.orbstack.yml
- Updated Python requirement to 3.10+ (3.11 recommended)

### Fixed
- Git clone failures now properly detected in checkout hook using pipefail
- GitHub authentication errors now provide specific, actionable fixes
- AI no longer suggests generic "network issues" for authentication failures
- Container now properly receives GitHub token from environment
- Fixed truncated AI analysis output

## [1.0.0] - 2025-01-20

### Added
- 🎉 **Initial release** of AI Error Analysis Buildkite Plugin
- 🤖 **Multi-AI Provider Support**:
  - OpenAI GPT (GPT-4o, GPT-4o-mini, GPT-4.1, GPT-4.1-mini)
  - Anthropic Claude (Claude-3.5-Haiku, Claude-3.5-Sonnet, Claude-3-Opus, Claude Opus 4, Claude Sonnet 4)
  - Google Gemini (Gemini-1.5-Flash, Gemini-1.5-Pro, Gemini-2.0-Flash, Gemini-2.0-Pro)
  - Automatic fallback between providers
- 🔍 **Intelligent Error Detection**:
  - Pattern recognition for compilation errors, test failures, dependency issues
  - Support for 7+ error categories with confidence scoring
  - Context-aware analysis using pipeline metadata
- 🔒 **Security-First Design**:
  - Comprehensive log sanitization before AI analysis
  - Automatic redaction of secrets, tokens, passwords, API keys
  - Configurable custom redaction patterns
  - File path and URL sanitization
- 📊 **Rich Output & Reporting**:
  - Beautiful HTML annotations in Buildkite with confidence scores
  - Structured JSON reports for programmatic consumption
  - Markdown reports for documentation
  - Optional artifact generation for detailed analysis
- ⚡ **Performance Optimizations**:
  - Intelligent caching to avoid redundant API calls
  - Configurable timeouts and rate limiting
  - Async execution options to not block builds
  - Smart context truncation to fit AI model limits
- 🛠 **Flexible Configuration**:
  - Zero-config defaults that work out of the box
  - Extensive customization options for advanced users
  - Branch-specific analysis controls
  - Custom prompts for different error types
- 🎯 **Error Categories**:
  - Compilation errors (syntax, imports, type errors)
  - Test failures (assertions, timeouts, setup errors)
  - Dependency issues (package not found, version conflicts)
  - Network problems (timeouts, DNS failures, certificates)
  - Permission errors (access denied, file permissions)
  - Memory issues (out of memory, segmentation faults)
  - Timeout errors (build timeouts, deployment timeouts)
- 🏗 **Plugin Architecture**:
  - Environment hook for setup and validation
  - Post-command hook for main error analysis
  - Pre-exit hook for cleanup and reporting
  - Comprehensive health check system
  - Utility functions for common operations
- 🧪 **Testing & Quality**:
  - Comprehensive BATS test suite for shell scripts
  - Python unit tests with pytest for core components
  - Integration tests using Docker Compose
  - Health check validation
  - Linting and code quality checks
- 📚 **Documentation**:
  - Comprehensive README with examples
  - Configuration reference
  - Security guidelines
  - Troubleshooting guide
  - API cost optimization tips

### Configuration Options
- **AI Providers**: Multi-provider configuration with fallback strategies
- **Triggers**: Auto, explicit, or always-on analysis modes
- **Conditions**: Exit code filtering, branch restrictions, pattern matching
- **Context**: Configurable log analysis depth and metadata inclusion
- **Security**: Custom redaction patterns and privacy controls
- **Output**: Annotation styling, artifact generation, confidence display
- **Performance**: Caching, timeouts, async execution, rate limiting
- **Advanced**: Debug mode, dry run, custom prompts, retry logic

### Plugin Hooks
- **Environment**: Python validation, dependency installation, API key verification
- **Post-Command**: Error detection, context building, AI analysis, report generation
- **Pre-Exit**: Cleanup, cache management, performance reporting

### Supported Error Types
- **High Confidence**: Compilation, test failures, dependencies, permissions, memory
- **Medium Confidence**: Network issues, timeouts, configuration problems
- **Automatic Detection**: 20+ built-in error patterns with regex matching
- **Custom Patterns**: User-defined error detection rules

### Security Features
- **Automatic Redaction**: Secrets, tokens, passwords, API keys, SSH keys
- **Safe Environment**: Only approved environment variables included
- **Log Sanitization**: File paths, URLs, email addresses, IP addresses
- **Custom Security**: Organization-specific redaction patterns
- **No Data Storage**: No persistent storage of sensitive information

### Performance Features
- **Smart Caching**: Context-based result caching with TTL
- **Rate Limiting**: Configurable API request throttling
- **Async Execution**: Optional background processing
- **Context Optimization**: Intelligent log truncation and relevance filtering
- **Resource Monitoring**: Memory and disk usage tracking

## [0.9.0-beta] - Development

### Added
- Beta testing with selected users
- Core functionality implementation
- Basic error detection patterns
- Single provider support (OpenAI)

### Fixed
- Initial bug fixes from beta testing
- Performance optimizations
- Configuration validation improvements

## [0.1.0-alpha] - Development

### Added
- Initial project structure
- Basic plugin scaffold
- Proof of concept implementation
- Development environment setup

---

## Release Notes

### v1.0.0 - "AI-Powered DevOps Intelligence"

This initial release brings comprehensive AI-powered error analysis to Buildkite pipelines. The plugin automatically detects build failures, analyzes them using state-of-the-art AI models, and provides actionable insights to help developers fix issues faster.

**Key Highlights:**
- 🚀 **Zero-config setup**: Works out of the box with just an API key
- 🔒 **Enterprise-ready security**: Comprehensive data sanitization and privacy controls
- ⚡ **Performance optimized**: Smart caching and async execution options
- 🎯 **High accuracy**: Advanced pattern recognition with confidence scoring
- 🛠 **Highly configurable**: Extensive customization for enterprise environments

**Getting Started:**
```yaml
steps:
  - command: "npm test"
    plugins:
      - JustinD-HNL/ai-error-analysis#v1.0.0: ~
```

**Migration from Beta:**
- No breaking changes from beta versions
- New configuration options are optional
- Existing configurations remain compatible

**Cost Considerations:**
- Typical analysis costs $0.001-0.005 per failure
- Caching reduces costs for similar errors
- Multiple provider options for cost optimization

**Known Limitations:**
- Requires Python 3.7+ on build agents
- API keys must be configured as environment variables
- Large log files (>10MB) may be truncated for analysis

**Next Release (v1.1.0) Preview:**
- Integration with popular notification systems (Slack, Teams)
- Enhanced error categorization with ML models
- Support for custom AI model endpoints
- Advanced analytics and reporting dashboard

---

## Support

For questions, bug reports, or feature requests:
- 📚 **Documentation**: [Plugin README](README.md)
- 🐛 **Issues**: [GitHub Issues](https://github.com/JustinD-HNL/ai-error-analysis-buildkite-plugin/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/JustinD-HNL/ai-error-analysis-buildkite-plugin/discussions)
- 📧 **Enterprise Support**: Contact your Buildkite representative

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.