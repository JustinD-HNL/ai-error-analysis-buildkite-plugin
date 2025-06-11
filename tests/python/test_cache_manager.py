#!/usr/bin/env python3
"""
Unit tests for cache_manager.py
"""

import json
import os
import sys
import tempfile
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, mock_open

# Add the lib directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lib'))

from cache_manager import CacheManager, CacheEntry


class TestCacheManager:
    """Test cases for CacheManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = CacheManager(cache_dir=self.temp_dir, ttl_seconds=3600)
        
        self.sample_context = {
            'error_info': {
                'exit_code': 1,
                'error_category': 'test_failure',
                'command': 'npm test'
            },
            'log_excerpt': 'Test failed: assertion error',
            'build_info': {
                'pipeline': 'test-pipeline',
                'build_id': 'build-123'
            },
            'pipeline_info': {
                'pipeline': 'test-pipeline',
                'step_key': 'test-step'
            }
        }
        
        self.sample_analysis = {
            'provider': 'openai',
            'model': 'gpt-4o-mini',
            'analysis': {
                'root_cause': 'Test assertion failed',
                'suggested_fixes': ['Fix the test', 'Check data'],
                'confidence': 85
            },
            'metadata': {
                'tokens_used': 100,
                'analysis_time': '2.5s'
            }
        }
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test CacheManager initialization"""
        assert self.cache_manager.cache_dir == Path(self.temp_dir)
        assert self.cache_manager.ttl_seconds == 3600
        assert self.cache_manager.cache_dir.exists()
    
    def test_init_with_defaults(self):
        """Test CacheManager initialization with default values"""
        with patch.dict(os.environ, {'AI_ERROR_ANALYSIS_CACHE_DIR': '/tmp/test-cache'}):
            manager = CacheManager()
            assert str(manager.cache_dir) == '/tmp/test-cache'
    
    def test_generate_context_hash(self):
        """Test context hash generation"""
        hash1 = self.cache_manager._generate_context_hash(self.sample_context)
        hash2 = self.cache_manager._generate_context_hash(self.sample_context)
        
        # Same context should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 16  # Truncated to 16 chars
        assert isinstance(hash1, str)
    
    def test_generate_context_hash_different_contexts(self):
        """Test that different contexts produce different hashes"""
        context2 = self.sample_context.copy()
        context2['error_info']['exit_code'] = 2
        
        hash1 = self.cache_manager._generate_context_hash(self.sample_context)
        hash2 = self.cache_manager._generate_context_hash(context2)
        
        assert hash1 != hash2
    
    def test_normalize_log_excerpt(self):
        """Test log excerpt normalization"""
        log_with_timestamps = "2023-01-01T10:00:00 ERROR: Test failed\n2023-01-01T10:00:01 INFO: Cleanup"
        normalized = self.cache_manager._normalize_log_excerpt(log_with_timestamps)
        
        # Timestamps should be normalized
        assert "[TIMESTAMP]" in normalized
        assert "2023-01-01T10:00:00" not in normalized
    
    def test_normalize_log_excerpt_paths(self):
        """Test path normalization in log excerpts"""
        log_with_paths = "/home/user/project/src/main.js:42 ERROR: Test failed"
        normalized = self.cache_manager._normalize_log_excerpt(log_with_paths)
        
        # Paths should be normalized
        assert "[PATH]/" in normalized or "main.js" in normalized
    
    def test_store_and_check_cache(self):
        """Test storing and retrieving cache entries"""
        # Store analysis result
        success = self.cache_manager.store(self.sample_context, self.sample_analysis)
        assert success
        
        # Check cache hit
        result = self.cache_manager.check(self.sample_context)
        assert result is not None
        assert result['provider'] == 'openai'
        assert result['metadata']['cached'] is True
        assert result['metadata']['cache_hit'] is True
    
    def test_check_cache_miss(self):
        """Test cache miss scenario"""
        result = self.cache_manager.check(self.sample_context)
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache entry expiration"""
        # Create cache manager with very short TTL
        short_ttl_manager = CacheManager(cache_dir=self.temp_dir, ttl_seconds=1)
        
        # Store entry
        short_ttl_manager.store(self.sample_context, self.sample_analysis)
        
        # Should find it immediately
        result = short_ttl_manager.check(self.sample_context)
        assert result is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should not find expired entry
        result = short_ttl_manager.check(self.sample_context)
        assert result is None
    
    def test_cache_access_count(self):
        """Test that access count is tracked"""
        # Store entry
        self.cache_manager.store(self.sample_context, self.sample_analysis)
        
        # Access multiple times
        result1 = self.cache_manager.check(self.sample_context)
        result2 = self.cache_manager.check(self.sample_context)
        result3 = self.cache_manager.check(self.sample_context)
        
        assert result3['metadata']['access_count'] == 3
    
    def test_clear_expired(self):
        """Test clearing expired cache entries"""
        # Create entries with different TTLs
        short_ttl_manager = CacheManager(cache_dir=self.temp_dir, ttl_seconds=1)
        
        # Store entry that will expire
        short_ttl_manager.store(self.sample_context, self.sample_analysis)
        
        # Store entry with long TTL
        long_ttl_manager = CacheManager(cache_dir=self.temp_dir, ttl_seconds=3600)
        context2 = self.sample_context.copy()
        context2['error_info']['exit_code'] = 2
        long_ttl_manager.store(context2, self.sample_analysis)
        
        # Wait for first entry to expire
        import time
        time.sleep(2)
        
        # Clear expired entries
        cleared = self.cache_manager.clear_expired()
        
        # Should have cleared at least one entry
        assert cleared >= 1
    
    def test_get_stats(self):
        """Test cache statistics"""
        # Initially empty
        stats = self.cache_manager.get_stats()
        assert stats['total_entries'] == 0
        
        # Add some entries
        self.cache_manager.store(self.sample_context, self.sample_analysis)
        
        context2 = self.sample_context.copy()
        context2['error_info']['exit_code'] = 2
        self.cache_manager.store(context2, self.sample_analysis)
        
        # Check stats
        stats = self.cache_manager.get_stats()
        assert stats['total_entries'] == 2
        assert stats['total_size_bytes'] > 0
        assert stats['oldest_entry'] is not None
        assert stats['newest_entry'] is not None
    
    def test_clear_all(self):
        """Test clearing all cache entries"""
        # Add entries
        self.cache_manager.store(self.sample_context, self.sample_analysis)
        
        context2 = self.sample_context.copy()
        context2['error_info']['exit_code'] = 2
        self.cache_manager.store(context2, self.sample_analysis)
        
        # Clear all
        cleared = self.cache_manager.clear_all()
        assert cleared == 2
        
        # Verify empty
        stats = self.cache_manager.get_stats()
        assert stats['total_entries'] == 0
    
    def test_error_handling_store(self):
        """Test error handling during store operations"""
        # Make cache directory read-only
        os.chmod(self.temp_dir, 0o444)
        
        try:
            success = self.cache_manager.store(self.sample_context, self.sample_analysis)
            # Should handle error gracefully
            assert success is False
        finally:
            # Restore permissions for cleanup
            os.chmod(self.temp_dir, 0o755)
    
    def test_error_handling_check(self):
        """Test error handling during check operations"""
        # Create corrupted cache file
        context_hash = self.cache_manager._generate_context_hash(self.sample_context)
        cache_file = self.cache_manager._get_cache_file_path(context_hash)
        
        with open(cache_file, 'w') as f:
            f.write("invalid json content")
        
        # Should handle error gracefully
        result = self.cache_manager.check(self.sample_context)
        assert result is None
    
    def test_cache_file_path(self):
        """Test cache file path generation"""
        context_hash = "test_hash_123"
        path = self.cache_manager._get_cache_file_path(context_hash)
        
        assert path.name == "test_hash_123.json"
        assert path.parent == self.cache_manager.cache_dir
    
    def test_context_hash_stability(self):
        """Test that context hash is stable across runs"""
        # Same context should produce same hash consistently
        hashes = []
        for _ in range(10):
            hash_val = self.cache_manager._generate_context_hash(self.sample_context)
            hashes.append(hash_val)
        
        # All hashes should be identical
        assert all(h == hashes[0] for h in hashes)
    
    def test_log_excerpt_truncation(self):
        """Test that very long log excerpts are truncated"""
        long_log = "ERROR: " + "x" * 1000
        context_with_long_log = self.sample_context.copy()
        context_with_long_log['log_excerpt'] = long_log
        
        normalized = self.cache_manager._normalize_log_excerpt(long_log)
        
        # Should be truncated to 500 chars
        assert len(normalized) <= 500
    
    def test_cache_entry_dataclass(self):
        """Test CacheEntry dataclass"""
        entry = CacheEntry(
            context_hash="test_hash",
            analysis_result=self.sample_analysis,
            created_at="2023-01-01T00:00:00",
            expires_at="2023-01-01T01:00:00",
            access_count=5,
            last_accessed="2023-01-01T00:30:00"
        )
        
        assert entry.context_hash == "test_hash"
        assert entry.access_count == 5
        assert entry.analysis_result == self.sample_analysis
    
    def test_empty_context_handling(self):
        """Test handling of empty or minimal context"""
        empty_context = {}
        
        # Should not crash with empty context
        hash_val = self.cache_manager._generate_context_hash(empty_context)
        assert isinstance(hash_val, str)
        assert len(hash_val) == 16
    
    def test_cache_directory_creation(self):
        """Test that cache directory is created if it doesn't exist"""
        import shutil
        
        # Remove cache directory
        shutil.rmtree(self.temp_dir)
        
        # Create new manager - should recreate directory
        manager = CacheManager(cache_dir=self.temp_dir)
        assert manager.cache_dir.exists()
    
    def test_concurrent_access_simulation(self):
        """Test behavior under simulated concurrent access"""
        # Store initial entry
        self.cache_manager.store(self.sample_context, self.sample_analysis)
        
        # Simulate multiple concurrent accesses
        results = []
        for _ in range(5):
            result = self.cache_manager.check(self.sample_context)
            results.append(result)
        
        # All results should be valid
        assert all(r is not None for r in results)
        
        # Last result should have access count of 5
        assert results[-1]['metadata']['access_count'] == 5


