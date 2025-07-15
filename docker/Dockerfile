# Buildkite Agent with AI Error Analysis Plugin Test Container
FROM ubuntu:24.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Buildkite agent dependencies
    curl \
    git \
    sudo \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    # Python and build tools
    python3.12 \
    python3.12-venv \
    python3-pip \
    build-essential \
    # Plugin requirements
    jq \
    # Additional useful tools
    vim \
    less \
    && rm -rf /var/lib/apt/lists/*

# Create buildkite user
RUN useradd -m -s /bin/bash buildkite && \
    usermod -aG sudo buildkite && \
    echo 'buildkite ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

# Install Buildkite agent
RUN curl -fsSL https://keys.openpgp.org/vks/v1/by-fingerprint/32A37959C2FA5C3C99EFBC32A79206696452D198 | sudo gpg --dearmor -o /usr/share/keyrings/buildkite-agent-archive-keyring.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/buildkite-agent-archive-keyring.gpg] https://apt.buildkite.com/buildkite-agent stable main" | sudo tee /etc/apt/sources.list.d/buildkite-agent.list && \
    apt-get update && \
    apt-get install -y buildkite-agent && \
    rm -rf /var/lib/apt/lists/*

# Set up Python environment
USER buildkite
WORKDIR /home/buildkite

# Create virtual environment
RUN python3.12 -m venv /home/buildkite/.venv

# Copy plugin files (excluding docker directory)
COPY --chown=buildkite:buildkite .. /home/buildkite/ai-error-analysis-buildkite-plugin/

# Install Python dependencies
RUN /home/buildkite/.venv/bin/pip install --upgrade pip && \
    /home/buildkite/.venv/bin/pip install -r /home/buildkite/ai-error-analysis-buildkite-plugin/requirements.txt && \
    /home/buildkite/.venv/bin/pip install -r /home/buildkite/ai-error-analysis-buildkite-plugin/requirements-dev.txt

# Set up Buildkite agent configuration
RUN mkdir -p /home/buildkite/.buildkite-agent/plugins && \
    ln -s /home/buildkite/ai-error-analysis-buildkite-plugin /home/buildkite/.buildkite-agent/plugins/ai-error-analysis

# Create a test pipeline directory
RUN mkdir -p /home/buildkite/test-pipeline

# Environment variables for the agent
ENV BUILDKITE_AGENT_TOKEN="xxx-your-agent-token-here-xxx"
ENV BUILDKITE_AGENT_NAME="docker-test-agent"
ENV BUILDKITE_AGENT_TAGS="docker=true,ai-error-analysis=true"
ENV BUILDKITE_PLUGINS_PATH="/home/buildkite/.buildkite-agent/plugins"
ENV PATH="/home/buildkite/.venv/bin:$PATH"
ENV PYTHONPATH="/home/buildkite/ai-error-analysis-buildkite-plugin/lib:$PYTHONPATH"

# Create startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Buildkite Agent Test Container with AI Error Analysis Plugin"\n\
echo "============================================================"\n\
echo ""\n\
\n\
if [ "$BUILDKITE_AGENT_TOKEN" = "xxx-your-agent-token-here-xxx" ]; then\n\
    echo "WARNING: Please set BUILDKITE_AGENT_TOKEN environment variable"\n\
    echo "You can do this by running the container with:"\n\
    echo "  docker run -e BUILDKITE_AGENT_TOKEN=your-actual-token ..."\n\
    echo ""\n\
fi\n\
\n\
echo "AI Provider Configuration:"\n\
if [ -n "$OPENAI_API_KEY" ]; then\n\
    echo "✓ OpenAI API key is set"\n\
elif [ -n "$ANTHROPIC_API_KEY" ]; then\n\
    echo "✓ Anthropic API key is set"\n\
elif [ -n "$GOOGLE_API_KEY" ]; then\n\
    echo "✓ Google API key is set"\n\
else\n\
    echo "⚠ No AI provider API key detected. Set one of:"\n\
    echo "  - OPENAI_API_KEY"\n\
    echo "  - ANTHROPIC_API_KEY"\n\
    echo "  - GOOGLE_API_KEY"\n\
fi\n\
echo ""\n\
\n\
echo "Plugin location: /home/buildkite/.buildkite-agent/plugins/ai-error-analysis"\n\
echo "Python version: $(python3 --version)"\n\
echo "Buildkite agent version: $(buildkite-agent --version)"\n\
echo ""\n\
\n\
if [ "$1" = "agent" ]; then\n\
    echo "Starting Buildkite agent..."\n\
    exec buildkite-agent start\n\
elif [ "$1" = "test" ]; then\n\
    echo "Running plugin tests..."\n\
    cd /home/buildkite/ai-error-analysis-buildkite-plugin\n\
    python -m pytest tests/python/ -v\n\
else\n\
    echo "Available commands:"\n\
    echo "  agent - Start the Buildkite agent"\n\
    echo "  test  - Run plugin tests"\n\
    echo "  bash  - Start a bash shell"\n\
    echo ""\n\
    echo "Starting bash shell..."\n\
    exec /bin/bash\n\
fi\n\
' > /home/buildkite/entrypoint.sh && chmod +x /home/buildkite/entrypoint.sh

# Create example pipeline for testing
RUN echo 'steps:\n\
  - label: ":hammer: Test Build with Error"\n\
    command: |\n\
      echo "Starting build..."\n\
      echo "This will fail to trigger the AI error analysis"\n\
      exit 1\n\
    plugins:\n\
      - ai-error-analysis:\n\
          enabled: true\n\
          provider: "${AI_PROVIDER:-openai}"\n\
          model: "${AI_MODEL:-gpt-4o}"\n\
          include_context:\n\
            command_output: true\n\
            environment_variables: true\n\
            system_information: true\n\
' > /home/buildkite/test-pipeline/pipeline.yml

WORKDIR /home/buildkite
ENTRYPOINT ["/home/buildkite/entrypoint.sh"]
CMD ["bash"]