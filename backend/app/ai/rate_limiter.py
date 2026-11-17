"""
DietSense — In-Memory Rate Limiter & Response Cache
Provides token-bucket rate limiting per user and global RPM, along with
SHA-256 hashed response caching to reduce redundant Gemini API calls.
"""

import time
import hashlib
import json
import threading
from typing import Dict, Any, Optional, Tuple


class RateLimiter:
    """Thread-safe sliding window rate limiter."""

    def __init__(self, max_requests: int = 60, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list[float]] = {}
        self.lock = threading.Lock()

    def is_allowed(self, key: str) -> Tuple[bool, float]:
        """
        Checks if key is within rate limit.
        Returns (is_allowed, seconds_to_wait).
        """
        now = time.time()
        with self.lock:
            user_reqs = self.requests.get(key, [])
            # Filter out timestamps outside current sliding window
            user_reqs = [t for t in user_reqs if now - t < self.window_seconds]
            if len(user_reqs) >= self.max_requests:
                oldest = user_reqs[0]
                wait_time = max(0.0, self.window_seconds - (now - oldest))
                self.requests[key] = user_reqs
                return False, wait_time

            user_reqs.append(now)
            self.requests[key] = user_reqs
            return True, 0.0


class ResponseCache:
    """Thread-safe in-memory cache with TTL eviction."""

    def __init__(self, ttl_seconds: float = 86400.0):  # Default 24 hours
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[float, Any]] = {}
        self.lock = threading.Lock()

    @staticmethod
    def generate_key(prefix: str, data: Dict[str, Any]) -> str:
        """Computes a deterministic SHA-256 key from prefix and sorted data."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return f"{prefix}:{digest}"

    def get(self, key: str) -> Optional[Any]:
        """Returns cached item if present and unexpired, else None."""
        now = time.time()
        with self.lock:
            entry = self.cache.get(key)
            if not entry:
                return None
            timestamp, value = entry
            if now - timestamp > self.ttl_seconds:
                del self.cache[key]
                return None
            return value

    def set(self, key: str, value: Any) -> None:
        """Stores item with current timestamp."""
        now = time.time()
        with self.lock:
            self.cache[key] = (now, value)

    def clear(self) -> None:
        """Clears all cached items."""
        with self.lock:
            self.cache.clear()


# Global singletons
global_rate_limiter = RateLimiter(max_requests=60, window_seconds=60.0)
user_rate_limiter = RateLimiter(max_requests=30, window_seconds=60.0)
ai_response_cache = ResponseCache(ttl_seconds=86400.0)
