#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - AI Providers (2025 Update)
Handles communication with multiple AI providers using correct 2025 model names
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class AIResponse:
    """Standardized response from AI providers"""
    provider: str
    model: str
    analysis: Dict[str, Any]
    metadata: Dict[str, Any]
    timestamp: str


class AIProviderError(Exception):
    """Custom exception for AI provider errors"""
    pass


class BaseAIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")
        self.model = config.get("model", "default")
        self.api_key = self._get_api_key()
        self.timeout = config.get("timeout", 60)
        self.max_tokens = config.get("max_tokens", 1000)
        self.endpoint = config.get("endpoint")
        self.enable_caching = config.get("enable_caching", True)
        
        # Validate configuration
        self._validate_config()
        
    def _validate_config(self):
        """Validate configuration for security"""
        if self.timeout > 300:
            raise AIProviderError("Timeout cannot exceed 300 seconds")
        if self.max_tokens > 4000:
            raise AIProviderError("Max tokens cannot exceed 4000")
        if len(self.model) > 100:
            raise AIProviderError("Model name too long")
    
    def _get_api_key(self) -> str:
        """Get API key from environment or external secret manager"""
        # Check if external secrets are enabled
        use_external_secrets = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_ENABLED', 'false').lower() == 'true'
        
        if use_external_secrets:
            return self._get_external_secret()
        
        # Fallback to environment variable
        api_key_env = self.config.get("api_key_env", f"{self.name.upper()}_API_KEY")
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise AIProviderError(f"API key not found in environment variable: {api_key_env}")
        
        return api_key
    
    def _get_external_secret(self) -> str:
        """Get API key from external secret manager"""
        provider = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_PROVIDER')
        
        if provider == 'aws-secrets-manager':
            return self._get_aws_secret()
        elif provider == 'hashicorp-vault':
            return self._get_vault_secret()
        elif provider == 'gcp-secret-manager':
            return self._get_gcp_secret()
        else:
            raise AIProviderError(f"Unsupported secret manager: {provider}")
    
    def _get_aws_secret(self) -> str:
        """Get secret from AWS Secrets Manager"""
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            region = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_REGION', 'us-east-1')
            secret_path = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_SECRET_PATH')
            
            if not secret_path:
                secret_path = f"buildkite/ai-error-analysis/{self.name}"
            
            client = boto3.client('secretsmanager', region_name=region)
            response = client.get_secret_value(SecretId=secret_path)
            
            # Handle both string and JSON secrets
            try:
                secret_data = json.loads(response['SecretString'])
                return secret_data.get('api_key') or secret_data.get('value')
            except json.JSONDecodeError:
                return response['SecretString']
                
        except ImportError:
            raise AIProviderError("boto3 not installed for AWS Secrets Manager")
        except ClientError as e:
            raise AIProviderError(f"Failed to get AWS secret: {e}")
    
    def _get_vault_secret(self) -> str:
        """Get secret from HashiCorp Vault"""
        try:
            import subprocess
            
            vault_url = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_VAULT_URL')
            secret_path = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_SECRET_PATH')
            
            if not secret_path:
                secret_path = f"secret/buildkite/ai-error-analysis/{self.name}"
            
            result = subprocess.run(
                ['vault', 'kv', 'get', '-format=json', secret_path],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                vault_data = json.loads(result.stdout)
                secret_data = vault_data.get('data', {}).get('data', {})
                return secret_data.get('api_key') or secret_data.get('value')
            else:
                raise AIProviderError(f"Vault error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise AIProviderError("Vault request timeout")
        except Exception as e:
            raise AIProviderError(f"Failed to get Vault secret: {e}")
    
    def _get_gcp_secret(self) -> str:
        """Get secret from Google Secret Manager"""
        try:
            from google.cloud import secretmanager
            
            project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
            secret_path = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_SECURITY_EXTERNAL_SECRETS_SECRET_PATH')
            
            if not project_id:
                raise AIProviderError("GOOGLE_CLOUD_PROJECT environment variable required")
            
            if not secret_path:
                secret_path = f"ai-error-analysis-{self.name}-key"
            
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/{secret_path}/versions/latest"
            response = client.access_secret_version(request={"name": name})
            
            return response.payload.data.decode('UTF-8')
            
        except ImportError:
            raise AIProviderError("google-cloud-secret-manager not installed")
        except Exception as e:
            raise AIProviderError(f"Failed to get GCP secret: {e}")
    
    @abstractmethod
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using the AI provider"""
        pass
    
    def _make_request(self, url: str, headers: Dict[str, str], data: bytes) -> Dict[str, Any]:
        """Make HTTP request to AI provider"""
        try:
            # Security: Only allow HTTPS in production
            if not url.startswith('https://'):
                raise AIProviderError("Only HTTPS URLs allowed")
            
            req = urllib.request.Request(url, data=data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')[:200]  # Limit error message
            raise AIProviderError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise AIProviderError(f"URL Error: {e.reason}")
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise AIProviderError(f"Request failed: {e}")
class OpenAIProvider(BaseAIProvider):
    """OpenAI provider with correct 2025 model names"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Validate 2025 OpenAI models - CORRECTED
        valid_models = [
            "GPT-4o", "GPT-4o mini", "GPT-4o nano",
            "o1-preview", "o1-mini", "GPT-4 Turbo"
        ]
        
        # Model name mapping: marketing name -> API name
        self.model_mapping = {
            "GPT-4o": "gpt-4o",
            "GPT-4o mini": "gpt-4o-mini", 
            "GPT-4o nano": "gpt-4o-nano",
            "o1-preview": "o1-preview",
            "o1-mini": "o1-mini",
            "GPT-4 Turbo": "gpt-4-turbo"
        }
        
        # Resolve model name (handle legacy names)
        self.model = self._resolve_model_name(self.model)
        
        if self.model not in valid_models:
            raise AIProviderError(f"Invalid OpenAI model: {self.model}. Valid models: {valid_models}")
        
        self.endpoint = config.get("endpoint", "https://api.openai.com/v1/chat/completions")
    
    def _resolve_model_name(self, model: str) -> str:
        """Resolve legacy model names to 2025 marketing names"""
        legacy_mappings = {
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o mini",
            "gpt-4o-nano": "GPT-4o nano",
            "gpt-4-turbo": "GPT-4 Turbo"
        }
        return legacy_mappings.get(model, model)
    
    def _get_api_model_name(self) -> str:
        """Get the technical API model name for requests"""
        return self.model_mapping.get(self.model, self.model.lower().replace(" ", "-"))
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using OpenAI"""
        start_time = time.time()
        
        prompt = self._build_prompt(context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = [
            {
                "role": "system",
                "content": "You are an expert DevOps engineer analyzing build failures. Provide concise, actionable analysis."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ]
        
        payload = {
            "model": self._get_api_model_name(),  # Use API technical name
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.1
        }
        
        data = json.dumps(payload).encode('utf-8')
        response = self._make_request(self.endpoint, headers, data)
        
        try:
            content = response["choices"][0]["message"]["content"]
            analysis = self._parse_analysis(content)
            
            return AIResponse(
                provider="openai",
                model=self.model,  # Return marketing name
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid OpenAI response format: {e}")


class AnthropicProvider(BaseAIProvider):
    """Anthropic Claude provider with correct 2025 model names"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Validate 2025 Anthropic models - CORRECTED to use marketing names
        valid_models = [
            "Claude Opus 4", "Claude Sonnet 4", "Claude 3.5 Haiku",
            "Claude 3.5 Sonnet", "Claude 3 Haiku"
        ]
        
        # Model name mapping: marketing name -> API name
        self.model_mapping = {
            "Claude Opus 4": "claude-3-opus-20240229",
            "Claude Sonnet 4": "claude-3-sonnet-20240229", 
            "Claude 3.5 Haiku": "claude-3-5-haiku-20241022",
            "Claude 3.5 Sonnet": "claude-3-5-sonnet-20241022",
            "Claude 3 Haiku": "claude-3-haiku-20240307"
        }
        
        # Resolve model name
        self.model = self._resolve_model_name(self.model)
        
        if self.model not in valid_models:
            raise AIProviderError(f"Invalid Anthropic model: {self.model}. Valid models: {valid_models}")
        
        self.endpoint = config.get("endpoint", "https://api.anthropic.com/v1/messages")
    
    def _resolve_model_name(self, model: str) -> str:
        """Resolve legacy model names to 2025 marketing names"""
        legacy_mappings = {
            "claude-3-opus-20240229": "Claude Opus 4",
            "claude-3-sonnet-20240229": "Claude Sonnet 4",
            "claude-3-5-haiku-20241022": "Claude 3.5 Haiku",
            "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
            "claude-3-haiku-20240307": "Claude 3 Haiku"
        }
        return legacy_mappings.get(model, model)
    
    def _get_api_model_name(self) -> str:
        """Get the technical API model name for requests"""
        return self.model_mapping.get(self.model, "claude-3-haiku-20240307")
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Claude"""
        start_time = time.time()
        
        prompt = self._build_prompt(context)
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        payload = {
            "model": self._get_api_model_name(),  # Use API technical name
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        data = json.dumps(payload).encode('utf-8')
        response = self._make_request(self.endpoint, headers, data)
        
        try:
            content = response["content"][0]["text"]
            analysis = self._parse_analysis(content)
            
            return AIResponse(
                provider="anthropic",
                model=self.model,  # Return marketing name
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usage", {}).get("output_tokens", 0),
                    "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid Anthropic response format: {e}")


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider with correct 2025 model names"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Validate 2025 Gemini models - ALREADY CORRECT
        valid_models = [
            "Gemini 2.5 Pro", "Gemini 2.0 Flash", 
            "Gemini 1.5 Flash", "Gemini 1.5 Flash 8B"
        ]
        
        # Model name mapping: marketing name -> API name
        self.model_mapping = {
            "Gemini 2.5 Pro": "gemini-1.5-pro",
            "Gemini 2.0 Flash": "gemini-1.5-flash",
            "Gemini 1.5 Flash": "gemini-1.5-flash",
            "Gemini 1.5 Flash 8B": "gemini-1.5-flash-8b"
        }
        
        # Resolve model name
        self.model = self._resolve_model_name(self.model)
        
        if self.model not in valid_models:
            raise AIProviderError(f"Invalid Gemini model: {self.model}. Valid models: {valid_models}")
        
        base_url = config.get("endpoint", "https://generativelanguage.googleapis.com")
        api_model_name = self._get_api_model_name()
        self.endpoint = f"{base_url}/v1beta/models/{api_model_name}:generateContent"
    
    def _resolve_model_name(self, model: str) -> str:
        """Resolve legacy model names to 2025 marketing names"""
        legacy_mappings = {
            "gemini-1.5-pro": "Gemini 2.5 Pro",
            "gemini-1.5-flash": "Gemini 2.0 Flash",
            "gemini-1.5-flash-8b": "Gemini 1.5 Flash 8B"
        }
        return legacy_mappings.get(model, model)
    
    def _get_api_model_name(self) -> str:
        """Get the technical API model name for requests"""
        return self.model_mapping.get(self.model, "gemini-1.5-flash")

# Common methods for all providers
def _build_generic_prompt(context: Dict[str, Any]) -> str:
    """Generic prompt builder for all providers"""
    prompt_parts = [
        "You are an expert DevOps engineer. Analyze this CI/CD build failure and provide actionable insights.",
        "",
        "FAILURE DETAILS:",
        f"Exit Code: {context.get('error_info', {}).get('exit_code', 'unknown')}",
        f"Error Category: {context.get('error_info', {}).get('error_category', 'unknown')}",
        f"Command: {context.get('error_info', {}).get('command', 'unknown')}",
        ""
    ]
    
    # Add log excerpt
    log_excerpt = context.get('log_excerpt', '')
    if log_excerpt:
        prompt_parts.extend([
            "LOG EXCERPT:",
            "```",
            log_excerpt[:2000],
            "```",
            ""
        ])
    
    # Add build context
    build_info = context.get('build_info', {})
    if build_info:
        prompt_parts.extend([
            "BUILD CONTEXT:",
            f"Pipeline: {build_info.get('pipeline_name', 'unknown')}",
            f"Branch: {context.get('git_info', {}).get('branch', 'unknown')}",
            ""
        ])
    
    prompt_parts.extend([
        "ANALYSIS REQUEST:",
        "Provide a structured analysis with:",
        "1. ROOT CAUSE: Clear explanation of what went wrong",
        "2. SUGGESTED FIXES: 3-5 specific, actionable solutions",
        "3. CONFIDENCE: Your confidence level (0-100%)",
        "4. SEVERITY: Impact level (low/medium/high)",
        "",
        "Keep your response concise and focused on actionable solutions."
    ])
    
    return "\n".join(prompt_parts)


def _parse_generic_analysis(content: str) -> Dict[str, Any]:
    """Generic response parser for all providers"""
    import re
    
    analysis = {
        "root_cause": "",
        "suggested_fixes": [],
        "confidence": 75,
        "severity": "medium",
        "error_type": "unknown"
    }
    
    # Extract sections using regex
    sections = {
        "root_cause": r"(?i)(?:root\s+cause|cause)[:\s]*(.+?)(?=(?:suggested|fix|confidence|severity|$))",
        "confidence": r"(?i)confidence[:\s]*(\d+)%?",
        "severity": r"(?i)severity[:\s]*(low|medium|high)"
    }
    
    for section, pattern in sections.items():
        match = re.search(pattern, content, re.DOTALL)
        if match:
            if section == "root_cause":
                analysis[section] = match.group(1).strip()[:500]
            elif section == "confidence":
                analysis[section] = min(100, max(0, int(match.group(1))))
            elif section == "severity":
                analysis[section] = match.group(1).lower()
    
    # Extract suggested fixes
    fixes_pattern = r"(?i)(?:suggested\s+)?fix(?:es)?[:\s]*(.+?)(?=(?:confidence|severity|$))"
    fixes_match = re.search(fixes_pattern, content, re.DOTALL)
    
    if fixes_match:
        fixes_text = fixes_match.group(1)
        fix_items = re.split(r'\n(?=\d+\.|\-|\*)', fixes_text)
        
        for item in fix_items:
            clean_item = re.sub(r'^\d+\.?\s*[\-\*]?\s*', '', item.strip())
            if clean_item and len(clean_item) > 10:
                analysis["suggested_fixes"].append(clean_item[:200])
    
    # Fallback
    if not analysis["root_cause"]:
        analysis["root_cause"] = content[:300] + "..." if len(content) > 300 else content
    
    if not analysis["suggested_fixes"]:
        analysis["suggested_fixes"] = [
            "Review the error logs carefully",
            "Check recent changes to the codebase", 
            "Verify configuration and dependencies",
            "Contact the DevOps team if the issue persists"
        ]
    
    return analysis


# Add common methods to provider classes
for provider_class in [OpenAIProvider, AnthropicProvider, GeminiProvider]:
    provider_class._build_generic_prompt = _build_generic_prompt
    provider_class._parse_generic_analysis = _parse_generic_analysis


class AIProviderManager:
    """Manages multiple AI providers with fallback strategy"""
    
    def __init__(self, providers_config: List[Dict[str, Any]], fallback_strategy: str = "priority"):
        self.providers = []
        self.fallback_strategy = fallback_strategy
        
        # Initialize providers
        for config in providers_config:
            provider = self._create_provider(config)
            if provider:
                self.providers.append(provider)
        
        if not self.providers:
            raise AIProviderError("No valid AI providers configured")
    
    def _create_provider(self, config: Dict[str, Any]) -> Optional[BaseAIProvider]:
        """Create provider instance from configuration"""
        provider_name = config.get("name", "").lower()
        
        try:
            if provider_name == "openai":
                return OpenAIProvider(config)
            elif provider_name == "anthropic":
                return AnthropicProvider(config)
            elif provider_name == "gemini":
                return GeminiProvider(config)
            else:
                print(f"Warning: Unknown provider '{provider_name}'", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Warning: Failed to initialize {provider_name}: {e}", file=sys.stderr)
            return None
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using configured providers with fallback"""
        last_error = None
        
        for provider in self.providers:
            try:
                print(f"Attempting analysis with {provider.name} ({provider.model})", file=sys.stderr)
                response = provider.analyze_error(context)
                print(f"Analysis successful with {provider.name}", file=sys.stderr)
                return response
                
            except Exception as e:
                last_error = e
                print(f"Provider {provider.name} failed: {e}", file=sys.stderr)
                
                if self.fallback_strategy == "fail_fast":
                    break
                
                continue
        
        raise AIProviderError(f"All AI providers failed. Last error: {last_error}")


def main():
    """Main entry point for AI analysis"""
    if len(sys.argv) != 2:
        print("Usage: ai_providers.py <context_file>", file=sys.stderr)
        sys.exit(1)
    
    context_file = sys.argv[1]
    
    try:
        # Load context
        with open(context_file, 'r') as f:
            context = json.load(f)
        
        # Load provider configuration
        providers_config_str = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_AI_PROVIDERS', 
                                             '[{"name":"openai","model":"gpt-4o-mini"}]')
        providers_config = json.loads(providers_config_str)
        
        if not isinstance(providers_config, list):
            providers_config = [providers_config]
        
        fallback_strategy = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_FALLBACK_STRATEGY', 'priority')
        
        # Initialize provider manager
        manager = AIProviderManager(providers_config, fallback_strategy)
        
        # Analyze error
        result = manager.analyze_error(context)
        
        # Output result
        print(json.dumps(asdict(result), indent=2))
        
    except Exception as e:
        # Output error result
        error_result = {
            "provider": "error",
            "model": "none",
            "analysis": {
                "root_cause": f"AI analysis failed: {str(e)}",
                "suggested_fixes": [
                    "Check AI provider configuration",
                    "Verify API keys are set correctly",
                    "Review error logs manually",
                    "Contact DevOps team for assistance"
                ],
                "confidence": 0,
                "severity": "high",
                "error_type": "ai_failure"
            },
            "metadata": {
                "analysis_time": "0s",
                "tokens_used": 0,
                "cached": False,
                "error": str(e)
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()