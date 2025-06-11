#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Error Detector
Analyzes logs to detect and categorize error patterns
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ErrorPattern:
    """Represents a detected error pattern"""
    pattern_type: str
    confidence: float
    message: str
    line_number: Optional[int] = None
    context_lines: Optional[List[str]] = None
    suggested_category: Optional[str] = None


@dataclass
class ErrorDetectionResult:
    """Result of error detection analysis"""
    error_detected: bool
    exit_code: int
    patterns: List[ErrorPattern]
    error_category: str
    summary: str
    log_lines_analyzed: int
    analysis_timestamp: str


class ErrorDetector:
    """Detects and categorizes errors from build logs"""
    
    def __init__(self):
        self.error_patterns = self._load_error_patterns()
        self.category_patterns = self._load_category_patterns()
        
    def _load_error_patterns(self) -> Dict[str, List[Dict]]:
        """Load predefined error patterns"""
        return {
            "compilation": [
                {
                    "pattern": r"(?i)(?:error|fatal):\s*(.+)",
                    "confidence": 0.9,
                    "description": "Compilation error"
                },
                {
                    "pattern": r"(?i)undefined reference to [`']([^'`]+)[`']",
                    "confidence": 0.95,
                    "description": "Undefined reference error"
                },
                {
                    "pattern": r"(?i)cannot find symbol\s*:\s*(.+)",
                    "confidence": 0.9,
                    "description": "Symbol not found error"
                },
                {
                    "pattern": r"(?i)syntax error.*?:(.+)",
                    "confidence": 0.85,
                    "description": "Syntax error"
                }
            ],
            "test_failure": [
                {
                    "pattern": r"(?i)(?:test|spec)\s+failed",
                    "confidence": 0.9,
                    "description": "Test failure"
                },
                {
                    "pattern": r"(?i)assertion.{0,20}failed",
                    "confidence": 0.9,
                    "description": "Assertion failure"
                },
                {
                    "pattern": r"(?i)expected\s+(.+?)\s+but\s+(?:got|was)\s+(.+)",
                    "confidence": 0.85,
                    "description": "Expectation mismatch"
                },
                {
                    "pattern": r"(?i)\d+\s+(?:test|spec)s?\s+failed",
                    "confidence": 0.95,
                    "description": "Multiple test failures"
                }
            ],
            "dependency": [
                {
                    "pattern": r"(?i)could not (?:resolve|find) dependency[:\s]*(.+)",
                    "confidence": 0.9,
                    "description": "Dependency resolution error"
                },
                {
                    "pattern": r"(?i)module[:\s]+(.+?)\s+not found",
                    "confidence": 0.9,
                    "description": "Module not found"
                },
                {
                    "pattern": r"(?i)package[:\s]+(.+?)\s+(?:not found|does not exist)",
                    "confidence": 0.9,
                    "description": "Package not found"
                },
                {
                    "pattern": r"(?i)no such file or directory[:\s]*(.+)",
                    "confidence": 0.8,
                    "description": "File not found"
                }
            ],
            "network": [
                {
                    "pattern": r"(?i)connection\s+(?:refused|timeout|timed out)",
                    "confidence": 0.9,
                    "description": "Network connection error"
                },
                {
                    "pattern": r"(?i)could not connect to\s+(.+)",
                    "confidence": 0.85,
                    "description": "Connection failure"
                },
                {
                    "pattern": r"(?i)(?:network|dns)\s+(?:error|failure)",
                    "confidence": 0.8,
                    "description": "Network error"
                },
                {
                    "pattern": r"(?i)certificate\s+(?:verification|validation)\s+failed",
                    "confidence": 0.9,
                    "description": "Certificate error"
                }
            ],
            "permission": [
                {
                    "pattern": r"(?i)permission denied",
                    "confidence": 0.95,
                    "description": "Permission denied"
                },
                {
                    "pattern": r"(?i)access denied",
                    "confidence": 0.9,
                    "description": "Access denied"
                },
                {
                    "pattern": r"(?i)operation not permitted",
                    "confidence": 0.9,
                    "description": "Operation not permitted"
                }
            ],
            "memory": [
                {
                    "pattern": r"(?i)out of memory",
                    "confidence": 0.95,
                    "description": "Out of memory error"
                },
                {
                    "pattern": r"(?i)memory allocation failed",
                    "confidence": 0.9,
                    "description": "Memory allocation failure"
                },
                {
                    "pattern": r"(?i)segmentation fault",
                    "confidence": 0.95,
                    "description": "Segmentation fault"
                }
            ],
            "timeout": [
                {
                    "pattern": r"(?i)timeout|timed out",
                    "confidence": 0.8,
                    "description": "Timeout error"
                },
                {
                    "pattern": r"(?i)operation cancelled.*?timeout",
                    "confidence": 0.9,
                    "description": "Operation timeout"
                }
            ]
        }
    
    def _load_category_patterns(self) -> Dict[str, float]:
        """Load patterns that help categorize the overall error type"""
        return {
            "compilation": 0.0,
            "test_failure": 0.0,
            "dependency": 0.0,
            "network": 0.0,
            "permission": 0.0,
            "memory": 0.0,
            "timeout": 0.0,
            "configuration": 0.0,
            "deployment": 0.0,
            "unknown": 0.0
        }
    
    def detect_errors(self, log_content: str, exit_code: int) -> ErrorDetectionResult:
        """Main method to detect errors in log content"""
        patterns = []
        category_scores = self.category_patterns.copy()
        
        lines = log_content.split('\n')
        
        # Analyze each line for error patterns
        for line_num, line in enumerate(lines, 1):
            line_patterns = self._analyze_line(line, line_num, lines)
            patterns.extend(line_patterns)
            
            # Update category scores based on detected patterns
            for pattern in line_patterns:
                if pattern.suggested_category:
                    category_scores[pattern.suggested_category] += pattern.confidence
        
        # Determine primary error category
        primary_category = max(category_scores.items(), key=lambda x: x[1])[0]
        if category_scores[primary_category] == 0.0:
            primary_category = "unknown"
        
        # Generate summary
        summary = self._generate_summary(patterns, primary_category, exit_code)
        
        return ErrorDetectionResult(
            error_detected=len(patterns) > 0 or exit_code != 0,
            exit_code=exit_code,
            patterns=patterns,
            error_category=primary_category,
            summary=summary,
            log_lines_analyzed=len(lines),
            analysis_timestamp=datetime.utcnow().isoformat()
        )
    
    def _analyze_line(self, line: str, line_num: int, all_lines: List[str]) -> List[ErrorPattern]:
        """Analyze a single line for error patterns"""
        detected_patterns = []
        
        for category, patterns in self.error_patterns.items():
            for pattern_def in patterns:
                regex = pattern_def["pattern"]
                
                try:
                    match = re.search(regex, line)
                    if match:
                        # Get context lines (2 before, 2 after)
                        context_start = max(0, line_num - 3)
                        context_end = min(len(all_lines), line_num + 2)
                        context_lines = all_lines[context_start:context_end]
                        
                        # Extract meaningful message from the match
                        message = match.group(1) if match.groups() else match.group(0)
                        
                        error_pattern = ErrorPattern(
                            pattern_type=pattern_def["description"],
                            confidence=pattern_def["confidence"],
                            message=message.strip(),
                            line_number=line_num,
                            context_lines=context_lines,
                            suggested_category=category
                        )
                        
                        detected_patterns.append(error_pattern)
                        
                except re.error:
                    # Skip invalid regex patterns
                    continue
        
        return detected_patterns
    
    def _generate_summary(self, patterns: List[ErrorPattern], category: str, exit_code: int) -> str:
        """Generate a human-readable summary of detected errors"""
        if not patterns and exit_code == 0:
            return "No errors detected, command executed successfully."
        
        if not patterns and exit_code != 0:
            return f"Command failed with exit code {exit_code}, but no specific error patterns were detected."
        
        # Group patterns by type
        pattern_groups = {}
        for pattern in patterns:
            pattern_type = pattern.pattern_type
            if pattern_type not in pattern_groups:
                pattern_groups[pattern_type] = []
            pattern_groups[pattern_type].append(pattern)
        
        # Build summary
        summary_parts = [f"Detected {len(patterns)} error pattern(s) in category '{category}':"]
        
        for pattern_type, group_patterns in pattern_groups.items():
            count = len(group_patterns)
            highest_confidence = max(p.confidence for p in group_patterns)
            
            if count == 1:
                summary_parts.append(f"- {pattern_type} (confidence: {highest_confidence:.0%})")
            else:
                summary_parts.append(f"- {count}x {pattern_type} (highest confidence: {highest_confidence:.0%})")
        
        return " ".join(summary_parts)
    
    def get_log_content(self) -> str:
        """Retrieve log content from Buildkite environment"""
        # Try to get log from BUILDKITE_BUILD_LOG_URL or local log file
        log_url = os.environ.get('BUILDKITE_BUILD_LOG_URL')
        
        if log_url:
            # In a real implementation, we'd fetch from the URL
            # For now, we'll use the local approach
            pass
        
        # Get log from current job output
        # This is a simplified approach - in practice, we'd need to capture
        # the actual command output more sophisticated
        return self._get_recent_log_content()
    
    def _get_recent_log_content(self) -> str:
        """Get recent log content from various sources"""
        log_sources = []
        
        # Try to read from common log locations
        possible_log_files = [
            '/tmp/buildkite-log',
            os.environ.get('BUILDKITE_BUILD_PATH', '.') + '/buildkite.log',
            './build.log',
            '/var/log/buildkite/agent.log'
        ]
        
        for log_file in possible_log_files:
            if os.path.exists(log_file):
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                        # Read last N lines
                        lines = f.readlines()
                        log_sources.append(''.join(lines[-500:]))  # Last 500 lines
                except Exception:
                    continue
        
        # If no log files found, create a minimal log from environment
        if not log_sources:
            log_sources.append(self._create_minimal_log())
        
        return '\n'.join(log_sources)
    
    def _create_minimal_log(self) -> str:
        """Create minimal log content from environment variables"""
        minimal_log = []
        
        # Add basic command information
        command = os.environ.get('BUILDKITE_COMMAND', 'unknown command')
        exit_status = os.environ.get('BUILDKITE_COMMAND_EXIT_STATUS', '1')
        
        minimal_log.append(f"Command: {command}")
        minimal_log.append(f"Exit status: {exit_status}")
        
        # Add any error-related environment variables
        for key, value in os.environ.items():
            if 'ERROR' in key.upper() or 'FAIL' in key.upper():
                minimal_log.append(f"{key}: {value}")
        
        return '\n'.join(minimal_log)


def main():
    """Main entry point for the error detector"""
    try:
        detector = ErrorDetector()
        
        # Get exit code from environment
        exit_code = int(os.environ.get('BUILDKITE_COMMAND_EXIT_STATUS', '1'))
        
        # Get log content
        log_content = detector.get_log_content()
        
        # Detect errors
        result = detector.detect_errors(log_content, exit_code)
        
        # Output result as JSON
        result_dict = asdict(result)
        print(json.dumps(result_dict, indent=2, default=str))
        
    except Exception as e:
        # Output error in a format that can be consumed by the calling script
        error_result = {
            "error_detected": True,
            "exit_code": int(os.environ.get('BUILDKITE_COMMAND_EXIT_STATUS', '1')),
            "patterns": [],
            "error_category": "detector_failure",
            "summary": f"Error detector failed: {str(e)}",
            "log_lines_analyzed": 0,
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "detector_error": str(e)
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()