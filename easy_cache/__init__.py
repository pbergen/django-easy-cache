"""
Django Easy Cache - Intelligent caching decorators for Django

This package provides advanced caching decorators with features like:
- Time-based invalidation with timezone support
- Cron-based invalidation with flexible scheduling
- Database analytics and performance tracking
- Comprehensive Django Admin integration
- Management commands for cache operations
"""

__version__ = "0.1.0-alpha-01"
__author__ = "Peter Bergen"
__email__ = "bergen@peterbergen-softwaresolutions.de"
__license__ = "MIT"

from .exceptions import (
    EasyCacheException,
    CacheKeyValidationError,
)
from .decorators.easy_cache import easy_cache


__all__ = [
    "easy_cache",
    "EasyCacheException",
    "CacheKeyValidationError",
]
