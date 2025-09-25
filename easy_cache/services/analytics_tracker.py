import logging
from datetime import timedelta

from django.db import transaction

from ..utils.validation import CacheInputValidator

logger = logging.getLogger(__name__)


class AnalyticsTracker:
    """Simple synchronous analytics tracking"""

    def __init__(self, config):
        self.config = config

    def track_hit(
        self,
        *,
        cache_backend: str,
        cache_key: str,
        function_name: str,
        original_params: str,
        timeout: int,
        execution_time_ms: float,
    ) -> None:
        """Track cache hit synchronously"""

        from easy_cache.models import CacheEntry, CacheEventHistory
        from django.db.models import F
        from django.utils import timezone

        try:
            validated_cache_key = CacheInputValidator.validate_cache_key(cache_key)

            cache_entry, created = CacheEntry.objects.get_or_create(
                cache_key=validated_cache_key,
                function_name=function_name,
                defaults={
                    "cache_backend": cache_backend,
                    "original_params": original_params,
                    "timeout": timeout,
                    "expires_at": timezone.now() + timedelta(seconds=timeout) if timeout and timeout > 0 else None,
                    "hit_count": 1,
                    "access_count": 1,
                    "last_accessed": timezone.now(),
                },
            )

            if not created:
                with transaction.atomic():
                    entry_to_update = CacheEntry.objects.select_for_update().get(pk=cache_entry.pk)

                    entry_to_update.hit_count = F("hit_count") + 1
                    entry_to_update.access_count = F("access_count") + 1
                    entry_to_update.last_accessed = timezone.now()
                    entry_to_update.save(update_fields=["hit_count", "access_count", "last_accessed"])

            if self.config.should_log_event("CACHE_HITS"):
                CacheEventHistory.objects.create(
                    cache_backend=cache_backend,
                    event_name="cache_hit",
                    event_type=CacheEventHistory.EventType.HIT,
                    function_name=function_name,
                    cache_key=cache_key,
                    duration_ms=int(execution_time_ms) if execution_time_ms is not None else None,
                    original_params=original_params,
                )

        except Exception as e:
            if self.config.should_log_event("CACHE_ERRORS"):
                CacheEventHistory.objects.create(
                    cache_backend=cache_backend,
                    event_name="tracking failed",
                    event_type=CacheEventHistory.EventType.ERROR,
                    function_name=function_name,
                    cache_key=cache_key,
                    duration_ms=int(execution_time_ms) if execution_time_ms is not None else None,
                    original_params=original_params,
                )
            logger.warning(f"Analytics tracking failed: {e}")

    def track_miss(
        self,
        *,
        cache_backend: str,
        cache_key: str,
        function_name: str,
        original_params: str,
        timeout: int,
        execution_time_ms: float,
    ) -> None:
        """Track cache miss"""

        from easy_cache.models import CacheEntry, CacheEventHistory
        from django.db.models import F
        from django.utils import timezone

        try:
            validated_cache_key = CacheInputValidator.validate_cache_key(cache_key)

            cache_entry, created = CacheEntry.objects.get_or_create(
                cache_key=validated_cache_key,
                function_name=function_name,
                defaults={
                    "cache_backend": cache_backend,
                    "original_params": original_params,
                    "timeout": timeout,
                    "expires_at": timezone.now() + timedelta(seconds=timeout) if timeout and timeout > 0 else None,
                    "miss_count": 1,
                    "access_count": 1,
                    "last_accessed": timezone.now(),
                },
            )

            if not created:
                with transaction.atomic():
                    entry_to_update = CacheEntry.objects.select_for_update().get(pk=cache_entry.pk)

                    entry_to_update.miss_count = F("miss_count") + 1
                    entry_to_update.access_count = F("access_count") + 1
                    entry_to_update.last_accessed = timezone.now()
                    entry_to_update.save(update_fields=["miss_count", "access_count", "last_accessed"])

            if self.config.should_log_event("CACHE_MISSES"):
                CacheEventHistory.objects.create(
                    cache_backend=cache_backend,
                    event_name="cache_miss",
                    event_type=CacheEventHistory.EventType.MISS,
                    function_name=function_name,
                    cache_key=cache_key,
                    duration_ms=int(execution_time_ms) if execution_time_ms is not None else None,
                    original_params=original_params,
                )

        except Exception as e:
            if self.config.should_log_event("CACHE_ERRORS"):
                CacheEventHistory.objects.create(
                    cache_backend=cache_backend,
                    event_name="tracking failed",
                    event_type=CacheEventHistory.EventType.ERROR,
                    function_name=function_name,
                    cache_key=cache_key,
                    duration_ms=int(execution_time_ms) if execution_time_ms is not None else None,
                    original_params=original_params,
                )
            logger.warning(f"Analytics tracking failed: {e}")
