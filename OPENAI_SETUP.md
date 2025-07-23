# OpenAI Setup Guide for AI Error Analysis Plugin

## Available OpenAI Models (January 2025)

### Recommended Models

1. **GPT-4o-mini** (Default) - Best for most use cases
   - Cost: $0.15 per 1M tokens
   - 128K context window
   - Fast and cost-effective
   - Great for error analysis

2. **GPT-4o** - For complex analysis
   - Cost: $5 per 1M tokens  
   - 128K context window
   - Multimodal capabilities
   - Best performance

3. **o1-mini** - For technical problems
   - Cost: $3 per 1M tokens
   - Advanced reasoning
   - Great for debugging complex issues
   - STEM-focused

### Configuration Examples

#### Basic Setup (Recommended)
```yaml
steps:
  - label: "Tests"
    command: "npm test"
    plugins:
      - JustinD-HNL/ai-error-analysis-buildkite-plugin:
          provider: "openai"
          model: "gpt-4o-mini"  # Cost-effective default
```

#### Advanced Analysis
```yaml
steps:
  - label: "Complex Build"
    command: "make build"
    plugins:
      - JustinD-HNL/ai-error-analysis-buildkite-plugin:
          provider: "openai"
          model: "gpt-4o"  # More powerful analysis
          max_tokens: 2000
```

#### Technical/STEM Issues
```yaml
steps:
  - label: "Scientific Computing"
    command: "python test_simulation.py"
    plugins:
      - JustinD-HNL/ai-error-analysis-buildkite-plugin:
          provider: "openai"
          model: "o1-mini"  # Better reasoning for technical issues
```

## Setting Up Your API Key

### Option 1: Environment Variable (Development)
```bash
export OPENAI_API_KEY="sk-..."
```

### Option 2: AWS Secrets Manager (Production)
```yaml
plugins:
  - JustinD-HNL/ai-error-analysis-buildkite-plugin:
      provider: "openai"
      model: "gpt-4o-mini"
      secret_source:
        type: aws_secrets_manager
        secret_name: buildkite/openai-api-key
        region: us-east-1
```

### Option 3: .env File (Local Testing)
```bash
# .env file
OPENAI_API_KEY=sk-...
```

## Cost Optimization Tips

1. **Start with gpt-4o-mini** - It's extremely cost-effective at $0.15/1M tokens
2. **Use caching** - Enable caching to avoid redundant API calls:
   ```yaml
   enable_caching: true
   ```
3. **Limit token usage** - Set reasonable limits:
   ```yaml
   max_tokens: 1000  # Usually sufficient for error analysis
   ```

## Model Selection Guide

| Use Case | Recommended Model | Why |
|----------|------------------|-----|
| General CI/CD errors | `gpt-4o-mini` | Fast, cheap, effective |
| Complex build failures | `gpt-4o` | Better understanding |
| Mathematical/algorithmic errors | `o1-mini` | Advanced reasoning |
| Legacy compatibility | `gpt-4-turbo` | Stable, well-tested |

## Troubleshooting

### Common Issues

1. **Authentication Error**
   ```
   Error: Invalid API key
   ```
   - Verify your API key starts with `sk-`
   - Check it hasn't expired
   - Ensure no extra spaces

2. **Model Not Found**
   ```
   Error: Model 'gpt-4' does not exist
   ```
   - Use the full model name: `gpt-4o` or `gpt-4o-mini`
   - Check the supported models list above

3. **Rate Limits**
   - GPT-4o-mini: 30,000 TPM (tokens per minute)
   - GPT-4o: 10,000 TPM
   - Consider using retry logic

## Example Pipeline

```yaml
# .buildkite/pipeline.yml
steps:
  - label: "Unit Tests"
    command: "npm test"
    plugins:
      - JustinD-HNL/ai-error-analysis-buildkite-plugin:
          provider: "openai"
          model: "gpt-4o-mini"
          max_tokens: 1500
          enable_caching: true
          debug: false
          
  - label: "Integration Tests"
    command: "npm run test:integration"
    plugins:
      - JustinD-HNL/ai-error-analysis-buildkite-plugin:
          provider: "openai"
          model: "gpt-4o"  # More complex analysis needed
          max_tokens: 2000
          context:
            include_git_info: true
            custom_context: "Docker-based integration tests"
```

## Getting an API Key

1. Go to https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Give it a descriptive name (e.g., "buildkite-error-analysis")
4. Copy the key (starts with `sk-`)
5. Store it securely in your secret management system

## Further Resources

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [OpenAI Pricing](https://openai.com/pricing)
- [Model Comparison](https://platform.openai.com/docs/models)