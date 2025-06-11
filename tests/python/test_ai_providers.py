#!/usr/bin/env python3
"""
Unit tests for ai_providers.py
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, Mock, MagicMock
from datetime import datetime

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lib'))

from ai_providers import (
    AIProviderError, BaseAIProvider, OpenAIProvider, ClaudeProvider, 
    GeminiProvider, AIProviderManager, AIResponse
)


class TestBaseAIProvider:
    """Test cases for BaseAIProvider abstract class"""
    
    def test_init_with_config(self):
        """Test BaseAIProvider initialization"""
        config = {
            "name": "test",
            "model": "test-model",
            "api_key_env": "TEST_API_KEY",
            "timeout": 30,
            "max_tokens": 500
        }
        
        with patch.dict(os.environ, {"TEST_API_KEY": "test-key"}):
            provider = TestProvider(config)
            
            assert provider.name == "test"
            assert provider.model == "test-model"
            assert provider.api_key == "test-key"
            assert provider.timeout == 30
            assert provider.max_tokens == 500
    
    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises AIProviderError"""
        config = {
            "name": "test",
            "api_key_env": "MISSING_API_KEY"
        }
        
        with pytest.raises(AIProviderError, match="API key not found"):
            TestProvider(config)
    
    def test_default_api_key_env(self):
        """Test default API key environment variable naming"""
        config = {"name": "openai"}
        
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}):
            provider = TestProvider(config)
            assert provider.api_key == "test-key"


class TestProvider(BaseAIProvider):
    """Test implementation of BaseAIProvider for testing"""
    
    def analyze_error(self, context):
        return AIResponse(
            provider=self.name,
            model=self.model,
            analysis={"root_cause": "test", "suggested_fixes": []},
            metadata={"tokens_used": 0},
            timestamp=datetime.utcnow().isoformat()
        )


class TestOpenAIProvider:
    """Test cases for OpenAIProvider"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "name": "openai",
            "model": "gpt-4o-mini",
            "api_key_env": "OPENAI_API_KEY",
            "max_tokens": 1000
        }
        
        self.context = {
            "error_info": {
                "exit_code": 1,
                "error_category": "test_failure",
                "command": "npm test"
            },
            "log_excerpt": "Test failed: assertion error",
            "build_info": {
                "pipeline": "test-pipeline",
                "branch": "main"
            }
        }
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_init(self):
        """Test OpenAIProvider initialization"""
        provider = OpenAIProvider(self.config)
        
        assert provider.name == "openai"
        assert provider.model == "gpt-4o-mini"
        assert provider.endpoint == "https://api.openai.com/v1/chat/completions"
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('ai_providers.OpenAIProvider._make_request')
    def test_analyze_error_success(self, mock_request):
        """Test successful error analysis"""
        mock_request.return_value = {
            "choices": [{
                "message": {
                    "content": "Root cause: Test assertion failed\n\nSuggested fixes:\n1. Check test data\n2. Update assertions\n\nConfidence: 85%\nSeverity: medium"
                }
            }],
            "usage": {"total_tokens": 245}
        }
        
        provider = OpenAIProvider(self.config)
        result = provider.analyze_error(self.context)
        
        assert result.provider == "openai"
        assert result.model == "gpt-4o-mini"
        assert "Test assertion failed" in result.analysis["root_cause"]
        assert len(result.analysis["suggested_fixes"]) >= 1
        assert result.analysis["confidence"] == 85
        assert result.metadata["tokens_used"] == 245
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('ai_providers.OpenAIProvider._make_request')
    def test_analyze_error_invalid_response(self, mock_request):
        """Test handling of invalid API response"""
        mock_request.return_value = {"invalid": "response"}
        
        provider = OpenAIProvider(self.config)
        
        with pytest.raises(AIProviderError, match="Invalid OpenAI response format"):
            provider.analyze_error(self.context)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_build_prompt(self):
        """Test prompt building"""
        provider = OpenAIProvider(self.config)
        prompt = provider._build_prompt(self.context)
        
        assert "Exit Code: 1" in prompt
        assert "test_failure" in prompt
        assert "npm test" in prompt
        assert "Test failed: assertion error" in prompt
        assert "pipeline: test-pipeline" in prompt
        assert "Root cause analysis" in prompt
        assert "Specific suggested fixes" in prompt


class TestClaudeProvider:
    """Test cases for ClaudeProvider"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "name": "claude",
            "model": "claude-3-haiku-20240307",
            "api_key_env": "ANTHROPIC_API_KEY"
        }
        
        self.context = {
            "error_info": {"exit_code": 1, "error_category": "compilation"},
            "log_excerpt": "error: syntax error before token '{'",
            "build_info": {"pipeline": "build-pipeline"}
        }
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_init(self):
        """Test ClaudeProvider initialization"""
        provider = ClaudeProvider(self.config)
        
        assert provider.name == "claude"
        assert provider.model == "claude-3-haiku-20240307"
        assert provider.endpoint == "https://api.anthropic.com/v1/messages"
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch('ai_providers.ClaudeProvider._make_request')
    def test_analyze_error_success(self, mock_request):
        """Test successful error analysis with Claude"""
        mock_request.return_value = {
            "content": [{
                "text": "ROOT CAUSE: Missing semicolon in C++ code\n\nSUGGESTED FIXES:\n1. Add semicolon after variable declaration\n2. Check syntax highlighting\n\nCONFIDENCE: 90%\nSEVERITY: low"
            }],
            "usage": {"output_tokens": 156}
        }
        
        provider = ClaudeProvider(self.config)
        result = provider.analyze_error(self.context)
        
        assert result.provider == "claude"
        assert result.model == "claude-3-haiku-20240307"
        assert "Missing semicolon" in result.analysis["root_cause"]
        assert result.analysis["confidence"] == 90
        assert result.analysis["severity"] == "low"


