import pytest
import json
import os
from unittest.mock import patch, MagicMock
from lib.core_functions import (
    validate_config,
    sanitize_logs,
    collect_build_context,
    format_error_analysis,
    handle_api_response
)

class TestCoreFunctions:
    def test_validate_config(self):
        # Test valid configuration
        config = {
            "provider": "openai",
            "model": "gpt-4",
            "max_tokens": 1000
        }
        assert validate_config(config) is True

        # Test invalid provider
        config["provider"] = "invalid"
        with pytest.raises(ValueError):
            validate_config(config)

        # Test invalid max_tokens
        config["provider"] = "openai"
        config["max_tokens"] = 5000
        with pytest.raises(ValueError):
            validate_config(config)

    def test_sanitize_logs(self):
        # Test API key redaction
        log_content = "API key: sk-1234567890abcdef"
        sanitized = sanitize_logs(log_content)
        assert "sk-1234567890abcdef" not in sanitized
        assert "API key: [REDACTED]" in sanitized

        # Test database URL redaction
        log_content = "Database URL: postgresql://user:pass@host:5432/db"
        sanitized = sanitize_logs(log_content)
        assert "pass" not in sanitized
        assert "user:****@host" in sanitized

        # Test SSH key redaction
        log_content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA..."
        sanitized = sanitize_logs(log_content)
        assert "PRIVATE KEY" not in sanitized
        assert "[REDACTED SSH KEY]" in sanitized

    @patch('os.environ.get')
    def test_collect_build_context(self, mock_env):
        mock_env.side_effect = lambda x, y=None: {
            "BUILDKITE_BUILD_ID": "123",
            "BUILDKITE_COMMAND": "npm test",
            "BUILDKITE_COMMAND_EXIT_STATUS": "1"
        }.get(x, y)

        context = collect_build_context()
        assert context["build_info"]["build_id"] == "123"
        assert context["build_info"]["command"] == "npm test"
        assert context["error_info"]["exit_code"] == 1

    def test_format_error_analysis(self):
        analysis = {
            "root_cause": "Test failure",
            "suggested_fixes": ["Fix 1", "Fix 2"],
            "confidence": 0.95
        }
        
        formatted = format_error_analysis(analysis)
        assert "Root Cause" in formatted
        assert "Suggested Fixes" in formatted
        assert "Confidence" in formatted
        assert "95%" in formatted

    def test_handle_api_response(self):
        # Test successful response
        response = {
            "status": "success",
            "data": {"analysis": "Test analysis"}
        }
        result = handle_api_response(response)
        assert result["status"] == "success"
        assert "analysis" in result["data"]

        # Test error response
        response = {
            "status": "error",
            "error": "API error"
        }
        with pytest.raises(Exception) as exc:
            handle_api_response(response)
        assert "API error" in str(exc.value)

        # Test timeout response
        response = {
            "status": "timeout",
            "error": "Request timed out"
        }
        with pytest.raises(TimeoutError) as exc:
            handle_api_response(response)
        assert "Request timed out" in str(exc.value) 