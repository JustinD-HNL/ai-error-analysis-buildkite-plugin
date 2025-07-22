# AI Error Analysis Buildkite Plugin - Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Core Components](#core-components)
4. [File Structure](#file-structure)
5. [Data Flow](#data-flow)
6. [Security Architecture](#security-architecture)
7. [Plugin Lifecycle](#plugin-lifecycle)
8. [Source File Documentation](#source-file-documentation)
9. [Configuration Management](#configuration-management)
10. [Extension Points](#extension-points)

## Overview

The AI Error Analysis Buildkite Plugin is a sophisticated CI/CD enhancement tool that automatically analyzes build failures using AI providers (Claude/Anthropic, OpenAI, Google Gemini). When a build command fails, the plugin collects contextual information, sanitizes sensitive data, sends it to an AI provider for analysis, and generates actionable insights that are displayed as Buildkite annotations.

### Key Features
- **Multi-provider AI support** with unified interface
- **Advanced log sanitization** to protect sensitive data
- **Intelligent caching** to reduce API costs and improve performance
- **Flexible report generation** in multiple formats
- **Enterprise-grade security** with external secret management support
- **Container-optimized** architecture for scalability

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Buildkite Agent                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Plugin Hooks                           │  │
│  │                                                          │  │
│  │  environment ──► post-command ──► pre-exit              │  │
│  │       │               │              │                   │  │
│  │       │               │              │                   │  │
│  └───────┼───────────────┼──────────────┼──────────────────┘  │
│          │               │              │                       │
│          ▼               ▼              ▼                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐          │
│  │ Environment  │ │ Error        │ │ Cleanup      │          │
│  │ Setup        │ │ Analysis     │ │ Operations   │          │
│  └──────────────┘ └──────┬───────┘ └──────────────┘          │
│                          │                                      │
│                          ▼                                      │
│        ┌─────────────────────────────────────┐                │
│        │         Core Python Modules          │                │
│        │                                      │                │
│        │  ┌────────────┐  ┌────────────┐    │                │
│        │  │   Log      │  │    AI      │    │                │
│        │  │ Sanitizer  │  │  Analyzer  │    │                │
│        │  └────────────┘  └─────┬──────┘    │                │
│        │                        │            │                │
│        │  ┌────────────┐  ┌────▼──────┐    │                │
│        │  │   Cache    │  │ AI Provider│    │                │
│        │  │  Manager   │  │ Interface  │    │                │
│        │  └────────────┘  └────┬──────┘    │                │
│        │                        │            │                │
│        │  ┌────────────────────▼──────┐     │                │
│        │  │    Report Generator       │     │                │
│        │  └───────────────────────────┘     │                │
│        └─────────────────────────────────────┘                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   External Services    │
                    │                        │
                    │  • Anthropic Claude   │
                    │  • OpenAI GPT         │
                    │  • Google Gemini      │
                    │  • AWS Secrets Mgr    │
                    │  • HashiCorp Vault    │
                    └────────────────────────┘
```

## Core Components

### 1. **Hook Scripts** (Bash)
The plugin integrates with Buildkite through three lifecycle hooks:

- **environment**: Validates prerequisites and sets up the execution environment
- **post-command**: Main entry point that triggers analysis after command failure
- **pre-exit**: Cleanup operations and resource management

### 2. **Python Analysis Engine**
Core business logic implemented in Python for:
- Complex data processing and AI communication
- Secure handling of sensitive information
- Structured report generation
- Caching and performance optimization

### 3. **AI Provider Abstraction**
Unified interface for multiple AI providers with:
- Provider-specific adapters
- Intelligent retry logic
- Token usage tracking
- Response normalization

### 4. **Security Layer**
Multi-layered security approach:
- Comprehensive log sanitization
- External secret management integration
- Container security enforcement
- Audit logging

## File Structure

```
ai-error-analysis-buildkite-plugin/
│
├── hooks/                      # Buildkite lifecycle hooks
│   ├── environment            # Pre-execution setup and validation
│   ├── post-command           # Main analysis trigger
│   └── pre-exit              # Cleanup and finalization
│
├── lib/                       # Core Python modules
│   ├── __init__.py           # Package initialization
│   ├── analyze.py            # AI analysis orchestrator
│   ├── ai_providers.py       # Provider abstraction layer
│   ├── cache_manager.py      # Caching implementation
│   ├── log_sanitizer.py      # Security sanitization
│   └── report_generator.py   # Report formatting engine
│
├── docker/                    # Container configurations
│   ├── Dockerfile            # Main container image
│   ├── docker-compose.yml    # Standard deployment
│   └── docker-compose.orbstack.yml # OrbStack deployment
│
├── testing/                   # Test scripts and pipelines
│   ├── test-*.sh             # Test scripts
│   ├── *-pipeline.yml        # Test pipeline configurations
│   └── README.md             # Testing documentation
│
├── tests/                     # Test suite (future)
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test data
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md       # This file
│   ├── ORBSTACK-README.md    # OrbStack setup guide
│   └── API.md               # API documentation
│
├── plugin.yml                # Buildkite plugin definition
├── requirements.txt          # Python dependencies
└── README.md                # Project overview
```

## Data Flow

### 1. **Failure Detection**
```
Build Command Fails → Exit Code ≠ 0 → post-command hook triggered
```

### 2. **Context Collection**
```
Build Metadata + Command Output + Git Information → Context JSON
```

### 3. **Sanitization Pipeline**
```
Raw Context → Log Sanitizer → Redacted Context → Safe for AI
```

### 4. **AI Analysis**
```
Sanitized Context → AI Provider → Structured Analysis → Cache Storage
```

### 5. **Report Generation**
```
Analysis Result + Build Context → Report Generator → Markdown/HTML/JSON
```

### 6. **Annotation Creation**
```
Formatted Report → Buildkite Agent → Build Annotation → User Interface
```

## Security Architecture

### Threat Model
The plugin handles sensitive data including:
- API keys and tokens
- Build logs with potential secrets
- Database connection strings
- Internal file paths and URLs

### Security Controls

1. **Input Sanitization**
   - Comprehensive regex patterns for 50+ secret types
   - Intelligent redaction preserving context
   - File path anonymization
   - URL credential removal

2. **Secret Management**
   - Support for external secret stores (AWS, Vault, GCP)
   - Environment variable isolation
   - Secure credential passing
   - Automatic cleanup on exit

3. **Container Security**
   - Non-root user enforcement
   - Read-only filesystem mounts
   - Network isolation options
   - Resource limits

4. **Audit Trail**
   - Sanitization metrics tracking
   - Security score calculation
   - Pattern match logging
   - Performance monitoring

## Plugin Lifecycle

### 1. **Initialization Phase** (`environment` hook)
```python
1. Validate Python 3.10+ availability
2. Check required commands (curl, jq)
3. Validate AI provider configuration
4. Set up secure environment variables
5. Initialize cache directory
6. Install Python dependencies
```

### 2. **Analysis Phase** (`post-command` hook)
```python
1. Check command exit status
2. Validate plugin configuration
3. Retrieve API credentials securely
4. Collect build context:
   - Build metadata
   - Command output (last 100 lines)
   - Git information
   - Pipeline details
5. Sanitize collected data
6. Check cache for existing analysis
7. If not cached:
   - Send to AI provider
   - Parse response
   - Store in cache
8. Generate report
9. Create Buildkite annotation
```

### 3. **Cleanup Phase** (`pre-exit` hook)
```python
1. Remove temporary files
2. Clear sensitive environment variables
3. Finalize any pending operations
4. Log performance metrics
```

## Source File Documentation

### `/hooks/environment`
**Purpose**: Pre-execution environment setup and validation

**Key Functions**:
- `validate_ai_providers()`: Ensures AI provider/model combinations are valid
- `validate_external_secrets()`: Checks secret management configuration
- `setup_caching()`: Initializes secure cache directory
- `install_dependencies()`: Ensures Python packages are available

**Why**: Fails fast if configuration is invalid, preventing wasted compute time

### `/hooks/post-command`
**Purpose**: Main plugin logic triggered after command execution

**Key Functions**:
- `get_api_key()`: Securely retrieves API credentials from configured source
- `analyze_error()`: Orchestrates the entire analysis pipeline
- `generate_report()`: Creates formatted output for users
- `create_fallback_annotation()`: Provides useful feedback even on failure

**Why**: Central orchestrator that coordinates all plugin operations

### `/hooks/pre-exit`
**Purpose**: Cleanup operations ensuring no sensitive data persists

**Key Functions**:
- `cleanup_temp_files()`: Secure deletion of temporary data
- `clear_environment()`: Removes sensitive variables
- `log_metrics()`: Records performance data

**Why**: Security best practice to minimize data exposure window

### `/lib/analyze.py`
**Purpose**: Core AI analysis engine with provider abstraction

**Key Classes**:
- `AIAnalyzer`: Main analysis orchestrator
- `AnalysisResult`: Structured result container

**Key Methods**:
- `analyze()`: Performs AI analysis of build failure
- `_build_prompt()`: Constructs optimized prompts for each provider
- `_parse_response()`: Extracts structured data from AI responses

**Why**: Centralizes AI logic, making it easy to add new providers

### `/lib/ai_providers.py`
**Purpose**: Legacy provider interface (being phased out)

**Note**: Functionality being merged into `analyze.py` for simplification

### `/lib/cache_manager.py`
**Purpose**: Intelligent caching to reduce API costs

**Key Classes**:
- `CacheManager`: Handles cache operations
- `CacheKey`: Generates deterministic cache keys

**Key Methods**:
- `get()`: Retrieves cached analysis if available
- `set()`: Stores analysis results with TTL
- `invalidate()`: Clears cache entries

**Why**: Prevents duplicate API calls for identical failures, saving costs

### `/lib/log_sanitizer.py`
**Purpose**: Comprehensive security sanitization

**Key Classes**:
- `LogSanitizer`: Main sanitization engine
- `SanitizationResult`: Detailed sanitization report

**Key Features**:
- 50+ regex patterns for secret detection
- Partial redaction for IPs and emails
- Security score calculation
- Pattern match tracking

**Why**: Critical security component preventing secret leakage

### `/lib/report_generator.py`
**Purpose**: Flexible report generation in multiple formats

**Key Classes**:
- `ReportGenerator`: Main report engine
- `ReportSection`: Modular report components

**Supported Formats**:
- **Markdown**: For Buildkite annotations
- **HTML**: For web display (legacy)
- **JSON**: For programmatic access

**Why**: Provides flexibility in how results are consumed

## Configuration Management

### Plugin Configuration (`plugin.yml`)
```yaml
name: AI Error Analysis
description: Automated error analysis using AI
author: https://github.com/your-org
configuration:
  properties:
    provider:
      type: string
      enum: [anthropic, openai, gemini]
    model:
      type: string
    max_tokens:
      type: integer
      default: 1000
```

### Environment Variables
```bash
# Required
BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER
BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_API_KEY_ENV

# Optional
BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL
BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MAX_TOKENS
BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ENABLE_CACHING
BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG
```

### Secret Sources
1. **Environment Variables** (development)
2. **AWS Secrets Manager** (recommended for AWS)
3. **HashiCorp Vault** (recommended for multi-cloud)
4. **Google Secret Manager** (recommended for GCP)

## Extension Points

### Adding New AI Providers

1. Update `SUPPORTED_MODELS` in `analyze.py`:
```python
"newprovider": {
    "model-name": {
        "endpoint": "chat/completions",
        "max_tokens": 4096,
        "cost_per_1k": 0.01
    }
}
```

2. Implement provider method:
```python
def _call_newprovider(self, prompt: str) -> Dict[str, Any]:
    # Provider-specific API call
    pass
```

3. Add response parser in `_parse_response()`

### Adding New Sanitization Patterns

1. Add pattern to `_compile_redaction_patterns()`:
```python
patterns['new_secret_type'] = re.compile(
    r'pattern-regex-here',
    re.MULTILINE
)
```

2. Optionally add custom redaction logic in `_sanitize_text()`

### Custom Report Formats

1. Add new method to `ReportGenerator`:
```python
def generate_custom_report(self, analysis_result, context):
    # Custom formatting logic
    pass
```

2. Update `main()` to handle new format

## Performance Considerations

### Caching Strategy
- Cache key based on: command + exit code + log hash
- Default TTL: 1 hour
- Cache size limit: 100MB
- LRU eviction policy

### API Optimization
- Batched context collection
- Compressed API payloads
- Retry with exponential backoff
- Connection pooling

### Resource Limits
- Max log size: 5000 characters
- Max analysis time: 120 seconds
- Max memory usage: 512MB
- Max tokens per request: 4096

## Monitoring and Observability

### Metrics Tracked
- Analysis success/failure rate
- API response times
- Token usage per provider
- Cache hit rate
- Sanitization performance

### Debug Mode
Enable with `AI_DEBUG=true` for:
- Raw AI responses
- Sanitization details
- Cache operations
- Performance timings

### Health Checks
- Provider API connectivity
- Secret retrieval success
- Python dependency availability
- Disk space for cache

## Best Practices

### For Plugin Users
1. Use external secret management in production
2. Configure appropriate models for your use case
3. Monitor token usage to control costs
4. Review sanitization patterns regularly
5. Test with non-sensitive pipelines first

### For Contributors
1. Maintain backward compatibility
2. Add tests for new features
3. Update documentation
4. Follow security-first approach
5. Consider performance impact

## Future Roadmap

### Planned Features
1. **Multi-language support** for international teams
2. **Custom AI model fine-tuning** for domain-specific analysis
3. **Trend analysis** across multiple failures
4. **Integration with incident management** systems
5. **Advanced caching** with distributed storage
6. **Webhook notifications** for critical failures

### Architecture Evolution
1. **Microservices architecture** for scalability
2. **GraphQL API** for flexible querying
3. **WebAssembly plugins** for custom logic
4. **Kubernetes operator** for cloud-native deployment

## Conclusion

The AI Error Analysis Buildkite Plugin represents a sophisticated approach to automated failure analysis in CI/CD pipelines. Its modular architecture, comprehensive security measures, and flexible extension points make it suitable for both small teams and large enterprises.

The plugin's design prioritizes:
- **Security**: Multiple layers of protection for sensitive data
- **Reliability**: Robust error handling and fallback mechanisms
- **Performance**: Intelligent caching and optimization
- **Extensibility**: Clear interfaces for customization
- **Usability**: Simple configuration with sensible defaults

By leveraging modern AI capabilities while maintaining strict security standards, the plugin transforms build failures from frustrating interruptions into learning opportunities, ultimately improving development velocity and code quality.