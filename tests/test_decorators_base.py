"""Unit tests for BaseCacheDecorator"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from easy_cache.decorators.base import BaseCacheDecorator
from easy_cache.exceptions import CacheKeyValidationError


class TestBaseCacheDecorator(TestCase):
    """Test cases for BaseCacheDecorator"""

    def setUp(self):
        """Set up test fixtures"""
        self.decorator = TestableBaseCacheDecorator()

    def test_init_default_values(self):
        """Test decorator initialization with default values"""
        decorator = TestableBaseCacheDecorator()
        self.assertIsNotNone(decorator.config)
        self.assertEqual(decorator.cache_name, "default")
        self.assertIsNotNone(decorator.cache)
        self.assertIsNotNone(decorator.key_generator)
        self.assertIsNotNone(decorator.storage)
        self.assertIsNotNone(decorator.analytics)

    def test_init_custom_cache_backend(self):
        """Test decorator initialization with custom cache backend"""
        decorator = TestableBaseCacheDecorator(cache_backend="test_cache")
        self.assertEqual(decorator.cache_name, "test_cache")

    @override_settings(TIME_ZONE="Europe/Berlin")
    def test_init_custom_timezone(self):
        """Test decorator initialization with custom timezone"""
        decorator = TestableBaseCacheDecorator(timezone_name="America/New_York")
        self.assertEqual(decorator.timezone_name, "America/New_York")

    @patch("easy_cache.decorators.base.logger")
    def test_init_invalid_cache_backend(self, mock_logger):
        """Test decorator initialization with invalid cache backend"""
        # Invalid cache backends should log errors but not raise ValueError
        decorator = TestableBaseCacheDecorator(cache_backend="nonexistent")
        self.assertIsNone(decorator.cache)
        mock_logger.error.assert_called()

    def test_health_check_cache_backend_success(self):
        """Test successful cache backend health check"""
        cache_mock = Mock()
        cache_mock.get.return_value = "health_check_value"
        cache_mock.set.return_value = True
        cache_mock.delete.return_value = True

        result = self.decorator._health_check_cache_backend(cache_mock)
        self.assertTrue(result)
        cache_mock.set.assert_called_once()
        cache_mock.get.assert_called_once()
        cache_mock.delete.assert_called_once()

    def test_health_check_cache_backend_failure(self):
        """Test failed cache backend health check"""
        cache_mock = Mock()
        cache_mock.get.return_value = "wrong_value"
        cache_mock.set.return_value = True

        result = self.decorator._health_check_cache_backend(cache_mock)
        self.assertFalse(result)

    @patch("easy_cache.decorators.base.logger")
    def test_health_check_cache_backend_exception(self, mock_logger):
        """Test cache backend health check with exception"""
        cache_mock = Mock()
        cache_mock.set.side_effect = ConnectionError("Connection failed")

        result = self.decorator._health_check_cache_backend(cache_mock)
        self.assertFalse(result)
        mock_logger.error.assert_called()

    def test_callable_returns_wrapper(self):
        """Test that decorator returns a callable wrapper"""

        def test_function():
            return "test_result"

        wrapped = self.decorator(test_function)
        self.assertTrue(callable(wrapped))
        self.assertTrue(hasattr(wrapped, "_easy_cache_decorator"))
        self.assertTrue(hasattr(wrapped, "_easy_cache_original"))
        self.assertEqual(wrapped._easy_cache_original, test_function)

    @patch("django.utils.timezone.localtime")
    def test_execute_with_cache_hit(self, mock_localtime):
        """Test cache hit scenario"""
        mock_localtime.return_value = datetime(2025, 9, 15, 12, 0, 0)

        # Mock cache hit
        self.decorator.storage.get = Mock(return_value="cached_result")
        self.decorator.analytics.track_hit = Mock()

        def test_function():
            return "original_result"

        result = self.decorator._execute_with_cache(test_function)

        self.assertEqual(result, "cached_result")
        self.decorator.analytics.track_hit.assert_called_once()

    @patch("django.utils.timezone.localtime")
    def test_execute_with_cache_miss(self, mock_localtime):
        """Test cache miss scenario"""
        mock_localtime.return_value = datetime(2025, 9, 15, 12, 0, 0)

        # Mock cache miss
        self.decorator.storage.get = Mock(return_value=None)
        self.decorator.storage.set = Mock(return_value=True)
        self.decorator.analytics.track_miss = Mock()

        def test_function():
            return "original_result"

        result = self.decorator._execute_with_cache(test_function)

        self.assertEqual(result, "original_result")
        self.decorator.storage.set.assert_called_once()
        self.decorator.analytics.track_miss.assert_called_once()

    @patch("django.utils.timezone.localtime")
    def test_execute_with_cache_key_validation_error(self, mock_localtime):
        """Test cache execution with invalid cache key"""
        mock_localtime.return_value = datetime(2025, 9, 15, 12, 0, 0)

        # Mock key validation error
        self.decorator.key_generator.validate_cache_key = Mock(side_effect=CacheKeyValidationError("Invalid key"))

        def test_function():
            return "original_result"

        result = self.decorator._execute_with_cache(test_function)

        # Should fallback to original function
        self.assertEqual(result, "original_result")

    def test_get_expiration_date_not_implemented(self):
        """Test that _get_expiration_date raises NotImplementedError"""
        base_decorator = BaseCacheDecorator()
        with self.assertRaises(NotImplementedError):
            base_decorator._get_expiration_date(datetime.now())

    def test_calculate_timeout_not_implemented(self):
        """Test that _calculate_timeout raises NotImplementedError"""
        base_decorator = BaseCacheDecorator()
        with self.assertRaises(NotImplementedError):
            base_decorator._calculate_timeout(datetime.now())


class TestableBaseCacheDecorator(BaseCacheDecorator):
    """Testable version of BaseCacheDecorator with implemented abstract methods"""

    def _get_expiration_date(self, now: datetime) -> datetime:
        """Test implementation of abstract method"""
        return now + timedelta(hours=1)

    def _calculate_timeout(self, now: datetime) -> int:
        """Test implementation of abstract method"""
        return 3600  # 1 hour

    def get_cache_type(self) -> str:
        """Test implementation of abstract method"""
        return "time"
