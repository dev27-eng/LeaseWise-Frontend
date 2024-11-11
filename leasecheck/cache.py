from flask_caching import Cache
from functools import wraps
import logging
import hashlib
from datetime import datetime

# Initialize cache
cache = Cache()

# Configure logging
logger = logging.getLogger(__name__)

# Cache version for invalidation
CACHE_VERSION = "v1"

def init_cache(app):
    """Initialize the caching system"""
    cache_config = {
        'CACHE_TYPE': 'simple',  # Use simple cache for development
        'CACHE_DEFAULT_TIMEOUT': 300,  # 5 minutes default timeout
        'CACHE_THRESHOLD': 1000,  # Maximum number of items the cache will store
        'CACHE_KEY_PREFIX': f'{CACHE_VERSION}_'  # Add version to cache keys
    }
    
    app.config.update(cache_config)
    cache.init_app(app)
    logger.info("Cache initialized successfully")

def clear_all_caches():
    """Clear all cached data"""
    try:
        cache.clear()
        logger.info("All caches cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing caches: {str(e)}")
        raise

def clear_cache_by_key(key):
    """Clear specific cache by key"""
    try:
        versioned_key = f"{CACHE_VERSION}_{key}"
        cache.delete(versioned_key)
        logger.info(f"Cache cleared for key: {key}")
    except Exception as e:
        logger.error(f"Error clearing cache for key {key}: {str(e)}")
        raise

def clear_cache_by_pattern(pattern):
    """Clear all caches matching a pattern"""
    try:
        keys = cache.cache._cache.keys()
        for key in keys:
            if pattern in str(key):
                cache.delete(key)
        logger.info(f"Caches cleared for pattern: {pattern}")
    except Exception as e:
        logger.error(f"Error clearing caches for pattern {pattern}: {str(e)}")
        raise

def cached_with_key(key_prefix, timeout=300):
    """Custom caching decorator with versioned keys"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = f"{key_prefix}_{hashlib.md5(str(args).encode() + str(kwargs).encode()).hexdigest()}"
            return cache.cached(timeout=timeout, key_prefix=cache_key)(f)(*args, **kwargs)
        return decorated_function
    return decorator

def clear_user_cache(user_email):
    """Clear all caches related to a specific user"""
    clear_cache_by_pattern(f'user_{user_email}')
    logger.info(f"User cache cleared for: {user_email}")

def clear_document_cache(document_id):
    """Clear all caches related to a specific document"""
    clear_cache_by_pattern(f'doc_{document_id}')
    logger.info(f"Document cache cleared for ID: {document_id}")

def clear_plan_cache():
    """Clear all plan-related caches"""
    clear_cache_by_pattern('plan_')
    logger.info("Plan cache cleared")

def clear_admin_cache():
    """Clear all admin-related caches"""
    clear_cache_by_pattern('admin_')
    logger.info("Admin cache cleared")

def get_cache_stats():
    """Get cache statistics"""
    try:
        total_keys = len(cache.cache._cache.keys())
        return {
            'total_keys': total_keys,
            'version': CACHE_VERSION,
            'last_cleared': datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return None
