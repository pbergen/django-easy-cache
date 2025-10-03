"""Simple Cache Key Generation System"""

import hashlib
import inspect
import json
from datetime import datetime
from enum import Enum
from typing import Any
from collections.abc import Callable

from easy_cache.config import get_config
from easy_cache.exceptions import CacheKeyValidationError, UncachableArgumentError


class KeyGenerator:
    """
    Simple cache key generation using split-based approach.

    Supports both traditional period-based caching and new expiration-based caching
    where the period is excluded from the cache key for stable keys within cron intervals.

    Automatically excludes inherently unstable types from cache keys to prevent
    cache invalidation on every call. This makes caching "just work" for most cases.
    """

    MAX_VALUE_LENGTH = 100

    def __init__(self, prefix: str = "easy_cache"):
        """Initialize KeyGenerator."""
        self.config = get_config()
        self.prefix: str = prefix
        self.function_name: str | None = None
        self.original_params: str | None = None

        # Load exclude_types from config
        self.exclude_types = tuple(self.config.get("DEFAULT_EXCLUDE_TYPES", ()))

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

        hashed_params = hashlib.sha256(self.original_params.encode()).hexdigest()[:16]
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
            has_self = params and params[0] == "self"
        except Exception:
            has_self = False

        # Filter out 'self' for methods
        filtered_args = args[1:] if has_self and args else args

        # Serialize all values using JSON with custom encoder
        simple_values = []

        # Process args
        for i, arg in enumerate(filtered_args):
            if hasattr(arg, "pk"):  # Handle Django Models specially
                simple_values.append(f"{arg.__class__.__name__}:{arg.pk}")

            elif hasattr(arg, "GET") and hasattr(arg.GET, "items"):  # Handle Django Request
                for key, value in arg.GET.items():
                    try:
                        serialized = json.dumps(
                            value, sort_keys=True, separators=(",", ":"), default=self._json_default
                        )
                        safe_value = self._process_value(serialized)
                        if safe_value:
                            param_str = f"{key}={safe_value}"
                            simple_values.append(param_str)
                    except (TypeError, ValueError) as e:
                        raise UncachableArgumentError(
                            f"Request parameter '{key}' of type '{type(value).__name__}' for function "
                            f"'{func.__qualname__}' is not automatically cachable: {e}"
                        )
            elif isinstance(arg, (dict, list, tuple, set)):
                # Handle collections using deterministic JSON serialization
                try:
                    serialized = self._serialize_collection(arg, for_display=False)
                    simple_values.append(serialized)
                except (TypeError, ValueError) as e:
                    raise UncachableArgumentError(
                        f"Argument of type '{type(arg).__name__}' for function "
                        f"'{func.__qualname__}' contains non-serializable objects: {e}"
                    )
            else:
                # Handle all other types (str, int, float, bool, None, objects) using JSON serialization
                try:
                    serialized = json.dumps(arg, sort_keys=True, separators=(",", ":"), default=self._json_default)
                    safe_value = self._process_value(serialized)
                    if safe_value:
                        simple_values.append(safe_value)
                except (TypeError, ValueError) as e:
                    raise UncachableArgumentError(
                        f"Argument of type '{type(arg).__name__}' for function "
                        f"'{func.__qualname__}' is not automatically cachable: {e}"
                    )

        # Process kwargs
        for key, value in kwargs.items():
            if key not in ["request", "args", "kwargs"]:
                if isinstance(value, (dict, list, tuple, set)):
                    # Handle collections in kwargs
                    try:
                        serialized = self._serialize_collection(value, for_display=False)
                        param_str = f"{key}={serialized}"
                        simple_values.append(param_str)
                    except (TypeError, ValueError) as e:
                        raise UncachableArgumentError(
                            f"Keyword argument '{key}' of type '{type(value).__name__}' for function "
                            f"'{func.__qualname__}' contains non-serializable objects: {e}"
                        )
                else:
                    # Handle all other types using JSON serialization
                    try:
                        serialized = json.dumps(
                            value, sort_keys=True, separators=(",", ":"), default=self._json_default
                        )
                        safe_value = self._process_value(serialized)
                        if safe_value:
                            param_str = f"{key}={safe_value}"
                            simple_values.append(param_str)
                    except (TypeError, ValueError) as e:
                        raise UncachableArgumentError(
                            f"Keyword argument '{key}' of type '{type(value).__name__}' for function "
                            f"'{func.__qualname__}' is not automatically cachable: {e}"
                        )

        # Return representation or ''
        result = "&".join(simple_values) if simple_values else ""

        return result

    def _should_exclude_value(self, value: Any) -> bool:
        """
        Determine if a value should be excluded from cache key generation based on its type.

        Args:
            value: Value to check

        Returns:
            True if value should be excluded, False otherwise
        """
        return isinstance(value, self.exclude_types)

    def _filter_dict_for_cache(self, data: dict) -> dict:
        """
        Filter dictionary to remove values with unstable types (recursively).

        Args:
            data: Dictionary to filter

        Returns:
            Filtered dictionary with unstable types removed at all levels
        """
        filtered = {}
        for key, value in data.items():
            # Skip values with unstable types
            if self._should_exclude_value(value):
                continue

            # Recursively filter nested dicts
            if isinstance(value, dict):
                filtered[key] = self._filter_dict_for_cache(value)
            # Recursively filter dicts in lists
            elif isinstance(value, list):
                filtered[key] = [
                    self._filter_dict_for_cache(item) if isinstance(item, dict) else item
                    for item in value
                    if not self._should_exclude_value(item)
                ]
            else:
                filtered[key] = value

        return filtered

    def _json_default(self, obj: Any) -> Any:
        """
        Custom JSON encoder that handles complex objects deterministically.

        This encoder creates stable representations without memory addresses by:
        1. Handling Enum types with stable serialization
        2. Handling Django models via primary key
        3. Converting datetime objects to ISO format
        4. Falling back to a stable string representation

        Args:
            obj: The object to encode for JSON serialization

        Returns:
            A JSON-serializable representation
        """
        # Handle Enum types with stable serialization
        if isinstance(obj, Enum):
            return f"{obj.__class__.__name__}.{obj.name}"

        # Handle frozensets deterministically (sort for consistent ordering)
        if isinstance(obj, frozenset):
            return sorted(list(obj), key=lambda x: (type(x).__name__, str(x)))

        # Handle Django models - use class name and primary key (stable identifier)
        if hasattr(obj, "pk") and hasattr(obj, "__class__"):
            return f"{obj.__class__.__name__}:{obj.pk}"

        # Handle datetime objects with consistent formatting
        if isinstance(obj, datetime):
            return obj.isoformat(timespec="microseconds")

        # For dataclasses, use their dict representation (already excludes methods)
        try:
            import dataclasses

            if dataclasses.is_dataclass(obj):
                # Respect field(hash=False) by filtering
                fields_dict = {}
                for field in dataclasses.fields(obj):
                    if field.hash is not False:  # Include if hash is True or None
                        fields_dict[field.name] = getattr(obj, field.name)
                return fields_dict
        except ImportError:
            pass

        # Fallback for custom objects: serialize their __dict__ with auto-exclude
        if hasattr(obj, "__dict__"):
            # Get object's dict and filter to remove unstable types
            obj_dict = {key: value for key, value in obj.__dict__.items() if not key.startswith("_")}
            obj_dict = self._filter_dict_for_cache(obj_dict)
            return obj_dict

        # Last resort: use string representation (no memory address)
        return str(obj)

    def _serialize_collection(self, obj: dict | list | tuple | set, for_display: bool = False) -> str:
        """
        Deterministically serialize collections (dict, list, tuple, set) to a stable string.
        Uses JSON with sorted keys to ensure the same object always produces the same cache key,
        regardless of memory address or insertion order.

        Args:
            obj: The collection to serialize
            for_display: If True, uses pretty-printed JSON for human readability in database.
                        If False, uses compact format for cache keys.
        """
        # Convert sets, frozensets, and tuples to lists for JSON serialization
        if isinstance(obj, (set, frozenset)):
            obj = sorted(list(obj), key=lambda x: (type(x).__name__, str(x)))
        elif isinstance(obj, tuple):
            obj = list(obj)

        # For dictionaries, apply filtering and sort keys for deterministic output
        if isinstance(obj, dict):
            # Apply filter to remove dynamic fields
            obj = self._filter_dict_for_cache(obj)
            obj = dict(sorted(obj.items()))

        # Serialize to JSON with sorted keys using custom encoder
        if for_display:
            # Pretty format for human readability in database/admin
            json_str = json.dumps(obj, sort_keys=True, indent=2, default=self._json_default)
        else:
            # Compact format for cache keys
            json_str = json.dumps(obj, sort_keys=True, separators=(",", ":"), default=self._json_default)

        # Hash if too long for cache key efficiency (only for cache keys, not display)
        if not for_display and len(json_str) > self.MAX_VALUE_LENGTH:
            return hashlib.sha256(json_str.encode()).hexdigest()[:16]

        return json_str

    def _process_value(self, value: Any) -> str | None:
        """Minimal value processing - only essential cache-specific handling"""
        if value is None:
            return None

        str_value = str(value)

        # Hash if too long for cache key efficiency
        if len(str_value) > self.config.get("MAX_VALUE_LENGTH"):
            value_hash = hashlib.sha256(str_value.encode()).hexdigest()[:8]
            return f"_{value_hash}"

        # Minimal cleaning - only chars that break cache backends
        if isinstance(value, str):
            # Only remove control characters that actually cause problems
            cleaned = str_value.replace("\n", "_").replace("\r", "_").replace("\0", "_")
            return cleaned.replace(" ", "_")  # Spaces to underscores for readability

        return str_value

    def validate_cache_key(self, cache_key: str) -> None:
        """Minimal cache key validation - only Django limits and cache backend compatibility"""
        # Django's hard limit
        if len(cache_key) > 250:
            raise CacheKeyValidationError(f"Cache key too long: {len(cache_key)} chars")

        # Only check for characters that actually break cache backends
        problematic_chars = ["\n", "\r", "\0"]
        for char in problematic_chars:
            if char in cache_key:
                raise CacheKeyValidationError(f"Cache key contains problematic character: {repr(char)}")
