#!/usr/bin/env python3
"""
Advanced Caching System for Daily Cash Usage API
==============================================

This module implements a sophisticated caching system with:
1. Different cache durations for different endpoint types
2. ETag support for conditional requests  
3. Cache invalidation strategies
4. Performance monitoring

Cache Strategy:
- Daily summaries: 6 hours cache
- Trends data: 1 hour cache
- Terminal history: 30 minutes cache
- Cash usage summary: 15 minutes cache
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import logging

# Configure logging
logger = logging.getLogger(__name__)

class CacheConfig:
    """Cache configuration for different endpoint types"""
    
    # Cache durations in seconds
    CACHE_DURATIONS = {
        'daily_summaries': 21600,    # 6 hours
        'trends': 3600,              # 1 hour  
        'terminal_history': 1800,    # 30 minutes
        'cash_summary': 900,         # 15 minutes
        'default': 300               # 5 minutes
    }
    
    # Cache key prefixes
    CACHE_PREFIXES = {
        'daily_cash': 'daily_cash',
        'trends': 'trends',
        'summary': 'summary',
        'terminal_history': 'term_hist',
        'terminal_list': 'term_list'
    }

class AdvancedCache:
    """Advanced caching system with ETag support and performance monitoring"""
    
    def __init__(self):
        self.cache_store: Dict[str, Dict[str, Any]] = {}
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'invalidations': 0,
            'total_requests': 0
        }
        
    def generate_cache_key(self, endpoint: str, params: dict) -> str:
        """Generate a unique cache key for endpoint and parameters"""
        # Sort parameters for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        cache_string = f"{endpoint}:{sorted_params}"
        return hashlib.sha256(cache_string.encode()).hexdigest()[:16]
    
    def generate_etag(self, data: Any) -> str:
        """Generate ETag from response data"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(data_string.encode()).hexdigest()
    
    def get_cache_duration(self, cache_type: str) -> int:
        """Get cache duration for specific cache type"""
        return CacheConfig.CACHE_DURATIONS.get(cache_type, CacheConfig.CACHE_DURATIONS['default'])
    
    def is_cache_valid(self, cache_entry: dict, cache_type: str = 'default') -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry or 'timestamp' not in cache_entry:
            return False
        
        cache_duration = self.get_cache_duration(cache_type)
        age = (datetime.utcnow() - cache_entry['timestamp']).total_seconds()
        return age < cache_duration
    
    def get_cached_response(self, cache_key: str, cache_type: str = 'default') -> Optional[dict]:
        """Get cached response if valid"""
        self.cache_stats['total_requests'] += 1
        
        if cache_key in self.cache_store:
            cache_entry = self.cache_store[cache_key]
            if self.is_cache_valid(cache_entry, cache_type):
                self.cache_stats['hits'] += 1
                logger.debug(f"Cache HIT for key: {cache_key}")
                return cache_entry
            else:
                # Remove expired entry
                del self.cache_store[cache_key]
                logger.debug(f"Cache EXPIRED for key: {cache_key}")
        
        self.cache_stats['misses'] += 1
        logger.debug(f"Cache MISS for key: {cache_key}")
        return None
    
    def set_cached_response(self, cache_key: str, data: Any, cache_type: str = 'default') -> str:
        """Cache response data and return ETag"""
        etag = self.generate_etag(data)
        
        cache_entry = {
            'data': data,
            'etag': etag,
            'timestamp': datetime.utcnow(),
            'cache_type': cache_type
        }
        
        self.cache_store[cache_key] = cache_entry
        logger.debug(f"Cache SET for key: {cache_key}, type: {cache_type}")
        return etag
    
    def check_etag(self, request: Request, etag: str) -> bool:
        """Check if client's ETag matches current ETag"""
        client_etag = request.headers.get('If-None-Match')
        return client_etag == f'"{etag}"'
    
    def invalidate_cache_pattern(self, pattern: str):
        """Invalidate all cache entries matching pattern"""
        keys_to_remove = [key for key in self.cache_store.keys() if pattern in key]
        for key in keys_to_remove:
            del self.cache_store[key]
            self.cache_stats['invalidations'] += 1
        
        logger.info(f"Invalidated {len(keys_to_remove)} cache entries for pattern: {pattern}")
    
    def get_cache_stats(self) -> dict:
        """Get cache performance statistics"""
        total_requests = self.cache_stats['total_requests']
        if total_requests == 0:
            hit_rate = 0
        else:
            hit_rate = (self.cache_stats['hits'] / total_requests) * 100
        
        return {
            'total_requests': total_requests,
            'cache_hits': self.cache_stats['hits'],
            'cache_misses': self.cache_stats['misses'],
            'hit_rate_percent': round(hit_rate, 2),
            'invalidations': self.cache_stats['invalidations'],
            'cached_entries': len(self.cache_store)
        }
    
    def cleanup_expired_entries(self):
        """Remove all expired cache entries"""
        current_time = datetime.utcnow()
        expired_keys = []
        
        for key, entry in self.cache_store.items():
            cache_type = entry.get('cache_type', 'default')
            cache_duration = self.get_cache_duration(cache_type)
            age = (current_time - entry['timestamp']).total_seconds()
            
            if age >= cache_duration:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache_store[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")

# Global cache instance
advanced_cache = AdvancedCache()

def cached_response(cache_type: str = 'default', cache_prefix: str = ''):
    """Decorator for caching API responses with ETag support"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            # Generate cache key from function name and parameters
            cache_params = {
                'args': str(args),
                'kwargs': {k: str(v) for k, v in kwargs.items() if k != 'request'}
            }
            
            cache_key = advanced_cache.generate_cache_key(
                f"{cache_prefix}_{func.__name__}", 
                cache_params
            )
            
            # Check for cached response
            cached_data = advanced_cache.get_cached_response(cache_key, cache_type)
            
            if cached_data:
                etag = cached_data['etag']
                
                # Check if client has current version (ETag match)
                if advanced_cache.check_etag(request, etag):
                    return Response(status_code=304)  # Not Modified
                
                # Return cached data with ETag header
                response = JSONResponse(cached_data['data'])
                response.headers['ETag'] = f'"{etag}"'
                response.headers['X-Cache'] = 'HIT'
                response.headers['Cache-Control'] = f'max-age={advanced_cache.get_cache_duration(cache_type)}'
                return response
            
            # Execute original function
            result = await func(request, *args, **kwargs)
            
            # Cache the result if it's successful
            if hasattr(result, 'status_code') and result.status_code == 200:
                if hasattr(result, 'body'):
                    try:
                        # For JSONResponse objects
                        data = json.loads(result.body.decode())
                        etag = advanced_cache.set_cached_response(cache_key, data, cache_type)
                        
                        # Add cache headers to response
                        result.headers['ETag'] = f'"{etag}"'
                        result.headers['X-Cache'] = 'MISS'
                        result.headers['Cache-Control'] = f'max-age={advanced_cache.get_cache_duration(cache_type)}'
                        
                    except (json.JSONDecodeError, AttributeError):
                        logger.warning(f"Could not cache response for {func.__name__}")
            
            return result
        
        return wrapper
    return decorator

def create_optimized_cache_response(data: Any, cache_type: str, cache_key: str) -> JSONResponse:
    """Create optimized JSON response with caching headers"""
    etag = advanced_cache.generate_etag(data)
    cache_duration = advanced_cache.get_cache_duration(cache_type)
    
    response = JSONResponse(data)
    response.headers['ETag'] = f'"{etag}"'
    response.headers['Cache-Control'] = f'max-age={cache_duration}, public'
    response.headers['X-Cache-Type'] = cache_type
    response.headers['X-Cache-Duration'] = str(cache_duration)
    
    return response

# Cache management endpoints
async def get_cache_statistics():
    """Get cache performance statistics"""
    stats = advanced_cache.get_cache_stats()
    return {
        'cache_performance': stats,
        'cache_config': {
            'durations': CacheConfig.CACHE_DURATIONS,
            'prefixes': CacheConfig.CACHE_PREFIXES
        }
    }

async def clear_cache(pattern: Optional[str] = None):
    """Clear cache entries (optionally by pattern)"""
    if pattern:
        advanced_cache.invalidate_cache_pattern(pattern)
        return {'message': f'Cache cleared for pattern: {pattern}'}
    else:
        advanced_cache.cache_store.clear()
        advanced_cache.cache_stats = {'hits': 0, 'misses': 0, 'invalidations': 0, 'total_requests': 0}
        return {'message': 'All cache cleared'}

# Background task for cache cleanup
import asyncio

async def cache_cleanup_task():
    """Background task to clean up expired cache entries"""
    while True:
        try:
            advanced_cache.cleanup_expired_entries()
            await asyncio.sleep(3600)  # Run every hour
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            await asyncio.sleep(300)  # Retry in 5 minutes on error
