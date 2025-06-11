#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Log Sanitizer
Sanitizes logs and context to remove sensitive information before AI analysis
2025 Update: Enhanced security patterns and external secret manager integration
"""

import json
import os
import re
import sys
from typing import Dict, List, Any, Pattern, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib
import base64


@dataclass
class SanitizationResult:
    """Result of log sanitization process"""
    sanitized_context: Dict[str, Any]
    redactions_made: int
    patterns_matched: List[str]
    sanitization_metadata: Dict[str, Any]
    security_score: float  # 0-100, higher is more secure


class LogSanitizer:
    """Sanitizes logs and context data to remove sensitive information"""
    
    def __init__(self):
        self.redaction_patterns = self._compile_redaction_patterns()
        self.file_path_patterns = self._compile_file_path_patterns()
        self.url_patterns = self._compile_url_patterns()
        self.custom_patterns = self._load_custom_patterns()
        self.cloud_patterns = self._compile_cloud_patterns()  # 2025: Cloud-specific patterns
        self.ai_patterns = self._compile_ai_patterns()  # 2025: AI service patterns
        
    def _compile_redaction_patterns(self) -> Dict[str, Pattern]:
        """Compile regex patterns for detecting sensitive information (2025 enhanced)"""
        patterns = {}
        
        # Enhanced API Keys and tokens (2025 patterns)
        patterns['api_key_v2'] = re.compile(
            r'(?i)(?:api[_-]?key|apikey|token|secret|password|passwd|pwd|auth[_-]?token)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{8,})[\'"]?',
            re.MULTILINE
        )
        
        # OpenAI API Keys (2025 format)
        patterns['openai_key'] = re.compile(
            r'sk-proj-[a-zA-Z0-9]{20,}T3BlbkFJ[a-zA-Z0-9]{20,}',
            re.MULTILINE
        )
        
        # Anthropic API Keys (2025 format)
        patterns['anthropic_key'] = re.compile(
            r'sk-ant-api03-[a-zA-Z0-9_-]{95,}',
            re.MULTILINE
        )
        
        # Google API Keys (2025 format)
        patterns['google_key'] = re.compile(
            r'AIza[a-zA-Z0-9_-]{35}',
            re.MULTILINE
        )
        
        # GitHub Personal Access Tokens (2025 fine-grained)
        patterns['github_token'] = re.compile(
            r'github_pat_[a-zA-Z0-9_]{82,}',
            re.MULTILINE
        )
        
        # Generic secrets (enhanced pattern)
        patterns['generic_secret'] = re.compile(
            r'(?i)(?:secret|token|key|password|passwd|pwd|auth|credential|cred|bearer)[\s]*[=:]+[\s]*[\'"]?([^\s\'"]{12,})[\'"]?',
            re.MULTILINE
        )
        
        # URLs with credentials (enhanced)
        patterns['url_credentials'] = re.compile(
            r'(https?://)[^:\s]+:[^@\s]+@([^\s]+)',
            re.MULTILINE
        )
        
        # Database connection strings (enhanced)
        patterns['db_connection'] = re.compile(
            r'(?i)(?:postgresql|mysql|mongodb|redis|sqlite)://[^:\s]+:[^@\s]+@[^\s]+',
            re.MULTILINE
        )
        
        # SSH private keys (all formats)
        patterns['ssh_keys'] = re.compile(
            r'-----BEGIN[\s\w]*PRIVATE[\s\w]*KEY-----[\s\S]*?-----END[\s\w]*PRIVATE[\s\w]*KEY-----',
            re.MULTILINE
        )
        
        # JWT tokens (enhanced)
        patterns['jwt'] = re.compile(
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            re.MULTILINE
        )
        
        # Credit card numbers
        patterns['credit_card'] = re.compile(
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            re.MULTILINE
        )
        
        # Email addresses (configurable)
        patterns['email'] = re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            re.MULTILINE
        )
        
        # IPv4 addresses
        patterns['ipv4'] = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
            re.MULTILINE
        )
        
        # IPv6 addresses
        patterns['ipv6'] = re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            re.MULTILINE
        )
        
        # Base64 encoded strings (longer than 20 chars)
        patterns['base64'] = re.compile(
            r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',
            re.MULTILINE
        )
        
        # UUIDs
        patterns['uuid'] = re.compile(
            r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Docker registry authentication
        patterns['docker_auth'] = re.compile(
            r'(?i)docker\s+login.*?(?:-p|--password)\s+([^\s]+)',
            re.MULTILINE
        )
        
        # Kubernetes secrets and tokens
        patterns['k8s_secret'] = re.compile(
            r'(?i)(?:kubectl|kubernetes).*?(?:secret|token).*?[=:]\s*([a-zA-Z0-9+/=]{20,})',
            re.MULTILINE
        )
        
        return patterns
    
    def _compile_cloud_patterns(self) -> Dict[str, Pattern]:
        """Compile cloud service specific patterns (2025)"""
        patterns = {}
        
        # AWS patterns
        patterns['aws_access_key'] = re.compile(
            r'AKIA[0-9A-Z]{16}',
            re.MULTILINE
        )
        
        patterns['aws_secret_key'] = re.compile(
            r'(?i)aws[_-]?secret[_-]?access[_-]?key[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9+/]{40})[\'"]?',
            re.MULTILINE
        )
        
        patterns['aws_session_token'] = re.compile(
            r'(?i)aws[_-]?session[_-]?token[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9+/=]{100,})[\'"]?',
            re.MULTILINE
        )
        
        # Azure patterns
        patterns['azure_client_secret'] = re.compile(
            r'(?i)azure[_-]?client[_-]?secret[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9~._-]{34,})[\'"]?',
            re.MULTILINE
        )
        
        patterns['azure_tenant_id'] = re.compile(
            r'(?i)azure[_-]?tenant[_-]?id[\s]*[=:]+[\s]*[\'"]?([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})[\'"]?',
            re.MULTILINE
        )
        
        # GCP patterns
        patterns['gcp_service_account'] = re.compile(
            r'"type":\s*"service_account"[^}]*"private_key":\s*"[^"]*"',
            re.MULTILINE | re.DOTALL
        )
        
        patterns['gcp_api_key'] = re.compile(
            r'(?i)gcp[_-]?api[_-]?key[\s]*[=:]+[\s]*[\'"]?(AIza[a-zA-Z0-9_-]{35})[\'"]?',
            re.MULTILINE
        )
        
        return patterns
    
    def _compile_ai_patterns(self) -> Dict[str, Pattern]:
        """Compile AI service specific patterns (2025)"""
        patterns = {}
        
        # OpenAI specific
        patterns['openai_org_id'] = re.compile(
            r'org-[a-zA-Z0-9]{24}',
            re.MULTILINE
        )
        
        patterns['openai_project_id'] = re.compile(
            r'proj_[a-zA-Z0-9]{24}',
            re.MULTILINE
        )
        
        # Anthropic specific
        patterns['anthropic_workspace'] = re.compile(
            r'ws_[a-zA-Z0-9]{24}',
            re.MULTILINE
        )
        
        # Hugging Face
        patterns['hf_token'] = re.compile(
            r'hf_[a-zA-Z0-9]{34}',
            re.MULTILINE
        )
        
        # Replicate
        patterns['replicate_token'] = re.compile(
            r'r8_[a-zA-Z0-9]{40}',
            re.MULTILINE
        )
        
        return patterns
    
    def _compile_file_path_patterns(self) -> List[Pattern]:
        """Compile patterns for sanitizing file paths"""
        return [
            # Unix home directories
            re.compile(r'/home/([^/\s]+)', re.MULTILINE),
            # macOS home directories  
            re.compile(r'/Users/([^/\s]+)', re.MULTILINE),
            # Windows user directories
            re.compile(r'C:\\Users\\([^\\s]+)', re.MULTILINE | re.IGNORECASE),
            # Temp directories with usernames
            re.compile(r'/tmp/[^/\s]*([a-zA-Z0-9]{8,})[^/\s]*', re.MULTILINE),
            # Docker bind mounts that might expose user info
            re.compile(r'-v\s+/home/([^/\s]+)', re.MULTILINE),
            re.compile(r'--volume\s+/home/([^/\s]+)', re.MULTILINE),
        ]
    
    def _compile_url_patterns(self) -> List[Pattern]:
        """Compile patterns for sanitizing URLs"""
        return [
            # URLs with tokens in query parameters
            re.compile(r'([?&](?:token|key|auth|secret|access_token|api_key)=)[^&\s]+', re.MULTILINE | re.IGNORECASE),
            # URLs with tokens in path
            re.compile(r'/(tokens?|keys?|secrets?|auth)/([^/\s]+)', re.MULTILINE | re.IGNORECASE),
            # GitHub URLs with tokens
            re.compile(r'(https://)[^@]+@(github\.com)', re.MULTILINE),
            # Generic URLs with credentials
            re.compile(r'(https?://)[^:]+:[^@]+@', re.MULTILINE),
        ]
    
    def _load_custom_patterns(self) -> List[Pattern]:
        """Load custom redaction patterns from configuration"""
        custom_patterns_str = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_CUSTOM_PATTERNS', '[]')
        
        try:
            custom_patterns_list = json.loads(custom_patterns_str)
            compiled_patterns = []
            
            for pattern_str in custom_patterns_list:
                try:
                    compiled_patterns.append(re.compile(pattern_str, re.MULTILINE | re.IGNORECASE))
                except re.error as e:
                    print(f"Warning: Invalid custom pattern '{pattern_str}': {e}", file=sys.stderr)
            
            return compiled_patterns
        except json.JSONDecodeError:
            print(f"Warning: Invalid custom patterns JSON: {custom_patterns_str}", file=sys.stderr)
            return []
    
    def sanitize_context(self, context: Dict[str, Any]) -> SanitizationResult:
        """Sanitize entire context object"""
        redactions_made = 0
        patterns_matched = []
        
        # Deep copy the context to avoid modifying the original
        sanitized_context = self._deep_copy_dict(context)
        
        # Sanitize different sections
        if 'log_excerpt' in sanitized_context:
            sanitized_context['log_excerpt'], log_redactions, log_patterns = self._sanitize_text(
                sanitized_context['log_excerpt']
            )
            redactions_made += log_redactions
            patterns_matched.extend(log_patterns)
        
        if 'environment' in sanitized_context:
            sanitized_context['environment'], env_redactions, env_patterns = self._sanitize_environment(
                sanitized_context['environment']
            )
            redactions_made += env_redactions
            patterns_matched.extend(env_patterns)
        
        if 'error_info' in sanitized_context and 'command' in sanitized_context['error_info']:
            sanitized_context['error_info']['command'], cmd_redactions, cmd_patterns = self._sanitize_text(
                sanitized_context['error_info']['command']
            )
            redactions_made += cmd_redactions
            patterns_matched.extend(cmd_patterns)
        
        if 'git_info' in sanitized_context:
            sanitized_context['git_info'], git_redactions, git_patterns = self._sanitize_git_info(
                sanitized_context['git_info']
            )
            redactions_made += git_redactions
            patterns_matched.extend(git_patterns)
        
        if 'custom_context' in sanitized_context:
            sanitized_context['custom_context'], custom_redactions, custom_patterns = self._sanitize_text(
                sanitized_context['custom_context']
            )
            redactions_made += custom_redactions
            patterns_matched.extend(custom_patterns)
        
        # Sanitize nested dictionaries and lists recursively
        sanitized_context, nested_redactions, nested_patterns = self._sanitize_nested_data(sanitized_context)
        redactions_made += nested_redactions
        patterns_matched.extend(nested_patterns)
        
        # Calculate security score
        security_score = self._calculate_security_score(context, sanitized_context, redactions_made)
        
        return SanitizationResult(
            sanitized_context=sanitized_context,
            redactions_made=redactions_made,
            patterns_matched=list(set(patterns_matched)),  # Remove duplicates
            sanitization_metadata={
                "sanitization_time": datetime.utcnow().isoformat(),
                "sanitizer_version": "2.0.0",  # 2025 version
                "redact_file_paths": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_FILE_PATHS', 'true').lower() == 'true',
                "redact_urls": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_URLS', 'true').lower() == 'true',
                "custom_patterns_count": len(self.custom_patterns),
                "cloud_patterns_enabled": True,
                "ai_patterns_enabled": True,
                "external_secrets_used": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_USE_EXTERNAL_SECRETS', 'false').lower() == 'true'
            },
            security_score=security_score
        )
    
    def _calculate_security_score(self, original: Dict[str, Any], sanitized: Dict[str, Any], redactions: int) -> float:
        """Calculate security score based on sanitization effectiveness"""
        score = 100.0
        
        # Reduce score for each redaction (indicates presence of sensitive data)
        score -= min(redactions * 2, 40)  # Max 40 point reduction
        
        # Check for remaining potential issues
        sanitized_str = json.dumps(sanitized).lower()
        
        # Critical patterns that should never appear
        critical_patterns = [
            r'password\s*[=:]',
            r'secret\s*[=:]',
            r'token\s*[=:]',
            r'-----begin.*private.*key-----'
        ]
        
        for pattern in critical_patterns:
            if re.search(pattern, sanitized_str, re.IGNORECASE):
                score -= 25  # Severe penalty
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[a-f0-9]{32,}',  # Long hex strings
            r'[a-zA-Z0-9+/]{40,}',  # Long base64-like strings
        ]
        
        for pattern in suspicious_patterns:
            matches = len(re.findall(pattern, sanitized_str))
            score -= min(matches * 5, 20)  # Max 20 point reduction
        
        return max(0.0, score)
    
    def _sanitize_text(self, text: str) -> tuple[str, int, List[str]]:
        """Sanitize a text string"""
        if not text:
            return text, 0, []
        
        redactions_made = 0
        patterns_matched = []
        sanitized = text
        
        # Apply built-in redaction patterns
        for pattern_name, pattern in self.redaction_patterns.items():
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append(pattern_name)
                
                # Different redaction strategies based on pattern type
                if pattern_name == 'email':
                    # Only redact emails if configured to do so
                    redact_emails = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_EMAILS', 'false').lower() == 'true'
                    if redact_emails:
                        sanitized = pattern.sub(lambda m: self._redact_email(m.group(0)), sanitized)
                        redactions_made += len(matches)
                elif pattern_name in ['ipv4', 'ipv6']:
                    # Partially redact IPs: 192.168.1.1 -> 192.168.*.* 
                    sanitized = pattern.sub(lambda m: self._redact_ip(m.group(0)), sanitized)
                    redactions_made += len(matches)
                elif pattern_name == 'base64':
                    # Only redact long base64 strings (likely to be sensitive)
                    def redact_long_base64(match):
                        b64_string = match.group(0)
                        if len(b64_string) > 20:  # Only redact long base64 strings
                            return '[REDACTED_BASE64]'
                        return b64_string
                    sanitized = pattern.sub(redact_long_base64, sanitized)
                    redactions_made += len([m for m in matches if len(str(m)) > 20])
                elif pattern_name == 'uuid':
                    # UUIDs might be useful for debugging, partially redact
                    sanitized = pattern.sub(lambda m: m.group(0)[:8] + '-****-****-****-************', sanitized)
                    redactions_made += len(matches)
                else:
                    # Full redaction for sensitive patterns
                    redaction_label = f'[REDACTED_{pattern_name.upper()}]'
                    sanitized = pattern.sub(redaction_label, sanitized)
                    redactions_made += len(matches)
        
        # Apply cloud-specific patterns
        for pattern_name, pattern in self.cloud_patterns.items():
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append(f'cloud_{pattern_name}')
                redaction_label = f'[REDACTED_CLOUD_{pattern_name.upper()}]'
                sanitized = pattern.sub(redaction_label, sanitized)
                redactions_made += len(matches)
        
        # Apply AI-specific patterns
        for pattern_name, pattern in self.ai_patterns.items():
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append(f'ai_{pattern_name}')
                redaction_label = f'[REDACTED_AI_{pattern_name.upper()}]'
                sanitized = pattern.sub(redaction_label, sanitized)
                redactions_made += len(matches)
        
        # Apply custom patterns
        for i, pattern in enumerate(self.custom_patterns):
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append(f'custom_pattern_{i}')
                sanitized = pattern.sub(f'[REDACTED_CUSTOM_{i}]', sanitized)
                redactions_made += len(matches)
        
        # Apply file path redaction if enabled
        if os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_FILE_PATHS', 'true').lower() == 'true':
            for pattern in self.file_path_patterns:
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append('file_path')
                    sanitized = pattern.sub(lambda m: m.group(0).replace(m.group(1), '[USER]'), sanitized)
                    redactions_made += len(matches)
        
        # Apply URL redaction if enabled
        if os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_URLS', 'true').lower() == 'true':
            for pattern in self.url_patterns:
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append('url_credentials')
                    sanitized = pattern.sub(r'\1[REDACTED]', sanitized)
                    redactions_made += len(matches)
        
        return sanitized, redactions_made, patterns_matched
    
    def _sanitize_environment(self, env_dict: Dict[str, str]) -> tuple[Dict[str, str], int, List[str]]:
        """Sanitize environment variables"""
        sanitized_env = {}
        redactions_made = 0
        patterns_matched = []
        
        for key, value in env_dict.items():
            # Check if the key itself suggests sensitive data
            if self._is_sensitive_env_key(key):
                sanitized_env[key] = '[REDACTED]'
                redactions_made += 1
                patterns_matched.append('sensitive_env_key')
            else:
                # Sanitize the value
                sanitized_value, value_redactions, value_patterns = self._sanitize_text(value)
                sanitized_env[key] = sanitized_value
                redactions_made += value_redactions
                patterns_matched.extend(value_patterns)
        
        return sanitized_env, redactions_made, patterns_matched
    
    def _sanitize_git_info(self, git_info: Dict[str, Any]) -> tuple[Dict[str, Any], int, List[str]]:
        """Sanitize git information"""
        sanitized_git = git_info.copy()
        redactions_made = 0
        patterns_matched = []
        
        # Sanitize text fields
        text_fields = ['message', 'repo', 'recent_changes']
        for field in text_fields:
            if field in sanitized_git and isinstance(sanitized_git[field], str):
                sanitized_git[field], field_redactions, field_patterns = self._sanitize_text(sanitized_git[field])
                redactions_made += field_redactions
                patterns_matched.extend(field_patterns)
        
        # Additional git-specific sanitization
        if 'author_email' in sanitized_git:
            original_email = sanitized_git['author_email']
            sanitized_git['author_email'] = self._redact_email(original_email)
            if original_email != sanitized_git['author_email']:
                redactions_made += 1
                patterns_matched.append('email')
        
        return sanitized_git, redactions_made, patterns_matched
    
    def _sanitize_nested_data(self, data: Any) -> tuple[Any, int, List[str]]:
        """Recursively sanitize nested dictionaries and lists"""
        redactions_made = 0
        patterns_matched = []
        
        if isinstance(data, dict):
            sanitized_dict = {}
            for key, value in data.items():
                sanitized_value, nested_redactions, nested_patterns = self._sanitize_nested_data(value)
                sanitized_dict[key] = sanitized_value
                redactions_made += nested_redactions
                patterns_matched.extend(nested_patterns)
            return sanitized_dict, redactions_made, patterns_matched
        
        elif isinstance(data, list):
            sanitized_list = []
            for item in data:
                sanitized_item, nested_redactions, nested_patterns = self._sanitize_nested_data(item)
                sanitized_list.append(sanitized_item)
                redactions_made += nested_redactions
                patterns_matched.extend(nested_patterns)
            return sanitized_list, redactions_made, patterns_matched
        
        elif isinstance(data, str):
            return self._sanitize_text(data)
        
        else:
            # Return non-string, non-dict, non-list data as-is
            return data, 0, []
    
    def _is_sensitive_env_key(self, key: str) -> bool:
        """Check if an environment variable key suggests sensitive data (2025 enhanced)"""
        sensitive_keywords = [
            'secret', 'token', 'key', 'password', 'passwd', 'pwd',
            'auth', 'credential', 'cred', 'private', 'priv',
            # 2025 additions
            'bearer', 'oauth', 'jwt', 'session', 'cookie',
            'certificate', 'cert', 'pem', 'p12', 'pfx',
            'webhook', 'endpoint', 'connection', 'dsn'
        ]
        
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in sensitive_keywords)
    
    def _redact_email(self, email: str) -> str:
        """Partially redact an email address"""
        if '@' not in email:
            return email
        
        parts = email.split('@')
        if len(parts) != 2:
            return '[REDACTED_EMAIL]'
        
        username, domain = parts
        if len(username) <= 2:
            return f"[REDACTED]@{domain}"
        
        # Keep first character and last character, redact middle
        redacted_username = username[0] + '*' * (len(username) - 2) + username[-1]
        return f"{redacted_username}@{domain}"
    
    def _redact_ip(self, ip: str) -> str:
        """Partially redact an IP address"""
        if ':' in ip:  # IPv6
            parts = ip.split(':')
            if len(parts) >= 4:
                return ':'.join(parts[:2]) + ':****:****:****:****'
            return '[REDACTED_IPV6]'
        else:  # IPv4
            parts = ip.split('.')
            if len(parts) != 4:
                return '[REDACTED_IP]'
            
            # Keep first two octets, redact last two
            return f"{parts[0]}.{parts[1]}.*.*"
    
    def _deep_copy_dict(self, data: Any) -> Any:
        """Create a deep copy of data structure"""
        if isinstance(data, dict):
            return {key: self._deep_copy_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy_dict(item) for item in data]
        else:
            return data


def validate_sanitization(original: Dict[str, Any], sanitized: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that sanitization was effective (2025 enhanced)"""
    validation_result = {
        "validation_passed": True,
        "issues_found": [],
        "validation_time": datetime.utcnow().isoformat(),
        "security_warnings": [],
        "recommendations": []
    }
    
    # Check for common patterns that should have been redacted
    sensitive_patterns = [
        (r'(?i)password\s*[=:]\s*[^\s]+', 'Unredacted password'),
        (r'(?i)token\s*[=:]\s*[^\s]+', 'Unredacted token'),
        (r'(?i)secret\s*[=:]\s*[^\s]+', 'Unredacted secret'),
        (r'-----BEGIN.*PRIVATE.*KEY-----', 'Unredacted private key'),
        (r'sk-proj-[a-zA-Z0-9]+', 'OpenAI API key'),
        (r'sk-ant-api03-[a-zA-Z0-9_-]+', 'Anthropic API key'),
        (r'AIza[a-zA-Z0-9_-]{35}', 'Google API key'),
        (r'AKIA[0-9A-Z]{16}', 'AWS access key'),
        (r'github_pat_[a-zA-Z0-9_]+', 'GitHub token'),
    ]
    
    sanitized_str = json.dumps(sanitized)
    
    for pattern, description in sensitive_patterns:
        if re.search(pattern, sanitized_str):
            validation_result["validation_passed"] = False
            validation_result["issues_found"].append(f"{description}: {pattern}")
            validation_result["security_warnings"].append(description)
    
    # Additional security checks
    if len(sanitized_str) < len(json.dumps(original)) * 0.5:
        validation_result["security_warnings"].append("Significant content reduction - verify important data wasn't over-redacted")
    
    # Generate recommendations
    if validation_result["security_warnings"]:
        validation_result["recommendations"].extend([
            "Review custom redaction patterns",
            "Consider using external secret management",
            "Implement additional environment variable filtering"
        ])
    
    return validation_result


