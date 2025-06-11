#!/usr/bin/env python3
"""
Unit tests for error_detector.py
"""

import json
import os
import sys
import pytest
from unittest.mock import patch, mock_open
from datetime import datetime

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lib'))

from error_detector import ErrorDetector, ErrorPattern, ErrorDetectionResult


class TestErrorDetector:
    """Test cases for ErrorDetector class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.detector = ErrorDetector()
    
    def test_init(self):
        """Test ErrorDetector initialization"""
        assert self.detector is not None
        assert hasattr(self.detector, 'error_patterns')
        assert hasattr(self.detector, 'category_patterns')
        assert isinstance(self.detector.error_patterns, dict)
        assert isinstance(self.detector.category_patterns, dict)
    
    def test_detect_compilation_error(self):
        """Test detection of compilation errors"""
        log_content = """
        Building project...
        error: syntax error before token '{'
        error: expected ';' before 'return'
        Build failed with 2 errors
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert result.exit_code == 1
        assert len(result.patterns) >= 1
        assert any(p.suggested_category == "compilation" for p in result.patterns)
        assert "compilation" in result.summary.lower()
    
    def test_detect_test_failure(self):
        """Test detection of test failures"""
        log_content = """
        Running tests...
        Test failed: expected 42 but got 24
        assertion failed: user should be authenticated
        2 tests failed, 5 passed
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert len(result.patterns) >= 1
        assert any(p.suggested_category == "test_failure" for p in result.patterns)
    
    def test_detect_dependency_error(self):
        """Test detection of dependency errors"""
        log_content = """
        Installing dependencies...
        ERROR: Could not resolve dependency: package-not-found@1.0.0
        Module 'missing-lib' not found
        Package installation failed
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert any(p.suggested_category == "dependency" for p in result.patterns)
    
    def test_detect_network_error(self):
        """Test detection of network errors"""
        log_content = """
        Downloading dependencies...
        Connection timeout: failed to connect to registry.npmjs.org
        DNS resolution failed for github.com
        Network operation failed
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert any(p.suggested_category == "network" for p in result.patterns)
    
    def test_detect_permission_error(self):
        """Test detection of permission errors"""
        log_content = """
        Writing to filesystem...
        Permission denied: cannot write to /var/log/app.log
        Access denied: insufficient privileges
        Operation failed
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert any(p.suggested_category == "permission" for p in result.patterns)
    
    def test_detect_memory_error(self):
        """Test detection of memory errors"""
        log_content = """
        Processing large dataset...
        Out of memory: cannot allocate 4GB
        Segmentation fault (core dumped)
        Process terminated
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert any(p.suggested_category == "memory" for p in result.patterns)
    
    def test_no_error_on_success(self):
        """Test that no errors are detected on successful builds"""
        log_content = """
        Building project...
        Compilation successful
        All tests passed
        Build completed successfully
        """
        
        result = self.detector.detect_errors(log_content, 0)
        
        assert not result.error_detected
        assert result.exit_code == 0
        assert len(result.patterns) == 0
    
    def test_error_with_zero_exit_code(self):
        """Test detection when exit code is 0 but patterns suggest errors"""
        log_content = """
        Running tests...
        ERROR: Test suite failed
        Fatal error occurred
        Process completed (ignoring errors)
        """
        
        result = self.detector.detect_errors(log_content, 0)
        
        assert result.error_detected  # Should detect based on patterns
        assert result.exit_code == 0
        assert len(result.patterns) > 0
    
    def test_analyze_line_with_context(self):
        """Test that context lines are properly extracted"""
        lines = [
            "Line 1: Starting process",
            "Line 2: Processing data", 
            "Line 3: ERROR: Something went wrong",
            "Line 4: Stack trace follows",
            "Line 5: Cleanup completed"
        ]
        
        patterns = self.detector._analyze_line("ERROR: Something went wrong", 3, lines)
        
        assert len(patterns) >= 1
        pattern = patterns[0]
        assert pattern.line_number == 3
        assert pattern.context_lines is not None
        assert len(pattern.context_lines) > 0
        assert "Line 1: Starting process" in pattern.context_lines
        assert "Line 5: Cleanup completed" in pattern.context_lines
    
    def test_generate_summary_multiple_patterns(self):
        """Test summary generation with multiple error patterns"""
        patterns = [
            ErrorPattern("Compilation Error", 0.9, "syntax error", 1, [], "compilation"),
            ErrorPattern("Compilation Error", 0.8, "missing semicolon", 2, [], "compilation"),
            ErrorPattern("Test Failure", 0.7, "assertion failed", 5, [], "test_failure")
        ]
        
        summary = self.detector._generate_summary(patterns, "compilation", 1)
        
        assert "3 error pattern(s)" in summary
        assert "compilation" in summary
        assert "2x Compilation Error" in summary
        assert "Test Failure" in summary
    
    def test_generate_summary_no_patterns_with_exit_code(self):
        """Test summary generation when no patterns but non-zero exit code"""
        summary = self.detector._generate_summary([], "unknown", 1)
        
        assert "exit code 1" in summary
        assert "no specific error patterns" in summary
    
    def test_generate_summary_success(self):
        """Test summary generation for successful builds"""
        summary = self.detector._generate_summary([], "unknown", 0)
        
        assert "No errors detected" in summary
        assert "successfully" in summary
    
    @patch.dict(os.environ, {
        'BUILDKITE_COMMAND': 'npm test',
        'BUILDKITE_COMMAND_EXIT_STATUS': '1'
    })
    def test_get_log_content_from_environment(self):
        """Test log content extraction from environment"""
        log_content = self.detector._get_recent_log_content()
        
        assert isinstance(log_content, str)
        # Should contain at least basic command info
        assert len(log_content) > 0
    
    def test_create_minimal_log(self):
        """Test minimal log creation from environment"""
        with patch.dict(os.environ, {
            'BUILDKITE_COMMAND': 'npm test',
            'BUILDKITE_COMMAND_EXIT_STATUS': '1',
            'TEST_ERROR_VAR': 'some error info'
        }):
            minimal_log = self.detector._create_minimal_log()
            
            assert "npm test" in minimal_log
            assert "Exit status: 1" in minimal_log
            assert "TEST_ERROR_VAR" in minimal_log
    
    @patch('builtins.open', mock_open(read_data="Test log content\nERROR: Something failed\n"))
    @patch('os.path.exists', return_value=True)
    def test_read_file_safely(self, mock_exists):
        """Test safe file reading with limits"""
        content = self.detector._read_file_safely("/fake/path", max_lines=10)
        
        assert "Test log content" in content
        assert "ERROR: Something failed" in content
    
    def test_extract_relevant_log_lines(self):
        """Test extraction of relevant log lines"""
        logs = """
        Starting application
        Loading configuration
        ERROR: Database connection failed
        Retrying connection
        FATAL: Unable to start server
        Cleaning up resources
        Process terminated
        """
        
        relevant = self.detector._extract_relevant_log_lines(logs, 5)
        lines = relevant.split('\n')
        
        # Should prioritize error lines and their context
        assert len(lines) <= 5
        assert any("ERROR" in line for line in lines)
        assert any("FATAL" in line for line in lines)
    
    def test_pattern_confidence_scoring(self):
        """Test that patterns return appropriate confidence scores"""
        log_content = "FATAL ERROR: System crashed with code 0x80004005"
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert len(result.patterns) > 0
        
        # Check that confidence scores are reasonable
        for pattern in result.patterns:
            assert 0.0 <= pattern.confidence <= 1.0
            assert pattern.confidence > 0.5  # Should be reasonably confident
    
    def test_error_category_scoring(self):
        """Test that error categories are scored correctly"""
        compilation_log = "error: syntax error before token 'return'"
        test_log = "Test failed: assertion error in login test"
        
        comp_result = self.detector.detect_errors(compilation_log, 1)
        test_result = self.detector.detect_errors(test_log, 1)
        
        assert comp_result.error_category == "compilation"
        assert test_result.error_category == "test_failure"
    
    @pytest.mark.parametrize("exit_code,log_content,should_detect", [
        (0, "Build completed successfully", False),
        (1, "ERROR: Build failed", True),
        (2, "Compilation error occurred", True),
        (0, "ERROR: Non-fatal error", True),  # Error detected despite exit code 0
        (1, "Process completed without issues", True),  # Exit code indicates error
    ])
    def test_error_detection_combinations(self, exit_code, log_content, should_detect):
        """Test various combinations of exit codes and log content"""
        result = self.detector.detect_errors(log_content, exit_code)
        
        assert result.error_detected == should_detect
        assert result.exit_code == exit_code
    
    def test_pattern_message_extraction(self):
        """Test that meaningful messages are extracted from patterns"""
        log_content = 'Error: Module "nonexistent-package" not found'
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert len(result.patterns) > 0
        
        # Should extract the module name or meaningful part
        pattern = result.patterns[0]
        assert len(pattern.message) > 0
        assert pattern.message != 'Error: Module "nonexistent-package" not found'  # Should be cleaned
    
    def test_multiline_error_detection(self):
        """Test detection of errors spanning multiple lines"""
        log_content = """
        Build started...
        
        src/main.cpp:42:15: error: expected ';' before 'return'
           42 |     int x = 5
              |               ^
              |               ;
           43 |     return x;
              |     ~~~~~~
        
        Build failed
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        assert any(p.suggested_category == "compilation" for p in result.patterns)
    
    def test_large_log_handling(self):
        """Test handling of very large log content"""
        # Create a large log with errors scattered throughout
        large_log_lines = []
        for i in range(1000):
            if i % 100 == 0:
                large_log_lines.append(f"Line {i}: ERROR: Something went wrong")
            else:
                large_log_lines.append(f"Line {i}: Normal log message")
        
        large_log = '\n'.join(large_log_lines)
        
        result = self.detector.detect_errors(large_log, 1)
        
        assert result.error_detected
        assert result.log_lines_analyzed == 1000
        assert len(result.patterns) > 0  # Should find the scattered errors
    
    def test_unicode_and_special_characters(self):
        """Test handling of unicode and special characters in logs"""
        log_content = """
        启动应用程序...
        ERROR: ファイルが見つかりません
        Błąd: nie można połączyć się z bazą danych
        🚨 Critical failure detected!
        """
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.error_detected
        # Should handle unicode gracefully without crashing
        assert len(result.patterns) > 0
    
    def test_timestamp_handling(self):
        """Test that analysis includes proper timestamps"""
        log_content = "ERROR: Test failed"
        
        result = self.detector.detect_errors(log_content, 1)
        
        assert result.analysis_timestamp is not None
        # Should be a valid ISO format timestamp
        datetime.fromisoformat(result.analysis_timestamp)
    
    def test_empty_log_content(self):
        """Test handling of empty log content"""
        result = self.detector.detect_errors("", 1)
        
        assert result.error_detected  # Due to exit code
        assert result.exit_code == 1
        assert len(result.patterns) == 0
        assert "no specific error patterns" in result.summary
    
    def test_regex_error_handling(self):
        """Test that invalid regex patterns don't crash the detector"""
        # This tests the try/catch around re.search in _analyze_line
        # We can't easily inject bad regex without modifying the patterns,
        # but we can test that the detector handles regex errors gracefully
        
        log_content = "Some log content with special regex chars: [[[((("
        
        # Should not raise an exception
        result = self.detector.detect_errors(log_content, 1)
        
        assert isinstance(result, ErrorDetectionResult)
        assert result.exit_code == 1


