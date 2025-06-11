# Contributing to AI Error Analysis Buildkite Plugin

Thank you for your interest in contributing to the AI Error Analysis Buildkite Plugin! We welcome contributions from the community and are grateful for any help you can provide.

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Use a clear and descriptive title** for the issue
- **Describe the exact steps to reproduce the problem** in as many details as possible
- **Provide specific examples** to demonstrate the steps
- **Describe the behavior you observed** after following the steps
- **Explain which behavior you expected to see instead** and why
- **Include configuration details** such as:
  - Plugin version
  - Buildkite agent version
  - Operating system and version
  - AI provider and model being used
  - Relevant environment variables (redacted)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Use a clear and descriptive title** for the issue
- **Provide a step-by-step description** of the suggested enhancement
- **Provide specific examples** to demonstrate how the enhancement would work
- **Describe the current behavior** and **explain which behavior you expected to see instead**
- **Explain why this enhancement would be useful** to most users

### Your First Code Contribution

Unsure where to begin contributing? You can start by looking through these `beginner` and `help-wanted` issues:

- Beginner issues - issues which should only require a few lines of code
- Help wanted issues - issues which should be a bit more involved than `beginner` issues

### Pull Requests

The process described here has several goals:

- Maintain the plugin's quality
- Fix problems that are important to users
- Engage the community in working toward the best possible plugin
- Enable a sustainable system for maintainers to review contributions

Please follow these steps to have your contribution considered by the maintainers:

