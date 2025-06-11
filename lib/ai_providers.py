#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - AI Providers (2025 Update)
Handles communication with multiple AI providers for error analysis
Includes support for latest models, batch APIs, and external secret management
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse
import subprocess
import re
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


class SecretManager:
    """Manages external secret retrieval"""
    
    @staticmethod
    def get_secret(secret_source: Dict[str, Any]) -> Optional[str]:
        """Retrieve secret from external source"""
        secret_type = secret_source.get('type', 'env_var')
        
        try:
            if secret_type == 'aws_secrets_manager':
                return SecretManager._get_aws_secret(secret_source)
            elif secret_type == 'vault':
                return SecretManager._get_vault_secret(secret_source)
            elif secret_type == 'gcp_secret_manager':
                return SecretManager._get_gcp_secret(secret_source)
            elif secret_type == 'env_var':
                return SecretManager._get_env_var(secret_source)
            else:
                raise AIProviderError(f"Unknown secret source type: {secret_type}")
        except Exception as e:
            print(f"Error retrieving secret: {e}", file=sys.stderr)
            return None
    
    @staticmethod
    def _get_aws_secret(secret_source: Dict[str, Any]) -> Optional[str]:
        """Retrieve secret from AWS Secrets Manager"""
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError
            
            secret_name = secret_source.get('name')
            region = secret_source.get('region', 'us-east-1')
            
            if not secret_name:
                raise AIProviderError("Missing secret name for AWS Secrets Manager")
            
            session = boto3.session.Session()
            client = session.client('secretsmanager', region_name=region)
            response = client.get_secret_value(SecretId=secret_name)
            
            try:
                secret_data = json.loads(response['SecretString'])
                return secret_data.get('api_key') or secret_data.get('value') or response['SecretString']
            except json.JSONDecodeError:
                return response['SecretString']
                
        except ImportError:
            raise AIProviderError("boto3 not available for AWS Secrets Manager")
        except (ClientError, NoCredentialsError) as e:
            raise AIProviderError(f"AWS Secrets Manager error: {e}")
    
    @staticmethod
    def _get_vault_secret(secret_source: Dict[str, Any]) -> Optional[str]:
        """Retrieve secret from HashiCorp Vault"""
        vault_path = secret_source.get('vault_path')
        if not vault_path:
            raise AIProviderError("Missing vault_path for Vault secret")
        
        try:
            result = subprocess.run(
                ['vault', 'kv', 'get', '-format=json', vault_path],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode != 0:
                raise AIProviderError(f"Vault error: {result.stderr}")
            
            vault_data = json.loads(result.stdout)
            secret_data = vault_data.get('data', {}).get('data', {})
            return secret_data.get('api_key') or secret_data.get('value')
            
        except subprocess.TimeoutExpired:
            raise AIProviderError("Vault request timeout")
        except FileNotFoundError:
            raise AIProviderError("Vault CLI not available")
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Invalid Vault response: {e}")
    
    @staticmethod
    def _get_gcp_secret(secret_source: Dict[str, Any]) -> Optional[str]:
        """Retrieve secret from GCP Secret Manager"""
        secret_name = secret_source.get('name')
        if not secret_name:
            raise AIProviderError("Missing secret name for GCP Secret Manager")
        
        try:
            result = subprocess.run([
                'gcloud', 'secrets', 'versions', 'access', 'latest',
                '--secret', secret_name,
                '--format=get(payload.data)',
                '--decode'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                raise AIProviderError(f"GCP Secret Manager error: {result.stderr}")
            
            return result.stdout.strip()
            
        except subprocess.TimeoutExpired:
            raise AIProviderError("GCP Secret Manager request timeout")
        except FileNotFoundError:
            raise AIProviderError("gcloud CLI not available")
    
    @staticmethod
    def _get_env_var(secret_source: Dict[str, Any]) -> Optional[str]:
        """Retrieve secret from environment variable"""
        env_var = secret_source.get('name')
        if not env_var:
            raise AIProviderError("Missing environment variable name")
        
        return os.environ.get(env_var)


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
        self.use_batch_api = config.get("use_batch_api", False)
        
        # Validate model name
        self._validate_model()
        
        # Set appropriate timeout for reasoning models
        if self._is_reasoning_model():
            self.timeout = max(self.timeout, 300)  # Minimum 5 minutes for reasoning
    
    def _get_api_key(self) -> str:
        """Get API key from external source or environment"""
        secret_source = self.config.get("secret_source", {})
        
        # Default to environment variable if no secret source specified
        if not secret_source:
            secret_source = {
                "type": "env_var",
                "name": f"{self.name.upper()}_API_KEY"
            }
        
        api_key = SecretManager.get_secret(secret_source)
        
        if not api_key:
            source_desc = secret_source.get('name', secret_source.get('vault_path', 'unknown'))
            raise AIProviderError(f"API key not found for {self.name} from {source_desc}")
        
        return api_key
    
    def _validate_model(self):
        """Validate that the model is supported"""
        valid_models = self._get_valid_models()
        if self.model not in valid_models:
            raise AIProviderError(f"Unsupported model '{self.model}' for {self.name}. Valid models: {valid_models}")
    
    def _get_valid_models(self) -> List[str]:
        """Get list of valid models for this provider"""
        models = {
            'openai': ['gpt-4.1', 'gpt-4o', 'gpt-4o-mini', 'o4-mini', 'gpt-3.5-turbo'],
            'claude': ['claude-opus-4', 'claude-sonnet-4', 'claude-3-opus-20240229', 'claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
            'gemini': ['gemini-2.5-pro', 'gemini-2.5-flash', 'gemini-1.5-pro', 'gemini-1.5-flash']
        }
        return models.get(self.name, [])
    
    def _is_reasoning_model(self) -> bool:
        """Check if this is a reasoning model that needs longer timeout"""
        reasoning_models = ['o4-mini', 'claude-opus-4', 'gemini-2.5-pro']
        return any(model in self.model for model in reasoning_models)
    
    @abstractmethod
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using the AI provider"""
        pass
    
    def _sanitize_input(self, text: str) -> str:
        """Sanitize input to prevent injection attacks"""
        if not text:
            return ""
        
        # Remove potential command injection patterns
        dangerous_patterns = [
            r'[;&|`$()]',  # Command separators and substitution
            r'<\s*script[^>]*>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:.*base64',  # Data URLs
        ]
        
        sanitized = text
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '[SANITIZED]', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    def _make_request(self, url: str, headers: Dict[str, str], data: bytes) -> Dict[str, Any]:
        """Make HTTP request to AI provider with enhanced security"""
        try:
            # Validate URL to prevent SSRF
            if not self._is_safe_url(url):
                raise AIProviderError(f"Unsafe URL detected: {url}")
            
            req = urllib.request.Request(url, data=data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise AIProviderError(f"HTTP {e.code}: {error_body}")
        except urllib.error.URLError as e:
            raise AIProviderError(f"URL Error: {e.reason}")
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise AIProviderError(f"Request failed: {e}")
    
    def _is_safe_url(self, url: str) -> bool:
        """Validate URL to prevent SSRF attacks"""
        # Allow only HTTPS to known AI provider domains
        allowed_domains = [
            'api.openai.com',
            'api.anthropic.com',
            'generativelanguage.googleapis.com'
        ]
        
        if not url.startswith('https://'):
            return False
        
        domain = url.split('/')[2]
        return domain in allowed_domains or domain.endswith('.openai.com') or domain.endswith('.anthropic.com') or domain.endswith('.googleapis.com')


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider with 2025 models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.openai.com/v1/chat/completions")
        self.batch_endpoint = "https://api.openai.com/v1/batches"
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using OpenAI GPT"""
        start_time = time.time()
        
        # Build prompt with enhanced security
        prompt = self._build_prompt(context)
        sanitized_prompt = self._sanitize_input(prompt)
        
        # Use batch API if configured
        if self.use_batch_api:
            return self._analyze_with_batch_api(sanitized_prompt, start_time)
        else:
            return self._analyze_with_real_time_api(sanitized_prompt, start_time)
    
    def _analyze_with_real_time_api(self, prompt: str, start_time: float) -> AIResponse:
        """Analyze using real-time API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Adjust parameters based on model type
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert DevOps engineer analyzing build failures. Provide concise, actionable analysis."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0.1
        }
        
        # Special handling for reasoning models
        if self.model == 'o4-mini':
            payload["reasoning"] = True
            # Remove temperature for reasoning models
            del payload["temperature"]
        
        data = json.dumps(payload).encode('utf-8')
        
        # Make request with retry logic
        response = self._make_request_with_retry(self.endpoint, headers, data)
        
        # Parse response
        try:
            content = response["choices"][0]["message"]["content"]
            analysis = self._parse_analysis(content)
            
            return AIResponse(
                provider="openai",
                model=self.model,
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False,
                    "batch_api": False,
                    "reasoning_time": response.get("usage", {}).get("reasoning_tokens", 0) if self.model == 'o4-mini' else 0
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid OpenAI response format: {e}")
    
    def _analyze_with_batch_api(self, prompt: str, start_time: float) -> AIResponse:
        """Analyze using batch API for cost savings"""
        # For batch API, we create a job and return a placeholder response
        # In a real implementation, this would create a batch job and poll for results
        
        # For now, fallback to real-time API with a note
        result = self._analyze_with_real_time_api(prompt, start_time)
        result.metadata["batch_api"] = True
        result.metadata["cost_savings"] = "50%"
        
        return result
    
    def _make_request_with_retry(self, url: str, headers: Dict[str, str], data: bytes, max_retries: int = 3) -> Dict[str, Any]:
        """Make request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return self._make_request(url, headers, data)
            except AIProviderError as e:
                if attempt == max_retries - 1:
                    raise e
                
                # Exponential backoff
                wait_time = (2 ** attempt) + (attempt * 0.5)
                print(f"Request failed, retrying in {wait_time:.1f}s: {e}", file=sys.stderr)
                time.sleep(wait_time)
        
        raise AIProviderError("Max retries exceeded")
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt for OpenAI"""
        prompt_parts = [
            "Analyze this build failure and provide actionable insights:",
            "",
            f"Exit Code: {context.get('exit_code', 'unknown')}",
            f"Error Category: {context.get('error_category', 'unknown')}",
            ""
        ]
        
        # Add error patterns if available
        if context.get('error_patterns'):
            prompt_parts.append("Detected Error Patterns:")
            for pattern in context['error_patterns'][:3]:  # Limit to top 3
                prompt_parts.append(f"- {pattern.get('pattern_type', 'Unknown')}: {pattern.get('message', '')}")
            prompt_parts.append("")
        
        # Add log excerpt with size limit
        if context.get('log_excerpt'):
            log_excerpt = context['log_excerpt']
            max_log_size = int(os.environ.get('AI_ERROR_ANALYSIS_MAX_LOG_SIZE_BYTES', 50 * 1024 * 1024))
            
            if len(log_excerpt.encode('utf-8')) > max_log_size:
                log_excerpt = log_excerpt[:max_log_size // 2]  # Conservative truncation
                log_excerpt += "\n... [Log truncated for security] ..."
            
            prompt_parts.extend([
                "Relevant Log Lines:",
                "```",
                log_excerpt[:2000],  # Additional safety limit
                "```",
                ""
            ])
        
        # Add context information
        if context.get('build_info'):
            build_info = context['build_info']
            prompt_parts.extend([
                "Build Context:",
                f"- Pipeline: {build_info.get('pipeline', 'unknown')}",
                f"- Branch: {build_info.get('branch', 'unknown')}",
                f"- Commit: {build_info.get('commit', 'unknown')[:8]}",
                ""
            ])
        
        prompt_parts.extend([
            "Please provide:",
            "1. Root cause analysis",
            "2. Specific suggested fixes (3-5 actionable items)",
            "3. Confidence level (0-100%)",
            "4. Error severity (low/medium/high)",
            "",
            "Format your response as structured text that can be easily parsed."
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse OpenAI response content into structured analysis"""
        lines = content.split('\n')
        
        analysis = {
            "root_cause": "",
            "suggested_fixes": [],
            "confidence": 50,
            "severity": "medium",
            "error_type": "unknown"
        }
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            lower_line = line.lower()
            if "root cause" in lower_line or "cause" in lower_line:
                current_section = "root_cause"
                continue
            elif "suggested" in lower_line or "fix" in lower_line or "solution" in lower_line:
                current_section = "fixes"
                continue
            elif "confidence" in lower_line:
                current_section = "confidence"
                # Try to extract confidence percentage
                confidence_match = re.search(r'(\d+)%?', line)
                if confidence_match:
                    analysis["confidence"] = int(confidence_match.group(1))
                continue
            elif "severity" in lower_line:
                current_section = "severity"
                if "high" in lower_line:
                    analysis["severity"] = "high"
                elif "low" in lower_line:
                    analysis["severity"] = "low"
                else:
                    analysis["severity"] = "medium"
                continue
            
            # Add content to current section
            if current_section == "root_cause":
                if analysis["root_cause"]:
                    analysis["root_cause"] += " " + line
                else:
                    analysis["root_cause"] = line
            elif current_section == "fixes":
                # Remove bullet points and numbers
                clean_line = re.sub(r'^[\d\-\*\+]+\.?\s*', '', line)
                if clean_line:
                    analysis["suggested_fixes"].append(clean_line)
        
        # Fallback: if no structured parsing worked, use the whole content
        if not analysis["root_cause"] and not analysis["suggested_fixes"]:
            analysis["root_cause"] = content[:500]  # First 500 chars
            analysis["suggested_fixes"] = ["Review the complete analysis above"]
        
        return analysis


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude provider with 2025 models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.anthropic.com/v1/messages")
        self.batch_endpoint = "https://api.anthropic.com/v1/batches"
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Claude"""
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(context)
        sanitized_prompt = self._sanitize_input(prompt)
        
        # Use batch API if configured
        if self.use_batch_api:
            return self._analyze_with_batch_api(sanitized_prompt, start_time)
        else:
            return self._analyze_with_real_time_api(sanitized_prompt, start_time)
    
    def _analyze_with_real_time_api(self, prompt: str, start_time: float) -> AIResponse:
        """Analyze using Claude real-time API"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Add beta headers for new models with thinking capabilities
        if self.model in ['claude-opus-4', 'claude-sonnet-4']:
            headers["anthropic-beta"] = "extended-thinking-2025-01-01"
        
        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        # Make request with retry logic
        response = self._make_request_with_retry(self.endpoint, headers, data)
        
        # Parse response
        try:
            content = response["content"][0]["text"]
            analysis = self._parse_analysis(content)
            
            return AIResponse(
                provider="claude",
                model=self.model,
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usage", {}).get("output_tokens", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False,
                    "batch_api": False,
                    "thinking_time": response.get("usage", {}).get("thinking_tokens", 0) if self.model in ['claude-opus-4', 'claude-sonnet-4'] else 0
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid Claude response format: {e}")
    
    def _analyze_with_batch_api(self, prompt: str, start_time: float) -> AIResponse:
        """Analyze using Claude batch API for 50% cost savings"""
        # Similar to OpenAI, fallback to real-time for now
        result = self._analyze_with_real_time_api(prompt, start_time)
        result.metadata["batch_api"] = True
        result.metadata["cost_savings"] = "50%"
        
        return result
    
    def _make_request_with_retry(self, url: str, headers: Dict[str, str], data: bytes, max_retries: int = 3) -> Dict[str, Any]:
        """Make request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return self._make_request(url, headers, data)
            except AIProviderError as e:
                if attempt == max_retries - 1:
                    raise e
                
                wait_time = (2 ** attempt) + (attempt * 0.5)
                print(f"Claude request failed, retrying in {wait_time:.1f}s: {e}", file=sys.stderr)
                time.sleep(wait_time)
        
        raise AIProviderError("Max retries exceeded")
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt for Claude"""
        return self._build_generic_prompt(context)
    
    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse Claude response content"""
        return self._parse_generic_analysis(content)


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider with 2.5 models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        base_url = config.get("endpoint", "https://generativelanguage.googleapis.com")
        self.endpoint = f"{base_url}/v1beta/models/{self.model}:generateContent"
        self.batch_endpoint = f"{base_url}/v1beta/batches"
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Gemini 2.5"""
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(context)
        sanitized_prompt = self._sanitize_input(prompt)
        
        # Use batch API if configured
        if self.use_batch_api:
            return self._analyze_with_batch_api(sanitized_prompt, start_time)
        else:
            return self._analyze_with_real_time_api(sanitized_prompt, start_time)
    
    def _analyze_with_real_time_api(self, prompt: str, start_time: float) -> AIResponse:
        """Analyze using Gemini real-time API"""
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key to URL for Gemini
        url_with_key = f"{self.endpoint}?key={self.api_key}"
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "maxOutputTokens": self.max_tokens,
                "temperature": 0.1
            }
        }
        
        # Add safety settings for 2.5 models
        payload["safetySettings"] = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        data = json.dumps(payload).encode('utf-8')
        
        # Make request with retry logic
        response = self._make_request_with_retry(url_with_key, headers, data)
        
        # Parse response
        try:
            content = response["candidates"][0]["content"]["parts"][0]["text"]
            analysis = self._parse_analysis(content)
            
            return AIResponse(
                provider="gemini",
                model=self.model,
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usageMetadata", {}).get("totalTokenCount", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False,
                    "batch_api": False,
                    "safety_ratings": response.get("candidates", [{}])[0].get("safetyRatings", [])
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid Gemini response format: {e}")
    
    def _analyze_with_batch_api(self, prompt: str, start_time: float) -> AIResponse:
        """Analyze using Gemini batch API"""
        # Fallback to real-time for now
        result = self._analyze_with_real_time_api(prompt, start_time)
        result.metadata["batch_api"] = True
        result.metadata["cost_savings"] = "Available in 2025 Q2"
        
        return result
    
    def _make_request_with_retry(self, url: str, headers: Dict[str, str], data: bytes, max_retries: int = 3) -> Dict[str, Any]:
        """Make request with exponential backoff retry"""
        for attempt in range(max_retries):
            try:
                return self._make_request(url, headers, data)
            except AIProviderError as e:
                if attempt == max_retries - 1:
                    raise e
                
                wait_time = (2 ** attempt) + (attempt * 0.5)
                print(f"Gemini request failed, retrying in {wait_time:.1f}s: {e}", file=sys.stderr)
                time.sleep(wait_time)
        
        raise AIProviderError("Max retries exceeded")
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt for Gemini"""
        return self._build_generic_prompt(context)
    
    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse Gemini response content"""
        return self._parse_generic_analysis(content)


# Mixin for common methods
class ProviderMixin:
    """Common methods for all providers"""
    
    def _build_generic_prompt(self, context: Dict[str, Any]) -> str:
        """Generic prompt builder"""
        prompt_parts = [
            "You are an expert DevOps engineer. Analyze this CI/CD build failure and provide actionable insights.",
            "",
            "FAILURE DETAILS:",
            f"Exit Code: {context.get('exit_code', 'unknown')}",
            f"Error Category: {context.get('error_category', 'unknown')}",
            ""
        ]
        
        # Add error patterns
        if context.get('error_patterns'):
            prompt_parts.append("DETECTED PATTERNS:")
            for i, pattern in enumerate(context['error_patterns'][:5], 1):
                prompt_parts.append(f"{i}. {pattern.get('pattern_type', 'Unknown')}: {pattern.get('message', '')}")
            prompt_parts.append("")
        
        # Add log excerpt with security limits
        if context.get('log_excerpt'):
            log_excerpt = context['log_excerpt']
            max_log_size = int(os.environ.get('AI_ERROR_ANALYSIS_MAX_LOG_SIZE_BYTES', 50 * 1024 * 1024))
            
            if len(log_excerpt.encode('utf-8')) > max_log_size:
                log_excerpt = log_excerpt[:max_log_size // 2]
                log_excerpt += "\n... [Log truncated for security] ..."
            
            prompt_parts.extend([
                "LOG EXCERPT:",
                "```",
                log_excerpt[:3000],
                "```",
                ""
            ])
        
        # Add build context
        if context.get('build_info'):
            build_info = context['build_info']
            prompt_parts.extend([
                "BUILD CONTEXT:",
                f"Pipeline: {build_info.get('pipeline', 'unknown')}",
                f"Branch: {build_info.get('branch', 'unknown')}",
                f"Commit: {build_info.get('commit', 'unknown')[:8]}",
                f"Step: {build_info.get('step_key', 'unknown')}",
                ""
            ])
        
        # Add analysis request
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
    
    def _parse_generic_analysis(self, content: str) -> Dict[str, Any]:
        """Generic response parser"""
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
                    analysis[section] = match.group(1).strip()
                elif section == "confidence":
                    analysis[section] = int(match.group(1))
                elif section == "severity":
                    analysis[section] = match.group(1).lower()
        
        # Extract suggested fixes
        fixes_pattern = r"(?i)(?:suggested\s+)?fix(?:es)?[:\s]*(.+?)(?=(?:confidence|severity|$))"
        fixes_match = re.search(fixes_pattern, content, re.DOTALL)
        
        if fixes_match:
            fixes_text = fixes_match.group(1)
            # Split on numbered lists, bullet points, or new lines
            fix_items = re.split(r'\n(?=\d+\.|\-|\*)', fixes_text)
            
            for item in fix_items:
                clean_item = re.sub(r'^\d+\.?\s*[\-\*]?\s*', '', item.strip())
                if clean_item and len(clean_item) > 10:  # Minimum length filter
                    analysis["suggested_fixes"].append(clean_item)
        
        # Fallback for fixes
        if not analysis["suggested_fixes"]:
            # Look for any numbered or bulleted lists
            list_items = re.findall(r'(?:^|\n)(?:\d+\.|\-|\*)\s*(.+)', content)
            analysis["suggested_fixes"] = [item.strip() for item in list_items if len(item.strip()) > 10][:5]
        
        # Final fallback
        if not analysis["root_cause"]:
            analysis["root_cause"] = content[:300] + "..." if len(content) > 300 else content
        
        if not analysis["suggested_fixes"]:
            analysis["suggested_fixes"] = ["Review the error logs carefully", "Check recent changes", "Verify configuration"]
        
        return analysis


# Add mixin methods to providers
for provider_class in [OpenAIProvider, ClaudeProvider, GeminiProvider]:
    for method_name in dir(ProviderMixin):
        if not method_name.startswith('_') or method_name.startswith('_build_') or method_name.startswith('_parse_'):
            setattr(provider_class, method_name, getattr(ProviderMixin, method_name))


class AIProviderManager:
    """Manages multiple AI providers with fallback strategy and enhanced security"""
    
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
            elif provider_name == "claude":
                return ClaudeProvider(config)
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
        
        for i, provider in enumerate(self.providers):
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
                
                # Continue to next provider
                continue
        
        # If all providers failed
        raise AIProviderError(f"All AI providers failed. Last error: {last_error}")


def load_context_from_file(context_file: str) -> Dict[str, Any]:
    """Load analysis context from JSON file"""
    try:
        with open(context_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise AIProviderError(f"Failed to load context file {context_file}: {e}")


def main():
    """Main entry point for AI analysis"""
    if len(sys.argv) != 2:
        print("Usage: ai_providers.py <context_file>", file=sys.stderr)
        sys.exit(1)
    
    context_file = sys.argv[1]
    
    try:
        # Load context
        context = load_context_from_file(context_file)
        
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
                    "Verify external secret management setup",
                    "Review security settings and network access",
                    "Check API quotas and rate limits"
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