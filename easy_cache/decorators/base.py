import logging
import time
from datetime import datetime
from functools import wraps
from typing import Optional, Any
from collections.abc import Callable

from django.conf import settings
from django.utils import timezone

from easy_cache import CacheKeyValidationError
from easy_cache.config import get_config
from easy_cache.services import AnalyticsTracker, KeyGenerator, StorageHandler

logger = logging.getLogger(__name__)


class BaseCacheDecorator:
    """
    Base class for cache decorators with shared logic and expiration-based caching.

    This class provides the foundation for time-based and cron-based caching decorators.
    It includes features like:

    - Automatic cache key generation with expiration dates
    - Analytics tracking with circuit breaker protection
    - Graceful degradation when cache backend fails
    - Health checks for cache backends
    - Comprehensive error handling and logging
    - Expiration date validation and fallback mechanisms

    The decorators use expiration-based caching where cache keys include explicit
    expiration dates. This ensures:
    - Stable cache keys within expiration periods
    - Automatic invalidation when expiration dates are reached
    - Proper cache hits for identical requests before expiration
    - New cache creation after expiration

    Attributes:
        timezone_name (str): Timezone for cache invalidation calculations
        timeout (Optional[int]): Default cache timeout in seconds
        key_template (str): Template for generating cache keys
        cache_name (str): Name of the Django cache backend to use
        cache: Django cache backend instance
        config: EasyCacheConfig instance
    """

    @staticmethod
    def _cache_template_response_callback(storage, cache_key: str, timeout: int):
        """Static callback to avoid closure memory leaks"""

        def callback(response):
            try:
                storage.set(cache_key, response, timeout)
            except Exception as e:
                logger.warning(f"Failed to cache template response: {e}")

        return callback

    def __init__(self, timezone_name: str | None = None, cache_backend: str = "default") -> None:
        # Get configuration
        self.config = get_config()
        self.timezone_name = timezone_name or settings.TIME_ZONE
        self.cache_name = cache_backend or self.config.get("CACHE_BACKEND")
        self._cache_checked = False

        # Initialize components with separated concerns
        self.cache = self._initialize_cache_backend(cache_backend)

        if self.cache is None:
            logger.error(f"Cache backend '{cache_backend}' not available. Caching will be disabled for this decorator.")

        # Separated components
        self.key_generator = KeyGenerator(prefix=self.config.get("KEY_PREFIX"))
        self.storage = StorageHandler(self.cache)
        self.analytics = AnalyticsTracker(self.config)

    def get_cache_type(self) -> str:
        """Get the cache type for this decorator - to be overridden by subclasses"""
        raise NotImplementedError

    def _initialize_cache_backend(self, cache_name: str) -> Any:
        """Initialize cache backend with health check"""
        try:
            cache_backend = self.config.get_cache_backend(cache_name)
            if cache_backend is None:
                return None

            return cache_backend
        except (ImportError, AttributeError) as e:
            # Configuration or import issues
            logger.error(f"Cache backend configuration error for '{cache_name}': {e}")
            return None
        except (ConnectionError, TimeoutError) as e:
            # Network connectivity issues
            logger.error(f"Cache backend connection failed for '{cache_name}': {e}")
            return None
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error initializing cache backend '{cache_name}': {e}")
            return None

    def _health_check_cache_backend(self, cache_backend: Any) -> bool:
        """Perform basic health check on cache backend"""
        try:
            # Try to set and get a test key
            test_key = f"health_check_{int(time.time())}"
            test_value = "health_check_value"

            cache_backend.set(test_key, test_value, 10)
            retrieved_value = cache_backend.get(test_key)

            if retrieved_value == test_value:
                # Clean up test key
                cache_backend.delete(test_key)
                return True
            else:
                logger.warning("Cache backend health check failed: set/get mismatch")
                return False
        except (ConnectionError, TimeoutError) as e:
            # Network connectivity issues
            logger.error(f"Cache backend connection failed during health check: {e}")
            return False
        except Exception as e:
            # Unexpected health check errors
            logger.error(f"Unexpected cache backend health check error: {e}")
            return False

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return self._execute_with_cache(func, *args, **kwargs)

        wrapper._easy_cache_decorator = self  # type: ignore
        wrapper._easy_cache_original = func  # type: ignore

        return wrapper

    def _execute_with_cache(self, func: Callable, *args, **kwargs) -> Any:
        """Simplified cache logic using separated components"""

        if self.cache is None:
            logger.warning("No cache backend available. Executing function directly.")
            return func(*args, **kwargs)

        if not self._cache_checked:
            if not self._health_check_cache_backend(self.cache):
                # TODO: TRACK MISS AND ERROR
                logger.error(f"Cache backend '{self.cache_name}' is unavailable.")
                return func(*args, **kwargs)
            self._cache_checked = True
        now = timezone.now()
        start_time = time.time()
        execution_time = None

        # Generate cache key with expiration date
        expiration_date = self._get_expiration_date(now)
        cache_key = self.key_generator.generate_key(
            func=func, args=args, kwargs=kwargs, expiration_date=expiration_date
        )
        # Calculate timeout
        timeout = self._calculate_timeout(now)

        try:
            self.key_generator.validate_cache_key(cache_key)
        except CacheKeyValidationError as e:
            logger.error(f"Cache key validation failed: {e}")
            # Fallback: Execute without caching
            return func(*args, **kwargs)

        # Try cache hit using storage handler
        cached_result = self.storage.get(cache_key)

        if cached_result is not None:
            # Track analytics using dedicated component
            if self.config.should_track("PERFORMANCE"):
                execution_time = (time.time() - start_time) * 1000
            self.analytics.track_hit(
                cache_backend=self.cache_name,
                cache_key=cache_key,
                function_name=self.key_generator.function_name,
                original_params=self.key_generator.original_params,
                timeout=timeout,
                execution_time_ms=execution_time,
                cache_type=self.get_cache_type(),
            )
            return cached_result

        # CACHE MISS: Thundering Herd Protection
        lock_key = f"{cache_key}:lock"
        if self.storage.add(lock_key, 1, timeout=15):
            try:
                result = func(*args, **kwargs)
                # Handle TemplateResponse caching
                if hasattr(result, "render") and callable(result.render):
                    callback = self._cache_template_response_callback(self.storage, cache_key, timeout)
                    result.add_post_render_callback(callback)
                else:
                    self.storage.set(cache_key, result, timeout)

                if self.config.should_track("PERFORMANCE"):
                    execution_time = (time.time() - start_time) * 1000
                # Track cache miss
                self.analytics.track_miss(
                    cache_backend=self.cache_name,
                    cache_key=cache_key,
                    function_name=self.key_generator.function_name,
                    original_params=self.key_generator.original_params,
                    timeout=timeout,
                    execution_time_ms=execution_time,
                    cache_type=self.get_cache_type(),
                )
                return result
            finally:
                self.storage.delete(lock_key)
        else:
            # Another process has the lock, I wait and try again
            for _ in range(5):  # Retry 5 times
                time.sleep(0.1)  # Wait 100ms
                cached_result = self.storage.get(cache_key)
                if cached_result is not None:
                    # The other process finished, great!
                    return cached_result

            # Fallback: After 5 retries, execute the function myself without caching
            logger.warning(f"Could not acquire cache lock for key '{cache_key}'. Executing function directly.")
            return func(*args, **kwargs)

    def _get_expiration_date(self, now: datetime) -> datetime:
        """Calculate expiration date for cache key - must be implemented in subclass"""
        raise NotImplementedError

    def _calculate_timeout(self, now: datetime) -> int:
        """Must be implemented in subclass"""
        raise NotImplementedError
