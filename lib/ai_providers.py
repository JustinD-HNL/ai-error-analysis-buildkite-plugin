#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - AI Providers
Handles communication with multiple AI providers for error analysis (2025 Update)
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
        self.use_batch_api = config.get("use_batch_api", False)
        
        # Security: Validate inputs
        self._validate_config()
        
    def _validate_config(self):
        """Validate configuration for security"""
        if self.timeout > 600:
            raise AIProviderError("Timeout cannot exceed 600 seconds")
        if self.max_tokens > 100000:
            raise AIProviderError("Max tokens cannot exceed 100,000")
        if len(self.model) > 100:
            raise AIProviderError("Model name too long")
    
    def _get_api_key(self) -> str:
        """Get API key from environment with external secret support"""
        api_key_env = self.config.get("api_key_env", f"{self.name.upper()}_API_KEY")
        
        # Check for external secret manager configuration
        use_external_secrets = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_USE_EXTERNAL_SECRETS', 'false').lower() == 'true'
        
        if use_external_secrets:
            return self._get_external_secret(api_key_env)
        
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise AIProviderError(f"API key not found in environment variable: {api_key_env}")
        
        return api_key
    
    def _get_external_secret(self, secret_name: str) -> str:
        """Get API key from external secret manager"""
        secret_config = json.loads(os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_SECRET_MANAGER_CONFIG', '{}'))
        provider = secret_config.get('provider')
        
        if provider == 'aws-secrets-manager':
            return self._get_aws_secret(secret_name, secret_config)
        elif provider == 'hashicorp-vault':
            return self._get_vault_secret(secret_name, secret_config)
        elif provider == 'google-secret-manager':
            return self._get_gcp_secret(secret_name, secret_config)
        else:
            raise AIProviderError(f"Unsupported secret manager: {provider}")
    
    def _get_aws_secret(self, secret_name: str, config: Dict) -> str:
        """Get secret from AWS Secrets Manager"""
        try:
            import boto3
            client = boto3.client('secretsmanager', region_name=config.get('region', 'us-east-1'))
            response = client.get_secret_value(SecretId=config.get('secret_path', secret_name))
            return response['SecretString']
        except ImportError:
            raise AIProviderError("boto3 not installed for AWS Secrets Manager")
        except Exception as e:
            raise AIProviderError(f"Failed to get AWS secret: {e}")
    
    def _get_vault_secret(self, secret_name: str, config: Dict) -> str:
        """Get secret from HashiCorp Vault"""
        try:
            vault_url = os.environ.get('VAULT_ADDR')
            vault_token = os.environ.get('VAULT_TOKEN')
            
            if not vault_url or not vault_token:
                raise AIProviderError("VAULT_ADDR and VAULT_TOKEN must be set")
            
            secret_path = config.get('secret_path', f'secret/data/{secret_name}')
            url = f"{vault_url}/v1/{secret_path}"
            
            headers = {'X-Vault-Token': vault_token}
            req = urllib.request.Request(url, headers=headers)
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data['data']['data'][secret_name]
                
        except Exception as e:
            raise AIProviderError(f"Failed to get Vault secret: {e}")
    
    def _get_gcp_secret(self, secret_name: str, config: Dict) -> str:
        """Get secret from Google Secret Manager"""
        try:
            from google.cloud import secretmanager
            client = secretmanager.SecretManagerServiceClient()
            
            project_id = config.get('project_id') or os.environ.get('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                raise AIProviderError("Project ID required for Google Secret Manager")
            
            secret_path = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
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
        """Make HTTP request to AI provider with enhanced security"""
        try:
            # Security: Validate URL
            if not url.startswith(('https://', 'http://localhost', 'http://127.0.0.1')):
                raise AIProviderError("Only HTTPS URLs allowed in production")
            
            req = urllib.request.Request(url, data=data, headers=headers)
            
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            # Security: Don't log full error body which might contain sensitive info
            sanitized_error = error_body[:200] + "..." if len(error_body) > 200 else error_body
            raise AIProviderError(f"HTTP {e.code}: {sanitized_error}")
        except urllib.error.URLError as e:
            raise AIProviderError(f"URL Error: {e.reason}")
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise AIProviderError(f"Request failed: {e}")


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider with 2025 models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 2025 Model mapping
        model_mappings = {
            'gpt-4o-mini': 'o4-mini',  # Backward compatibility
            'gpt-4o': 'gpt-4.1',       # Backward compatibility
        }
        
        # Update model name if using old naming
        if self.model in model_mappings:
            self.model = model_mappings[self.model]
        
        # Set appropriate endpoints
        if self.use_batch_api:
            self.endpoint = config.get("endpoint", "https://api.openai.com/v1/batches")
        else:
            self.endpoint = config.get("endpoint", "https://api.openai.com/v1/chat/completions")
        
        # Adjust timeout for reasoning models
        if self.model in ['o4-mini', 'o4', 'o3-mini']:
            self.timeout = max(self.timeout, 300)  # Reasoning models need more time
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using OpenAI GPT"""
        start_time = time.time()
        
        if self.use_batch_api:
            return self._analyze_with_batch_api(context, start_time)
        else:
            return self._analyze_realtime(context, start_time)
    
    def _analyze_realtime(self, context: Dict[str, Any], start_time: float) -> AIResponse:
        """Real-time analysis"""
        prompt = self._build_prompt(context)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Enhanced reasoning for o4 models
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
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": 0.1
        }
        
        # Enable reasoning for o4 models
        if self.model.startswith('o4'):
            payload["reasoning"] = True
        
        data = json.dumps(payload).encode('utf-8')
        response = self._make_request(self.endpoint, headers, data)
        
        try:
            content = response["choices"][0]["message"]["content"]
            reasoning = response["choices"][0]["message"].get("reasoning", "")
            
            analysis = self._parse_analysis(content)
            
            # Add reasoning for o4 models
            if reasoning:
                analysis["reasoning"] = reasoning[:500]  # Limit reasoning length
            
            return AIResponse(
                provider="openai",
                model=self.model,
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False,
                    "reasoning_tokens": response.get("usage", {}).get("reasoning_tokens", 0) if self.model.startswith('o4') else 0
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid OpenAI response format: {e}")
    
    def _analyze_with_batch_api(self, context: Dict[str, Any], start_time: float) -> AIResponse:
        """Batch API analysis (50% cost savings)"""
        # For now, fall back to real-time. Batch API implementation would require
        # job queuing and result polling which is complex for this use case
        return self._analyze_realtime(context, start_time)
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt for OpenAI"""
        prompt_parts = [
            "Analyze this build failure and provide actionable insights:",
            "",
            f"Exit Code: {context.get('error_info', {}).get('exit_code', 'unknown')}",
            f"Error Category: {context.get('error_info', {}).get('error_category', 'unknown')}",
            f"Command: {context.get('error_info', {}).get('command', 'unknown')}",
            ""
        ]
        
        # Add error patterns if available
        error_patterns = context.get('error_info', {}).get('error_patterns', [])
        if error_patterns:
            prompt_parts.append("Detected Error Patterns:")
            for pattern in error_patterns[:3]:  # Limit to top 3
                pattern_type = pattern.get('pattern_type', 'Unknown') if isinstance(pattern, dict) else str(pattern)
                pattern_message = pattern.get('message', '') if isinstance(pattern, dict) else ''
                prompt_parts.append(f"- {pattern_type}: {pattern_message}")
            prompt_parts.append("")
        
        # Add log excerpt
        log_excerpt = context.get('log_excerpt', '')
        if log_excerpt:
            prompt_parts.extend([
                "Relevant Log Lines:",
                "```",
                log_excerpt[:2000],  # Limit log size
                "```",
                ""
            ])
        
        # Add context information
        build_info = context.get('build_info', {})
        if build_info:
            prompt_parts.extend([
                "Build Context:",
                f"- Pipeline: {build_info.get('pipeline_name', 'unknown')}",
                f"- Branch: {context.get('git_info', {}).get('branch', 'unknown')}",
                f"- Commit: {context.get('git_info', {}).get('commit', 'unknown')[:8]}",
                ""
            ])
        
        # Custom context from user
        custom_context = context.get('custom_context', '')
        if custom_context:
            prompt_parts.extend([
                "Additional Context:",
                custom_context,
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
                # Extract confidence percentage
                import re
                confidence_match = re.search(r'(\d+)%?', line)
                if confidence_match:
                    analysis["confidence"] = min(100, max(0, int(confidence_match.group(1))))
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
                import re
                clean_line = re.sub(r'^[\d\-\*\+]+\.?\s*', '', line)
                if clean_line and len(clean_line) > 5:
                    analysis["suggested_fixes"].append(clean_line)
        
        # Fallback: if no structured parsing worked, use the whole content
        if not analysis["root_cause"] and not analysis["suggested_fixes"]:
            analysis["root_cause"] = content[:500]  # First 500 chars
            analysis["suggested_fixes"] = ["Review the complete analysis above", "Check recent code changes", "Verify configuration"]
        
        # Ensure we have suggested fixes
        if not analysis["suggested_fixes"]:
            analysis["suggested_fixes"] = ["Check error logs for more details", "Verify dependencies and configuration", "Contact DevOps team if issue persists"]
        
        return analysis


class ClaudeProvider(BaseAIProvider):
    """Anthropic Claude provider with 2025 models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 2025 Model mapping
        model_mappings = {
            'claude-3-haiku-20240307': 'claude-sonnet-4',
            'claude-3-sonnet-20240229': 'claude-sonnet-4', 
            'claude-3-opus-20240229': 'claude-opus-4',
        }
        
        # Update model name if using old naming
        if self.model in model_mappings:
            self.model = model_mappings[self.model]
        
        self.endpoint = config.get("endpoint", "https://api.anthropic.com/v1/messages")
        
        # Extended thinking mode for Opus 4
        self.use_extended_thinking = self.model == 'claude-opus-4'
        if self.use_extended_thinking:
            self.timeout = max(self.timeout, 300)
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Claude"""
        start_time = time.time()
        
        prompt = self._build_prompt(context)
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Enable extended thinking for Opus 4
        if self.use_extended_thinking:
            headers["anthropic-beta"] = "extended-thinking-2024-12-15"
        
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
        
        # Enable extended thinking
        if self.use_extended_thinking:
            payload["thinking"] = True
        
        data = json.dumps(payload).encode('utf-8')
        response = self._make_request(self.endpoint, headers, data)
        
        try:
            content = response["content"][0]["text"]
            thinking = response.get("thinking", "") if self.use_extended_thinking else ""
            
            analysis = self._parse_analysis(content)
            
            # Add thinking process for Opus 4
            if thinking:
                analysis["thinking_process"] = thinking[:500]  # Limit thinking length
            
            return AIResponse(
                provider="claude",
                model=self.model,
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usage", {}).get("output_tokens", 0),
                    "input_tokens": response.get("usage", {}).get("input_tokens", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False,
                    "thinking_tokens": len(thinking.split()) if thinking else 0
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid Claude response format: {e}")
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt for Claude"""
        return self._build_generic_prompt(context)
    
    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse Claude response content"""
        return self._parse_generic_analysis(content)


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider with 2025 models"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # 2025 Model mapping
        model_mappings = {
            'gemini-1.5-flash': 'gemini-2.5-flash',
            'gemini-1.5-pro': 'gemini-2.5-pro',
        }
        
        # Update model name if using old naming
        if self.model in model_mappings:
            self.model = model_mappings[self.model]
        
        base_url = config.get("endpoint", "https://generativelanguage.googleapis.com")
        self.endpoint = f"{base_url}/v1beta/models/{self.model}:generateContent"
        
        # Deep Think mode for Pro models
        self.use_deep_think = 'pro' in self.model.lower()
        if self.use_deep_think:
            self.timeout = max(self.timeout, 300)
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Gemini"""
        start_time = time.time()
        
        prompt = self._build_prompt(context)
        
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add API key to URL for Gemini
        url_with_key = f"{self.endpoint}?key={self.api_key}"
        
        generation_config = {
            "maxOutputTokens": self.max_tokens,
            "temperature": 0.1
        }
        
        # Enable Deep Think for Pro models
        if self.use_deep_think:
            generation_config["deepThink"] = True
        
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
            "generationConfig": generation_config
        }
        
        data = json.dumps(payload).encode('utf-8')
        response = self._make_request(url_with_key, headers, data)
        
        try:
            candidate = response["candidates"][0]
            content = candidate["content"]["parts"][0]["text"]
            
            # Extract thinking process if available
            thinking_metadata = candidate.get("thinkingMetadata", {})
            thinking_process = thinking_metadata.get("thinking", "") if self.use_deep_think else ""
            
            analysis = self._parse_analysis(content)
            
            # Add thinking process for Pro models
            if thinking_process:
                analysis["thinking_process"] = thinking_process[:500]
            
            return AIResponse(
                provider="gemini",
                model=self.model,
                analysis=analysis,
                metadata={
                    "tokens_used": response.get("usageMetadata", {}).get("totalTokenCount", 0),
                    "input_tokens": response.get("usageMetadata", {}).get("promptTokenCount", 0),
                    "output_tokens": response.get("usageMetadata", {}).get("candidatesTokenCount", 0),
                    "analysis_time": f"{time.time() - start_time:.2f}s",
                    "cached": False,
                    "thinking_tokens": len(thinking_process.split()) if thinking_process else 0
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid Gemini response format: {e}")
    
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
            f"Exit Code: {context.get('error_info', {}).get('exit_code', 'unknown')}",
            f"Error Category: {context.get('error_info', {}).get('error_category', 'unknown')}",
            f"Command: {context.get('error_info', {}).get('command', 'unknown')}",
            ""
        ]
        
        # Add error patterns
        error_patterns = context.get('error_info', {}).get('error_patterns', [])
        if error_patterns:
            prompt_parts.append("DETECTED PATTERNS:")
            for i, pattern in enumerate(error_patterns[:5], 1):
                if isinstance(pattern, dict):
                    pattern_type = pattern.get('pattern_type', 'Unknown')
                    message = pattern.get('message', '')
                    prompt_parts.append(f"{i}. {pattern_type}: {message}")
                else:
                    prompt_parts.append(f"{i}. {str(pattern)}")
            prompt_parts.append("")
        
        # Add log excerpt
        log_excerpt = context.get('log_excerpt', '')
        if log_excerpt:
            prompt_parts.extend([
                "LOG EXCERPT:",
                "```",
                log_excerpt[:3000],  # Increased limit for 2025 models
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
                f"Commit: {context.get('git_info', {}).get('commit', 'unknown')[:8]}",
                f"Step: {build_info.get('step_key', 'unknown')}",
                ""
            ])
        
        # Add custom context
        custom_context = context.get('custom_context', '')
        if custom_context:
            prompt_parts.extend([
                "ADDITIONAL CONTEXT:",
                custom_context,
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
                    analysis[section] = match.group(1).strip()[:500]  # Limit length
                elif section == "confidence":
                    analysis[section] = min(100, max(0, int(match.group(1))))
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
                    analysis["suggested_fixes"].append(clean_item[:200])  # Limit length
        
        # Fallback for fixes
        if not analysis["suggested_fixes"]:
            # Look for any numbered or bulleted lists
            list_items = re.findall(r'(?:^|\n)(?:\d+\.|\-|\*)\s*(.+)', content)
            analysis["suggested_fixes"] = [item.strip()[:200] for item in list_items if len(item.strip()) > 10][:5]
        
        # Final fallback
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


# Add mixin methods to providers
for provider_class in [OpenAIProvider, ClaudeProvider, GeminiProvider]:
    for method_name in dir(ProviderMixin):
        if not method_name.startswith('_') or method_name.startswith('_build_') or method_name.startswith('_parse_'):
            method = getattr(ProviderMixin, method_name)
            if callable(method):
                setattr(provider_class, method_name, method)


class AIProviderManager:
    """Manages multiple AI providers with fallback strategy"""
    
    def __init__(self, providers_config: List[Dict[str, Any]], fallback_strategy: str = "priority"):
        self.providers = []
        self.fallback_strategy = fallback_strategy
        self.rate_limiter = self._setup_rate_limiter()
        
        # Initialize providers
        for config in providers_config:
            provider = self._create_provider(config)
            if provider:
                self.providers.append(provider)
        
        if not self.providers:
            raise AIProviderError("No valid AI providers configured")
    
    def _setup_rate_limiter(self) -> Dict[str, Any]:
        """Setup rate limiting"""
        return {
            "requests_per_minute": int(os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_RATE_LIMIT_REQUESTS_PER_MINUTE', '30')),
            "burst_limit": int(os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_RATE_LIMIT_BURST_LIMIT', '10')),
            "request_times": []
        }
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        minute_ago = now - 60
        
        # Remove old requests
        self.rate_limiter["request_times"] = [
            t for t in self.rate_limiter["request_times"] if t > minute_ago
        ]
        
        # Check limits
        recent_requests = len(self.rate_limiter["request_times"])
        if recent_requests >= self.rate_limiter["requests_per_minute"]:
            return False
        
        # Add current request
        self.rate_limiter["request_times"].append(now)
        return True
    
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
        # Check rate limits
        if not self._check_rate_limit():
            raise AIProviderError("Rate limit exceeded")
        
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
                                             '[{"name":"openai","model":"o4-mini"}]')
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