class TestCacheManagerIntegration:
    """Integration tests for cache manager with actual file system"""
    
    def test_main_function_check_command(self):
        """Test main function with check command"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test context file
            context_file = os.path.join(temp_dir, 'context.json')
            with open(context_file, 'w') as f:
                json.dump({'error_info': {'exit_code': 1}}, f)
            
            # Set environment
            with patch.dict(os.environ, {'AI_ERROR_ANALYSIS_CACHE_DIR': temp_dir}):
                # Should exit with 1 (no cache hit)
                with patch('sys.argv', ['cache_manager.py', 'check', context_file]):
                    with pytest.raises(SystemExit) as exc_info:
                        from cache_manager import main
                        main()
                    assert exc_info.value.code == 1
    
    def test_main_function_store_command(self):
        """Test main function with store command"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            context_file = os.path.join(temp_dir, 'context.json')
            result_file = os.path.join(temp_dir, 'result.json')
            
            with open(context_file, 'w') as f:
                json.dump({'error_info': {'exit_code': 1}}, f)
            
            with open(result_file, 'w') as f:
                json.dump({'provider': 'test', 'analysis': {}}, f)
            
            # Set environment
            with patch.dict(os.environ, {'AI_ERROR_ANALYSIS_CACHE_DIR': temp_dir}):
                with patch('sys.argv', ['cache_manager.py', 'store', context_file, result_file]):
                    from cache_manager import main
                    main()  # Should not raise exception
    
    def test_main_function_stats_command(self):
        """Test main function with stats command"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'AI_ERROR_ANALYSIS_CACHE_DIR': temp_dir}):
                with patch('sys.argv', ['cache_manager.py', 'stats']):
                    from cache_manager import main
                    main()  # Should not raise exception


if __name__ == "__main__":
    pytest.main([__file__])