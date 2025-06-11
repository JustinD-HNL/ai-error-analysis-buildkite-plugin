#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Log Sanitizer (2025 Update)
Sanitizes logs and context to remove sensitive information before AI analysis
Enhanced with 2025 security patterns and modern threat protection
"""

import json
import os
import re
import sys
from typing import Dict, List, Any, Pattern
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SanitizationResult:
    """Result of log sanitization process"""
    sanitized_context: Dict[str, Any]
    redactions_made: int
    patterns_matched: List[str]
    sanitization_metadata: Dict[str, Any]


class LogSanitizer:
    """Sanitizes logs and context data to remove sensitive information"""
    
    def __init__(self):
        self.redaction_patterns = self._compile_redaction_patterns()
        self.file_path_patterns = self._compile_file_path_patterns()
        self.url_patterns = self._compile_url_patterns()
        self.custom_patterns = self._load_custom_patterns()
        
    def _compile_redaction_patterns(self) -> Dict[str, Pattern]:
        """Compile regex patterns for detecting sensitive information (2025 update)"""
        patterns = {}
        
        # Modern API Keys and tokens (2025 patterns)
        patterns['api_key'] = re.compile(
            r'(?i)(?:api[_-]?key|apikey|token|secret|password|passwd|pwd)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{8,})[\'"]?',
            re.MULTILINE
        )
        
        # Bearer tokens (JWT and OAuth)
        patterns['bearer_token'] = re.compile(
            r'Bearer[\s]+([a-zA-Z0-9._-]{20,})',
            re.MULTILINE
        )
        
        # JWT tokens (updated pattern for 2025)
        patterns['jwt'] = re.compile(
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            re.MULTILINE
        )
        
        # Modern OAuth tokens
        patterns['oauth_token'] = re.compile(
            r'(?i)(access[_-]?token|refresh[_-]?token|oauth[_-]?token)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{20,})[\'"]?',
            re.MULTILINE
        )
        
        # Cloud provider specific patterns
        patterns['aws_access_key'] = re.compile(
            r'AKIA[0-9A-Z]{16}',
            re.MULTILINE
        )
        
        patterns['aws_secret_key'] = re.compile(
            r'(?i)aws[_-]?secret[_-]?access[_-]?key[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9/+=]{40})[\'"]?',
            re.MULTILINE
        )
        
        patterns['gcp_service_account'] = re.compile(
            r'"type":\s*"service_account"[^}]*}',
            re.MULTILINE | re.DOTALL
        )
        
        patterns['azure_connection_string'] = re.compile(
            r'(?i)(?:DefaultEndpointsProtocol|AccountName|AccountKey|EndpointSuffix)=[^;]+',
            re.MULTILINE
        )
        
        # Container registry tokens
        patterns['docker_auth'] = re.compile(
            r'(?i)(docker[_-]?|registry[_-]?)(token|password|auth)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{20,})[\'"]?',
            re.MULTILINE
        )
        
        # Database connection strings (comprehensive)
        patterns['db_connection'] = re.compile(
            r'(?i)(mongodb|postgresql|mysql|redis|mssql|oracle)://[^:\s]+:[^@\s]+@[^\s/]+[^\s]*',
            re.MULTILINE
        )
        
        patterns['db_password'] = re.compile(
            r'(?i)(password|pwd)[\s]*[=:]+[\s]*[\'"]?([^;\s\'"]{8,})[\'"]?',
            re.MULTILINE
        )
        
        # SSH and TLS keys
        patterns['ssh_private_key'] = re.compile(
            r'-----BEGIN[\\s\\w]*PRIVATE[\\s\\w]*KEY-----[\\s\\S]*?-----END[\\s\\w]*PRIVATE[\\s\\w]*KEY-----',
            re.MULTILINE
        )
        
        patterns['tls_certificate'] = re.compile(
            r'-----BEGIN CERTIFICATE-----[\\s\\S]*?-----END CERTIFICATE-----',
            re.MULTILINE
        )
        
        patterns['tls_private_key'] = re.compile(
            r'-----BEGIN RSA PRIVATE KEY-----[\\s\\S]*?-----END RSA PRIVATE KEY-----',
            re.MULTILINE
        )
        
        # Modern webhook URLs with tokens
        patterns['webhook_url'] = re.compile(
            r'https://hooks\.slack\.com/services/[A-Z0-9]{9}/[A-Z0-9]{9}/[a-zA-Z0-9]{24}',
            re.MULTILINE
        )
        
        patterns['discord_webhook'] = re.compile(
            r'https://discord\.com/api/webhooks/[0-9]+/[a-zA-Z0-9_-]+',
            re.MULTILINE
        )
        
        patterns['teams_webhook'] = re.compile(
            r'https://[a-zA-Z0-9]+\.webhook\.office\.com/webhookb2/[a-f0-9-]+@[a-f0-9-]+/IncomingWebhook/[a-f0-9]+/[a-f0-9-]+',
            re.MULTILINE
        )
        
        # Credit card numbers (PCI DSS compliance)
        patterns['credit_card'] = re.compile(
            r'\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\\b',
            re.MULTILINE
        )
        
        # Social Security Numbers (US)
        patterns['ssn'] = re.compile(
            r'\\b(?!000|666|9\\d{2})\\d{3}-(?!00)\\d{2}-(?!0000)\\d{4}\\b',
            re.MULTILINE
        )
        
        # Email addresses (configurable - might be useful context)
        patterns['email'] = re.compile(
            r'\\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}\\b',
            re.MULTILINE
        )
        
        # IP addresses (configurable - might be useful context)
        patterns['ipv4'] = re.compile(
            r'\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b',
            re.MULTILINE
        )
        
        patterns['ipv6'] = re.compile(
            r'\\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\\b',
            re.MULTILINE
        )
        
        # Base64 encoded data (potential secrets)
        patterns['base64'] = re.compile(
            r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',
            re.MULTILINE
        )
        
        # UUIDs (might contain sensitive identifiers)
        patterns['uuid'] = re.compile(
            r'\\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\b',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Kubernetes secrets and tokens
        patterns['k8s_token'] = re.compile(
            r'(?i)(serviceaccount|bearer)[_-]?token[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{20,})[\'"]?',
            re.MULTILINE
        )
        
        # CI/CD specific tokens
        patterns['buildkite_token'] = re.compile(
            r'bkua_[a-f0-9]{40}',
            re.MULTILINE
        )
        
        patterns['github_token'] = re.compile(
            r'gh[pousr]_[A-Za-z0-9_]{36,255}',
            re.MULTILINE
        )
        
        patterns['gitlab_token'] = re.compile(
            r'glpat-[a-zA-Z0-9_-]{20}',
            re.MULTILINE
        )
        
        # Terraform and infrastructure tokens
        patterns['terraform_token'] = re.compile(
            r'(?i)(terraform|tf)[_-]?(token|key)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{20,})[\'"]?',
            re.MULTILINE
        )
        
        # Modern messaging and communication tokens
        patterns['slack_token'] = re.compile(
            r'xox[baprs]-([0-9a-zA-Z]{10,48})',
            re.MULTILINE
        )
        
        patterns['discord_token'] = re.compile(
            r'[MN][A-Za-z\\d]{23}\\.[\\w-]{6}\\.[\\w-]{27}',
            re.MULTILINE
        )
        
        # Package manager tokens
        patterns['npm_token'] = re.compile(
            r'npm_[a-zA-Z0-9]{36}',
            re.MULTILINE
        )
        
        patterns['pypi_token'] = re.compile(
            r'pypi-[a-zA-Z0-9_-]{59}',
            re.MULTILINE
        )
        
        # Generic secrets (catch-all for new patterns)
        patterns['generic_secret'] = re.compile(
            r'(?i)(?:secret|token|key|password|passwd|pwd|auth|credential|cred)[\s]*[=:]+[\s]*[\'"]?([^\\s\'"]{12,})[\'"]?',
            re.MULTILINE
        )
        
        return patterns
    
    def _compile_file_path_patterns(self) -> List[Pattern]:
        """Compile patterns for sanitizing file paths"""
        return [
            # Unix home directories
            re.compile(r'/home/([^/\\s]+)', re.MULTILINE),
            # macOS home directories  
            re.compile(r'/Users/([^/\\s]+)', re.MULTILINE),
            # Windows user directories
            re.compile(r'C:\\\\Users\\\\([^\\\\s]+)', re.MULTILINE | re.IGNORECASE),
            # Windows profile paths
            re.compile(r'C:\\\\Documents and Settings\\\\([^\\\\s]+)', re.MULTILINE | re.IGNORECASE),
            # Temp directories with usernames
            re.compile(r'/tmp/[^/\\s]*([a-zA-Z0-9]{8,})[^/\\s]*', re.MULTILINE),
            # Container specific paths
            re.compile(r'/var/lib/docker/[^\\s]+', re.MULTILINE),
            re.compile(r'/var/lib/containers/[^\\s]+', re.MULTILINE),
        ]
    
    def _compile_url_patterns(self) -> List[Pattern]:
        """Compile patterns for sanitizing URLs"""
        return [
            # URLs with tokens in query parameters
            re.compile(r'([?&](?:token|key|auth|secret|password|access_token|refresh_token)=)[^&\\s]+', re.MULTILINE | re.IGNORECASE),
            # URLs with tokens in path
            re.compile(r'/(tokens?|keys?|secrets?|auth)/([^/\\s]+)', re.MULTILINE | re.IGNORECASE),
            # URLs with credentials in authority
            re.compile(r'(https?://)([^:]+):([^@]+)@', re.MULTILINE),
            # Git URLs with tokens
            re.compile(r'(git\\+https?://)[^:]+:[^@]+@', re.MULTILINE),
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
        
        # Input validation
        max_log_size = int(os.environ.get('AI_ERROR_ANALYSIS_MAX_LOG_SIZE_BYTES', 50 * 1024 * 1024))
        
        # Sanitize different sections
        if 'log_excerpt' in sanitized_context:
            log_excerpt = sanitized_context['log_excerpt']
            
            # Check log size
            if len(log_excerpt.encode('utf-8')) > max_log_size:
                print(f"Warning: Log excerpt exceeds maximum size ({max_log_size} bytes), truncating", file=sys.stderr)
                log_excerpt = log_excerpt[:max_log_size // 2]  # Conservative truncation
                log_excerpt += "\\n... [Log truncated for security] ..."
                sanitized_context['log_excerpt'] = log_excerpt
            
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
            # Validate command for injection attacks
            command = sanitized_context['error_info']['command']
            if self._contains_command_injection(command):
                print("Warning: Potential command injection detected in command, sanitizing", file=sys.stderr)
                sanitized_context['error_info']['command'] = '[SANITIZED_COMMAND]'
                redactions_made += 1
                patterns_matched.append('command_injection')
            else:
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
            custom_context = sanitized_context['custom_context']
            
            # Validate custom context size
            if len(custom_context) > 2000:
                print("Warning: Custom context exceeds maximum length, truncating", file=sys.stderr)
                custom_context = custom_context[:2000]
            
            sanitized_context['custom_context'], custom_redactions, custom_patterns = self._sanitize_text(
                custom_context
            )
            redactions_made += custom_redactions
            patterns_matched.extend(custom_patterns)
        
        # Sanitize nested dictionaries and lists recursively
        sanitized_context, nested_redactions, nested_patterns = self._sanitize_nested_data(sanitized_context)
        redactions_made += nested_redactions
        patterns_matched.extend(nested_patterns)
        
        return SanitizationResult(
            sanitized_context=sanitized_context,
            redactions_made=redactions_made,
            patterns_matched=list(set(patterns_matched)),  # Remove duplicates
            sanitization_metadata={
                "sanitization_time": datetime.utcnow().isoformat(),
                "sanitizer_version": "2.0.0",  # Updated for 2025
                "redact_file_paths": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_FILE_PATHS', 'true').lower() == 'true',
                "redact_urls": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_URLS', 'true').lower() == 'true',
                "enable_builtin_patterns": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_ENABLE_BUILTIN_PATTERNS', 'true').lower() == 'true',
                "custom_patterns_count": len(self.custom_patterns),
                "max_log_size_bytes": int(os.environ.get('AI_ERROR_ANALYSIS_MAX_LOG_SIZE_BYTES', 50 * 1024 * 1024))
            }
        )
    
    def _contains_command_injection(self, command: str) -> bool:
        """Check for potential command injection patterns"""
        if not command:
            return False
        
        dangerous_patterns = [
            r'[;&|`$()]',  # Command separators and substitution
            r'\\b(rm|del|format|mkfs)\\s',  # Destructive commands
            r'\\b(wget|curl)\\s+[^\\s]*\\|',  # Download and pipe
            r'\\b(nc|netcat)\\s',  # Network tools
            r'\\b(python|perl|ruby|php)\\s+-[ce]',  # Script execution
            r'/dev/(tcp|udp)/',  # Network devices
            r'>(>?)\\s*/dev/',  # Output redirection to devices
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False
    
    def _sanitize_text(self, text: str) -> tuple[str, int, List[str]]:
        """Sanitize a text string"""
        if not text:
            return text, 0, []
        
        redactions_made = 0
        patterns_matched = []
        sanitized = text
        
        # Check if builtin patterns are enabled
        enable_builtin = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_ENABLE_BUILTIN_PATTERNS', 'true').lower() == 'true'
        
        if enable_builtin:
            # Apply built-in redaction patterns
            for pattern_name, pattern in self.redaction_patterns.items():
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append(pattern_name)
                    
                    # Different redaction strategies based on pattern type
                    if pattern_name == 'email':
                        # Partially redact emails: user@domain.com -> u***@domain.com
                        sanitized = pattern.sub(lambda m: self._redact_email(m.group(0)), sanitized)
                    elif pattern_name in ['ipv4', 'ipv6']:
                        # Partially redact IPs: 192.168.1.1 -> 192.168.*.* 
                        sanitized = pattern.sub(lambda m: self._redact_ip(m.group(0)), sanitized)
                    elif pattern_name == 'base64':
                        # Only redact long base64 strings (likely to be sensitive)
                        def redact_long_base64(match):
                            b64_string = match.group(0)
                            if len(b64_string) > 20:  # Only redact long base64 strings
                                return '[REDACTED_BASE64]'
                            return b64_string
                        sanitized = pattern.sub(redact_long_base64, sanitized)
                    elif pattern_name == 'uuid':
                        # UUIDs might be useful for debugging, partially redact
                        sanitized = pattern.sub(lambda m: m.group(0)[:8] + '-****-****-****-************', sanitized)
                    elif pattern_name in ['credit_card', 'ssn']:
                        # Full redaction for PCI/PII data
                        sanitized = pattern.sub('[REDACTED_PII]', sanitized)
                    elif pattern_name in ['aws_access_key', 'github_token', 'gitlab_token', 'buildkite_token']:
                        # Full redaction for known token formats
                        sanitized = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', sanitized)
                    else:
                        # Full redaction for sensitive patterns
                        sanitized = pattern.sub(f'[REDACTED_{pattern_name.upper()}]', sanitized)
                    
                    redactions_made += len(matches)
        
        # Apply custom patterns
        for pattern in self.custom_patterns:
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append('custom_pattern')
                sanitized = pattern.sub('[REDACTED_CUSTOM]', sanitized)
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
                    sanitized = pattern.sub(r'\\1[REDACTED]', sanitized)
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
        
        # Sanitize repository URL
        if 'repo' in sanitized_git:
            repo_url = sanitized_git['repo']
            if self._contains_credentials_in_url(repo_url):
                sanitized_git['repo'] = self._sanitize_repo_url(repo_url)
                redactions_made += 1
                patterns_matched.append('repo_credentials')
        
        return sanitized_git, redactions_made, patterns_matched
    
    def _contains_credentials_in_url(self, url: str) -> bool:
        """Check if URL contains credentials"""
        if not url:
            return False
        
        # Check for user:pass@host pattern
        return re.search(r'://[^:]+:[^@]+@', url) is not None
    
    def _sanitize_repo_url(self, url: str) -> str:
        """Sanitize repository URL to remove credentials"""
        if not url:
            return url
        
        # Remove credentials from git URLs
        # https://user:pass@github.com/org/repo.git -> https://github.com/org/repo.git
        sanitized = re.sub(r'(https?://)([^:]+:[^@]+@)', r'\\1', url)
        
        return sanitized
    
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
        """Check if an environment variable key suggests sensitive data (2025 update)"""
        sensitive_keywords = [
            'secret', 'token', 'key', 'password', 'passwd', 'pwd',
            'auth', 'credential', 'cred', 'private', 'priv',
            'api_key', 'apikey', 'access_token', 'refresh_token',
            'webhook', 'slack_token', 'discord_token', 'github_token',
            'aws_secret', 'gcp_key', 'azure_key', 'connection_string',
            'certificate', 'cert', 'ssl', 'tls'
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
                return f"{parts[0]}:{parts[1]}:****:****"
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
    """Validate that sanitization was effective (2025 enhanced validation)"""
    validation_result = {
        "validation_passed": True,
        "issues_found": [],
        "validation_time": datetime.utcnow().isoformat(),
        "security_score": 100
    }
    
    # Check for common patterns that should have been redacted
    sensitive_patterns = [
        r'(?i)password\\s*[=:]\\s*[^\\s]+',
        r'(?i)token\\s*[=:]\\s*[^\\s]+',
        r'(?i)secret\\s*[=:]\\s*[^\\s]+',
        r'-----BEGIN.*PRIVATE.*KEY-----',
        r'AKIA[0-9A-Z]{16}',  # AWS Access Key
        r'eyJ[a-zA-Z0-9_-]*\\.eyJ[a-zA-Z0-9_-]*\\.[a-zA-Z0-9_-]*',  # JWT
        r'Bearer [a-zA-Z0-9._-]{20,}',  # Bearer tokens
        r'gh[pousr]_[A-Za-z0-9_]{36,255}',  # GitHub tokens
        r'xox[baprs]-[0-9a-zA-Z]{10,48}',  # Slack tokens
    ]
    
    sanitized_str = json.dumps(sanitized)
    
    for i, pattern in enumerate(sensitive_patterns):
        if re.search(pattern, sanitized_str):
            validation_result["validation_passed"] = False
            validation_result["issues_found"].append(f"Potential sensitive data found (pattern {i+1})")
            validation_result["security_score"] -= 10
    
    # Check for potential PII
    pii_patterns = [
        r'\\b(?!000|666|9\\d{2})\\d{3}-(?!00)\\d{2}-(?!0000)\\d{4}\\b',  # SSN
        r'\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\\b',  # Credit cards
    ]
    
    for i, pattern in enumerate(pii_patterns):
        if re.search(pattern, sanitized_str):
            validation_result["validation_passed"] = False
            validation_result["issues_found"].append(f"Potential PII found (pattern {i+1})")
            validation_result["security_score"] -= 20
    
    # Ensure security score doesn't go below 0
    validation_result["security_score"] = max(0, validation_result["security_score"])
    
    return validation_result


def main():
    """Main entry point for log sanitizer"""
    if len(sys.argv) != 3:
        print("Usage: log_sanitizer.py <input_context_file> <output_context_file>", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    try:
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
            "validation": validation
        }
        
        # Write sanitized context to output file
        with open(output_file, 'w') as f:
            json.dump(result.sanitized_context, f, indent=2, default=str)
        
        # Report sanitization summary to stderr
        print(f"Sanitization complete: {result.redactions_made} redactions made", file=sys.stderr)
        if result.patterns_matched:
            print(f"Patterns matched: {', '.join(set(result.patterns_matched))}", file=sys.stderr)
        
        print(f"Security score: {validation['security_score']}/100", file=sys.stderr)
        
        if not validation["validation_passed"]:
            print("⚠️ Validation found potential security issues:", file=sys.stderr)
            for issue in validation["issues_found"]:
                print(f"  - {issue}", file=sys.stderr)
            
            # Exit with warning code if security score is too low
            if validation["security_score"] < 70:
                sys.exit(2)
        
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
                }
            }
        }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(minimal_output, f, indent=2)
        except Exception:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()