import pytest
from easy_cache.utils.validation import CacheInputValidator


class TestCacheInputValidator:
    def test_cache_key_validation_normal(self):
        key = "user:123:profile"
        assert CacheInputValidator.validate_cache_key(key) == key

    def test_cache_key_validation_sanitizes_special_chars(self):
        key = "user@123#profile"
        result = CacheInputValidator.validate_cache_key(key)
        assert result == "user_123_profile"

    def test_cache_key_validation_length_limit(self):
        long_key = "x" * 300
        with pytest.raises(ValueError, match="Cache key too long"):
            CacheInputValidator.validate_cache_key(long_key)

    def test_cache_key_validation_non_string(self):
        with pytest.raises(ValueError, match="Cache key must be string"):
            CacheInputValidator.validate_cache_key(123)
