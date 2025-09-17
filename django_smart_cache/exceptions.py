"""Django Smart Cache Exceptions"""


class SmartCacheException(Exception):
    """Base exception for Smart Cache"""

    pass


class CacheKeyValidationError(SmartCacheException):
    """Cache key validation error"""

    pass


class InvalidCronExpression(SmartCacheException):
    """Invalid cron expression"""

    pass


class InvalidTimeExpression(SmartCacheException):
    """Invalid time expression"""

    pass


class UncachableArgumentError(TypeError, SmartCacheException):
    """Raised when a function argument is not of a cachable type."""

    pass
