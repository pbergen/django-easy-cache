from datetime import datetime
from cron_converter import Cron
from cron_converter.sub_modules.seeker import Seeker

from django_smart_cache.decorators.base import BaseCacheDecorator
from django_smart_cache.exceptions import InvalidCronExpression

class CronDecorator(BaseCacheDecorator):
    """
    Cron-based cache invalidation decorator with expiration date caching.

    This decorator invalidates cached results based on cron expressions,
    allowing for flexible scheduling of cache invalidation. Uses
    expiration-based caching where cache keys include explicit expiration dates
    calculated from cron intervals.

    Supported cron patterns:
    - Every X minutes: "*/5 * * * *" (every 5 minutes)
    - Every X hours: "0 */2 * * *" (every 2 hours at minute 0)
    - Daily at specific time: "30 14 * * *" (daily at 14:30)
    - Hourly: "0 * * * *" (every hour at minute 0)

    Example:
        @smart_cache.cron_based(cron_expression="*/15 * * * *")
        def get_frequently_updated_data():
            return fetch_from_api()

    The cache key includes the next cron execution time as expiration date,
    ensuring cache hits for identical requests within the same cron interval.
    When the expiration date is reached, a new cache key with updated expiration
    is automatically generated.

    Args:
        cron_expression (str): Cron expression in standard format (5 fields)
        timezone_name (str): Timezone for cron scheduling (default: "UTC")
        cache_backend (str): Django cache backend name (default: "default")

    Raises:
        ValueError: If cron_expression is invalid
    """

    def __init__(
        self,
        cron_expression: str,
        timezone_name: str | None = None,
        cache_backend: str = "default"
    ) -> None:
        self.cron_expression = cron_expression
        super().__init__(timezone_name, cache_backend)


    def _get_expiration_date(self, now: datetime) -> datetime:
        """Calculate expiration date based on the next cron execution"""
        return self._parse_cron_expression(self.cron_expression, now).next()

    def _calculate_timeout(self, now: datetime) -> int:
        """Calculate seconds until next cron execution"""
        next_execution = self._parse_cron_expression(self.cron_expression, now).next()
        return int((next_execution - now).total_seconds())

    @staticmethod
    def _parse_cron_expression(cron_expression: str, now: datetime) -> Seeker:
        try:
            cron = Cron(cron_expression)
            schedule= cron.schedule(now)
            return schedule
        except Exception as e:
            raise InvalidCronExpression(e)




