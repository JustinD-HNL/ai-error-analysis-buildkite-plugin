#!/bin/bash
# AI Error Analysis Buildkite Plugin - Provider Switching Script
# This script helps you easily switch between AI providers

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${BLUE}AI Error Analysis Provider Switcher${NC}"
    echo ""
    echo "Usage: ./switch-provider.sh [provider]"
    echo ""
    echo "Available providers:"
    echo "  openai     - Use OpenAI GPT models"
    echo "  anthropic  - Use Anthropic Claude models"
    echo "  gemini     - Use Google Gemini models"
    echo ""
    echo "Examples:"
    echo "  ./switch-provider.sh openai"
    echo "  ./switch-provider.sh anthropic"
    echo ""
    echo "Current configuration:"
    if [[ -n "${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER:-}" ]]; then
        echo -e "  Provider: ${GREEN}${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER}${NC}"
        echo -e "  Model: ${GREEN}${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL:-default}${NC}"
    else
        echo -e "  ${YELLOW}No provider currently configured${NC}"
    fi
}

# Function to check if .env file exists
check_env_file() {
    local provider=$1
    local env_file=".env.${provider}"
    
    if [[ ! -f "${env_file}" ]]; then
        echo -e "${RED}Error: ${env_file} not found!${NC}"
        echo "Please create the environment file first."
        exit 1
    fi
}

# Function to validate API key
validate_api_key() {
    local provider=$1
    local api_key_var
    
    case "${provider}" in
        openai)
            api_key_var="OPENAI_API_KEY"
            ;;
        anthropic)
            api_key_var="ANTHROPIC_API_KEY"
            ;;
        gemini)
            api_key_var="GEMINI_API_KEY"
            ;;
    esac
    
    if [[ -z "${!api_key_var:-}" ]] || [[ "${!api_key_var}" == "your-${provider}-api-key-here" ]]; then
        echo -e "${YELLOW}Warning: ${api_key_var} is not set or contains placeholder value${NC}"
        echo "Please update your API key in .env.${provider}"
    fi
}

# Main logic
if [[ $# -eq 0 ]]; then
    usage
    exit 0
fi

PROVIDER=$1

case "${PROVIDER}" in
    openai|anthropic|gemini)
        check_env_file "${PROVIDER}"
        
        echo -e "${BLUE}Switching to ${PROVIDER} provider...${NC}"
        
        # Source the environment file
        source ".env.${PROVIDER}"
        
        # Validate configuration
        validate_api_key "${PROVIDER}"
        
        echo -e "${GREEN}Successfully switched to ${PROVIDER}!${NC}"
        echo ""
        echo "Configuration loaded:"
        echo "  Provider: ${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PROVIDER}"
        echo "  Model: ${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MODEL}"
        echo "  Max Tokens: ${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_MAX_TOKENS}"
        echo "  Debug Mode: ${BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_DEBUG}"
        echo ""
        echo -e "${YELLOW}Note: This configuration is only active in your current shell session.${NC}"
        echo "To make it permanent, add 'source $(pwd)/.env.${PROVIDER}' to your shell profile."
        ;;
    *)
        echo -e "${RED}Error: Unknown provider '${PROVIDER}'${NC}"
        echo ""
        usage
        exit 1
        ;;
esac