def main():
    """Main entry point for log sanitizer"""
    if len(sys.argv) != 3:
        print("Usage: log_sanitizer.py <input_context_file> <output_context_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
        # Security: Validate file paths
        for file_path in [input_file, output_file]:
            if '..' in file_path or file_path.startswith('/'):
                if not file_path.startswith(('/tmp/', '/var/tmp/')):
                    print(f"Security: Invalid file path: {file_path}", file=sys.stderr)
                    sys.exit(1)
        
        # Load context from input file
        with open(input_file, 'r') as f:
            context = json.load(f)
        
        # Initialize sanitizer and sanitize context
        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_context(context)
        
        # Validate sanitization
        validation = validate_sanitization(context, result.sanitized_context)
        
        # Add sanitization metadata to the result
        result.sanitized_context['_sanitization'] = {
            "redactions_made": result.redactions_made,
            "patterns_matched": result.patterns_matched,
            "metadata": result.sanitization_metadata,
            "validation": validation,
            "security_score": result.security_score
        }
        
        # Write sanitized context to output file with secure permissions
        with open(output_file, 'w') as f:
            json.dump(result.sanitized_context, f, indent=2, default=str)
        
        # Set secure file permissions
        os.chmod(output_file, 0o600)
        
        # Report sanitization summary to stderr
        print(f"Sanitization complete: {result.redactions_made} redactions made", file=sys.stderr)
        print(f"Security score: {result.security_score:.1f}/100", file=sys.stderr)
        
        if result.patterns_matched:
            print(f"Patterns matched: {', '.join(set(result.patterns_matched))}", file=sys.stderr)
        
        if not validation["validation_passed"]:
            print("🚨 SECURITY WARNING: Validation found potential issues:", file=sys.stderr)
            for issue in validation["issues_found"]:
                print(f"  - {issue}", file=sys.stderr)
            sys.exit(2)  # Exit with warning code
        
        if validation["security_warnings"]:
            print("⚠️ Security warnings:", file=sys.stderr)
            for warning in validation["security_warnings"]:
                print(f"  - {warning}", file=sys.stderr)
        
    except Exception as e:
        print(f"Error during sanitization: {e}", file=sys.stderr)
        
        # Create minimal sanitized output
        minimal_output = {
            "error": "Sanitization failed",
            "error_details": str(e),
            "_sanitization": {
                "redactions_made": 0,
                "patterns_matched": [],
                "metadata": {
                    "sanitization_time": datetime.utcnow().isoformat(),
                    "error": str(e)
                },
                "security_score": 0.0
            }
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(minimal_output, f, indent=2)
            os.chmod(output_file, 0o600)
        except Exception:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()