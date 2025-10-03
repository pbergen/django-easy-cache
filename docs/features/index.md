# Features

## Core Features

### Time-Based Invalidation
Automatically invalidate caches at specific times with timezone support.

```python
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="14:00")
def get_daily_report(date: str):
    return generate_expensive_report(date)
```

### Cron-Based Scheduling
Flexible cache invalidation using cron expressions.

```python
from easy_cache import easy_cache


@easy_cache.cron_based(cron_expression="*/30 * * * *")
def get_live_metrics():
    return fetch_realtime_data()
```

### Object Parameter Caching
Automatic handling of Django models and custom objects as parameters.

```python
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="14:00")
def get_user_profile(user_obj, settings_obj):
    """Cache based on user.pk and settings attributes automatically"""
    return expensive_profile_calculation(user_obj, settings_obj)
```

**[Learn more about Object Parameter Caching](object-parameter-caching.md)**

## Additional Features

### Database Analytics

Comprehensive cache performance tracking and monitoring:

```bash
# View cache performance
python manage.py easy_cache analytics

# Output:
# Cache Analytics (last 7 days)
# ----------------------------------------
# Total Entries: 42
# Average Hit Rate: 78.5%

# JSON format for automation
python manage.py easy_cache analytics --format=json
```

### Cache Key Validation

Built-in validation for cache keys:

- **Length Limits**: Maximum 220 characters (Memcached limit)
- **Character Validation**: Allowed characters: `a-z`, `A-Z`, `0-9`, `.`, `_`, `:`, `-`
- **Automatic Sanitization**: Invalid characters replaced with underscores
- **Type Exclusion**: Automatically exclude unstable types (datetime, UUID, etc.) from cache keys

Configure which types to exclude:

```python
from datetime import datetime, date, time
import uuid

easy_cache = {
    "DEFAULT_EXCLUDE_TYPES": (datetime, date, time, uuid.UUID),
}
```

### Security Features

- **Cache Key Validation**: Automatic validation of cache keys for length and problematic characters
- **Length Limits**: Configurable maximum key lengths (default: 250 characters)
- **Input Sanitization**: Automatic sanitization of cache keys

### Django Admin Integration

Administrative interface for cache entries and events at `/admin/django_easy_cache/`:

- **Cache Entries**: Monitor cache performance, hit rates, and access patterns
- **Event History**: Analyze cache events and performance metrics

### Type Hints

Complete type annotations for better IDE support and type checking.

### Modular Architecture

Separated concerns for better maintainability:
- Decorators
- Services (KeyGenerator, StorageHandler, AnalyticsTracker)
- Utilities (Validation, Formatting)
- Configuration management

### Robust Error Handling

Graceful degradation with specific exceptions:
- `CacheKeyValidationError`
- `InvalidCronExpression`
- `InvalidTimeExpression`
- `UncachableArgumentError`
- `InvalidCacheType`
