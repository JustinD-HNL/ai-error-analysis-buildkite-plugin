#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE_NAME="ai-error-analysis-buildkite-plugin"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY_URL="${REGISTRY_URL:-}"

echo "AI Error Analysis Buildkite Plugin - Docker Deployment"
echo "====================================================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Function to build the image
build_image() {
    echo "Building Docker image..."
    cd "$SCRIPT_DIR"
    docker build -t "${IMAGE_NAME}:${IMAGE_TAG}" -f Dockerfile ..
    echo "✓ Image built successfully: ${IMAGE_NAME}:${IMAGE_TAG}"
}

# Function to tag and push to registry
push_to_registry() {
    if [ -z "$REGISTRY_URL" ]; then
        echo "Error: REGISTRY_URL not set"
        echo "Usage: REGISTRY_URL=your-registry.com/path $0 push"
        exit 1
    fi
    
    FULL_IMAGE_NAME="${REGISTRY_URL}/${IMAGE_NAME}:${IMAGE_TAG}"
    echo "Tagging image for registry: $FULL_IMAGE_NAME"
    docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "$FULL_IMAGE_NAME"
    
    echo "Pushing to registry..."
    docker push "$FULL_IMAGE_NAME"
    echo "✓ Image pushed successfully: $FULL_IMAGE_NAME"
}

# Function to run locally with docker-compose
run_compose() {
    echo "Starting with docker-compose..."
    cd "$SCRIPT_DIR"
    docker-compose up -d
    echo "✓ Container started. View logs with: docker-compose logs -f"
    echo "  Stop with: docker-compose down"
}

# Function to run standalone container
run_standalone() {
    echo "Running standalone container..."
    
    # Check for required environment variables
    if [ -z "$BUILDKITE_AGENT_TOKEN" ]; then
        echo "Warning: BUILDKITE_AGENT_TOKEN not set"
    fi
    
    if [ -z "$OPENAI_API_KEY" ] && [ -z "$ANTHROPIC_API_KEY" ] && [ -z "$GOOGLE_API_KEY" ]; then
        echo "Warning: No AI provider API key set (OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY)"
    fi
    
    docker run -d \
        --name buildkite-ai-error-agent \
        -e BUILDKITE_AGENT_TOKEN="${BUILDKITE_AGENT_TOKEN}" \
        -e OPENAI_API_KEY="${OPENAI_API_KEY}" \
        -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
        -e GOOGLE_API_KEY="${GOOGLE_API_KEY}" \
        -e AI_PROVIDER="${AI_PROVIDER:-openai}" \
        -e AI_MODEL="${AI_MODEL:-gpt-4o}" \
        "${IMAGE_NAME}:${IMAGE_TAG}" \
        agent
    
    echo "✓ Agent container started"
    echo "  View logs: docker logs -f buildkite-ai-error-agent"
    echo "  Stop: docker stop buildkite-ai-error-agent && docker rm buildkite-ai-error-agent"
}

# Function to export image
export_image() {
    OUTPUT_FILE="${1:-ai-error-analysis-buildkite-plugin.tar}"
    echo "Exporting Docker image to $OUTPUT_FILE..."
    docker save -o "$OUTPUT_FILE" "${IMAGE_NAME}:${IMAGE_TAG}"
    echo "✓ Image exported to: $OUTPUT_FILE"
    echo "  Load with: docker load -i $OUTPUT_FILE"
}

# Main command handling
case "${1:-help}" in
    build)
        build_image
        ;;
    push)
        build_image
        push_to_registry
        ;;
    compose)
        build_image
        run_compose
        ;;
    run)
        build_image
        run_standalone
        ;;
    export)
        build_image
        export_image "${2}"
        ;;
    help|*)
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  build   - Build the Docker image locally"
        echo "  push    - Build and push to registry (requires REGISTRY_URL env var)"
        echo "  compose - Run with docker-compose"
        echo "  run     - Run standalone container"
        echo "  export  - Export image to tar file"
        echo ""
        echo "Environment variables:"
        echo "  REGISTRY_URL          - Docker registry URL (for push command)"
        echo "  IMAGE_TAG            - Docker image tag (default: latest)"
        echo "  BUILDKITE_AGENT_TOKEN - Buildkite agent token"
        echo "  OPENAI_API_KEY       - OpenAI API key"
        echo "  ANTHROPIC_API_KEY    - Anthropic API key"
        echo "  GOOGLE_API_KEY       - Google API key"
        echo "  AI_PROVIDER          - AI provider to use (default: openai)"
        echo "  AI_MODEL             - AI model to use (default: gpt-4o)"
        echo ""
        echo "Examples:"
        echo "  # Build and run locally"
        echo "  $0 build"
        echo "  $0 run"
        echo ""
        echo "  # Push to Docker Hub"
        echo "  REGISTRY_URL=docker.io/username $0 push"
        echo ""
        echo "  # Push to AWS ECR"
        echo "  REGISTRY_URL=123456789.dkr.ecr.us-east-1.amazonaws.com $0 push"
        echo ""
        echo "  # Export for offline deployment"
        echo "  $0 export my-plugin.tar"
        ;;
esac