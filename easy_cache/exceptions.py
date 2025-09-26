"""Django Easy Cache Exceptions"""


class EasyCacheException(Exception):
    """Base exception for Easy Cache"""

    pass


class CacheKeyValidationError(EasyCacheException):
    """Cache key validation error"""

    pass


class InvalidCronExpression(EasyCacheException):
    """Invalid cron expression"""

    pass


class InvalidTimeExpression(EasyCacheException):
    """Invalid time expression"""

    pass


class UncachableArgumentError(TypeError, EasyCacheException):
    """Raised when a function argument is not of a cachable type."""

    pass


class InvalidCacheType(EasyCacheException):
    """Invalid cache type"""

    pass
