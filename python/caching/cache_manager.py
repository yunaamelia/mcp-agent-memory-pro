"""
Advanced Cache Manager
Multi-level caching with intelligent strategies
"""

import hashlib
import json
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

try:
    from diskcache import Cache
except ImportError:
    Cache = None

try:
    from cachetools import LRUCache, TTLCache
except ImportError:
    # Fallback to simple dict-based caches
    class LRUCache(dict):
        def __init__(self, maxsize=1000):
            super().__init__()
            self.maxsize = maxsize

    class TTLCache(dict):
        def __init__(self, maxsize=500, ttl=300):
            super().__init__()
            self.maxsize = maxsize
            self.ttl = ttl


try:
    import redis
except ImportError:
    redis = None


class CacheManager:
    """Multi-level cache manager"""

    def __init__(self, cache_dir: str, use_redis: bool = False):
        # Level 1: In-memory LRU cache (fastest)
        self.memory_cache = LRUCache(maxsize=1000)

        # Level 2: In-memory TTL cache (time-based)
        self.ttl_cache = TTLCache(maxsize=500, ttl=300)  # 5 minutes

        # Level 3: Disk cache (persistent)
        if Cache:
            self.disk_cache = Cache(cache_dir)
        else:
            self.disk_cache = {}
            self._disk_cache_dir = Path(cache_dir)
            self._disk_cache_dir.mkdir(parents=True, exist_ok=True)

        # Level 4: Redis cache (optional, for distributed systems)
        self.redis_cache = None
        if use_redis and redis:
            try:
                self.redis_cache = redis.Redis(host="localhost", port=6379, db=0)
                self.redis_cache.ping()
            except Exception:
                print("Redis not available, using local caches only")

    def get(self, key: str, level: str = "auto") -> Any | None:
        """
        Get value from cache

        Args:
            key: Cache key
            level: Cache level ('memory', 'ttl', 'disk', 'redis', 'auto')

        Returns:
            Cached value or None
        """

        if level == "auto":
            # Try each level in order
            value = self._get_from_memory(key)
            if value is not None:
                return value

            value = self._get_from_disk(key)
            if value is not None:
                # Promote to memory cache
                self.memory_cache[key] = value
                return value

            if self.redis_cache:
                value = self._get_from_redis(key)
                if value is not None:
                    # Promote to memory and disk
                    self.memory_cache[key] = value
                    self._set_disk(key, value)
                    return value

            return None

        elif level == "memory":
            return self._get_from_memory(key)
        elif level == "ttl":
            return self.ttl_cache.get(key)
        elif level == "disk":
            return self._get_from_disk(key)
        elif level == "redis":
            return self._get_from_redis(key)

        return None

    def set(self, key: str, value: Any, ttl: int | None = None, levels: list[str] | None = None):
        """
        Set value in cache

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            levels: Which cache levels to use
        """
        if levels is None:
            levels = ["memory", "disk"]

        if "memory" in levels:
            self.memory_cache[key] = value

        if "ttl" in levels and ttl:
            self.ttl_cache[key] = value

        if "disk" in levels:
            self._set_disk(key, value, ttl)

        if "redis" in levels and self.redis_cache:
            serialized = json.dumps(value, default=str)
            if ttl:
                self.redis_cache.setex(key, ttl, serialized)
            else:
                self.redis_cache.set(key, serialized)

    def _set_disk(self, key: str, value: Any, ttl: int | None = None):
        """Set value in disk cache"""
        if Cache and isinstance(self.disk_cache, Cache):
            if ttl:
                self.disk_cache.set(key, value, expire=ttl)
            else:
                self.disk_cache[key] = value
        else:
            self.disk_cache[key] = value

    def delete(self, key: str):
        """Delete from all cache levels"""

        if key in self.memory_cache:
            del self.memory_cache[key]

        if key in self.ttl_cache:
            del self.ttl_cache[key]

        if Cache and isinstance(self.disk_cache, Cache):
            if key in self.disk_cache:
                del self.disk_cache[key]
        elif key in self.disk_cache:
            del self.disk_cache[key]

        if self.redis_cache:
            self.redis_cache.delete(key)

    def clear(self, level: str = "all"):
        """Clear cache"""

        if level in ["all", "memory"]:
            self.memory_cache.clear()
            self.ttl_cache.clear()

        if level in ["all", "disk"]:
            if Cache and isinstance(self.disk_cache, Cache):
                self.disk_cache.clear()
            else:
                self.disk_cache.clear()

        if level in ["all", "redis"] and self.redis_cache:
            self.redis_cache.flushdb()

    def _get_from_memory(self, key: str) -> Any | None:
        """Get from memory cache"""
        value = self.memory_cache.get(key)
        if value is None:
            value = self.ttl_cache.get(key)
        return value

    def _get_from_disk(self, key: str) -> Any | None:
        """Get from disk cache"""
        if Cache and isinstance(self.disk_cache, Cache):
            return self.disk_cache.get(key)
        return self.disk_cache.get(key)

    def _get_from_redis(self, key: str) -> Any | None:
        """Get from Redis cache"""
        if not self.redis_cache:
            return None

        value = self.redis_cache.get(key)
        if value:
            return json.loads(value)
        return None

    def cached(self, ttl: int | None = None, key_prefix: str = "", levels: list[str] | None = None):
        """
        Decorator for caching function results

        Usage:
            @cache_manager.cached(ttl=300, key_prefix='search_')
            def search_memories(query):
                # expensive operation
                return results
        """
        if levels is None:
            levels = ["memory", "disk"]

        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key from function name and arguments
                key_parts = [key_prefix, func.__name__]
                key_parts.extend(str(arg) for arg in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

                cache_key = hashlib.md5("_".join(key_parts).encode()).hexdigest()

                # Try to get from cache
                cached_value = self.get(cache_key)
                if cached_value is not None:
                    return cached_value

                # Compute value
                result = func(*args, **kwargs)

                # Store in cache
                self.set(cache_key, result, ttl=ttl, levels=levels)

                return result

            return wrapper

        return decorator

    def get_stats(self) -> dict:
        """Get cache statistics"""

        stats = {
            "memory_size": len(self.memory_cache),
            "memory_maxsize": getattr(self.memory_cache, "maxsize", 1000),
            "ttl_size": len(self.ttl_cache),
            "disk_size": len(self.disk_cache) if isinstance(self.disk_cache, dict) else 0,
        }

        if Cache and isinstance(self.disk_cache, Cache):
            stats["disk_size"] = len(self.disk_cache)

        if self.redis_cache:
            try:
                info = self.redis_cache.info()
                stats["redis_keys"] = info.get("db0", {}).get("keys", 0)
                stats["redis_memory_mb"] = info.get("used_memory", 0) / (1024 * 1024)
            except Exception:
                stats["redis_keys"] = 0
                stats["redis_memory_mb"] = 0

        return stats
