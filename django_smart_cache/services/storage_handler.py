import logging
from typing import Any


logger = logging.getLogger(__name__)

class StorageHandler:
    """Simple cache storage operations"""

    def __init__(self, cache_backend):
        self.cache = cache_backend

    def get(self, key: str) -> Any:
        """Get value from cache"""
        if self.cache is None:
            return None
        try:
            return self.cache.get(key)
        except Exception as e:
            logger.warning(f"Cache get failed for key '{key}': {e}")
            return None

    def set(self, key: str, value: Any, timeout: int) -> bool:
        """Set value in cache"""
        if self.cache is None:
            return False
        try:
            return self.cache.set(key, value, timeout)
        except Exception as e:
            logger.warning(f"Cache set failed for key '{key}': {e}")

        return False


    def add(self, key: str, value: Any, timeout: int) -> bool:
        """Set value in cache only if it does not already exist."""
        if self.cache is None:
            return False
        try:
            return self.cache.add(key, value, timeout)
        except Exception as e:
            logger.warning(f"Cache add failed for key '{key}': {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if self.cache is None:
            return False
        try:
            # gibt es in manchen backends nicht, daher absichern
            if hasattr(self.cache, 'delete'):
                return self.cache.delete(key)
            return False
        except Exception as e:
            logger.warning(f"Cache delete failed for key '{key}': {e}")
            return False