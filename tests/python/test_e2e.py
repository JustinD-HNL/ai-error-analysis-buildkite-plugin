import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
from lib.error_analyzer import ErrorAnalyzer
from lib.secret_management import SecretManager
from lib.ai_providers import OpenAIProvider

class TestEndToEnd:
    @pytest.fixture
    def mock_build_context(self):
        return {
            "build_info": {
                "build_id": "test-build-123",
                "command": "npm test",
                "exit_code": 1
            },
            "error_info": {
                "error_message": "Test failure",
                "stack_trace": "Error: Test failed\n    at test.js:10:5"
            }
        }

    @pytest.fixture
    def mock_ai_response(self):
        return {
            "root_cause": "Test failure in test.js",
            "suggested_fixes": [
                "Fix the test case in test.js",
                "Update the test dependencies"
            ],
            "confidence": 0.95
        }

    @patch('lib.secret_management.SecretManager.get_secret')
    @patch('lib.ai_providers.OpenAIProvider.analyze_error')
    def test_complete_error_analysis_flow(self, mock_analyze, mock_get_secret, mock_build_context, mock_ai_response):
        # Setup mocks
        mock_get_secret.return_value = "test-api-key"
        mock_analyze.return_value = mock_ai_response

        # Create temporary directory for test artifacts
        with tempfile.TemporaryDirectory() as temp_dir:
            # Initialize analyzer
            analyzer = ErrorAnalyzer(
                provider="openai",
                model="gpt-4",
                secret_manager=SecretManager(),
                output_dir=temp_dir
            )

            # Run analysis
            result = analyzer.analyze_build_failure(mock_build_context)

            # Verify results
            assert result["status"] == "success"
            assert result["analysis"]["root_cause"] == "Test failure in test.js"
            assert len(result["analysis"]["suggested_fixes"]) == 2
            assert result["analysis"]["confidence"] == 0.95

            # Verify API calls
            mock_get_secret.assert_called_once()
            mock_analyze.assert_called_once()

            # Verify artifact creation
            artifact_path = os.path.join(temp_dir, "analysis_result.json")
            assert os.path.exists(artifact_path)
            with open(artifact_path) as f:
                artifact_data = json.load(f)
                assert artifact_data["build_id"] == "test-build-123"
                assert "analysis" in artifact_data

    @patch('lib.secret_management.SecretManager.get_secret')
    @patch('lib.ai_providers.OpenAIProvider.analyze_error')
    def test_error_analysis_with_retry(self, mock_analyze, mock_get_secret, mock_build_context):
        # Setup mocks to simulate temporary failure
        mock_get_secret.return_value = "test-api-key"
        mock_analyze.side_effect = [
            Exception("Rate limit exceeded"),
            {
                "root_cause": "Test failure",
                "suggested_fixes": ["Fix 1"],
                "confidence": 0.9
            }
        ]

        analyzer = ErrorAnalyzer(
            provider="openai",
            model="gpt-4",
            secret_manager=SecretManager(),
            max_retries=1
        )

        # Run analysis
        result = analyzer.analyze_build_failure(mock_build_context)

        # Verify retry behavior
        assert result["status"] == "success"
        assert mock_analyze.call_count == 2

    @patch('lib.secret_management.SecretManager.get_secret')
    @patch('lib.ai_providers.OpenAIProvider.analyze_error')
    def test_error_analysis_with_timeout(self, mock_analyze, mock_get_secret, mock_build_context):
        # Setup mocks
        mock_get_secret.return_value = "test-api-key"
        mock_analyze.side_effect = TimeoutError("Request timed out")

        analyzer = ErrorAnalyzer(
            provider="openai",
            model="gpt-4",
            secret_manager=SecretManager(),
            timeout=5
        )

        # Run analysis
        with pytest.raises(TimeoutError) as exc:
            analyzer.analyze_build_failure(mock_build_context)
        assert "Request timed out" in str(exc.value)

    @patch('lib.secret_management.SecretManager.get_secret')
    @patch('lib.ai_providers.OpenAIProvider.analyze_error')
    def test_error_analysis_with_invalid_secret(self, mock_analyze, mock_get_secret, mock_build_context):
        # Setup mocks
        mock_get_secret.side_effect = Exception("Invalid secret")

        analyzer = ErrorAnalyzer(
            provider="openai",
            model="gpt-4",
            secret_manager=SecretManager()
        )

        # Run analysis
        with pytest.raises(Exception) as exc:
            analyzer.analyze_build_failure(mock_build_context)
        assert "Invalid secret" in str(exc.value)

    @patch('lib.secret_management.SecretManager.get_secret')
    @patch('lib.ai_providers.OpenAIProvider.analyze_error')
    def test_error_analysis_with_log_sanitization(self, mock_analyze, mock_get_secret, mock_build_context, mock_ai_response):
        # Setup mocks
        mock_get_secret.return_value = "test-api-key"
        mock_analyze.return_value = mock_ai_response

        # Add sensitive data to build context
        mock_build_context["error_info"]["error_message"] = "API key: sk-1234567890abcdef"

        analyzer = ErrorAnalyzer(
            provider="openai",
            model="gpt-4",
            secret_manager=SecretManager()
        )

        # Run analysis
        result = analyzer.analyze_build_failure(mock_build_context)

        # Verify log sanitization
        assert "sk-1234567890abcdef" not in result["analysis"]["root_cause"]
        assert "[REDACTED]" in result["analysis"]["root_cause"]

    @patch('lib.secret_management.SecretManager.get_secret')
    @patch('lib.ai_providers.OpenAIProvider.analyze_error')
    def test_error_analysis_with_custom_context(self, mock_analyze, mock_get_secret, mock_build_context, mock_ai_response):
        # Setup mocks
        mock_get_secret.return_value = "test-api-key"
        mock_analyze.return_value = mock_ai_response

        # Add custom context
        mock_build_context["custom_context"] = {
            "framework": "React",
            "version": "18.0.0"
        }

        analyzer = ErrorAnalyzer(
            provider="openai",
            model="gpt-4",
            secret_manager=SecretManager()
        )

        # Run analysis
        result = analyzer.analyze_build_failure(mock_build_context)

        # Verify custom context is included
        assert result["status"] == "success"
        assert "React" in str(mock_analyze.call_args[0][0])
        assert "18.0.0" in str(mock_analyze.call_args[0][0]) 