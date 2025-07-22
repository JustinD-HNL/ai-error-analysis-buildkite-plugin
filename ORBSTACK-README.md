# OrbStack Setup for AI Error Analysis Buildkite Plugin

This guide provides instructions for running and testing the AI Error Analysis Buildkite Plugin using OrbStack on macOS.

## Prerequisites

- **OrbStack** installed on macOS ([Download here](https://orbstack.dev/))
- **Buildkite account** with an agent token
- **AI provider API key** (Anthropic/Claude, OpenAI, or Google)
- **Docker Compose** (included with OrbStack)

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/JustinD-HNL/ai-error-analysis-buildkite-plugin.git
cd ai-error-analysis-buildkite-plugin
```

### 2. Configure Environment

Create a `.env` file in the project root:

```bash
# Required: Buildkite Configuration
BUILDKITE_AGENT_TOKEN=your-buildkite-agent-token-here

# Required: AI Provider API Key (choose one)
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here  # For Claude
# OR
OPENAI_API_KEY=sk-proj-your-key-here          # For OpenAI
# OR
GOOGLE_API_KEY=your-google-api-key-here       # For Gemini

# Optional: Plugin Configuration
AI_PROVIDER=anthropic              # Options: anthropic, openai, gemini
AI_MODEL=claude-3-opus-20240229    # Model to use
AI_MAX_TOKENS=2000                 # Max response tokens
AI_DEBUG=false                     # Enable debug logging
```

### 3. Launch the Container

```bash
# Build and start the agent
docker compose -f docker-compose.orbstack.yml up -d --build

# View logs
docker compose -f docker-compose.orbstack.yml logs -f

# Check status
docker ps | grep buildkite-agent-ai-analysis
```

## Testing the Plugin

### 1. Create a Test Pipeline

In your Buildkite dashboard, create a new pipeline with this YAML:

```yaml
steps:
  - label: ":boom: Test AI Error Analysis"
    command: |
      echo "=== Starting Application ==="
      echo "Loading configuration..."
      echo "Connecting to database..."
      echo ""
      echo "ERROR: Failed to connect to PostgreSQL"
      echo "psql: could not connect to server: Connection refused"
      echo "  Is the server running on host 'localhost' and accepting"
      echo "  TCP/IP connections on port 5432?"
      echo ""
      echo "Stack trace:"
      echo "  at connectDB() database.js:45"
      echo "  at main() app.js:12"
      exit 1
    agents:
      queue: default
```

**Important**: Set the repository to a public GitHub repo (e.g., `https://github.com/buildkite/agent`) or leave it empty to avoid authentication issues.

### 2. Run the Build

1. Trigger a new build in Buildkite
2. The agent will pick up the job
3. The command will fail (exit 1)
4. The AI Error Analysis plugin will analyze the error
5. Check the build page for the AI-generated analysis annotation

### 3. Expected Output

You should see an annotation on the build page with:
- **Root cause analysis** of the PostgreSQL connection error
- **Suggested fixes** from Claude/your chosen AI
- **Confidence level** of the analysis
- **Related context** from the build

## Common Operations

### View Agent Logs

```bash
# Real-time logs
docker logs -f buildkite-agent-ai-analysis

# Last 100 lines
docker logs --tail 100 buildkite-agent-ai-analysis
```

### Restart the Agent

```bash
docker compose -f docker-compose.orbstack.yml restart
```

### Stop the Agent

```bash
docker compose -f docker-compose.orbstack.yml down
```

### Update Plugin Code

After making changes to the plugin:

```bash
# Rebuild with latest changes
docker compose -f docker-compose.orbstack.yml down
docker compose -f docker-compose.orbstack.yml up -d --build
```

### Run Multiple Agents

```bash
# Run 3 agents for parallel processing
docker compose -f docker-compose.orbstack.yml up -d --scale buildkite-agent=3
```

## Debugging

### Check Environment Variables

```bash
docker exec buildkite-agent-ai-analysis env | grep -E "(AI_|ANTHROPIC|OPENAI|BUILDKITE_PLUGIN)" | sort
```

### Access Container Shell

```bash
docker exec -it buildkite-agent-ai-analysis bash
```

### Test Python Scripts Directly

```bash
# Enter container
docker exec -it buildkite-agent-ai-analysis bash

# Activate Python environment
source /home/buildkite-user/.venv/bin/activate

# Test scripts
python3 /buildkite/plugins/ai-error-analysis/lib/ai_providers.py
```

### Enable Debug Mode

Set `AI_DEBUG=true` in your `.env` file for verbose logging.

## Troubleshooting

### Agent Not Connecting

- Verify `BUILDKITE_AGENT_TOKEN` is correct
- Check agent logs: `docker logs buildkite-agent-ai-analysis`
- Ensure agent tags match pipeline requirements

### AI Analysis Not Running

- Verify AI provider API key is set correctly
- Ensure command actually fails (exits with non-zero status)
- Check post-command hook logs in build output
- Verify Python dependencies: `docker exec buildkite-agent-ai-analysis pip list`

### Repository Clone Errors

- Use HTTPS URLs instead of SSH for public repos
- Leave repository field empty for testing
- Or add SSH keys to container if needed

### JSON Parsing Errors

If you see "Expecting ',' delimiter" errors:
- Rebuild the container to get latest fixes
- Check for special characters in command output

## Advanced Configuration

### Using Different AI Models

```bash
# Claude 3.5 Sonnet (faster, cheaper)
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022

# GPT-4
AI_PROVIDER=openai
AI_MODEL=gpt-4o

# Gemini Pro
AI_PROVIDER=gemini
AI_MODEL=gemini-pro
```

### Custom Pipeline Example

```yaml
steps:
  - label: ":rocket: Build Application"
    command: |
      npm install
      npm run build
      npm test
    plugins:
      - ai-error-analysis-buildkite-plugin:
          enabled: true
          provider: "anthropic"
          model: "claude-3-opus-20240229"
          max_tokens: 3000
          include_context:
            command_output: true
            environment_variables: true
            system_information: true
          output:
            style: "error"
            include_confidence: true
            save_artifact: true
    agents:
      queue: default
```

## Monitoring in OrbStack

1. Open OrbStack app
2. Navigate to Containers
3. Find `buildkite-agent-ai-analysis`
4. View:
   - Resource usage (CPU, Memory)
   - Real-time logs
   - Network activity
   - File system changes

## Cleanup

To completely remove the setup:

```bash
# Stop and remove containers
docker compose -f docker-compose.orbstack.yml down

# Remove volumes
docker volume rm ai-error-analysis-buildkite-plugin_buildkite-builds

# Remove images
docker rmi ai-error-analysis-buildkite-plugin-buildkite-agent
```

## Support

- **Plugin Issues**: Create an issue in this repository
- **OrbStack Issues**: Check [OrbStack Documentation](https://docs.orbstack.dev/)
- **Buildkite Issues**: Visit [Buildkite Support](https://buildkite.com/support)