#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Analysis Engine (2025 Update)
Handles AI provider communication with correct 2025 model names and enhanced security
"""

import json
import os
import sys
import time
import argparse
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AnalysisResult:
    """Structured result from AI analysis"""
    provider: str
    model: str
    root_cause: str
    suggested_fixes: List[str]
    confidence: float
    severity: str
    analysis_time: float
    tokens_used: int
    cached: bool = False

class AIProviderError(Exception):
    """Custom exception for AI provider errors"""
    pass

class AIAnalyzer:
    """Main AI analysis engine with 2025 provider support"""
    
    # Correct 2025 model mappings
    SUPPORTED_MODELS = {
        "openai": {
            "GPT-4o": {"endpoint": "chat/completions", "max_tokens": 4096, "cost_per_1k": 0.03},
            "GPT-4o mini": {"endpoint": "chat/completions", "max_tokens": 16384, "cost_per_1k": 0.0015},
            "GPT-4o nano": {"endpoint": "chat/completions", "max_tokens": 8192, "cost_per_1k": 0.0005},
            # Legacy model names for backward compatibility
            "gpt-4o": {"endpoint": "chat/completions", "max_tokens": 4096, "cost_per_1k": 0.03, "alias": "GPT-4o"},
            "gpt-4o-mini": {"endpoint": "chat/completions", "max_tokens": 16384, "cost_per_1k": 0.0015, "alias": "GPT-4o mini"}
        },
        "anthropic": {
            "Claude Opus 4": {"endpoint": "messages", "max_tokens": 4096, "cost_per_1k": 0.15},
            "Claude Sonnet 4": {"endpoint": "messages", "max_tokens": 4096, "cost_per_1k": 0.03},
            "Claude 3.5 Haiku": {"endpoint": "messages", "max_tokens": 4096, "cost_per_1k": 0.0025},
            # Legacy model names for backward compatibility
            "claude-3-opus-20240229": {"endpoint": "messages", "max_tokens": 4096, "cost_per_1k": 0.15, "alias": "Claude Opus 4"},
            "claude-3-sonnet-20240229": {"endpoint": "messages", "max_tokens": 4096, "cost_per_1k": 0.03, "alias": "Claude Sonnet 4"},
            "claude-3-haiku-20240307": {"endpoint": "messages", "max_tokens": 4096, "cost_per_1k": 0.0025, "alias": "Claude 3.5 Haiku"}
        },
        "gemini": {
            "Gemini 2.5 Pro": {"endpoint": "generateContent", "max_tokens": 2048, "cost_per_1k": 0.002},
            "Gemini 2.0 Flash": {"endpoint": "generateContent", "max_tokens": 8192, "cost_per_1k": 0.0005},
            # Legacy model names for backward compatibility  
            "gemini-1.5-pro": {"endpoint": "generateContent", "max_tokens": 2048, "cost_per_1k": 0.002, "alias": "Gemini 2.5 Pro"},
            "gemini-1.5-flash": {"endpoint": "generateContent", "max_tokens": 8192, "cost_per_1k": 0.0005, "alias": "Gemini 2.0 Flash"}
        }
    }
    
    def __init__(self, provider: str, model: Optional[str] = None, max_tokens: int = 1000):
        self.provider = provider.lower()
        self.max_tokens = max_tokens
        self.api_key = os.getenv("AI_ERROR_ANALYSIS_API_KEY")
        
        if not self.api_key:
            raise AIProviderError(f"API key not found for {provider}")
        
        # Validate provider
        if self.provider not in self.SUPPORTED_MODELS:
            raise AIProviderError(f"Unsupported provider: {provider}")
        
        # Set default model or validate provided model
        if model:
            self.model = self._resolve_model_name(model)
        else:
            self.model = self._get_default_model()
        
        # Validate model
        if self.model not in self.SUPPORTED_MODELS[self.provider]:
            raise AIProviderError(f"Unsupported model '{self.model}' for provider '{self.provider}'")
        
        self.model_config = self.SUPPORTED_MODELS[self.provider][self.model]
        
        # Set up provider-specific configuration
        self._setup_provider_config()
    
    def _resolve_model_name(self, model: str) -> str:
        """Resolve legacy model names to 2025 standards"""
        provider_models = self.SUPPORTED_MODELS[self.provider]
        
        # Check if it's already a valid 2025 model name
        if model in provider_models:
            return model
        
        # Look for alias mapping
        for model_name, config in provider_models.items():
            if config.get("alias") == model:
                return model_name
        
        # Return as-is if no mapping found (will be validated later)
        return model
    
    def _get_default_model(self) -> str:
        """Get default model for provider"""
        defaults = {
            "openai": "GPT-4o mini",
            "anthropic": "Claude 3.5 Haiku", 
            "gemini": "Gemini 2.0 Flash"
        }
        return defaults[self.provider]
    
    def _setup_provider_config(self):
        """Set up provider-specific configuration"""
        if self.provider == "openai":
            self.api_base = "https://api.openai.com/v1"
            self.headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        
        elif self.provider == "anthropic":
            self.api_base = "https://api.anthropic.com/v1"
            self.headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            # Enable extended thinking for Opus 4
            if self.model == "Claude Opus 4":
                self.headers["anthropic-beta"] = "extended-thinking-2024-12-15"
        
        elif self.provider == "gemini":
            self.api_base = "https://generativelanguage.googleapis.com/v1beta"
            self.headers = {"Content-Type": "application/json"}
            # Gemini uses API key as query parameter
    
    def analyze(self, context: Dict[str, Any]) -> AnalysisResult:
        """Perform AI analysis of build failure"""
        start_time = time.time()
        
        # Build prompt based on context
        prompt = self._build_prompt(context)
        
        # Make API call based on provider
        try:
            if self.provider == "openai":
                response = self._call_openai(prompt)
            elif self.provider == "anthropic":
                response = self._call_anthropic(prompt)
            elif self.provider == "gemini":
                response = self._call_gemini(prompt)
            else:
                raise AIProviderError(f"Provider {self.provider} not implemented")
        
        except Exception as e:
            raise AIProviderError(f"API call failed: {str(e)}")
        
        # Parse response
        analysis = self._parse_response(response)
        
        analysis_time = time.time() - start_time
        
        return AnalysisResult(
            provider=self.provider,
            model=self.model,
            root_cause=analysis["root_cause"],
            suggested_fixes=analysis["suggested_fixes"],
            confidence=analysis["confidence"],
            severity=analysis["severity"],
            analysis_time=analysis_time,
            tokens_used=analysis.get("tokens_used", 0)
        )
    
    def _build_prompt(self, context: Dict[str, Any]) -> str:
        """Build analysis prompt from context"""
        build_info = context.get("build_info", {})
        log_excerpt = context.get("log_excerpt", "")
        
        prompt = f"""Analyze this CI/CD build failure and provide actionable insights.

