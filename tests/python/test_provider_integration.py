import pytest
import json
from unittest.mock import patch, MagicMock
from lib.ai_providers import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider
)

class TestProviderIntegration:
    @pytest.fixture
    def mock_openai_response(self):
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "root_cause": "Test failure",
                        "suggested_fixes": ["Fix 1", "Fix 2"],
                        "confidence": 0.95
                    })
                }
            }]
        }

    @pytest.fixture
    def mock_anthropic_response(self):
        return {
            "content": [{
                "text": json.dumps({
                    "root_cause": "Test failure",
                    "suggested_fixes": ["Fix 1", "Fix 2"],
                    "confidence": 0.95
                })
            }]
        }

    @pytest.fixture
    def mock_gemini_response(self):
        return {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": json.dumps({
                            "root_cause": "Test failure",
                            "suggested_fixes": ["Fix 1", "Fix 2"],
                            "confidence": 0.95
                        })
                    }]
                }
            }]
        }

    @patch('openai.ChatCompletion.create')
    def test_openai_provider(self, mock_create, mock_openai_response):
        mock_create.return_value = mock_openai_response
        
        provider = OpenAIProvider(api_key="test-key")
        result = provider.analyze_error("Test error message")
        
        assert result["root_cause"] == "Test failure"
        assert len(result["suggested_fixes"]) == 2
        assert result["confidence"] == 0.95
        
        # Verify API call
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert "model" in call_args
        assert "messages" in call_args

    @patch('anthropic.Anthropic.messages.create')
    def test_anthropic_provider(self, mock_create, mock_anthropic_response):
        mock_create.return_value = mock_anthropic_response
        
        provider = AnthropicProvider(api_key="test-key")
        result = provider.analyze_error("Test error message")
        
        assert result["root_cause"] == "Test failure"
        assert len(result["suggested_fixes"]) == 2
        assert result["confidence"] == 0.95
        
        # Verify API call
        mock_create.assert_called_once()
        call_args = mock_create.call_args[1]
        assert "model" in call_args
        assert "messages" in call_args

    @patch('google.generativeai.generate_content')
    def test_gemini_provider(self, mock_generate, mock_gemini_response):
        mock_generate.return_value = mock_gemini_response
        
        provider = GeminiProvider(api_key="test-key")
        result = provider.analyze_error("Test error message")
        
        assert result["root_cause"] == "Test failure"
        assert len(result["suggested_fixes"]) == 2
        assert result["confidence"] == 0.95
        
        # Verify API call
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args[1]
        assert "model" in call_args
        assert "contents" in call_args

    @pytest.mark.parametrize("provider_class,error_type", [
        (OpenAIProvider, "openai.error.APIError"),
        (AnthropicProvider, "anthropic.APIError"),
        (GeminiProvider, "google.api_core.exceptions.GoogleAPIError")
    ])
    def test_provider_error_handling(self, provider_class, error_type):
        with patch(f"{provider_class.__module__}.{provider_class.__name__}._make_api_call") as mock_call:
            mock_call.side_effect = Exception("API Error")
            
            provider = provider_class(api_key="test-key")
            with pytest.raises(Exception) as exc:
                provider.analyze_error("Test error message")
            assert "API Error" in str(exc.value)

    @pytest.mark.parametrize("provider_class", [
        OpenAIProvider,
        AnthropicProvider,
        GeminiProvider
    ])
    def test_provider_rate_limiting(self, provider_class):
        with patch(f"{provider_class.__module__}.{provider_class.__name__}._make_api_call") as mock_call:
            mock_call.side_effect = [
                Exception("Rate limit exceeded"),
                {"result": "success"}
            ]
            
            provider = provider_class(api_key="test-key")
            result = provider.analyze_error("Test error message", retry_count=1)
            assert result["result"] == "success"
            assert mock_call.call_count == 2

    @pytest.mark.parametrize("provider_class", [
        OpenAIProvider,
        AnthropicProvider,
        GeminiProvider
    ])
    def test_provider_timeout_handling(self, provider_class):
        with patch(f"{provider_class.__module__}.{provider_class.__name__}._make_api_call") as mock_call:
            mock_call.side_effect = TimeoutError("Request timed out")
            
            provider = provider_class(api_key="test-key")
            with pytest.raises(TimeoutError) as exc:
                provider.analyze_error("Test error message")
            assert "Request timed out" in str(exc.value) 