1. Follow all instructions in [the template](PULL_REQUEST_TEMPLATE.md)
2. Follow the [styleguides](#styleguides)
3. After you submit your pull request, verify that all [status checks](https://help.github.com/articles/about-status-checks/) are passing

## Styleguides

### Git Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line
- Consider starting the commit message with an applicable emoji:
  - 🎨 `:art:` when improving the format/structure of the code
  - 🐎 `:racehorse:` when improving performance
  - 🚱 `:non-potable_water:` when plugging memory leaks
  - 📝 `:memo:` when writing docs
  - 🐧 `:penguin:` when fixing something on Linux
  - 🍎 `:apple:` when fixing something on macOS
  - 🏁 `:checkered_flag:` when fixing something on Windows
  - 🐛 `:bug:` when fixing a bug
  - 🔥 `:fire:` when removing code or files
  - 💚 `:green_heart:` when fixing the CI build
  - ✅ `:white_check_mark:` when adding tests
  - 🔒 `:lock:` when dealing with security
  - ⬆️ `:arrow_up:` when upgrading dependencies
  - ⬇️ `:arrow_down:` when downgrading dependencies

### Shell Script Styleguide

- Use 2 spaces for indentation
- Use `#!/bin/bash` as the shebang
- Use `set -euo pipefail` for error handling
- Quote variables: `"$variable"` not `$variable`
- Use meaningful variable names
- Comment complex logic
- Follow [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)

Example:
```bash
#!/bin/bash
set -euo pipefail

# Process build output for error analysis
process_build_output() {
  local build_log="$1"
  local output_file="$2"
  
  if [[ ! -f "${build_log}" ]]; then
    echo "Build log not found: ${build_log}" >&2
    return 1
  fi
  
  # Extract error patterns
  grep -E "(ERROR|FAILED|Exception)" "${build_log}" > "${output_file}"
}
```

### Python Styleguide

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use 4 spaces for indentation
- Use type hints where appropriate
- Use docstrings for functions and classes
- Maximum line length: 88 characters (Black formatter default)
- Use meaningful variable and function names
- Import statements should be grouped and sorted

Example:
```python
#!/usr/bin/env python3
"""
Module for analyzing build errors using AI providers.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ErrorAnalysis:
    """Represents the result of AI error analysis."""
    
    root_cause: str
    suggested_fixes: List[str]
    confidence: float
    

def analyze_build_error(log_content: str, provider: str) -> Optional[ErrorAnalysis]:
    """
    Analyze build error using specified AI provider.
    
    Args:
        log_content: The build log content to analyze
        provider: Name of the AI provider to use
        
    Returns:
        ErrorAnalysis object if successful, None otherwise
    """
    if not log_content.strip():
        return None
        
    # Implementation here
    pass
```

### YAML Styleguide

- Use 2 spaces for indentation
- Use double quotes for strings that contain special characters
- Use single quotes for simple strings
- Keep lines under 100 characters when possible
- Use meaningful key names

Example:
```yaml
# Plugin configuration
name: AI Error Analysis
description: Automatically analyzes build failures using AI models
author: https://github.com/your-org/ai-error-analysis-buildkite-plugin

configuration:
  properties:
    ai_providers:
      type: array
      description: List of AI providers to use for error analysis
      items:
        type: object
        properties:
          name:
            type: string
            enum: ["openai", "claude", "gemini"]
```

## Development Setup

### Prerequisites

- Python 3.7 or later
- Docker and Docker Compose
- Git
- Text editor or IDE

### Local Development

1. **Fork and clone the repository**:
```bash
git clone https://github.com/your-username/ai-error-analysis-buildkite-plugin.git
cd ai-error-analysis-buildkite-plugin
```

2. **Set up environment variables**:
```bash
export OPENAI_API_KEY="your-openai-key"  # Optional for testing
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DRY_RUN="true"
export BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_ADVANCED_DEBUG_MODE="true"
```

3. **Run tests**:
```bash
# Run all tests
docker-compose run --rm tests

# Run specific test files
docker-compose run --rm tests tests/post-command.bats
docker-compose run --rm python-tests

# Run linting
docker-compose run --rm lint
```

4. **Test the plugin manually**:
```bash
# Set up test environment
export BUILDKITE_COMMAND_EXIT_STATUS="1"
export BUILDKITE_COMMAND="npm test"
export AI_ERROR_ANALYSIS_PLUGIN_DIR="$PWD"

# Run the hooks
./hooks/environment
./hooks/post-command
./hooks/pre-exit
```

### Testing

We use multiple testing approaches:

1. **BATS tests** for shell script functionality
2. **Python unit tests** with pytest for Python components
3. **Integration tests** using Docker Compose
4. **Manual testing** with real Buildkite pipelines

#### Writing Tests

**BATS Tests** (for shell scripts):
```bash
#!/usr/bin/env bats

load '/usr/local/lib/bats-support/load'
load '/usr/local/lib/bats-assert/load'

@test "description of what you're testing" {
  # Arrange
  export TEST_VAR="test_value"
  
  # Act
  run your_script_or_function
  
  # Assert
  assert_success
  assert_output --partial "expected output"
}
```

**Python Tests** (with pytest):
```python
import pytest
from unittest.mock import patch, Mock

def test_function_name():
    """Test description."""
    # Arrange
    input_data = {"key": "value"}
    
    # Act
    result = function_to_test(input_data)
    
    # Assert
    assert result.status == "success"
    assert "expected" in result.message
```

#### Test Coverage

We aim for high test coverage across all components:

- Shell scripts: Test all major code paths and error conditions
- Python modules: Aim for >90% line coverage
- Integration: Test real-world scenarios and edge cases

### Documentation

- Update README.md for user-facing changes
- Add inline comments for complex logic
- Update configuration examples
- Include docstrings in Python code
- Update CHANGELOG.md for all changes

### Performance Considerations

When contributing, please consider:

- **Plugin execution time**: Keep hooks fast to not slow down builds
- **Memory usage**: Be mindful of memory consumption, especially with large logs
- **API costs**: Optimize AI provider usage to minimize costs
- **Caching**: Implement caching for expensive operations
- **Error handling**: Ensure the plugin never blocks builds

### Security Guidelines

Security is paramount when handling build logs and external APIs:

- **Never log sensitive data**: API keys, secrets, tokens, etc.
- **Sanitize all inputs**: Before sending to AI providers
- **Use environment variables**: For sensitive configuration
- **Validate user inputs**: From plugin configuration
- **Follow least privilege**: Only request necessary permissions

## Release Process

1. Update version in `plugin.yml`
2. Update `CHANGELOG.md` with changes
3. Create a pull request with version bump
4. After merge, create a Git tag: `git tag v1.x.x`
5. Push the tag: `git push origin v1.x.x`
6. GitHub Actions will handle the release

## Questions?

Don't hesitate to ask questions! You can:

- Open an issue for clarification
- Start a discussion in GitHub Discussions
- Reach out to maintainers

## Recognition

Contributors will be recognized in:

- README.md contributors section
- Release notes
- GitHub contributors graph

Thank you for contributing to make CI/CD better for everyone! 🚀
