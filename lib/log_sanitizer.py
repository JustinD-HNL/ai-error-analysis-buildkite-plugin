#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Log Sanitizer (2025 Update)
Enhanced security patterns for comprehensive log sanitization
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
    security_score: float

class LogSanitizer:
    """Enhanced log sanitizer with 2025 security patterns"""
    
    def __init__(self):
        self.redaction_patterns = self._compile_redaction_patterns()
        self.file_path_patterns = self._compile_file_path_patterns()
        self.url_patterns = self._compile_url_patterns()
        
    def _compile_redaction_patterns(self) -> Dict[str, Pattern]:
        """Compile comprehensive 2025 security patterns"""
        patterns = {}
        
        # 2025 AI Provider API Keys (updated patterns)
        patterns['openai_key'] = re.compile(
            r'sk-proj-[a-zA-Z0-9]{20,}T3BlbkFJ[a-zA-Z0-9]{20,}',
            re.MULTILINE
        )
        
        patterns['anthropic_key'] = re.compile(
            r'sk-ant-api03-[a-zA-Z0-9_-]{95,}',
            re.MULTILINE
        )
        
        patterns['google_key'] = re.compile(
            r'AIza[a-zA-Z0-9_-]{35}',
            re.MULTILINE
        )
        
        # Generic API Keys and Tokens (enhanced)
        patterns['generic_api_key'] = re.compile(
            r'(?i)(?:api[_-]?key|apikey|token|secret|password|passwd|pwd)[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9._-]{8,})[\'"]?',
            re.MULTILINE
        )
        
        # Bearer Tokens (OAuth 2.0, JWT, etc.)
        patterns['bearer_token'] = re.compile(
            r'Bearer[\s]+[a-zA-Z0-9._-]{20,}',
            re.MULTILINE
        )
        
        # JWT Tokens (comprehensive pattern)
        patterns['jwt_token'] = re.compile(
            r'eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*',
            re.MULTILINE
        )
        
        # GitHub Personal Access Tokens (2025 format)
        patterns['github_token'] = re.compile(
            r'(?:ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{82,})',
            re.MULTILINE
        )
        
        # Docker Registry Tokens
        patterns['docker_token'] = re.compile(
            r'(?i)(?:docker[_-]?|registry[_-]?)(?:token|password)[\s]*[=:]+[\s]*[\'"]?([^\\s\'"]{20,})[\'"]?',
            re.MULTILINE
        )
        
        # Database Connection Strings (comprehensive)
        patterns['db_connection'] = re.compile(
            r'(?i)(?:postgresql|mysql|mongodb|redis|sqlite|mssql|oracle)://[^:\s]+:[^@\s]+@[^\s]+',
            re.MULTILINE
        )
        
        # SSH Private Keys (all formats)
        patterns['ssh_keys'] = re.compile(
            r'-----BEGIN[\s\w]*PRIVATE[\s\w]*KEY-----[\s\S]*?-----END[\s\w]*PRIVATE[\s\w]*KEY-----',
            re.MULTILINE
        )
        
        # Certificate Data
        patterns['certificates'] = re.compile(
            r'-----BEGIN CERTIFICATE-----[\s\S]*?-----END CERTIFICATE-----',
            re.MULTILINE
        )
        
        # AWS Credentials (enhanced)
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
        
        # Azure Credentials
        patterns['azure_client_secret'] = re.compile(
            r'(?i)azure[_-]?client[_-]?secret[\s]*[=:]+[\s]*[\'"]?([a-zA-Z0-9~._-]{34,})[\'"]?',
            re.MULTILINE
        )
        
        # GCP Service Account Keys
        patterns['gcp_service_account'] = re.compile(
            r'"type":\s*"service_account"[^}]*"private_key":\s*"[^"]*"',
            re.MULTILINE | re.DOTALL
        )
        
        # Slack Webhook URLs
        patterns['slack_webhook'] = re.compile(
            r'https://hooks\.slack\.com/services/[A-Z0-9]{9}/[A-Z0-9]{9}/[a-zA-Z0-9]{24}',
            re.MULTILINE
        )
        
        # Generic Webhooks with Tokens
        patterns['webhook_urls'] = re.compile(
            r'https://[^/\s]+/webhooks?/[a-zA-Z0-9/_-]{20,}',
            re.MULTILINE
        )
        
        # Credit Card Numbers (basic pattern)
        patterns['credit_card'] = re.compile(
            r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
            re.MULTILINE
        )
        
        # Email Addresses
        patterns['email'] = re.compile(
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            re.MULTILINE
        )
        
        # IP Addresses
        patterns['ipv4'] = re.compile(
            r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b',
            re.MULTILINE
        )
        
        patterns['ipv6'] = re.compile(
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',
            re.MULTILINE
        )
        
        # Base64 Encoded Strings (longer than 20 chars, likely sensitive)
        patterns['base64_long'] = re.compile(
            r'(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?',
            re.MULTILINE
        )
        
        # UUIDs
        patterns['uuid'] = re.compile(
            r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b',
            re.MULTILINE | re.IGNORECASE
        )
        
        # Kubernetes Secrets
        patterns['k8s_secret'] = re.compile(
            r'(?i)(?:kubectl|kubernetes).*?(?:secret|token).*?[=:]\s*([a-zA-Z0-9+/=]{20,})',
            re.MULTILINE
        )
        
        # 2025 Cloud Service Tokens
        patterns['vercel_token'] = re.compile(
            r'(?:vercel_[a-zA-Z0-9]{24}|vc_tok_[a-zA-Z0-9]{24})',
            re.MULTILINE
        )
        
        patterns['netlify_token'] = re.compile(
            r'(?:netlify_[a-zA-Z0-9]{64}|nf_[a-zA-Z0-9]{64})',
            re.MULTILINE
        )
        
        patterns['cloudflare_token'] = re.compile(
            r'(?:cloudflare_[a-zA-Z0-9]{40}|cf_[a-zA-Z0-9]{40})',
            re.MULTILINE
        )
        
        # CI/CD Platform Tokens
        patterns['circleci_token'] = re.compile(
            r'circle_[a-zA-Z0-9]{40}',
            re.MULTILINE
        )
        
        patterns['travis_token'] = re.compile(
            r'travis_[a-zA-Z0-9]{22}',
            re.MULTILINE
        )
        
        # Package Manager Tokens
        patterns['npm_token'] = re.compile(
            r'npm_[a-zA-Z0-9]{36}',
            re.MULTILINE
        )
        
        patterns['pypi_token'] = re.compile(
            r'pypi-[a-zA-Z0-9_-]{59,}',
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
            # Docker bind mounts
            re.compile(r'-v\s+/home/([^/\s]+)', re.MULTILINE),
            re.compile(r'--volume\s+/home/([^/\s]+)', re.MULTILINE),
            # Git clone paths
            re.compile(r'Cloning into \'[^\']*?/([^/\s\']+)', re.MULTILINE),
        ]
    
    def _compile_url_patterns(self) -> List[Pattern]:
        """Compile patterns for sanitizing URLs"""
        return [
            # URLs with credentials
            re.compile(r'(https?://)[^:]+:[^@]+@', re.MULTILINE),
            # URLs with tokens in query parameters
            re.compile(r'([?&](?:token|key|auth|secret|access_token|api_key)=)[^&\s]+', re.MULTILINE | re.IGNORECASE),
            # URLs with tokens in path
            re.compile(r'/(tokens?|keys?|secrets?|auth)/([^/\s]+)', re.MULTILINE | re.IGNORECASE),
            # GitHub URLs with tokens
            re.compile(r'(https://)[^@]+@(github\.com)', re.MULTILINE),
        ]
    
    def sanitize_context(self, context: Dict[str, Any]) -> SanitizationResult:
        """Sanitize entire context object"""
        redactions_made = 0
        patterns_matched = []
        
        # Deep copy to avoid modifying original
        sanitized_context = self._deep_copy_dict(context)
        
        # Sanitize different sections
        for key, value in sanitized_context.items():
            if isinstance(value, str):
                sanitized_value, section_redactions, section_patterns = self._sanitize_text(value)
                sanitized_context[key] = sanitized_value
                redactions_made += section_redactions
                patterns_matched.extend(section_patterns)
            elif isinstance(value, dict):
                sanitized_value, section_redactions, section_patterns = self._sanitize_dict(value)
                sanitized_context[key] = sanitized_value
                redactions_made += section_redactions
                patterns_matched.extend(section_patterns)
        
        # Calculate security score
        security_score = self._calculate_security_score(redactions_made, patterns_matched)
        
        return SanitizationResult(
            sanitized_context=sanitized_context,
            redactions_made=redactions_made,
            patterns_matched=list(set(patterns_matched)),  # Remove duplicates
            security_score=security_score
        )
    
    def _sanitize_text(self, text: str) -> tuple[str, int, List[str]]:
        """Sanitize a text string"""
        if not text:
            return text, 0, []
        
        redactions_made = 0
        patterns_matched = []
        sanitized = text
        
        # Apply redaction patterns
        for pattern_name, pattern in self.redaction_patterns.items():
            if pattern_name == 'email':
                # Only partially redact emails
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append(pattern_name)
                    sanitized = pattern.sub(lambda m: self._redact_email(m.group(0)), sanitized)
                    redactions_made += len(matches)
            elif pattern_name in ['ipv4', 'ipv6']:
                # Partially redact IPs
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append(pattern_name)
                    sanitized = pattern.sub(lambda m: self._redact_ip(m.group(0)), sanitized)
                    redactions_made += len(matches)
            elif pattern_name == 'base64_long':
                # Only redact long base64 strings
                def redact_long_base64(match):
                    b64_string = match.group(0)
                    if len(b64_string) > 20:
                        return '[REDACTED_BASE64]'
                    return b64_string
                
                original_count = len(pattern.findall(sanitized))
                sanitized = pattern.sub(redact_long_base64, sanitized)
                long_b64_count = original_count - len(pattern.findall(sanitized))
                
                if long_b64_count > 0:
                    patterns_matched.append(pattern_name)
                    redactions_made += long_b64_count
            elif pattern_name == 'uuid':
                # Partially redact UUIDs
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append(pattern_name)
                    sanitized = pattern.sub(lambda m: m.group(0)[:8] + '-****-****-****-************', sanitized)
                    redactions_made += len(matches)
            else:
                # Full redaction for sensitive patterns
                matches = pattern.findall(sanitized)
                if matches:
                    patterns_matched.append(pattern_name)
                    redaction_label = f'[REDACTED_{pattern_name.upper()}]'
                    sanitized = pattern.sub(redaction_label, sanitized)
                    redactions_made += len(matches)
        
        # Apply file path redaction
        for pattern in self.file_path_patterns:
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append('file_path')
                sanitized = pattern.sub(lambda m: m.group(0).replace(m.group(1), '[USER]'), sanitized)
                redactions_made += len(matches)
        
        # Apply URL redaction
        for pattern in self.url_patterns:
            matches = pattern.findall(sanitized)
            if matches:
                patterns_matched.append('url_credentials')
                sanitized = pattern.sub(r'\1[REDACTED]', sanitized)
                redactions_made += len(matches)
        
        return sanitized, redactions_made, patterns_matched
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> tuple[Dict[str, Any], int, List[str]]:
        """Recursively sanitize dictionary"""
        sanitized_dict = {}
        total_redactions = 0
        all_patterns = []
        
        for key, value in data.items():
            # Check if key itself suggests sensitive data
            if self._is_sensitive_key(key):
                sanitized_dict[key] = '[REDACTED]'
                total_redactions += 1
                all_patterns.append('sensitive_key')
            elif isinstance(value, str):
                sanitized_value, redactions, patterns = self._sanitize_text(value)
                sanitized_dict[key] = sanitized_value
                total_redactions += redactions
                all_patterns.extend(patterns)
            elif isinstance(value, dict):
                sanitized_value, redactions, patterns = self._sanitize_dict(value)
                sanitized_dict[key] = sanitized_value
                total_redactions += redactions
                all_patterns.extend(patterns)
            elif isinstance(value, list):
                sanitized_value, redactions, patterns = self._sanitize_list(value)
                sanitized_dict[key] = sanitized_value
                total_redactions += redactions
                all_patterns.extend(patterns)
            else:
                sanitized_dict[key] = value
        
        return sanitized_dict, total_redactions, all_patterns
    
    def _sanitize_list(self, data: List[Any]) -> tuple[List[Any], int, List[str]]:
        """Recursively sanitize list"""
        sanitized_list = []
        total_redactions = 0
        all_patterns = []
        
        for item in data:
            if isinstance(item, str):
                sanitized_item, redactions, patterns = self._sanitize_text(item)
                sanitized_list.append(sanitized_item)
                total_redactions += redactions
                all_patterns.extend(patterns)
            elif isinstance(item, dict):
                sanitized_item, redactions, patterns = self._sanitize_dict(item)
                sanitized_list.append(sanitized_item)
                total_redactions += redactions
                all_patterns.extend(patterns)
            elif isinstance(item, list):
                sanitized_item, redactions, patterns = self._sanitize_list(item)
                sanitized_list.append(sanitized_item)
                total_redactions += redactions
                all_patterns.extend(patterns)
            else:
                sanitized_list.append(item)
        
        return sanitized_list, total_redactions, all_patterns
    
    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key name suggests sensitive data"""
        sensitive_keywords = [
            'secret', 'token', 'key', 'password', 'passwd', 'pwd',
            'auth', 'credential', 'cred', 'private', 'priv',
            'bearer', 'oauth', 'jwt', 'session', 'cookie',
            'certificate', 'cert', 'pem', 'p12', 'pfx',
            'webhook', 'endpoint', 'connection', 'dsn',
            'api_key', 'apikey', 'access_token', 'refresh_token'
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
        
        # Keep first and last character, redact middle
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
    
    def _calculate_security_score(self, redactions: int, patterns: List[str]) -> float:
        """Calculate security score based on sanitization effectiveness"""
        score = 100.0
        
        # Reduce score for each redaction (indicates presence of sensitive data)
        score -= min(redactions * 2, 40)
        
        # Additional penalties for specific high-risk patterns
        high_risk_patterns = ['ssh_keys', 'certificates', 'aws_secret_key', 'gcp_service_account']
        for pattern in patterns:
            if pattern in high_risk_patterns:
                score -= 10
        
        return max(0.0, score)
    
    def _deep_copy_dict(self, data: Any) -> Any:
        """Create a deep copy of data structure"""
        if isinstance(data, dict):
            return {key: self._deep_copy_dict(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self._deep_copy_dict(item) for item in data]
        else:
            return data

def main():
    """CLI entry point for log sanitization"""
    if len(sys.argv) != 3:
        print("Usage: sanitizer.py <input_context_file> <output_context_file>", file=sys.stderr)
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
        
        # Load context
        with open(input_file, 'r') as f:
            context = json.load(f)
        
        # Sanitize
        sanitizer = LogSanitizer()
        result = sanitizer.sanitize_context(context)
        
        # Add sanitization metadata
        result.sanitized_context['_sanitization'] = {
            "redactions_made": result.redactions_made,
            "patterns_matched": result.patterns_matched,
            "security_score": result.security_score,
            "sanitization_time": datetime.utcnow().isoformat(),
            "sanitizer_version": "2.0.0"
        }
        
        # Write sanitized context
        with open(output_file, 'w') as f:
            json.dump(result.sanitized_context, f, indent=2, default=str)
        
        # Set secure permissions
        os.chmod(output_file, 0o600)
        
        # Report to stderr
        print(f"✅ Sanitization complete: {result.redactions_made} redactions made", file=sys.stderr)
        print(f"🛡️ Security score: {result.security_score:.1f}/100", file=sys.stderr)
        
        if result.patterns_matched:
            print(f"🔍 Patterns matched: {', '.join(set(result.patterns_matched))}", file=sys.stderr)
        
        # Security warning if score is low
        if result.security_score < 70:
            print("⚠️ Warning: Low security score - manual review recommended", file=sys.stderr)
    
    except Exception as e:
        print(f"❌ Sanitization failed: {e}", file=sys.stderr)
        
        # Create minimal safe output
        minimal_output = {
            "error": "Sanitization failed",
            "error_details": str(e),
            "_sanitization": {
                "redactions_made": 0,
                "patterns_matched": [],
                "security_score": 0.0,
                "sanitization_time": datetime.utcnow().isoformat(),
                "error": str(e)
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