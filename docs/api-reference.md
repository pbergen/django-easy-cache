# API Reference

## Decorators

### `@easy_cache.time_based()`

Time-based cache invalidation decorator.

**Parameters:**
- `invalidate_at` (str): Time in "HH:MM" format when cache should invalidate daily

**Example:**
```python
@easy_cache.time_based(invalidate_at="14:00")
def get_daily_report(date: str):
    return generate_expensive_report(date)
```

### `@easy_cache.cron_based()`

Cron-based cache invalidation decorator.

**Parameters:**
- `cron_expression` (str): Cron expression for invalidation schedule

**Example:**
```python
@easy_cache.cron_based(cron_expression="*/30 * * * *")
def get_live_metrics():
    return fetch_realtime_data()
```

## Configuration

Configure Easy Cache in your `settings.py`:

```python
easy_cache = {
    "DEFAULT_BACKEND": "default",
    "KEY_PREFIX": "easy_cache",
    "MAX_VALUE_LENGTH": 100,
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

## Management Commands

### `easy_cache status`

Check cache system health.

```bash
python manage.py easy_cache status
```

### `easy_cache analytics`

View cache analytics and performance metrics.

**Options:**
- `--days` (int): Number of days to analyze (default: 7)
- `--format` (str): Output format - "table" or "json" (default: table)

```bash
python manage.py easy_cache analytics --days=7 --format=table
python manage.py easy_cache analytics --format=json
```

### `easy_cache clear`

Clear cache entries and event history.

**Options:**
- `--all`: Clear all cache entries and database records
- `--cache-entries`: Clear only cache entries and their database records
- `--event-history`: Clear only event history

```bash
python manage.py easy_cache clear --all
python manage.py easy_cache clear --cache-entries
python manage.py easy_cache clear --event-history
```

## Admin Interface

Easy Cache provides a Django Admin interface at `/admin/django_easy_cache/`:

- **Cache Entries**: Monitor cache performance, hit rates, and access patterns
- **Event History**: Analyze cache events and performance metrics

## Exceptions

### `EasyCacheException`

Base exception for all Easy Cache errors.

### `CacheKeyValidationError`

Raised when a cache key fails validation (too long or contains invalid characters).

### `InvalidCronExpression`

Raised when an invalid cron expression is provided to `@easy_cache.cron_based()`.

### `InvalidTimeExpression`

Raised when an invalid time format is provided to `@easy_cache.time_based()`.

### `UncachableArgumentError`

Raised when a function argument cannot be serialized for caching (e.g., file handles, connections).

### `InvalidCacheType`

Raised when an invalid cache type is specified.

## Core Components

### KeyGenerator

Efficient cache key generation with expiration support.

**Features:**
- Automatic object serialization for Django models
- Deterministic serialization for dataclasses and custom objects
- Cache key validation and sanitization
- Collision avoidance with hashing for large payloads

### StorageHandler

Simple and robust cache storage operations.

**Features:**
- Django cache backend integration
- Automatic error handling and logging
- Support for all Django cache backends

### AnalyticsTracker

Optimized synchronous analytics tracking.

**Features:**
- Cache hit/miss tracking
- Performance monitoring
- Database persistence for analytics

### CacheInputValidator

Validates and sanitizes cache-related inputs.

**Features:**
- Cache key length validation (max 220 characters)
- Invalid character sanitization
- Pattern validation for cache keys

## Architecture

### Design Patterns

- **Decorator Pattern**: Clean separation of caching logic from business logic
- **Strategy Pattern**: Pluggable invalidation strategies
- **Singleton Pattern**: Configuration management
- **Observer Pattern**: Analytics event tracking
- **Factory Pattern**: Cache backend initialization
- **Composition Pattern**: Separated concerns for better maintainability
- **Single Responsibility**: Each component has one clear purpose