class TestGeminiProvider:
    """Test cases for GeminiProvider"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.config = {
            "name": "gemini",
            "model": "gemini-1.5-flash",
            "api_key_env": "GOOGLE_API_KEY"
        }
        
        self.context = {
            "error_info": {"exit_code": 2, "error_category": "dependency"},
            "log_excerpt": "Module 'react' not found",
            "build_info": {"pipeline": "frontend-build"}
        }
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    def test_init(self):
        """Test GeminiProvider initialization"""
        provider = GeminiProvider(self.config)
        
        assert provider.name == "gemini"
        assert provider.model == "gemini-1.5-flash"
        assert "generativelanguage.googleapis.com" in provider.endpoint
        assert "gemini-1.5-flash" in provider.endpoint
    
    @patch.dict(os.environ, {"GOOGLE_API_KEY": "test-key"})
    @patch('ai_providers.GeminiProvider._make_request')
    def test_analyze_error_success(self, mock_request):
        """Test successful error analysis with Gemini"""
        mock_request.return_value = {
            "candidates": [{
                "content": {
                    "parts": [{
                        "text": "ROOT CAUSE: Missing React dependency\n\nSUGGESTED FIXES:\n1. Run npm install react\n2. Check package.json\n3. Clear node_modules and reinstall\n\nCONFIDENCE: 95%\nSEVERITY: medium"
                    }]
                }
            }],
            "usageMetadata": {"totalTokenCount": 123}
        }
        
        provider = GeminiProvider(self.config)
        result = provider.analyze_error(self.context)
        
        assert result.provider == "gemini"
        assert result.model == "gemini-1.5-flash"
        assert "Missing React dependency" in result.analysis["root_cause"]
        assert result.analysis["confidence"] == 95
        assert result.metadata["tokens_used"] == 123


class TestAIProviderManager:
    """Test cases for AIProviderManager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.providers_config = [
            {
                "name": "openai",
                "model": "gpt-4o-mini",
                "api_key_env": "OPENAI_API_KEY"
            },
            {
                "name": "claude",
                "model": "claude-3-haiku-20240307",
                "api_key_env": "ANTHROPIC_API_KEY"
            }
        ]
        
        self.context = {
            "error_info": {"exit_code": 1, "error_category": "test_failure"},
            "log_excerpt": "Test failed"
        }
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "key1", "ANTHROPIC_API_KEY": "key2"})
    def test_init_multiple_providers(self):
        """Test initializing manager with multiple providers"""
        manager = AIProviderManager(self.providers_config)
        
        assert len(manager.providers) == 2
        assert manager.providers[0].name == "openai"
        assert manager.providers[1].name == "claude"
    
    def test_init_no_valid_providers_raises_error(self):
        """Test that no valid providers raises error"""
        invalid_config = [{"name": "invalid", "api_key_env": "MISSING_KEY"}]
        
        with pytest.raises(AIProviderError, match="No valid AI providers configured"):
            AIProviderManager(invalid_config)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_analyze_error_success_first_provider(self):
        """Test successful analysis with first provider"""
        config = [{"name": "openai", "api_key_env": "OPENAI_API_KEY"}]
        
        with patch('ai_providers.OpenAIProvider.analyze_error') as mock_analyze:
            mock_analyze.return_value = AIResponse(
                provider="openai",
                model="gpt-4o-mini",
                analysis={"root_cause": "test"},
                metadata={"tokens_used": 100},
                timestamp=datetime.utcnow().isoformat()
            )
            
            manager = AIProviderManager(config)
            result = manager.analyze_error(self.context)
            
            assert result.provider == "openai"
            mock_analyze.assert_called_once_with(self.context)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "key1", "ANTHROPIC_API_KEY": "key2"})
    def test_analyze_error_fallback_on_failure(self):
        """Test fallback to second provider when first fails"""
        manager = AIProviderManager(self.providers_config, "priority")
        
        with patch('ai_providers.OpenAIProvider.analyze_error') as mock_openai:
            with patch('ai_providers.ClaudeProvider.analyze_error') as mock_claude:
                # First provider fails
                mock_openai.side_effect = AIProviderError("OpenAI failed")
                
                # Second provider succeeds
                mock_claude.return_value = AIResponse(
                    provider="claude",
                    model="claude-3-haiku-20240307",
                    analysis={"root_cause": "fallback test"},
                    metadata={"tokens_used": 150},
                    timestamp=datetime.utcnow().isoformat()
                )
                
                result = manager.analyze_error(self.context)
                
                assert result.provider == "claude"
                mock_openai.assert_called_once()
                mock_claude.assert_called_once()
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_analyze_error_fail_fast_strategy(self):
        """Test fail-fast strategy stops on first failure"""
        config = [{"name": "openai", "api_key_env": "OPENAI_API_KEY"}]
        manager = AIProviderManager(config, "fail_fast")
        
        with patch('ai_providers.OpenAIProvider.analyze_error') as mock_analyze:
            mock_analyze.side_effect = AIProviderError("Provider failed")
            
            with pytest.raises(AIProviderError, match="All AI providers failed"):
                manager.analyze_error(self.context)
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "key1", "ANTHROPIC_API_KEY": "key2"})
    def test_analyze_error_all_providers_fail(self):
        """Test when all providers fail"""
        manager = AIProviderManager(self.providers_config)
        
        with patch('ai_providers.OpenAIProvider.analyze_error') as mock_openai:
            with patch('ai_providers.ClaudeProvider.analyze_error') as mock_claude:
                mock_openai.side_effect = AIProviderError("OpenAI failed")
                mock_claude.side_effect = AIProviderError("Claude failed")
                
                with pytest.raises(AIProviderError, match="All AI providers failed"):
                    manager.analyze_error(self.context)
    
    def test_create_provider_unknown_provider(self):
        """Test creating unknown provider returns None"""
        config = {"name": "unknown_provider"}
        manager = AIProviderManager([])
        
        provider = manager._create_provider(config)
        assert provider is None
    
    def test_create_provider_initialization_error(self):
        """Test provider initialization error returns None"""
        config = {"name": "openai", "api_key_env": "MISSING_KEY"}
        manager = AIProviderManager([])
        
        provider = manager._create_provider(config)
        assert provider is None


