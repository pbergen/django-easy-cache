from typing import Optional

from django.core.cache import caches

from django_smart_cache.decorators.cron import CronDecorator
from django_smart_cache.decorators.time import TimeDecorator


class SmartCacheDecorator:
    def __init__(self, key_template: str | None = None, cache_backend: str = "default") -> None:
        self.key_template = key_template or "{function_name}_{args_hash}"
        self.cache_name = cache_backend
        self.cache = caches[cache_backend]

    @classmethod
    def time_based(
        cls, invalidate_at: str, timezone_name: str | None = None, cache_backend: str = "default"
    ) -> TimeDecorator:
        """Time-based cache invalidation - simplified implementation"""
        return TimeDecorator(invalidate_at=invalidate_at, timezone_name=timezone_name, cache_backend=cache_backend)

    @classmethod
    def cron_based(
        cls, cron_expression: str, timezone_name: str | None = None, cache_backend: str = "default"
    ) -> CronDecorator:
        """Cron-based cache invalidation - supports cron syntax"""
        return CronDecorator(cron_expression=cron_expression, timezone_name=timezone_name, cache_backend=cache_backend)


smart_cache = SmartCacheDecorator()
