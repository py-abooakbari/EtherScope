"""Unit tests for cache service."""

import time

import pytest

from services.cache_service import CacheService


@pytest.fixture
def cache_service():
    """Create a cache service instance for testing."""
    return CacheService(enabled=True, ttl=1, max_size=10)


class TestCacheService:
    """Tests for cache service."""

    def test_cache_set_and_get(self, cache_service):
        """Test setting and getting values from cache."""
        cache_service.set("key1", "value1")
        result = cache_service.get("key1")
        assert result == "value1"

    def test_cache_get_nonexistent(self, cache_service):
        """Test getting non-existent key."""
        result = cache_service.get("nonexistent")
        assert result is None

    def test_cache_delete(self, cache_service):
        """Test deleting from cache."""
        cache_service.set("key1", "value1")
        cache_service.delete("key1")
        result = cache_service.get("key1")
        assert result is None

    def test_cache_clear(self, cache_service):
        """Test clearing all cache entries."""
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        cache_service.clear()

        assert cache_service.get("key1") is None
        assert cache_service.get("key2") is None

    def test_cache_expiration(self):
        """Test cache expiration."""
        cache_service = CacheService(enabled=True, ttl=1, max_size=10)
        cache_service.set("key1", "value1")

        # Immediately check - should exist
        assert cache_service.get("key1") == "value1"

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache_service.get("key1") is None

    def test_cache_disabled(self):
        """Test cache when disabled."""
        cache_service = CacheService(enabled=False)
        cache_service.set("key1", "value1")
        result = cache_service.get("key1")
        assert result is None

    def test_cache_custom_ttl(self, cache_service):
        """Test setting custom TTL for individual entries."""
        cache_service.set("key1", "value1", ttl=10)
        result = cache_service.get("key1")
        assert result == "value1"

    def test_cache_max_size(self):
        """Test cache respects max size."""
        cache_service = CacheService(enabled=True, ttl=10, max_size=3)

        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")
        cache_service.set("key3", "value3")

        # Cache should be at max size
        assert cache_service.get_stats()["size"] == 3

        # Add one more - should evict oldest
        cache_service.set("key4", "value4")

        # Should still be at max size
        assert cache_service.get_stats()["size"] == 3

    def test_cache_stats(self, cache_service):
        """Test cache statistics."""
        cache_service.set("key1", "value1")
        cache_service.set("key2", "value2")

        stats = cache_service.get_stats()

        assert stats["enabled"] is True
        assert stats["size"] == 2
        assert stats["max_size"] == 10
        assert stats["ttl"] == 1

    def test_cache_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache_service = CacheService(enabled=True, ttl=1, max_size=10)

        # Add entries
        cache_service.set("key1", "value1", ttl=1)
        cache_service.set("key2", "value2", ttl=10)

        # Wait for first to expire
        time.sleep(1.1)

        # Cleanup should remove expired entry
        removed = cache_service.cleanup_expired()
        assert removed >= 1

        # key1 should be gone, key2 should remain
        assert cache_service.get("key1") is None
        assert cache_service.get("key2") == "value2"

    def test_cache_complex_values(self, cache_service):
        """Test caching complex data structures."""
        complex_data = {
            "name": "test",
            "data": [1, 2, 3],
            "nested": {"key": "value"},
        }

        cache_service.set("complex", complex_data)
        result = cache_service.get("complex")

        assert result == complex_data
        assert result["nested"]["key"] == "value"
