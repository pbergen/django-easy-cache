# Getting Started

## Installation

```bash
pip install django-easy-cache
```

## Basic Setup

Add to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    # ... your apps
    "easy_cache",
]
```

Run migrations:

```bash
python manage.py migrate
```

## Quick Example

Replace manual cache management:

```python
# BEFORE: 20+ lines of manual cache management
def get_data(location_id: int):
    now = timezone.now()
    cache_key = f"data_{location_id}_{now.date()}_{now.hour >= 13}"

    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    result = expensive_data_calculation(location_id)

    # Calculate timeout until 13:00 next day
    next_invalidation = now.replace(hour=13, minute=0, second=0, microsecond=0)
    if now.hour >= 13:
        next_invalidation += timedelta(days=1)

    timeout = int((next_invalidation - now).total_seconds())
    cache.set(cache_key, result, timeout)

    return result
```

With Easy Cache:

```python
# AFTER: 3 lines with Easy Cache
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="13:00")
def get_data(location_id: int):
    return expensive_data_calculation(location_id)
```

## Configuration

Configure Easy Cache in your `settings.py`:

```python
from datetime import datetime, date, time
import uuid

easy_cache = {
    "DEFAULT_BACKEND": "default",
    "KEY_PREFIX": "easy_cache",
    "MAX_VALUE_LENGTH": 100,
    # Types to auto-exclude from cache keys (inherently unstable/dynamic)
    "DEFAULT_EXCLUDE_TYPES": (datetime, date, time, uuid.UUID),
    "DEBUG_TOOLBAR_INTEGRATION": False,
    "TRACKING": {
        "TRACK_CACHE_HITS": False,
        "TRACK_CACHE_MISSES": True,
        "TRACK_PERFORMANCE": False,
    },
    "EVENTS": {
        "EVENT_CACHE_HITS": False,
        "EVENT_CACHE_MISSES": False,
        "EVENT_CACHE_ERRORS": False,
    },
}
```

### Configuration Options

- **DEFAULT_BACKEND**: Django cache backend to use (default: "default")
- **KEY_PREFIX**: Prefix for all cache keys (default: "easy_cache")
- **MAX_VALUE_LENGTH**: Maximum length for cache key values (default: 100)
- **DEFAULT_EXCLUDE_TYPES**: Tuple of types to automatically exclude from cache key generation (default: datetime, date, time, uuid.UUID)
- **DEBUG_TOOLBAR_INTEGRATION**: Enable Django Debug Toolbar integration (not yet implemented)
- **TRACKING.TRACK_CACHE_HITS**: Track cache hits in database (default: False)
- **TRACKING.TRACK_CACHE_MISSES**: Track cache misses in database (default: True)
- **TRACKING.TRACK_PERFORMANCE**: Track performance metrics (default: False)
- **EVENTS.EVENT_CACHE_HITS**: Log cache hit events (default: False)
- **EVENTS.EVENT_CACHE_MISSES**: Log cache miss events (default: False)
- **EVENTS.EVENT_CACHE_ERRORS**: Log cache error events (default: False)

## Next Steps

- [Features Overview](features/index.md) - Learn about all available features
- [API Reference](api-reference.md) - Detailed API documentation
- [Object Parameter Caching](features/object-parameter-caching.md) - Advanced caching with objects
