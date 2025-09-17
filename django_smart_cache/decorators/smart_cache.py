from typing import Optional

from django.core.cache import caches

from django_smart_cache.decorators.cron import CronDecorator
from django_smart_cache.decorators.time import TimeDecorator


class SmartCacheDecorator:
    def __init__(self, key_template: str | None = None, cache_name: str = "default") -> None:
        self.key_template = key_template or "{function_name}_{args_hash}"
        self.cache_name = cache_name
        self.cache = caches[cache_name]

    @classmethod
    def time_based(cls, invalidate_at: str, timezone_name: str | None = None, **kwargs) -> TimeDecorator:
        """Time-based cache invalidation - simplified implementation"""
        return TimeDecorator(invalidate_at=invalidate_at, timezone_name=timezone_name, **kwargs)

    @classmethod
    def cron_based(cls, cron_expression: str, timezone_name: str | None = None, **kwargs) -> CronDecorator:
        """Cron-based cache invalidation - supports cron syntax"""
        return CronDecorator(cron_expression=cron_expression, timezone_name=timezone_name, **kwargs)


smart_cache = SmartCacheDecorator()
