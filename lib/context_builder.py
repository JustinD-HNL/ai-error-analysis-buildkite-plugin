#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Context Builder
Safely extracts and builds context information for AI analysis
"""

import json
import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class BuildContext:
    """Comprehensive build context for AI analysis"""
    # Basic build information
    build_info: Dict[str, Any]
    
    # Error information
    error_info: Dict[str, Any]
    
    # Log excerpts (sanitized)
    log_excerpt: str
    
    # Environment context (safe subset)
    environment: Dict[str, str]
    
    # Pipeline context
    pipeline_info: Dict[str, Any]
    
    # Git context
    git_info: Dict[str, Any]
    
    # Timing information
    timing_info: Dict[str, Any]
    
    # Additional context
    custom_context: str
    
    # Metadata
    context_metadata: Dict[str, Any]


class ContextBuilder:
    """Builds comprehensive context for AI error analysis"""
    
    def __init__(self):
        self.safe_env_patterns = self._get_safe_environment_patterns()
        self.sensitive_patterns = self._get_sensitive_patterns()
        
    def _get_safe_environment_patterns(self) -> List[str]:
        """Get patterns for environment variables that are safe to include"""
        return [
            r'^BUILDKITE_.*',
            r'^CI.*',
            r'^LANG$',
            r'^PATH$',
            r'^HOME$',
            r'^USER$',
            r'^SHELL$',
            r'^NODE_VERSION$',
            r'^PYTHON_VERSION$',
            r'^JAVA_VERSION$',
            r'^GO_VERSION$',
            r'^RUBY_VERSION$'
        ]
    
    def _get_sensitive_patterns(self) -> List[str]:
        """Get patterns for sensitive environment variables to exclude"""
        return [
            r'.*(?:SECRET|TOKEN|KEY|PASSWORD|PASSWD|PWD).*',
            r'.*(?:API_KEY|APIKEY).*',
            r'.*(?:AUTH|AUTHORIZATION).*',
            r'.*(?:CREDENTIAL|CREDS).*',
            r'.*(?:PRIVATE|PRIV).*'
        ]
    
    def build_context(self) -> BuildContext:
        """Build comprehensive context for AI analysis"""
        return BuildContext(
            build_info=self._extract_build_info(),
            error_info=self._extract_error_info(),
            log_excerpt=self._extract_log_excerpt(),
            environment=self._extract_safe_environment(),
            pipeline_info=self._extract_pipeline_info(),
            git_info=self._extract_git_info(),
            timing_info=self._extract_timing_info(),
            custom_context=self._extract_custom_context(),
            context_metadata=self._generate_metadata()
        )
    
    def _extract_build_info(self) -> Dict[str, Any]:
        """Extract basic build information"""
        return {
            "build_id": os.environ.get('BUILDKITE_BUILD_ID', 'unknown'),
            "build_number": os.environ.get('BUILDKITE_BUILD_NUMBER', 'unknown'),
            "build_url": os.environ.get('BUILDKITE_BUILD_URL', ''),
            "job_id": os.environ.get('BUILDKITE_JOB_ID', 'unknown'),
            "step_key": os.environ.get('BUILDKITE_STEP_KEY', 'unknown'),
            "step_id": os.environ.get('BUILDKITE_STEP_ID', 'unknown'),
            "agent_id": os.environ.get('BUILDKITE_AGENT_ID', 'unknown'),
            "agent_name": os.environ.get('BUILDKITE_AGENT_NAME', 'unknown'),
            "organization_slug": os.environ.get('BUILDKITE_ORGANIZATION_SLUG', 'unknown'),
            "pipeline_slug": os.environ.get('BUILDKITE_PIPELINE_SLUG', 'unknown'),
            "pipeline_name": os.environ.get('BUILDKITE_PIPELINE_NAME', 'unknown')
        }
    
    def _extract_error_info(self) -> Dict[str, Any]:
        """Extract error-specific information"""
        exit_status = int(os.environ.get('BUILDKITE_COMMAND_EXIT_STATUS', '1'))
        command = os.environ.get('BUILDKITE_COMMAND', '')
        
        # Try to load error detection results if available
        error_patterns = []
        error_category = "unknown"
        
        error_detection_file = os.environ.get('AI_ERROR_ANALYSIS_TEMP_DIR', '/tmp') + '/error_detection.json'
        if os.path.exists(error_detection_file):
            try:
                with open(error_detection_file, 'r') as f:
                    error_data = json.load(f)
                    error_patterns = error_data.get('patterns', [])
                    error_category = error_data.get('error_category', 'unknown')
            except Exception:
                pass
        
        return {
            "exit_code": exit_status,
            "command": command,
            "error_patterns": error_patterns,
            "error_category": error_category,
            "failed_step": os.environ.get('BUILDKITE_STEP_KEY', 'unknown'),
            "retry_count": os.environ.get('BUILDKITE_RETRY_COUNT', '0')
        }
    
    def _extract_log_excerpt(self) -> str:
        """Extract relevant log excerpts for analysis"""
        log_lines_limit = int(os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_LOG_LINES', '500'))
        
        # Try multiple log sources
        log_sources = self._get_log_sources()
        
        all_logs = []
        for source in log_sources:
            try:
                log_content = self._read_log_source(source)
                if log_content:
                    all_logs.append(f"=== {source} ===\n{log_content}")
            except Exception as e:
                continue
        
        # Combine logs and limit size
        combined_logs = "\n\n".join(all_logs)
        
        # If logs are too long, extract the most relevant parts
        if len(combined_logs.split('\n')) > log_lines_limit:
            combined_logs = self._extract_relevant_log_lines(combined_logs, log_lines_limit)
        
        return combined_logs[:10000]  # Hard limit on character count
    
    def _get_log_sources(self) -> List[str]:
        """Get potential log sources"""
        build_path = os.environ.get('BUILDKITE_BUILD_PATH', '.')
        
        sources = [
            'buildkite_agent_log',
            'current_step_output',
            'recent_logs'
        ]
        
        # Add specific log files if they exist
        potential_files = [
            f'{build_path}/build.log',
            f'{build_path}/error.log',
            f'{build_path}/test.log',
            '/tmp/buildkite-step.log',
            '/var/log/buildkite/agent.log'
        ]
        
        for file_path in potential_files:
            if os.path.exists(file_path):
                sources.append(f'file:{file_path}')
        
        return sources
    
    def _read_log_source(self, source: str) -> Optional[str]:
        """Read content from a specific log source"""
        try:
            if source == 'buildkite_agent_log':
                return self._get_buildkite_agent_log()
            elif source == 'current_step_output':
                return self._get_current_step_output()
            elif source == 'recent_logs':
                return self._get_recent_system_logs()
            elif source.startswith('file:'):
                file_path = source[5:]
                return self._read_file_safely(file_path)
            else:
                return None
        except Exception:
            return None
    
    def _get_buildkite_agent_log(self) -> str:
        """Get Buildkite agent log output"""
        # This would typically require access to agent logs
        # For now, return basic command information
        command = os.environ.get('BUILDKITE_COMMAND', 'unknown')
        exit_status = os.environ.get('BUILDKITE_COMMAND_EXIT_STATUS', '1')
        
        return f"Command: {command}\nExit Status: {exit_status}\n"
    
    def _get_current_step_output(self) -> str:
        """Get current step output if available"""
        # Try to capture recent output from common locations
        possible_outputs = [
            '/tmp/step-output.log',
            '/tmp/buildkite-output.log'
        ]
        
        for output_file in possible_outputs:
            if os.path.exists(output_file):
                return self._read_file_safely(output_file, max_lines=200)
        
        return ""
    
    def _get_recent_system_logs(self) -> str:
        """Get recent system logs that might be relevant"""
        try:
            # Try to get recent system logs (last few minutes)
            import subprocess
            
            # Get system logs from journalctl if available
            try:
                result = subprocess.run(
                    ['journalctl', '--since', '5 minutes ago', '--no-pager', '-q'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    return result.stdout[-2000:]  # Last 2000 chars
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Fallback to dmesg
            try:
                result = subprocess.run(
                    ['dmesg', '-T'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    lines = result.stdout.split('\n')
                    return '\n'.join(lines[-50:])  # Last 50 lines
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
                
        except Exception:
            pass
        
        return ""
    
    def _read_file_safely(self, file_path: str, max_lines: int = 1000) -> str:
        """Read file content safely with limits"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if i >= max_lines:
                        break
                    lines.append(line.rstrip())
                return '\n'.join(lines)
        except Exception:
            return ""
    
    def _extract_relevant_log_lines(self, logs: str, limit: int) -> str:
        """Extract the most relevant lines from logs"""
        lines = logs.split('\n')
        
        # Prioritize lines with error indicators
        error_indicators = [
            'error', 'fail', 'exception', 'fatal', 'panic', 'abort',
            'denied', 'timeout', 'refused', 'not found', 'missing'
        ]
        
        relevant_lines = []
        context_lines = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains error indicators
            is_error_line = any(indicator in line_lower for indicator in error_indicators)
            
            if is_error_line:
                # Add context around error lines (2 before, 2 after)
                start_idx = max(0, i - 2)
                end_idx = min(len(lines), i + 3)
                context = lines[start_idx:end_idx]
                relevant_lines.extend(context)
                
                # Mark these lines as processed
                for j in range(start_idx, end_idx):
                    if j < len(lines):
                        context_lines.append(j)
        
        # If we have too many relevant lines, take the most recent ones
        if len(relevant_lines) > limit:
            relevant_lines = relevant_lines[-limit:]
        
        # Fill remaining space with recent lines not already included
        if len(relevant_lines) < limit:
            remaining_space = limit - len(relevant_lines)
            recent_lines = []
            
            for i, line in enumerate(reversed(lines)):
                if len(recent_lines) >= remaining_space:
                    break
                    
                # Don't duplicate already included lines
                line_index = len(lines) - 1 - i
                if line_index not in context_lines:
                    recent_lines.insert(0, line)
            
            relevant_lines.extend(recent_lines)
        
        return '\n'.join(relevant_lines[:limit])
    
    def _extract_safe_environment(self) -> Dict[str, str]:
        """Extract safe environment variables"""
        include_env = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_INCLUDE_ENVIRONMENT', 'true').lower() == 'true'
        
        if not include_env:
            return {}
        
        safe_env = {}
        
        for key, value in os.environ.items():
            # Check if variable matches safe patterns
            is_safe = any(re.match(pattern, key, re.IGNORECASE) for pattern in self.safe_env_patterns)
            
            # Check if variable matches sensitive patterns
            is_sensitive = any(re.match(pattern, key, re.IGNORECASE) for pattern in self.sensitive_patterns)
            
            if is_safe and not is_sensitive:
                # Truncate very long values
                safe_value = value[:200] + "..." if len(value) > 200 else value
                safe_env[key] = safe_value
        
        return safe_env
    
    def _extract_pipeline_info(self) -> Dict[str, Any]:
        """Extract pipeline-specific information"""
        include_pipeline = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_INCLUDE_PIPELINE_INFO', 'true').lower() == 'true'
        
        if not include_pipeline:
            return {}
        
        return {
            "pipeline": os.environ.get('BUILDKITE_PIPELINE_SLUG', 'unknown'),
            "pipeline_name": os.environ.get('BUILDKITE_PIPELINE_NAME', 'unknown'),
            "pipeline_provider": os.environ.get('BUILDKITE_PIPELINE_PROVIDER', 'unknown'),
            "pipeline_url": os.environ.get('BUILDKITE_PIPELINE_URL', ''),
            "step_key": os.environ.get('BUILDKITE_STEP_KEY', 'unknown'),
            "step_label": os.environ.get('BUILDKITE_LABEL', 'unknown'),
            "parallel_job": os.environ.get('BUILDKITE_PARALLEL_JOB', '0'),
            "parallel_job_count": os.environ.get('BUILDKITE_PARALLEL_JOB_COUNT', '1')
        }
    
    def _extract_git_info(self) -> Dict[str, Any]:
        """Extract git-related information"""
        include_git = os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_INCLUDE_GIT_INFO', 'true').lower() == 'true'
        
        if not include_git:
            return {}
        
        git_info = {
            "branch": os.environ.get('BUILDKITE_BRANCH', 'unknown'),
            "commit": os.environ.get('BUILDKITE_COMMIT', 'unknown'),
            "repo": self._sanitize_repo_url(os.environ.get('BUILDKITE_REPO', 'unknown')),
            "message": os.environ.get('BUILDKITE_MESSAGE', 'unknown'),
            "author": os.environ.get('BUILDKITE_BUILD_AUTHOR', 'unknown'),
            "author_email": self._sanitize_email(os.environ.get('BUILDKITE_BUILD_AUTHOR_EMAIL', 'unknown')),
            "pull_request": os.environ.get('BUILDKITE_PULL_REQUEST', 'false'),
            "tag": os.environ.get('BUILDKITE_TAG', '')
        }
        
        # Add git diff summary if available
        try:
            git_info["recent_changes"] = self._get_git_diff_summary()
        except Exception:
            git_info["recent_changes"] = "Unable to retrieve git diff"
        
        return git_info
    
    def _sanitize_repo_url(self, repo_url: str) -> str:
        """Sanitize repository URL to remove credentials"""
        if not repo_url or repo_url == 'unknown':
            return repo_url
        
        # Remove credentials from git URLs
        # https://user:pass@github.com/org/repo.git -> https://github.com/org/repo.git
        sanitized = re.sub(r'(https?://)([^:]+:[^@]+@)', r'\1', repo_url)
        
        # git@github.com:org/repo.git is already safe
        return sanitized
    
    def _sanitize_email(self, email: str) -> str:
        """Sanitize email address for privacy"""
        if not email or email == 'unknown' or '@' not in email:
            return email
        
        # Replace email with masked version: user@domain.com -> u***@domain.com
        parts = email.split('@')
        if len(parts) == 2:
            username = parts[0]
            domain = parts[1]
            
            if len(username) > 1:
                masked_username = username[0] + '*' * (len(username) - 1)
                return f"{masked_username}@{domain}"
        
        return email
    
    def _get_git_diff_summary(self) -> str:
        """Get a summary of recent git changes"""
        try:
            import subprocess
            
            # Get summary of changes in last commit
            result = subprocess.run(
                ['git', 'diff', '--stat', 'HEAD~1', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.environ.get('BUILDKITE_BUILD_PATH', '.')
            )
            
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            
            # Fallback: get list of changed files
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
                capture_output=True,
                text=True,
                timeout=5,
                cwd=os.environ.get('BUILDKITE_BUILD_PATH', '.')
            )
            
            if result.returncode == 0 and result.stdout.strip():
                files = result.stdout.strip().split('\n')
                return f"Changed files: {', '.join(files[:10])}" + ("..." if len(files) > 10 else "")
            
        except Exception:
            pass
        
        return "Git diff not available"
    
    def _extract_timing_info(self) -> Dict[str, Any]:
        """Extract timing and performance information"""
        timing_info = {}
        
        # Build timing
        if 'BUILDKITE_JOB_STARTED_AT' in os.environ:
            timing_info['job_started_at'] = os.environ['BUILDKITE_JOB_STARTED_AT']
        
        if 'BUILDKITE_BUILD_CREATED_AT' in os.environ:
            timing_info['build_created_at'] = os.environ['BUILDKITE_BUILD_CREATED_AT']
        
        # Calculate duration if possible
        try:
            if 'BUILDKITE_JOB_STARTED_AT' in os.environ:
                from dateutil import parser
                start_time = parser.parse(os.environ['BUILDKITE_JOB_STARTED_AT'])
                duration = datetime.utcnow() - start_time.replace(tzinfo=None)
                timing_info['duration_seconds'] = int(duration.total_seconds())
        except Exception:
            pass
        
        # Add current time
        timing_info['analysis_time'] = datetime.utcnow().isoformat()
        
        return timing_info
    
    def _extract_custom_context(self) -> str:
        """Extract custom context provided by user"""
        return os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_CONTEXT_CUSTOM_CONTEXT', '')
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate metadata about the context extraction"""
        return {
            "context_version": "1.0",
            "extraction_time": datetime.utcnow().isoformat(),
            "builder_version": "1.0.0",
            "safe_env_count": len(self._extract_safe_environment()),
            "build_path": os.environ.get('BUILDKITE_BUILD_PATH', 'unknown'),
            "agent_version": os.environ.get('BUILDKITE_AGENT_VERSION', 'unknown')
        }


def main():
    """Main entry point for context builder"""
    try:
        builder = ContextBuilder()
        context = builder.build_context()
        
        # Convert to dictionary and output as JSON
        context_dict = asdict(context)
        print(json.dumps(context_dict, indent=2, default=str))
        
    except Exception as e:
        # Output minimal context even if extraction fails
        error_context = {
            "build_info": {"error": "Context extraction failed"},
            "error_info": {
                "exit_code": int(os.environ.get('BUILDKITE_COMMAND_EXIT_STATUS', '1')),
                "command": os.environ.get('BUILDKITE_COMMAND', 'unknown'),
                "error_patterns": [],
                "error_category": "context_failure"
            },
            "log_excerpt": f"Failed to extract context: {str(e)}",
            "environment": {},
            "pipeline_info": {},
            "git_info": {},
            "timing_info": {"analysis_time": datetime.utcnow().isoformat()},
            "custom_context": "",
            "context_metadata": {
                "extraction_error": str(e),
                "extraction_time": datetime.utcnow().isoformat()
            }
        }
        
        print(json.dumps(error_context, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()