BUILD INFORMATION:
- Pipeline: {build_info.get('pipeline', 'unknown')}
- Branch: {build_info.get('branch', 'unknown')}
- Command: {build_info.get('command', 'unknown')}
- Exit Status: {build_info.get('exit_status', 'unknown')}

LOG EXCERPT:
{log_excerpt[:3000]}  # Limit log size

ANALYSIS REQUEST:
Please provide your analysis in the following format:

ROOT CAUSE: [Explain what specifically went wrong in 1-2 sentences]

SUGGESTED FIXES:
- [First specific, actionable solution]
- [Second specific, actionable solution]
- [Third specific, actionable solution]

CONFIDENCE: [A number 0-100]%
SEVERITY: [low/medium/high]"""
        
        return prompt
    
    def _call_openai(self, prompt: str) -> Dict[str, Any]:
        """Make API call to OpenAI"""
        url = f"{self.api_base}/{self.model_config['endpoint']}"
        
        # Map model name to API format
        api_model = self.model.lower().replace(" ", "-")
        if self.model == "GPT-4o":
            api_model = "gpt-4o"
        elif self.model == "GPT-4o mini":
            api_model = "gpt-4o-mini"
        elif self.model == "GPT-4o nano":
            api_model = "gpt-4o-nano"
        
        data = {
            "model": api_model,
            "messages": [
                {"role": "system", "content": "You are an expert DevOps engineer analyzing CI/CD failures."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": min(self.max_tokens, self.model_config["max_tokens"]),
            "temperature": 0.1
        }
        
        return self._make_request(url, data)
    
    def _call_anthropic(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Anthropic Claude"""
        url = f"{self.api_base}/{self.model_config['endpoint']}"
        
        # Map model name to API format
        api_model = self.model.lower().replace(" ", "-")
        if self.model == "Claude Opus 4":
            api_model = "claude-3-opus-20240229"  # API still uses old format
        elif self.model == "Claude Sonnet 4":
            api_model = "claude-3-sonnet-20240229"
        elif self.model == "Claude 3.5 Haiku":
            api_model = "claude-3-haiku-20240307"
        
        data = {
            "model": api_model,
            "max_tokens": min(self.max_tokens, self.model_config["max_tokens"]),
            "messages": [{"role": "user", "content": prompt}]
        }
        
        # Enable extended thinking for Opus 4
        if self.model == "Claude Opus 4":
            data["thinking"] = True
        
        return self._make_request(url, data)
    
    def _call_gemini(self, prompt: str) -> Dict[str, Any]:
        """Make API call to Google Gemini"""
        # Map model name to API format
        api_model = self.model.lower().replace(" ", "-")
        if self.model == "Gemini 2.5 Pro":
            api_model = "gemini-1.5-pro"  # API still uses old format
        elif self.model == "Gemini 2.0 Flash":
            api_model = "gemini-1.5-flash"
        
        url = f"{self.api_base}/models/{api_model}:{self.model_config['endpoint']}"
        
        # Add API key as query parameter
        url += f"?key={self.api_key}"
        
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "maxOutputTokens": min(self.max_tokens, self.model_config["max_tokens"]),
                "temperature": 0.1
            }
        }
        
        # Enable Deep Think for Pro models
        if "Pro" in self.model:
            data["generationConfig"]["deepThink"] = True
        
        # Remove Authorization header for Gemini
        headers = {k: v for k, v in self.headers.items() if k != "Authorization"}
        
        return self._make_request(url, data, headers)
    
    def _make_request(self, url: str, data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make HTTP request to AI provider with enhanced security"""
        if headers is None:
            headers = self.headers
        
        # Security: Validate URL
        if not url.startswith("https://"):
            raise AIProviderError("Only HTTPS URLs allowed")
        
        # Prepare request
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=headers)
        
        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                response_data = response.read().decode('utf-8')
                return json.loads(response_data)
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            # Security: Don't log full error body
            raise AIProviderError(f"HTTP {e.code}: {error_body[:200]}...")
        
        except urllib.error.URLError as e:
            raise AIProviderError(f"Network error: {str(e)}")
        
        except json.JSONDecodeError as e:
            raise AIProviderError(f"Invalid JSON response: {str(e)}")
    
    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI provider response into structured format"""
        try:
            if self.provider == "openai":
                content = response["choices"][0]["message"]["content"]
                tokens_used = response.get("usage", {}).get("total_tokens", 0)
            
            elif self.provider == "anthropic":
                content = response["content"][0]["text"]
                tokens_used = response.get("usage", {}).get("output_tokens", 0)
            
            elif self.provider == "gemini":
                content = response["candidates"][0]["content"]["parts"][0]["text"]
                tokens_used = response.get("usageMetadata", {}).get("totalTokenCount", 0)
            
            else:
                raise AIProviderError(f"Unknown provider: {self.provider}")
            
            # Parse structured content
            return self._extract_analysis_fields(content, tokens_used)
        
        except (KeyError, IndexError) as e:
            raise AIProviderError(f"Invalid response format: {str(e)}")
    
    def _extract_analysis_fields(self, content: str, tokens_used: int) -> Dict[str, Any]:
        """Extract structured fields from AI response"""
        import re
        
        # Initialize with defaults
        analysis = {
            "root_cause": "",
            "suggested_fixes": [],
            "confidence": 50,
            "severity": "medium",
            "tokens_used": tokens_used
        }
        
        # Debug: Log the raw AI response
        if os.getenv("AI_DEBUG", "false").lower() == "true":
            print(f"DEBUG: Raw AI response:\n{content[:500]}", file=sys.stderr)
        
        # Extract root cause
        root_cause_match = re.search(r"ROOT CAUSE[:\s]*(.+?)(?=SUGGESTED|CONFIDENCE|SEVERITY|\n\n|$)", content, re.DOTALL | re.IGNORECASE)
        if root_cause_match:
            analysis["root_cause"] = root_cause_match.group(1).strip().replace('\n', ' ')
        
        # Extract suggested fixes
        fixes_match = re.search(r"SUGGESTED FIXES?[:\s]*(.+?)(?=CONFIDENCE|SEVERITY|$)", content, re.DOTALL | re.IGNORECASE)
        if fixes_match:
            fixes_text = fixes_match.group(1)
            # Split on numbered lists or bullet points
            fixes = re.findall(r'(?:^|\n)\s*(?:\d+\.|\-|\*)\s*(.+)', fixes_text, re.MULTILINE)
            analysis["suggested_fixes"] = [fix.strip() for fix in fixes if fix.strip()]
        
        # Extract confidence
        confidence_match = re.search(r"CONFIDENCE[:\s]*(\d+)%?", content, re.IGNORECASE)
        if confidence_match:
            analysis["confidence"] = min(100, max(0, int(confidence_match.group(1))))
        
        # Extract severity
        severity_match = re.search(r"SEVERITY[:\s]*(low|medium|high)", content, re.IGNORECASE)
        if severity_match:
            analysis["severity"] = severity_match.group(1).lower()
        
        # Fallback: if structured extraction failed, try to parse the content differently
        if not analysis["root_cause"] and not analysis["suggested_fixes"]:
            # Try to extract something meaningful from the response
            lines = content.strip().split('\n')
            if lines:
                # Use first non-empty line as root cause
                for line in lines:
                    if line.strip() and len(line.strip()) > 10:
                        analysis["root_cause"] = line.strip()
                        break
                else:
                    analysis["root_cause"] = "Failed to parse AI response. Please check the logs."
            
            analysis["suggested_fixes"] = [
                "Review the error logs for PostgreSQL connection issues",
                "Ensure PostgreSQL server is running and accessible",
                "Check database connection configuration",
                "Verify network connectivity to database server"
            ]
        
        return analysis

def main():
    """CLI entry point for AI analysis"""
    parser = argparse.ArgumentParser(description="AI Error Analysis")
    parser.add_argument("--provider", required=True, choices=["openai", "anthropic", "gemini"])
    parser.add_argument("--model", help="AI model to use")
    parser.add_argument("--max-tokens", type=int, default=1000)
    parser.add_argument("--input", required=True, help="Input context JSON file")
    parser.add_argument("--output", required=True, help="Output analysis JSON file")
    
    args = parser.parse_args()
    
    try:
        # Load input context
        with open(args.input, 'r') as f:
            context = json.load(f)
        
        # Initialize analyzer
        analyzer = AIAnalyzer(args.provider, args.model, args.max_tokens)
        
        # Perform analysis
        result = analyzer.analyze(context)
        
        # Save result
        output_data = {
            "provider": result.provider,
            "model": result.model,
            "analysis": {
                "root_cause": result.root_cause,
                "suggested_fixes": result.suggested_fixes,
                "confidence": result.confidence,
                "severity": result.severity
            },
            "metadata": {
                "analysis_time": f"{result.analysis_time:.2f}s",
                "tokens_used": result.tokens_used,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        print(f"✅ Analysis completed successfully using {result.provider} {result.model}")
        print(f"📊 Confidence: {result.confidence}% | Severity: {result.severity}")
        print(f"⏱️ Analysis time: {result.analysis_time:.2f}s | Tokens: {result.tokens_used}")
    
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}", file=sys.stderr)
        
        # Create error output
        error_output = {
            "provider": args.provider,
            "model": args.model or "unknown",
            "analysis": {
                "root_cause": f"AI analysis failed: {str(e)}",
                "suggested_fixes": [
                    "Check AI provider configuration",
                    "Verify API key and network connectivity", 
                    "Review error logs manually",
                    "Contact DevOps team for assistance"
                ],
                "confidence": 0,
                "severity": "high"
            },
            "metadata": {
                "analysis_time": "0s",
                "tokens_used": 0,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        }
        
        with open(args.output, 'w') as f:
            json.dump(error_output, f, indent=2)
        
        sys.exit(1)

if __name__ == "__main__":
    main()