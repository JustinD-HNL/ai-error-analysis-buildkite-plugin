# Testing Guide for AI Error Analysis Buildkite Plugin

This document provides comprehensive information about running and maintaining tests for the AI Error Analysis Buildkite Plugin.

## Prerequisites

Before running tests, ensure you have the following installed:

1. Python 3.8 or higher
2. pip (Python package manager)
3. Docker (for containerized tests)
4. Buildkite CLI (optional, for local testing)

## Installation

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Install the plugin in development mode:
```bash
pip install -e .
```

## Test Structure

The test suite is organized into several categories:

### 1. Unit Tests (`tests/python/test_core_functions.py`)
Tests for individual components and functions:
- Configuration validation
- Log sanitization
- Build context collection
- Error analysis formatting
- API response handling

### 2. Integration Tests (`tests/python/test_provider_integration.py`)
Tests for AI provider integrations:
- OpenAI provider
- Anthropic provider
- Gemini provider
- Error handling
- Rate limiting
- Timeout handling

### 3. Security Tests (`tests/python/test_secret_management.py`)
Tests for secret management and security features:
- AWS Secrets Manager
- HashiCorp Vault
- Google Cloud Secret Manager
- Secret rotation
- Secret validation
- Encryption/decryption

### 4. End-to-End Tests (`tests/python/test_e2e.py`)
Tests for complete workflows:
- Full error analysis flow
- Retry mechanisms
- Timeout handling
- Secret management
- Log sanitization
- Custom context handling

## Running Tests

### Run All Tests
```bash
pytest tests/python/
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest tests/python/test_core_functions.py

# Run only integration tests
pytest tests/python/test_provider_integration.py

# Run only security tests
pytest tests/python/test_secret_management.py

# Run only end-to-end tests
pytest tests/python/test_e2e.py
```

### Run Tests with Coverage
```bash
pytest --cov=lib tests/python/
```

### Run Tests in Parallel
```bash
pytest -n auto tests/python/
```

### Run Tests with Verbose Output
```bash
pytest -v tests/python/
```

## Test Configuration

### Environment Variables
Some tests require specific environment variables to be set:

```bash
# For AWS tests
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1

# For Vault tests
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=test

# For GCP tests
export GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
```

### Mocking External Services
Tests use mocking to avoid actual API calls. The following services are mocked:
- AI provider APIs (OpenAI, Anthropic, Gemini)
- Secret management services (AWS, Vault, GCP)
- Buildkite API

## Writing New Tests

### Test Structure
Follow this pattern for new tests:

```python
import pytest
from unittest.mock import patch, MagicMock

class TestNewFeature:
    @pytest.fixture
    def setup_data(self):
        # Setup test data
        return {}

    def test_feature_behavior(self, setup_data):
        # Test implementation
        pass
```

### Best Practices
1. Use descriptive test names
2. One assertion per test when possible
3. Use fixtures for common setup
4. Mock external dependencies
5. Include both positive and negative test cases

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project root directory
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   ```

2. **Missing Dependencies**
   ```bash
   # Update dependencies
   pip install -r requirements-dev.txt --upgrade
   ```

3. **Test Timeouts**
   ```bash
   # Increase timeout
   pytest --timeout=300 tests/python/
   ```

### Debugging Tests

1. Run with debug output:
```bash
pytest -vv --pdb tests/python/
```

2. Run specific test with debug:
```bash
pytest -vv --pdb tests/python/test_core_functions.py::TestCoreFunctions::test_specific_function
```

## Continuous Integration

Tests are automatically run in the following scenarios:
- On every pull request
- On every push to main branch
- On every release

### CI Configuration
The plugin uses Buildkite for CI. The pipeline configuration can be found in `.buildkite/pipeline.yml`.

## Test Maintenance

### Updating Tests
1. Keep tests up to date with code changes
2. Update mocks when external APIs change
3. Review and update test data regularly

### Adding New Tests
1. Create new test file in `tests/python/`
2. Follow existing naming conventions
3. Add appropriate test categories
4. Update this documentation

## Performance Considerations

- Tests should run quickly (under 5 minutes)
- Use appropriate mocking to avoid slow external calls
- Consider parallel test execution for large test suites

## Security Considerations

- Never commit real API keys or secrets
- Use test credentials in CI environment
- Sanitize test data before committing

## Contributing

When contributing new tests:
1. Follow the existing test structure
2. Add appropriate documentation
3. Include both positive and negative test cases
4. Update this guide if necessary 