#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - AI Providers
Handles communication with multiple AI providers for error analysis
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
        
    def _get_api_key(self) -> str:
        """Get API key from environment"""
        api_key_env = self.config.get("api_key_env", f"{self.name.upper()}_API_KEY")
        api_key = os.environ.get(api_key_env)
        
        if not api_key:
            raise AIProviderError(f"API key not found in environment variable: {api_key_env}")
        
        return api_key
    
    @abstractmethod
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using the AI provider"""
        pass
    
    def _make_request(self, url: str, headers: Dict[str, str], data: bytes) -> Dict[str, Any]:
        """Make HTTP request to AI provider"""
        try:
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


class OpenAIProvider(BaseAIProvider):
    """OpenAI GPT provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.openai.com/v1/chat/completions")
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using OpenAI GPT"""
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(context)
        
        # Prepare request
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
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
        
        data = json.dumps(payload).encode('utf-8')
        
        # Make request
        response = self._make_request(self.endpoint, headers, data)
        
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
                    "cached": False
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid OpenAI response format: {e}")
    
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
        
        # Add log excerpt
        if context.get('log_excerpt'):
            prompt_parts.extend([
                "Relevant Log Lines:",
                "```",
                context['log_excerpt'][:2000],  # Limit log size
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
        # Try to extract structured information from the response
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
                import re
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
    """Anthropic Claude provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.anthropic.com/v1/messages")
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Claude"""
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(context)
        
        # Prepare request
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
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
        
        # Make request
        response = self._make_request(self.endpoint, headers, data)
        
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
                    "cached": False
                },
                timestamp=datetime.utcnow().isoformat()
            )
            
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid Claude response format: {e}")
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt for Claude"""
        # Similar to OpenAI but optimized for Claude's format
        return self._build_generic_prompt(context)
    
    def _parse_analysis(self, content: str) -> Dict[str, Any]:
        """Parse Claude response content"""
        # Use same parsing logic as OpenAI for now
        return self._parse_generic_analysis(content)


class GeminiProvider(BaseAIProvider):
    """Google Gemini provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        base_url = config.get("endpoint", "https://generativelanguage.googleapis.com")
        self.endpoint = f"{base_url}/v1beta/models/{self.model}:generateContent"
    
    def analyze_error(self, context: Dict[str, Any]) -> AIResponse:
        """Analyze error using Gemini"""
        start_time = time.time()
        
        # Build prompt
        prompt = self._build_prompt(context)
        
        # Prepare request
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
        
        data = json.dumps(payload).encode('utf-8')
        
        # Make request
        response = self._make_request(url_with_key, headers, data)
        
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
                    "cached": False
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
        
        # Add log excerpt
        if context.get('log_excerpt'):
            prompt_parts.extend([
                "LOG EXCERPT:",
                "```",
                context['log_excerpt'][:3000],
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
                    "Verify API keys are set correctly",
                    "Review error logs manually"
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