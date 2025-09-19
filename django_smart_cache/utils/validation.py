import re
from typing import Any


class CacheInputValidator:
    """Validates and sanitizes cache-related inputs"""

    MAX_CACHE_KEY_LENGTH = 220  # Memcached limit
    MAX_FUNCTION_NAME_LENGTH = 255
    ALLOWED_CACHE_KEY_PATTERN = re.compile(r"^[a-zA-Z0-9._:-]+$")

    @classmethod
    def validate_cache_key(cls, cache_key: str) -> str:
        """
        Validate and sanitize cache key.

        Invalid characters will be replaced with underscores.
        Allowed characters: a-z, A-Z, 0-9, ., _, :, -
        """
        if not isinstance(cache_key, str):
            raise ValueError(f"Cache key must be string, got {type(cache_key)}")

        if not cache_key.strip():
            raise ValueError("Cache key cannot be empty")

        if len(cache_key) > cls.MAX_CACHE_KEY_LENGTH:
            raise ValueError(f"Cache key too long: {len(cache_key)} > {cls.MAX_CACHE_KEY_LENGTH}")

        if not cls.ALLOWED_CACHE_KEY_PATTERN.match(cache_key):
            # Sanitize by replacing invalid chars
            cache_key = re.sub(r"[^a-zA-Z0-9._:-]", "_", cache_key)

            # Re-validate length after sanitization
            if len(cache_key) > cls.MAX_CACHE_KEY_LENGTH:
                raise ValueError(
                    f"Cache key too long after sanitization: {len(cache_key)} > {cls.MAX_CACHE_KEY_LENGTH}"
                )

        return cache_key
