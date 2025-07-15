#!/bin/bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
MODE="bash"
AGENT_TOKEN="${BUILDKITE_AGENT_TOKEN:-}"
AI_PROVIDER="${AI_PROVIDER:-openai}"
AI_MODEL="${AI_MODEL:-gpt-4o}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        agent)
            MODE="agent"
            shift
            ;;
        test)
            MODE="test"
            shift
            ;;
        bash|shell)
            MODE="bash"
            shift
            ;;
        --token)
            AGENT_TOKEN="$2"
            shift 2
            ;;
        --provider)
            AI_PROVIDER="$2"
            shift 2
            ;;
        --model)
            AI_MODEL="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [mode] [options]"
            echo ""
            echo "Modes:"
            echo "  agent    - Start Buildkite agent"
            echo "  test     - Run plugin tests"
            echo "  bash     - Start interactive shell (default)"
            echo ""
            echo "Options:"
            echo "  --token TOKEN      - Buildkite agent token"
            echo "  --provider NAME    - AI provider (openai, anthropic, google)"
            echo "  --model NAME       - AI model name"
            echo ""
            echo "Environment variables:"
            echo "  BUILDKITE_AGENT_TOKEN"
            echo "  OPENAI_API_KEY"
            echo "  ANTHROPIC_API_KEY"
            echo "  GOOGLE_API_KEY"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Check for API keys
API_KEY_SET=false
if [ -n "${OPENAI_API_KEY:-}" ]; then
    echo -e "${GREEN}✓ OpenAI API key detected${NC}"
    API_KEY_SET=true
fi
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
    echo -e "${GREEN}✓ Anthropic API key detected${NC}"
    API_KEY_SET=true
fi
if [ -n "${GOOGLE_API_KEY:-}" ]; then
    echo -e "${GREEN}✓ Google API key detected${NC}"
    API_KEY_SET=true
fi

if [ "$API_KEY_SET" = false ]; then
    echo -e "${YELLOW}⚠ Warning: No AI provider API key detected${NC}"
    echo "Set one of: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY"
    echo ""
fi

# Check for agent token if running in agent mode
if [ "$MODE" = "agent" ] && [ -z "$AGENT_TOKEN" ]; then
    echo -e "${RED}Error: Buildkite agent token is required for agent mode${NC}"
    echo "Set BUILDKITE_AGENT_TOKEN or use --token option"
    exit 1
fi

# Set the agent token if provided
if [ -n "$AGENT_TOKEN" ]; then
    export BUILDKITE_AGENT_TOKEN="$AGENT_TOKEN"
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Build if image doesn't exist
if ! docker-compose -f "$SCRIPT_DIR/docker-compose.yml" images | grep -q buildkite-agent; then
    echo "Docker image not found. Building..."
    "$SCRIPT_DIR/docker-build.sh"
fi

echo ""
echo "Starting container in $MODE mode..."
echo "AI Provider: $AI_PROVIDER, Model: $AI_MODEL"
echo ""

# Run the container
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" run --rm \
    -e AI_PROVIDER="$AI_PROVIDER" \
    -e AI_MODEL="$AI_MODEL" \
    buildkite-agent "$MODE"