class TestResponseParsing:
    """Test cases for AI response parsing"""
    
    def test_parse_openai_response_structured(self):
        """Test parsing well-structured OpenAI response"""
        content = """
        Root Cause Analysis:
        The test failed because the authentication service is not properly mocked.
        
        Suggested Fixes:
        1. Add proper mocking for the auth service
        2. Update test credentials
        3. Check environment variables
        
        Confidence: 85%
        Severity: medium
        """
        
        provider = OpenAIProvider({"name": "openai"})
        analysis = provider._parse_analysis(content)
        
        assert "authentication service" in analysis["root_cause"]
        assert len(analysis["suggested_fixes"]) == 3
        assert "mocking for the auth service" in analysis["suggested_fixes"][0]
        assert analysis["confidence"] == 85
        assert analysis["severity"] == "medium"
    
    def test_parse_response_fallback_content(self):
        """Test parsing response when structured parsing fails"""
        content = "This is just plain text without clear structure about the error."
        
        provider = OpenAIProvider({"name": "openai"})
        analysis = provider._parse_analysis(content)
        
        # Should fall back to using content as root cause
        assert content in analysis["root_cause"]
        assert len(analysis["suggested_fixes"]) > 0  # Should have fallback suggestions
    
    def test_parse_response_with_confidence_variations(self):
        """Test parsing confidence in different formats"""
        test_cases = [
            ("Confidence: 90%", 90),
            ("confidence level: 75", 75),
            ("I'm 85% confident", 85),
            ("High confidence (95%)", 95),
        ]
        
        provider = OpenAIProvider({"name": "openai"})
        
        for content, expected_confidence in test_cases:
            analysis = provider._parse_analysis(content)
            assert analysis["confidence"] == expected_confidence
    
    def test_parse_response_with_severity_variations(self):
        """Test parsing severity in different formats"""
        test_cases = [
            ("Severity: high", "high"),
            ("This is a LOW severity issue", "low"),
            ("Medium impact error", "medium"),
            ("SEVERITY LEVEL: HIGH", "high"),
        ]
        
        provider = OpenAIProvider({"name": "openai"})
        
        for content, expected_severity in test_cases:
            analysis = provider._parse_analysis(content)
            assert analysis["severity"] == expected_severity