class TestErrorDetectionResult:
    """Test cases for ErrorDetectionResult dataclass"""
    
    def test_result_creation(self):
        """Test creating an ErrorDetectionResult"""
        patterns = [
            ErrorPattern("Test Error", 0.9, "test message", 1, ["context"], "test")
        ]
        
        result = ErrorDetectionResult(
            error_detected=True,
            exit_code=1,
            patterns=patterns,
            error_category="test_failure",
            summary="Test summary",
            log_lines_analyzed=100,
            analysis_timestamp="2023-01-01T00:00:00"
        )
        
        assert result.error_detected
        assert result.exit_code == 1
        assert len(result.patterns) == 1
        assert result.error_category == "test_failure"
        assert result.summary == "Test summary"
        assert result.log_lines_analyzed == 100
        assert result.analysis_timestamp == "2023-01-01T00:00:00"


class TestErrorPattern:
    """Test cases for ErrorPattern dataclass"""
    
    def test_pattern_creation(self):
        """Test creating an ErrorPattern"""
        pattern = ErrorPattern(
            pattern_type="Compilation Error",
            confidence=0.95,
            message="syntax error",
            line_number=42,
            context_lines=["line 41", "line 42", "line 43"],
            suggested_category="compilation"
        )
        
        assert pattern.pattern_type == "Compilation Error"
        assert pattern.confidence == 0.95
        assert pattern.message == "syntax error"
        assert pattern.line_number == 42
        assert len(pattern.context_lines) == 3
        assert pattern.suggested_category == "compilation"
    
    def test_pattern_optional_fields(self):
        """Test ErrorPattern with optional fields"""
        pattern = ErrorPattern(
            pattern_type="Generic Error",
            confidence=0.8,
            message="something went wrong"
        )
        
        assert pattern.pattern_type == "Generic Error"
        assert pattern.confidence == 0.8
        assert pattern.message == "something went wrong"
        assert pattern.line_number is None
        assert pattern.context_lines is None
        assert pattern.suggested_category is None


if __name__ == "__main__":
    pytest.main([__file__])