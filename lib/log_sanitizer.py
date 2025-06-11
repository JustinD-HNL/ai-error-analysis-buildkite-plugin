#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Log Sanitizer
Sanitizes logs and context to remove sensitive information before AI analysis
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
        """Compile regex patterns for detecting sensitive information"""
        patterns = {}
        
        # API Keys and tokens
        patterns['api_key'] = re.compile(
            r'(?i)(?:api[_-]?key|apikey|token|secret|password|passwd|pwd)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{8,})[\'"]?',
            re.MULTILINE
        )
        
        # Generic secrets (key=value patterns)
        patterns['generic_secret'] = re.compile(
            r'(?i)(?:secret|token|key|password|passwd|pwd|auth|credential|cred)[\s]*[=:]+[\s]*[\'"]?([^\s\'"]{8,})[\'"]?',
            re.MULTILINE
        )
        
        # URLs with credentials
        patterns['url_credentials'] = re.compile(
            r'(https?://)[^:\s]+:[^@\s]+@([^\s]+)',
            re.MULTILINE
        )
        
        # SSH private keys
        patterns['ssh_keys'] = re.compile(
            r'-----BEGIN[\s\w]*PRIVATE[\s\w]*KEY-----[\s\S]*?-----END[\s\w]*PRIVATE[\s\w]*KEY-----',
            re.MULTILINE
        )
        
        # JWT tokens
        patterns['jwt'] = re.compile(
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            re.MULTILINE
        )
        
        # Credit card numbers (simple pattern)
        patterns['credit_card'] = re.compile(
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            re.MULTILINE
        )
        
        # Email addresses (optional - might be useful context)
        patterns['email'] = re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            re.MULTILINE
        )
        
        # IPv4 addresses (optional - might be useful context)
        patterns['ipv4'] = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
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
        
        # Docker image references with tokens
        patterns['docker_auth'] = re.compile(
            r'docker\s+login.*?-p\s+([^\s]+)',
            re.MULTILINE | re.IGNORECASE
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
        ]
    
    def _compile_url_patterns(self) -> List[Pattern]:
        """Compile patterns for sanitizing URLs"""
        return [
            # URLs with tokens in query parameters
            re.compile(r'([?&](?:token|key|auth|secret)=)[^&\s]+', re.MULTILINE | re.IGNORECASE),
            # URLs with tokens in path
            re.compile(r'/(tokens?|keys?|secrets?)/([^/\s]+)', re.MULTILINE | re.IGNORECASE),
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
        
        return SanitizationResult(
            sanitized_context=sanitized_context,
            redactions_made=redactions_made,
            patterns_matched=list(set(patterns_matched)),  # Remove duplicates
            sanitization_metadata={
                "sanitization_time": datetime.utcnow().isoformat(),
                "sanitizer_version": "1.0.0",
                "redact_file_paths": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_FILE_PATHS', 'true').lower() == 'true',
                "redact_urls": os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_REDACTION_REDACT_URLS', 'true').lower() == 'true',
                "custom_patterns_count": len(self.custom_patterns)
            }
        )
    
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
                    # Partially redact emails: user@domain.com -> u***@domain.com
                    sanitized = pattern.sub(lambda m: self._redact_email(m.group(0)), sanitized)
                elif pattern_name == 'ipv4':
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
        """Check if an environment variable key suggests sensitive data"""
        sensitive_keywords = [
            'secret', 'token', 'key', 'password', 'passwd', 'pwd',
            'auth', 'credential', 'cred', 'private', 'priv'
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
        parts = ip.split('.')
        if len(parts) != 4:
            return '[REDACTED_IP]'
        
        # Keep first two octets, redact last two
        return f"{parts[0]}.{parts[1]}.*.* "
    
    def _deep_copy_dict(self, data: Any) -> Any:
        """Create a deep copy of data structure"""
        if isinstance(data, dict):
            return {key: self._deep_copy_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy_dict(item) for item in data]
        else:
            return data


def validate_sanitization(original: Dict[str, Any], sanitized: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that sanitization was effective"""
    validation_result = {
        "validation_passed": True,
        "issues_found": [],
        "validation_time": datetime.utcnow().isoformat()
    }
    
    # Check for common patterns that should have been redacted
    sensitive_patterns = [
        r'(?i)password\s*[=:]\s*[^\s]+',
        r'(?i)token\s*[=:]\s*[^\s]+',
        r'(?i)secret\s*[=:]\s*[^\s]+',
        r'-----BEGIN.*PRIVATE.*KEY-----'
    ]
    
    sanitized_str = json.dumps(sanitized)
    
    for pattern in sensitive_patterns:
        if re.search(pattern, sanitized_str):
            validation_result["validation_passed"] = False
            validation_result["issues_found"].append(f"Potential sensitive data found: {pattern}")
    
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
        
        if not validation["validation_passed"]:
            print("Warning: Validation found potential issues:", file=sys.stderr)
            for issue in validation["issues_found"]:
                print(f"  - {issue}", file=sys.stderr)
        
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