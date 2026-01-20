"""
Caching Service
Advanced caching system with LRU and TTL support
"""

import threading
import time
from collections import OrderedDict as PyOrderedDict
from typing import Any


class CachingService:
    """Caching service with LRU and TTL eviction policies"""

    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: PyOrderedDict[str, tuple[Any, float]] = PyOrderedDict()
        self.lock = threading.RLock()

        # Start cleanup thread
        self.running = True
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def get(self, key: str) -> Any | None:
        """Get value from cache"""
        with self.lock:
            if key not in self.cache:
                return None

            value, expiry = self.cache[key]

            # Check expiration
            if time.time() > expiry:
                del self.cache[key]
                return None

            # Move to end (LRU)
            self.cache.move_to_end(key)
            return value

    def set(self, key: str, value: Any, ttl: int | None = None):
        """Set value in cache"""
        ttl = ttl if ttl is not None else self.default_ttl
        expiry = time.time() + ttl

        with self.lock:
            # Evict if full
            if len(self.cache) >= self.max_size and key not in self.cache:
                self.cache.popitem(last=False)

            self.cache[key] = (value, expiry)
            self.cache.move_to_end(key)

    def invalidate(self, key: str):
        """Invalidate a key"""
        with self.lock:
            if key in self.cache:
                del self.cache[key]

    def clear(self):
        """Clear all cache"""
        with self.lock:
            self.cache.clear()

    def _cleanup_loop(self):
        """Periodically remove expired items"""
        while self.running:
            time.sleep(60)  # Check every minute
            self._cleanup_expired()

    def _cleanup_expired(self):
        """Remove expired items"""
        now = time.time()
        with self.lock:
            keys_to_remove = [k for k, (_, exp) in self.cache.items() if now > exp]
            for k in keys_to_remove:
                del self.cache[k]

    def stop(self):
        """Stop the cleanup thread"""
        self.running = False
