# Django Easy Cache

Intelligent caching decorators for Django with time-based invalidation, cron-based scheduling, and comprehensive analytics.
Transform your Django application's caching from manual, error-prone boilerplate into elegant, maintainable decorators.

[![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![PyPI version](https://badge.fury.io/py/django-easy-cache.svg)](https://pypi.org/project/django-easy-cache/)
[![Python versions](https://img.shields.io/pypi/pyversions/django-easy-cache.svg)](https://pypi.org/project/django-easy-cache/)
[![Django versions](https://img.shields.io/badge/Django-4.2%20%7C%205.0%20%7C%205.1-blue)](https://www.djangoproject.com/)

[![Tests](https://github.com/pbergen/django-easy-cache/workflows/Tests/badge.svg)](https://github.com/pbergen/django-easy-cache/actions)
[![Documentation Status](https://readthedocs.org/projects/django-easy-cache/badge/?version=latest)](https://django-easy-cache.readthedocs.io/en/latest/?badge=latest)

## ✨ Features

- **🕒 Time-Based Invalidation**: Automatically invalidate caches at specific times with timezone support
- **⏰ Cron-Based Scheduling**: Flexible cache invalidation using cron expressions
- **📊 Database Analytics**: Comprehensive cache performance tracking and monitoring
- **🔒 Cache Key Validation**: Built-in cache key validation and length limits
- **🎛️ Django Admin**: Administrative interface for cache entries and event history
- **📚 Type Hints**: Complete type annotations for better IDE support
- **🏗️ Modular Architecture**: Separated concerns for better maintainability
- **🛡️ Robust Error Handling**: Graceful degradation with specific exception handling

## 🚀 Quick Start

### Installation

```bash
pip install django-easy-cache
```

### Basic Setup

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

### Your First Easy Cache

Replace this caching boilerplate:

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

With this:

```python
# AFTER: 3 lines with Easy Cache
from easy_cache import easy_cache


@easy_cache.time_based(
    invalidate_at="13:00",
)
def get_data(location_id: int):
    return expensive_data_calculation(location_id)
```

## 📖 API Reference

### Time-Based Caching

```python
from easy_cache import easy_cache


@easy_cache.time_based(
    invalidate_at="14:00",  # Invalidate daily at 14:00
)
def get_daily_report(date: str):
    return generate_expensive_report(date)
```

### Cron-Based Caching

```python
from easy_cache import easy_cache


@easy_cache.cron_based(cron_expression="*/30 * * * *")
def get_live_metrics():
    return fetch_realtime_data()
```

### Advanced Configuration

```python
# settings.py
easy_cache = {
    "DEFAULT_BACKEND": "default",
    "KEY_PREFIX": "easy_cache",
    # Analytics & Monitoring
    "ANALYTICS_ENABLED": True,
    "PERFORMANCE_MONITORING": True,
    "DEBUG_TOOLBAR_INTEGRATION": True,
    # Cache Key
    "MAX_VALUE_LENGTH": 100,
    # Logging / TRACKING / ANALYTICS
    "TRACKING": {
        "TRACK_CACHE_HITS": True,
        "TRACK_CACHE_MISSES": True,
        "TRACK_ERRORS": True,
        "TRACK_PERFORMANCE": True,
    },
}
```

## 🛠️ Management Commands

### Cache Status & Analytics

```bash
# Check cache system health
python manage.py easy_cache status

# Detailed analytics report
python manage.py easy_cache analytics --days=7 --format=table

# JSON format for automation
python manage.py easy_cache analytics --format=json
```

### Cache Management

```bash
# Clear all cache entries and database records
python manage.py easy_cache clear --all

# Clear only cache entries and their database records
python manage.py easy_cache clear --cache-entries

# Clear only event history
python manage.py easy_cache clear --event-history
```

## 🎛️ Django Admin Integration

Easy Cache provides a Django Admin interface at `/admin/django_easy_cache/`:

- **Cache Entries**: Monitor cache performance, hit rates, and access patterns
- **Event History**: Analyze cache events and performance metrics

## 🐳 Docker Development

### Quick Start with Docker

Start the development environment:

```bash
docker-compose up -d
```

This will start:
- Django application with auto-reload
- Redis cache backend
- PostgreSQL database
- Qdrant vector database

### Docker Build Options

You can control which optional dependencies are installed during the Docker build process using build arguments:

```bash
# Build with all dependencies (default in docker-compose.yml)
docker-compose build

# Build with only core dependencies
docker build --build-arg UV_INSTALL_DEV=false --build-arg UV_INSTALL_REDIS=false --build-arg UV_INSTALL_POSTGRESQL=false -t django-easy-cache .

# Build with development dependencies only
docker build --build-arg UV_INSTALL_DEV=true --build-arg UV_INSTALL_REDIS=false --build-arg UV_INSTALL_POSTGRESQL=false -t django-easy-cache .

# Build with Redis support only
docker build --build-arg UV_INSTALL_DEV=false --build-arg UV_INSTALL_REDIS=true --build-arg UV_INSTALL_POSTGRESQL=false -t django-easy-cache .

# Build with PostgreSQL support only
docker build --build-arg UV_INSTALL_DEV=false --build-arg UV_INSTALL_REDIS=false --build-arg UV_INSTALL_POSTGRESQL=true -t django-easy-cache .

# Custom docker-compose override
```yml
services:
  dev:
    build:
      args:
        UV_INSTALL_DEV: "true"
        UV_INSTALL_REDIS: "true"
        UV_INSTALL_POSTGRESQL: "false"
```

### Available Build Arguments

- `UV_INSTALL_DEV`: Install development dependencies (default: `true`)
- `UV_INSTALL_REDIS`: Install Redis dependencies (default: `true`)
- `UV_INSTALL_POSTGRESQL`: Install PostgreSQL dependencies (default: `true`)

These can be combined as needed. For example, you can install both dev and Redis dependencies by setting both flags to `true`.

## 🧪 Testing Support

Easy Cache includes comprehensive testing utilities:

## 🔒 Security Features

- **Cache Key Validation**: Automatic validation of cache keys for length and problematic characters
- **Length Limits**: Configurable maximum key lengths (default: 250 characters)

## 📊 Performance Analytics

Easy Cache provides cache analytics:

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

## 🏗️ Architecture

### Core Components

- **`KeyGenerator`**: Efficient cache key generation with expiration support
- **`StorageHandler`**: Simple and robust cache storage operations
- **`AnalyticsTracker`**: Optimized synchronous analytics tracking
- **`TimeDecorator`**: Time-based caching implementation
- **`CronDecorator`**: Cron-based caching implementation
- **`BaseCacheDecorator`**: Refactored base class using separated components
- **`EasyCacheConfig`**: Centralized configuration management
- **Analytics Models**: Database tracking of cache performance

### Design Patterns

- **Decorator Pattern**: Clean separation of caching logic from business logic
- **Strategy Pattern**: Pluggable invalidation strategies
- **Singleton Pattern**: Configuration management
- **Observer Pattern**: Analytics event tracking
- **Factory Pattern**: Cache backend initialization
- **Composition Pattern**: Separated concerns for better maintainability
- **Single Responsibility**: Each component has one clear purpose

## 🤝 Contributing

We welcome contributions!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for your changes
5. Run the test suite (`pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 🐛 Bug Reports & Feature Requests

- **Bug Reports**: [GitHub Issues](https://github.com/pbergen/django-easy-cache/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/pbergen/django-easy-cache/discussions)
- **Security Issues**: Email security@django-easy-cache.com

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE.md) file for details.

## 🙏 Acknowledgments

Inspired by real-world caching challenges in Django applications. Built on the solid foundation of Django's caching framework with community-driven development and feedback.

## 🔗 Links

- **PyPI**: https://pypi.org/project/django-easy-cache/
- **GitHub**: https://github.com/pbergen/django-easy-cache
- **Full documentation**: https://django-easy-cache.readthedocs.io/en/latest/index.html
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
