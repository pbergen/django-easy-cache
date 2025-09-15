"""Simple Cache Key Generation System"""
import hashlib
import inspect
from datetime import datetime
from typing import Any, Callable

from django_smart_cache.config import get_config
from django_smart_cache.exceptions import CacheKeyValidationError, UncachableArgumentError


class KeyGenerator:
    """
    Simple cache key generation using split-based approach.

    Supports both traditional period-based caching and new expiration-based caching
    where the period is excluded from the cache key for stable keys within cron intervals.
    """

    MAX_VALUE_LENGTH = 100
    ALLOWED_TYPES = (str, int, float, bool, type(None))

    def __init__(self, prefix: str = "smart_cache"):
        self.config = get_config()
        self.prefix: str = prefix
        self.function_name: str | None = None
        self.original_params: str | None = None

    def generate_key(
        self,
        *,
        func: Callable,
        args: tuple,
        kwargs: dict,
        expiration_date: datetime = None,
    ) -> str:
        """Generate cache key with optional expiration date: Classname_methodname_params_expires_timestamp"""

        self.function_name = f"{func.__module__}.{func.__qualname__}"
        self.original_params = self._simple_params(func=func, args=args, kwargs=kwargs)

        hashed_params = hashlib.sha256(self.original_params.encode()).hexdigest()[:8]
        key_parts = [self.function_name, hashed_params]

        # Add expiration date to key if provided (takes precedence over period)
        if expiration_date:
            # Format: expires_20250905_143000 (YYYYMMDD_HHMMSS)
            expires_part = f"{expiration_date.strftime('%Y%m%d_%H%M%S')}"
            key_parts.append(expires_part)

        # Join with underscores and add prefix
        cache_key = "_".join(part for part in key_parts if part)
        return f"{self.prefix}:{cache_key}"

    def _simple_params(self, *, func: Callable, args: tuple, kwargs: dict) -> str:
        """Processes and serializes simple parameters from a function's arguments, filtering by allowed types and constraints."""
        # Check if this is a method (has 'self' parameter)
        try:
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            has_self = params and params[0] == 'self'
        except Exception:
            has_self = False

        # Filter out 'self' for methods
        filtered_args = args[1:] if has_self and args else args

        # Only include simple serializable values
        simple_values = []

        # Process args with basic validation
        for i, arg in enumerate(filtered_args):
            if isinstance(arg, self.ALLOWED_TYPES):
                safe_value = self._process_value(arg)
                if safe_value:
                    simple_values.append(safe_value)

            elif hasattr(arg, 'pk'):  # Handle Django Models
                simple_values.append(f"{arg.__class__.__name__}:{arg.pk}")

            elif hasattr(arg, 'GET') and hasattr(arg.GET, 'items'):
                for key, value in arg.GET.items():
                    if isinstance(value, self.ALLOWED_TYPES):

                        safe_value = self._process_value(value)
                        if safe_value:
                            param_str = f"{key}={safe_value}"
                            simple_values.append(param_str)
            else:
               raise UncachableArgumentError(
                   f"Argument of type '{type(arg).__name__}' for function "
                   f"'{func.__qualname__}' is not automatically cachable. "
                   f"Please use simple types, Django models, or implement a custom key generation strategy."
               )

        # Process kwargs with basic validation
        for key, value in kwargs.items():
            if (key not in ['request', 'args', 'kwargs'] and
            isinstance(value, self.ALLOWED_TYPES)):
                safe_value = self._process_value(value)
                if safe_value:
                    param_str = f"{key}={safe_value}"
                    simple_values.append(param_str)

        # Return representation or ''
        result = "&".join(simple_values) if simple_values else ""

        return result

    def _process_value(self, value: Any) -> str | None:
        """Minimal value processing - only essential cache-specific handling"""
        if value is None:
            return None

        str_value = str(value)

        # Hash if too long for cache key efficiency
        if len(str_value) > self.config.get('MAX_VALUE_LENGTH'):
            value_hash = hashlib.sha256(str_value.encode()).hexdigest()[:8]
            return f"_{value_hash}"

        # Minimal cleaning - only chars that break cache backends
        if isinstance(value, str):
            # Only remove control characters that actually cause problems
            cleaned = str_value.replace('\n', '_').replace('\r', '_').replace('\0', '_')
            return cleaned.replace(' ', '_')  # Spaces to underscores for readability

        return str_value

    def validate_cache_key(self, cache_key: str) -> None:
        """Minimal cache key validation - only Django limits and cache backend compatibility"""
        # Django's hard limit
        if len(cache_key) > 250:
            raise CacheKeyValidationError(f"Cache key too long: {len(cache_key)} chars")

        # Only check for characters that actually break cache backends
        problematic_chars = ['\n', '\r', '\0']
        for char in problematic_chars:
            if char in cache_key:
                raise CacheKeyValidationError(f"Cache key contains problematic character: {repr(char)}")
