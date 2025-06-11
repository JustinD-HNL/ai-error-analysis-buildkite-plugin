#!/usr/bin/env python3
"""
AI Error Analysis Buildkite Plugin - Cache Manager
Manages caching of AI analysis results to reduce API costs and improve performance
"""

import json
import os
import sys
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class CacheEntry:
    """Represents a cached analysis result"""
    context_hash: str
    analysis_result: Dict[str, Any]
    created_at: str
    expires_at: str
    access_count: int
    last_accessed: str


class CacheManager:
    """Manages caching of AI analysis results"""
    
    def __init__(self, cache_dir: Optional[str] = None, ttl_seconds: int = 3600):
        self.cache_dir = Path(cache_dir or os.environ.get('AI_ERROR_ANALYSIS_CACHE_DIR', '/tmp/ai-error-analysis-cache'))
        self.ttl_seconds = ttl_seconds
        self.ensure_cache_directory()
    
    def ensure_cache_directory(self):
        """Ensure cache directory exists"""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _generate_context_hash(self, context: Dict[str, Any]) -> str:
        """Generate a hash for the given context to use as cache key"""
        # Extract relevant parts for hashing (ignore timestamps and build-specific IDs)
        hashable_context = {
            'error_info': {
                'exit_code': context.get('error_info', {}).get('exit_code'),
                'error_category': context.get('error_info', {}).get('error_category'),
                'command': context.get('error_info', {}).get('command', '')[:100]  # First 100 chars
            },
            'log_excerpt': self._normalize_log_excerpt(context.get('log_excerpt', '')),
            'pipeline_info': {
                'pipeline': context.get('pipeline_info', {}).get('pipeline'),
                'step_key': context.get('pipeline_info', {}).get('step_key')
            }
        }
        
        # Convert to JSON string and hash
        context_json = json.dumps(hashable_context, sort_keys=True)
        return hashlib.sha256(context_json.encode('utf-8')).hexdigest()[:16]
    
    def _normalize_log_excerpt(self, log_excerpt: str) -> str:
        """Normalize log excerpt for consistent hashing"""
        if not log_excerpt:
            return ""
        
        # Remove timestamps, line numbers, and other variable content
        import re
        
        # Remove timestamps (various formats)
        normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', log_excerpt)
        normalized = re.sub(r'\d{2}:\d{2}:\d{2}', '[TIME]', normalized)
        
        # Remove line numbers
        normalized = re.sub(r'^\s*\d+[\s\|:]', '', normalized, flags=re.MULTILINE)
        
        # Remove absolute paths, keep relative structure
        normalized = re.sub(r'/[^\s]+/([^/\s]+)$', '[PATH]/\\1', normalized, flags=re.MULTILINE)
        
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized.strip())
        
        # Take first 500 chars for hashing (most relevant content)
        return normalized[:500]
    
    def _get_cache_file_path(self, context_hash: str) -> Path:
        """Get the cache file path for a given context hash"""
        return self.cache_dir / f"{context_hash}.json"
    
    def check(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check if a cached result exists for the given context"""
        try:
            context_hash = self._generate_context_hash(context)
            cache_file = self._get_cache_file_path(context_hash)
            
            if not cache_file.exists():
                return None
            
            # Load cache entry
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cache_entry = CacheEntry(**cache_data)
            
            # Check if cache entry has expired
            expires_at = datetime.fromisoformat(cache_entry.expires_at)
            if datetime.utcnow() > expires_at:
                # Remove expired cache entry
                cache_file.unlink()
                return None
            
            # Update access statistics
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.utcnow().isoformat()
            
            # Save updated statistics
            with open(cache_file, 'w') as f:
                json.dump(asdict(cache_entry), f, indent=2)
            
            # Mark result as cached
            result = cache_entry.analysis_result.copy()
            result['metadata']['cached'] = True
            result['metadata']['cache_hit'] = True
            result['metadata']['access_count'] = cache_entry.access_count
            
            return result
            
        except Exception as e:
            print(f"Error checking cache: {e}", file=sys.stderr)
            return None
    
    def store(self, context: Dict[str, Any], analysis_result: Dict[str, Any]) -> bool:
        """Store analysis result in cache"""
        try:
            context_hash = self._generate_context_hash(context)
            cache_file = self._get_cache_file_path(context_hash)
            
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=self.ttl_seconds)
            
            # Create cache entry
            cache_entry = CacheEntry(
                context_hash=context_hash,
                analysis_result=analysis_result,
                created_at=now.isoformat(),
                expires_at=expires_at.isoformat(),
                access_count=0,
                last_accessed=now.isoformat()
            )
            
            # Save to file
            with open(cache_file, 'w') as f:
                json.dump(asdict(cache_entry), f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error storing cache: {e}", file=sys.stderr)
            return False
    
    def clear_expired(self) -> int:
        """Clear expired cache entries"""
        cleared_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    expires_at = datetime.fromisoformat(cache_data['expires_at'])
                    if datetime.utcnow() > expires_at:
                        cache_file.unlink()
                        cleared_count += 1
                        
                except Exception:
                    # If we can't read the file, consider it corrupted and remove it
                    cache_file.unlink()
                    cleared_count += 1
                    
        except Exception as e:
            print(f"Error clearing expired cache: {e}", file=sys.stderr)
        
        return cleared_count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            'total_entries': 0,
            'expired_entries': 0,
            'total_size_bytes': 0,
            'oldest_entry': None,
            'newest_entry': None,
            'most_accessed': None,
            'cache_hit_rate': 0.0
        }
        
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            stats['total_entries'] = len(cache_files)
            
            if not cache_files:
                return stats
            
            entries = []
            total_access_count = 0
            
            for cache_file in cache_files:
                try:
                    with open(cache_file, 'r') as f:
                        cache_data = json.load(f)
                    
                    stats['total_size_bytes'] += cache_file.stat().st_size
                    
                    created_at = datetime.fromisoformat(cache_data['created_at'])
                    expires_at = datetime.fromisoformat(cache_data['expires_at'])
                    access_count = cache_data.get('access_count', 0)
                    
                    total_access_count += access_count
                    
                    if datetime.utcnow() > expires_at:
                        stats['expired_entries'] += 1
                    
                    entries.append({
                        'file': cache_file.name,
                        'created_at': created_at,
                        'access_count': access_count,
                        'data': cache_data
                    })
                    
                except Exception:
                    stats['expired_entries'] += 1
            
            if entries:
                # Find oldest and newest
                entries.sort(key=lambda x: x['created_at'])
                stats['oldest_entry'] = entries[0]['file']
                stats['newest_entry'] = entries[-1]['file']
                
                # Find most accessed
                entries.sort(key=lambda x: x['access_count'], reverse=True)
                stats['most_accessed'] = {
                    'file': entries[0]['file'],
                    'access_count': entries[0]['access_count']
                }
                
                # Calculate hit rate (rough estimate)
                if total_access_count > 0:
                    stats['cache_hit_rate'] = min(1.0, total_access_count / len(entries))
                    
        except Exception as e:
            print(f"Error getting cache stats: {e}", file=sys.stderr)
        
        return stats
    
    def clear_all(self) -> int:
        """Clear all cache entries"""
        cleared_count = 0
        
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
                cleared_count += 1
                
        except Exception as e:
            print(f"Error clearing cache: {e}", file=sys.stderr)
        
        return cleared_count


def main():
    """Main entry point for cache management operations"""
    if len(sys.argv) < 2:
        print("Usage: cache_manager.py <command> [args]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  check <context_file>              - Check for cached result", file=sys.stderr)
        print("  store <context_file> <result_file> - Store result in cache", file=sys.stderr)
        print("  stats                             - Show cache statistics", file=sys.stderr)
        print("  clear                             - Clear expired entries", file=sys.stderr)
        print("  clear-all                         - Clear all entries", file=sys.stderr)
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Initialize cache manager
    cache_ttl = int(os.environ.get('BUILDKITE_PLUGIN_AI_ERROR_ANALYSIS_PERFORMANCE_CACHE_TTL', '3600'))
    cache_manager = CacheManager(ttl_seconds=cache_ttl)
    
    try:
        if command == "check":
            if len(sys.argv) != 3:
                print("Usage: cache_manager.py check <context_file>", file=sys.stderr)
                sys.exit(1)
            
            context_file = sys.argv[2]
            with open(context_file, 'r') as f:
                context = json.load(f)
            
            result = cache_manager.check(context)
            if result:
                print(json.dumps(result, indent=2))
            else:
                sys.exit(1)  # No cache hit
        
        elif command == "store":
            if len(sys.argv) != 4:
                print("Usage: cache_manager.py store <context_file> <result_file>", file=sys.stderr)
                sys.exit(1)
            
            context_file = sys.argv[2]
            result_file = sys.argv[3]
            
            with open(context_file, 'r') as f:
                context = json.load(f)
            
            with open(result_file, 'r') as f:
                result = json.load(f)
            
            if cache_manager.store(context, result):
                print("Result stored in cache successfully")
            else:
                print("Failed to store result in cache", file=sys.stderr)
                sys.exit(1)
        
        elif command == "stats":
            stats = cache_manager.get_stats()
            print(json.dumps(stats, indent=2, default=str))
        
        elif command == "clear":
            cleared = cache_manager.clear_expired()
            print(f"Cleared {cleared} expired cache entries")
        
        elif command == "clear-all":
            cleared = cache_manager.clear_all()
            print(f"Cleared {cleared} cache entries")
        
        else:
            print(f"Unknown command: {command}", file=sys.stderr)
            sys.exit(1)
            
    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()