class TestAIResponse:
    """Test cases for AIResponse dataclass"""
    
    def test_ai_response_creation(self):
        """Test creating an AIResponse"""
        analysis = {
            "root_cause": "Test error",
            "suggested_fixes": ["Fix 1", "Fix 2"],
            "confidence": 85,
            "severity": "medium"
        }
        
        metadata = {
            "tokens_used": 245,
            "analysis_time": "2.3s",
            "cached": False
        }
        
        response = AIResponse(
            provider="openai",
            model="gpt-4o-mini",
            analysis=analysis,
            metadata=metadata,
            timestamp="2023-01-01T00:00:00Z"
        )
        
        assert response.provider == "openai"
        assert response.model == "gpt-4o-mini"
        assert response.analysis["confidence"] == 85
        assert response.metadata["tokens_used"] == 245
        assert response.timestamp == "2023-01-01T00:00:00Z"


class TestNetworkErrorHandling:
    """Test cases for network error handling"""
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('urllib.request.urlopen')
    def test_network_timeout_error(self, mock_urlopen):
        """Test handling of network timeout"""
        mock_urlopen.side_effect = OSError("Network timeout")
        
        provider = OpenAIProvider({"name": "openai"})
        
        with pytest.raises(AIProviderError, match="Request failed"):
            provider._make_request("http://test.com", {}, b'{}')
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch('urllib.request.urlopen')
    def test_http_error_handling(self, mock_urlopen):
        """Test handling of HTTP errors"""
        from urllib.error import HTTPError
        
        error_response = Mock()
        error_response.read.return_value = b'{"error": "API key invalid"}'
        
        mock_urlopen.side_effect = HTTPError(
            "http://test.com", 401, "Unauthorized", {}, error_response
        )
        
        provider = OpenAIProvider({"name": "openai"})
        
        with pytest.raises(AIProviderError, match="HTTP 401"):
            provider._make_request("http://test.com", {}, b'{}')


if __name__ == "__main__":
    pytest.main([__file__])