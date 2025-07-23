# AI Provider Setup Guide

This guide explains how to easily switch between different AI providers for the AI Error Analysis Buildkite Plugin.

## Quick Start

1. **Set up your API keys** in the respective `.env` files:
   - `.env.openai` - For OpenAI GPT models
   - `.env.anthropic` - For Anthropic Claude models
   - `.env.gemini` - For Google Gemini models

2. **Switch between providers** using one of these methods:

   ```bash
   # Method 1: Use the switch script (recommended)
   ./switch-provider.sh openai
   ./switch-provider.sh anthropic
   ./switch-provider.sh gemini

   # Method 2: Source directly
   source .env.openai
   source .env.anthropic
   source .env.gemini
   ```

## Environment Files Overview

### `.env.openai`
- **Provider**: OpenAI
- **Default Model**: GPT-4o mini (cost-effective)
- **Available Models**:
  - GPT-4o (most capable)
  - GPT-4o mini (recommended for most cases)
  - GPT-4o nano (fastest, cheapest)
  - o1-preview (advanced reasoning)
  - o1-mini (lightweight reasoning)
  - GPT-4 Turbo (high performance)

### `.env.anthropic`
- **Provider**: Anthropic
- **Default Model**: Claude 3.5 Haiku (cost-effective)
- **Available Models**:
  - Claude Opus 4 (most capable, supports thinking mode)
  - Claude Sonnet 4 (balanced performance)
  - Claude 3.5 Haiku (recommended for most cases)
  - Claude 3.5 Sonnet (high quality)
  - Claude 3 Haiku (fast, economical)

### `.env.gemini`
- **Provider**: Google Gemini
- **Default Model**: Gemini 2.0 Flash (cost-effective)
- **Available Models**:
  - Gemini 2.5 Pro (most capable, supports Deep Think)
  - Gemini 2.0 Flash (recommended for most cases)
  - Gemini 1.5 Flash (fast, reliable)
  - Gemini 1.5 Flash 8B (lightweight)

## Setting Up API Keys

1. **OpenAI**:
   - Get your API key from: https://platform.openai.com/api-keys
   - Edit `.env.openai` and replace `your-openai-api-key-here` with your actual key

2. **Anthropic**:
   - Get your API key from: https://console.anthropic.com/account/keys
   - Edit `.env.anthropic` and replace `your-anthropic-api-key-here` with your actual key

3. **Google Gemini**:
   - Get your API key from: https://makersuite.google.com/app/apikey
   - Edit `.env.gemini` and replace `your-google-gemini-api-key-here` with your actual key

## Usage Examples

### Basic Usage
```bash
# Switch to OpenAI
./switch-provider.sh openai

# Run your Buildkite pipeline
buildkite-agent pipeline upload
```

### Testing Different Providers
```bash
# Test with OpenAI
source .env.openai
buildkite-agent pipeline upload

# Test with Anthropic
source .env.anthropic
buildkite-agent pipeline upload

# Test with Gemini
source .env.gemini
buildkite-agent pipeline upload
```

### Customizing Models
Edit the respective `.env` file and uncomment your preferred model:

```bash
# In .env.openai
# export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL="GPT-4o mini"  # Default
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL="GPT-4o"  # More capable
```

## Environment Variables

Each `.env` file sets these key variables:

| Variable | Description |
|----------|-------------|
| `{PROVIDER}_API_KEY` | Your API key for the provider |
| `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER` | The AI provider to use |
| `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL` | The specific model to use |
| `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MAX_TOKENS` | Maximum response tokens (default: 1000) |
| `BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG` | Enable debug logging (default: false) |

## Cost Optimization Tips

1. **For development/testing**: Use cost-effective models
   - OpenAI: `GPT-4o mini` or `GPT-4o nano`
   - Anthropic: `Claude 3.5 Haiku` or `Claude 3 Haiku`
   - Gemini: `Gemini 2.0 Flash` or `Gemini 1.5 Flash`

2. **For production**: Consider more capable models for better analysis
   - OpenAI: `GPT-4o` or `o1-preview`
   - Anthropic: `Claude Opus 4` or `Claude 3.5 Sonnet`
   - Gemini: `Gemini 2.5 Pro`

3. **Enable caching**: All `.env` files have caching enabled by default to reduce API calls

## Making Configuration Permanent

To avoid sourcing the `.env` file in every new shell session:

```bash
# Add to your ~/.bashrc or ~/.zshrc
echo "source $(pwd)/.env.openai" >> ~/.bashrc  # or ~/.zshrc
```

## Troubleshooting

1. **"API key not found" error**:
   - Ensure you've set the correct API key in the `.env` file
   - Source the file again: `source .env.{provider}`

2. **"Unknown provider" error**:
   - Use only: `openai`, `anthropic`, or `gemini`

3. **Model not recognized**:
   - Check the supported models list above
   - Ensure you're using the exact model name (case-sensitive)

## Security Notes

- Never commit `.env` files with real API keys to version control
- Consider adding `*.env.*` to your `.gitignore`
- For production, use external secret management (AWS Secrets Manager, Vault, etc.)

## Need Help?

Run the switch script without arguments to see current configuration:
```bash
./switch-provider.sh
```