"""
Cache Utility

Provides centralized caching functions and cache key generators.
Uses Flask-Caching with Redis backend for distributed caching.
"""

from functools import wraps
from flask import request
from flask_caching import Cache
import json
import hashlib

# Cache instance (initialized in app/__init__.py)
cache = None


def init_cache(app):
    """
    Initialize cache with app configuration
    
    Args:
        app: Flask application instance
    """
    global cache
    
    config = {
        'CACHE_TYPE': app.config.get('CACHE_TYPE', 'SimpleCache'),
        'CACHE_DEFAULT_TIMEOUT': app.config.get('CACHE_DEFAULT_TIMEOUT', 300),
    }
    
    # Redis-specific configuration
    if config['CACHE_TYPE'] == 'redis':
        redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379/0')
        config['CACHE_KEY_PREFIX'] = app.config.get('CACHE_KEY_PREFIX', 'dogmatch:')
        
        # Create a custom Redis connection following Redis Labs official example
        from urllib.parse import urlparse
        import redis
        
        parsed = urlparse(redis_url)
        # Flask-Caching needs a Redis connection object, not just a URL
        try:
            # Extract connection details from URL
            host = parsed.hostname
            port = parsed.port or 6379
            password = parsed.password
            username = parsed.username or 'default'
            db = int(parsed.path.lstrip('/')) if parsed.path else 0
            is_ssl = parsed.scheme == 'rediss'
            
            # Create Redis connection with proper SSL configuration for Redis Labs
            if is_ssl:
                # For Redis Labs with SSL, try using from_url first
                try:
                    redis_connection = redis.from_url(
                        redis_url,
                        decode_responses=False,
                        socket_connect_timeout=10,
                        socket_timeout=10,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        ssl_cert_reqs=None,  # Disable certificate verification
                        ssl_check_hostname=False
                    )
                except Exception:
                    # Fallback to manual configuration
                    redis_connection = redis.Redis(
                        host=host,
                        port=port,
                        username=username,
                        password=password,
                        db=db,
                        decode_responses=False,  # Keep as False for compatibility
                        socket_connect_timeout=10,
                        socket_timeout=10,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        ssl=True,
                        ssl_cert_reqs=None,  # Use None instead of ssl.CERT_NONE
                        ssl_ca_certs=None,
                        ssl_check_hostname=False
                    )
            else:
                redis_connection = redis.Redis(
                    host=host,
                    port=port,
                    username=username,
                    password=password,
                    db=db,
                    decode_responses=False,  # Keep as False for compatibility
                    socket_connect_timeout=10,
                    socket_timeout=10,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
            # Test the connection
            redis_connection.ping()
            app.logger.info(f"✅ Redis cache connection successful to {host}:{port} (SSL: {is_ssl})")
            
            # Pass the Redis connection object to Flask-Caching
            config['CACHE_REDIS'] = redis_connection
        except Exception as e:
            app.logger.error(f"❌ Redis cache connection failed: {str(e)}")
            app.logger.error(f"   Host: {parsed.hostname}, Port: {parsed.port}")
            raise
    
    # Initialize cache with error handling
    try:
        cache = Cache(app, config=config)
        # Connection was already tested when creating the Redis connection object
        return cache
    except Exception as e:
        app.logger.error(f"Cache initialization failed: {str(e)}")
        app.logger.warning("Falling back to SimpleCache (in-memory)")
        # Fallback to SimpleCache
        config['CACHE_TYPE'] = 'SimpleCache'
        # Remove Redis-specific config
        if 'CACHE_REDIS' in config:
            del config['CACHE_REDIS']
        cache = Cache(app, config=config)
        return cache


# ==================== Cache Key Generators ====================

def make_cache_key_with_args(*args, **kwargs):
    """
    Generate cache key from function arguments
    
    Args:
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        str: Generated cache key
    """
    # Combine args and kwargs into string
    key_data = {
        'args': args,
        'kwargs': kwargs
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    
    # Hash for shorter keys
    return hashlib.md5(key_str.encode()).hexdigest()


def make_user_cache_key(user_id):
    """Generate cache key for user profile"""
    return f'user:{user_id}'


def make_dog_cache_key(dog_id):
    """Generate cache key for dog profile"""
    return f'dog:{dog_id}'


def make_dog_list_cache_key(owner_id):
    """Generate cache key for user's dog list"""
    return f'user:{owner_id}:dogs'


def make_match_cache_key(dog_id, status=None):
    """Generate cache key for match list"""
    if status:
        return f'dog:{dog_id}:matches:{status}'
    return f'dog:{dog_id}:matches'


def make_event_cache_key(event_id):
    """Generate cache key for event"""
    return f'event:{event_id}'


def make_event_list_cache_key(status='published', limit=20, offset=0):
    """Generate cache key for event list"""
    return f'events:status:{status}:limit:{limit}:offset:{offset}'


def make_message_cache_key(match_id, limit=100, offset=0):
    """Generate cache key for message list"""
    return f'match:{match_id}:messages:limit:{limit}:offset:{offset}'


def make_available_dogs_cache_key(limit=20, offset=0, filters=None):
    """Generate cache key for available dogs list"""
    filter_str = json.dumps(filters, sort_keys=True) if filters else 'none'
    filter_hash = hashlib.md5(filter_str.encode()).hexdigest()[:8]
    return f'dogs:available:filters:{filter_hash}:limit:{limit}:offset:{offset}'


# ==================== Cache Invalidation Helpers ====================

def invalidate_user_cache(user_id):
    """Invalidate all caches related to a user"""
    cache.delete(make_user_cache_key(user_id))
    cache.delete(make_dog_list_cache_key(user_id))


def invalidate_dog_cache(dog_id, owner_id=None):
    """Invalidate all caches related to a dog"""
    cache.delete(make_dog_cache_key(dog_id))
    
    if owner_id:
        cache.delete(make_dog_list_cache_key(owner_id))
    
    # Invalidate match caches
    cache.delete(make_match_cache_key(dog_id))
    cache.delete(make_match_cache_key(dog_id, 'matched'))
    cache.delete(make_match_cache_key(dog_id, 'pending'))
    
    # Invalidate available dogs list (since availability might change)
    invalidate_available_dogs_cache()


def invalidate_match_cache(dog_one_id, dog_two_id):
    """Invalidate match caches for both dogs"""
    for dog_id in [dog_one_id, dog_two_id]:
        cache.delete(make_match_cache_key(dog_id))
        cache.delete(make_match_cache_key(dog_id, 'matched'))
        cache.delete(make_match_cache_key(dog_id, 'pending'))


def invalidate_event_cache(event_id):
    """Invalidate event cache"""
    cache.delete(make_event_cache_key(event_id))
    # Invalidate event lists
    invalidate_event_list_cache()


def invalidate_event_list_cache():
    """Invalidate all event list caches"""
    # Delete common event list cache keys
    for status in ['published', 'draft', 'cancelled', 'completed']:
        for offset in range(0, 100, 20):  # Clear first 5 pages
            cache.delete(make_event_list_cache_key(status, limit=20, offset=offset))


def invalidate_message_cache(match_id):
    """Invalidate message cache for a match"""
    # Clear common pagination offsets
    for offset in range(0, 500, 100):
        cache.delete(make_message_cache_key(match_id, limit=100, offset=offset))


def invalidate_available_dogs_cache():
    """Invalidate available dogs cache (called when dogs change)"""
    # Delete pattern would be better, but not available in SimpleCache
    # For Redis, you could use cache.delete_many() with pattern matching
    pass


# ==================== Caching Decorators ====================

def cached_response(timeout=300, key_prefix=None, unless=None):
    """
    Decorator to cache route responses
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Function to generate cache key or string prefix
        unless: Function that returns True to skip caching
        
    Usage:
        @cached_response(timeout=600, key_prefix='my_route')
        def my_route():
            return expensive_operation()
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if we should skip caching
            if unless and unless():
                return f(*args, **kwargs)
            
            # Generate cache key
            if callable(key_prefix):
                cache_key = key_prefix(*args, **kwargs)
            elif key_prefix:
                cache_key = f"{key_prefix}:{make_cache_key_with_args(*args, **kwargs)}"
            else:
                cache_key = f"{f.__name__}:{make_cache_key_with_args(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result
        
        return decorated_function
    return decorator


def cache_result(timeout=300, key_generator=None):
    """
    Decorator to cache function results (for service/repository methods)
    
    Args:
        timeout: Cache timeout in seconds
        key_generator: Function to generate cache key from args
        
    Usage:
        @cache_result(timeout=600, key_generator=lambda dog_id: f'dog:{dog_id}')
        def get_dog_by_id(dog_id):
            return Dog.query.get(dog_id)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Generate cache key
            if key_generator:
                if callable(key_generator):
                    cache_key = key_generator(*args, **kwargs)
                else:
                    cache_key = str(key_generator)
            else:
                cache_key = f"{f.__module__}.{f.__name__}:{make_cache_key_with_args(*args, **kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            if result is not None:  # Don't cache None results
                cache.set(cache_key, result, timeout=timeout)
            return result
        
        return decorated_function
    return decorator


# ==================== Cache Statistics ====================

def get_cache_stats():
    """
    Get cache statistics (if available)
    
    Returns:
        dict: Cache statistics
    """
    stats = {
        'type': cache.config.get('CACHE_TYPE', 'unknown'),
        'default_timeout': cache.config.get('CACHE_DEFAULT_TIMEOUT', 0),
    }
    
    # Redis-specific stats
    if stats['type'] == 'redis':
        try:
            redis_client = cache.cache._write_client
            info = redis_client.info('stats')
            stats['redis'] = {
                'total_connections': info.get('total_connections_received', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'used_memory_human': redis_client.info('memory').get('used_memory_human', 'unknown'),
            }
            
            # Calculate hit rate
            hits = stats['redis']['keyspace_hits']
            misses = stats['redis']['keyspace_misses']
            total = hits + misses
            stats['redis']['hit_rate'] = f"{(hits / total * 100):.2f}%" if total > 0 else "0%"
        except Exception as e:
            stats['redis_error'] = str(e)
    
    return stats


def clear_all_cache():
    """Clear all cache entries (use with caution!)"""
    cache.clear()


# ==================== Utility Functions ====================

def get_or_set_cache(key, callable_func, timeout=300):
    """
    Get value from cache or execute function and cache result
    
    Args:
        key: Cache key
        callable_func: Function to execute if cache miss
        timeout: Cache timeout in seconds
        
    Returns:
        Cached or computed value
    """
    cached_value = cache.get(key)
    if cached_value is not None:
        return cached_value
    
    result = callable_func()
    if result is not None:
        cache.set(key, result, timeout=timeout)
    return result


def cache_many(key_value_dict, timeout=300):
    """
    Cache multiple key-value pairs at once
    
    Args:
        key_value_dict: Dictionary of cache keys and values
        timeout: Cache timeout in seconds
    """
    for key, value in key_value_dict.items():
        cache.set(key, value, timeout=timeout)


def get_many(keys):
    """
    Get multiple cache values at once
    
    Args:
        keys: List of cache keys
        
    Returns:
        dict: Dictionary of cache keys and values (None if not found)
    """
    return {key: cache.get(key) for key in keys}


def delete_many(keys):
    """
    Delete multiple cache entries at once
    
    Args:
        keys: List of cache keys
    """
    for key in keys:
        cache.delete(key)
