"""Cache service for EtherScope."""

import time
from typing import Any, Dict, Optional

from core.config import Config
from core.exceptions import CacheServiceError
from core.logger import get_logger

logger = get_logger(__name__)


class CacheEntry:
    """Represents a cached entry with TTL."""

    def __init__(self, value: Any, ttl: int):
        """Initialize cache entry.

        Args:
            value: Cached value
            ttl: Time-to-live in seconds

        """
        self.value = value
        self.ttl = ttl
        self.created_at = time.time()

    def is_expired(self) -> bool:
        """Check if entry has expired.

        Returns:
            True if entry has expired

        """
        elapsed = time.time() - self.created_at
        return elapsed > self.ttl


class CacheService:
    """In-memory cache service for wallet analysis results."""

    def __init__(
        self, enabled: bool = True, ttl: int = 300, max_size: int = 1000
    ):
        """Initialize cache service.

        Args:
            enabled: Whether caching is enabled
            ttl: Default time-to-live in seconds
            max_size: Maximum number of cached entries

        """
        self.enabled = enabled
        self.ttl = ttl
        self.max_size = max_size
        self._cache: Dict[str, CacheEntry] = {}
        logger.info(
            f"CacheService initialized: enabled={enabled}, ttl={ttl}s, max_size={max_size}"
        )

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired

        """
        if not self.enabled:
            return None

        if key not in self._cache:
            logger.debug(f"Cache miss: {key}")
            return None

        entry = self._cache[key]

        if entry.is_expired():
            logger.debug(f"Cache expired: {key}")
            del self._cache[key]
            return None

        logger.debug(f"Cache hit: {key}")
        return entry.value

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if not provided)

        Raises:
            CacheServiceError: If cache is full

        """
        if not self.enabled:
            return

        ttl = ttl or self.ttl

        # Check cache size
        if len(self._cache) >= self.max_size:
            # Remove oldest entry
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].created_at,
            )
            logger.debug(f"Cache full, evicting oldest entry: {oldest_key}")
            del self._cache[oldest_key]

        self._cache[key] = CacheEntry(value, ttl)
        logger.debug(f"Cache set: {key} (ttl={ttl}s)")

    def delete(self, key: str) -> None:
        """Delete value from cache.

        Args:
            key: Cache key

        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()
        logger.info("Cache cleared")

    def cleanup_expired(self) -> int:
        """Remove all expired entries from cache.

        Returns:
            Number of entries removed

        """
        expired_keys = [
            k for k, v in self._cache.items() if v.is_expired()
        ]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache stats

        """
        self.cleanup_expired()

        return {
            "enabled": self.enabled,
            "size": len(self._cache),
            "max_size": self.max_size,
            "ttl": self.ttl,
            "utilization": len(self._cache) / self.max_size,
        }


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get or create global cache service instance.

    Returns:
        CacheService instance

    """
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService(
            enabled=Config.CACHE_ENABLED,
            ttl=Config.CACHE_TTL_SECONDS,
            max_size=Config.CACHE_MAX_SIZE,
        )
    return _cache_service
