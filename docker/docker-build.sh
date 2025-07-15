#!/bin/bash
set -euo pipefail

echo "Building Buildkite Agent Docker container with AI Error Analysis Plugin..."
echo ""

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Build the Docker image
docker-compose -f "$SCRIPT_DIR/docker-compose.yml" build buildkite-agent

echo ""
echo "Build complete!"
echo ""
echo "To run the container:"
echo ""
echo "1. Interactive mode (recommended for testing):"
echo "   cd docker && docker-compose run --rm buildkite-agent"
echo ""
echo "2. Start the Buildkite agent:"
echo "   cd docker && BUILDKITE_AGENT_TOKEN=your-token docker-compose run --rm buildkite-agent agent"
echo ""
echo "3. Run plugin tests:"
echo "   cd docker && docker-compose run --rm buildkite-agent test"
echo ""
echo "4. Start with environment file:"
echo "   cd docker && docker-compose --env-file .env up"
echo ""
echo "Or use the docker-run.sh script from the project root:"
echo "   ./docker/docker-run.sh [agent|test|bash]"
echo ""
echo "Remember to set your API keys:"
echo "  - BUILDKITE_AGENT_TOKEN (required for agent)"
echo "  - OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY (at least one required)"