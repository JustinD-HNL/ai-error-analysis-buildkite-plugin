#!/bin/bash
# Setup SSH keys for the Buildkite agent container

# Create .ssh directory in container
docker exec buildkite-agent-ai-analysis mkdir -p /home/buildkite-user/.ssh
docker exec buildkite-agent-ai-analysis chmod 700 /home/buildkite-user/.ssh

# Copy your SSH key to the container (replace with your actual key path)
# docker cp ~/.ssh/id_rsa buildkite-agent-ai-analysis:/home/buildkite-user/.ssh/id_rsa
# docker exec buildkite-agent-ai-analysis chmod 600 /home/buildkite-user/.ssh/id_rsa

# Add GitHub to known hosts
docker exec buildkite-agent-ai-analysis bash -c 'ssh-keyscan github.com >> /home/buildkite-user/.ssh/known_hosts'

echo "SSH setup complete. Now copy your SSH key:"
echo "docker cp ~/.ssh/id_rsa buildkite-agent-ai-analysis:/home/buildkite-user/.ssh/id_rsa"
echo "docker exec buildkite-agent-ai-analysis chmod 600 /home/buildkite-user/.ssh/id_rsa"