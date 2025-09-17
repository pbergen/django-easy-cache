import re
from datetime import datetime, timedelta
from typing import Optional

from django_smart_cache.decorators.base import BaseCacheDecorator
from django_smart_cache.exceptions import InvalidTimeExpression


class TimeDecorator(BaseCacheDecorator):
    """
    Time-based cache invalidation decorator with expiration date caching.

    This decorator invalidates cached results at a specific time each day.
    Useful for caching data that needs to be refreshed at regular daily intervals.
    Uses expiration-based caching where cache keys include explicit expiration dates
    calculated from invalidation times.

    Example:
        @smart_cache.time_based(invalidate_at="06:00", timezone_name="UTC")
        def get_daily_report():
            return expensive_daily_calculation()

    The cache key includes the next invalidation time as expiration date,
    ensuring cache hits for identical requests within the same time interval.
    When the expiration date is reached, a new cache key with updated expiration
    is automatically generated.

    Args:
        invalidate_at (str): Time in HH:MM format when cache should be invalidated
        timezone_name (str): Timezone for invalidation time (default: "UTC")
        cache_backend (str): Django cache backend name (default: "default")

    Raises:
        ValueError: If invalidate_at format is invalid
    """

    def __init__(self, invalidate_at: str, timezone_name: str | None = None, cache_backend: str = "default") -> None:
        if not re.match(r"^([01]\d|2[0-3]):([0-5]\d)$", invalidate_at):
            raise InvalidTimeExpression(
                f"Invalid time format! 'HH:MM' was expected, but ‘{invalidate_at}’ was received."
            )
        self.invalidate_at = invalidate_at
        super().__init__(timezone_name, cache_backend)

    def _get_expiration_date(self, now: datetime) -> datetime:
        """Calculate expiration date based on next invalidation time"""

        invalidate_hour, invalidate_minute = map(int, self.invalidate_at.split(":"))

        # Calculate next invalidation
        next_invalidation = now.replace(hour=invalidate_hour, minute=invalidate_minute, second=0, microsecond=0)

        # If time has already passed today, next day
        if now >= next_invalidation:
            next_invalidation += timedelta(days=1)

        return next_invalidation

    def _calculate_timeout(self, now: datetime) -> int:
        """Calculate seconds until next invalidation"""
        expiration_date = self._get_expiration_date(now)

        # Seconds until invalidation
        return int((expiration_date - now).total_seconds())
