"""Unit tests for TimeDecorator"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.utils.timezone import localtime

from django_smart_cache.decorators.time import TimeDecorator
from django_smart_cache.exceptions import InvalidTimeExpression


class TestTimeDecorator(TestCase):
    """Test cases for TimeDecorator"""

    def test_init_valid_time_format(self):
        """Test initialization with valid time format"""
        decorator = TimeDecorator(invalidate_at="14:30")
        self.assertEqual(decorator.invalidate_at, "14:30")

    def test_init_invalid_time_format(self):
        """Test initialization with invalid time format"""
        invalid_formats = [
            "25:00",  # Invalid hour
            "14:60",  # Invalid minute
            "1:30",  # Single digit hour
            "14:5",  # Single digit minute
            "14",  # Missing minute
            "14:30:00",  # With seconds
            "abc",  # Non-numeric
            "",  # Empty string
        ]

        for invalid_format in invalid_formats:
            with self.assertRaises(InvalidTimeExpression):
                TimeDecorator(invalidate_at=invalid_format)

    def test_init_valid_time_edge_cases(self):
        """Test initialization with valid edge case time formats"""
        valid_formats = [
            "00:00",  # Midnight
            "23:59",  # One minute before midnight
            "12:00",  # Noon
            "01:01",  # Early morning
        ]

        for valid_format in valid_formats:
            decorator = TimeDecorator(invalidate_at=valid_format)
            self.assertEqual(decorator.invalidate_at, valid_format)

    @override_settings(TIME_ZONE="UTC")
    def test_init_with_timezone(self):
        """Test initialization with custom timezone"""
        decorator = TimeDecorator(invalidate_at="14:30", timezone_name="Europe/Berlin")
        self.assertEqual(decorator.timezone_name, "Europe/Berlin")

    def test_get_expiration_date_future_time(self):
        """Test expiration date calculation when invalidation time is in the future"""
        decorator = TimeDecorator(invalidate_at="15:30")

        # Current time is 14:00, invalidation at 15:30 today
        now = datetime(2025, 9, 15, 14, 0, 0)
        expiration = decorator._get_expiration_date(now)

        expected = datetime(2025, 9, 15, 15, 30, 0)
        self.assertEqual(expiration, expected)

    def test_get_expiration_date_past_time(self):
        """Test expiration date calculation when invalidation time has passed"""
        decorator = TimeDecorator(invalidate_at="10:30")

        # Current time is 14:00, invalidation at 10:30 tomorrow
        now = datetime(2025, 9, 15, 14, 0, 0)
        expiration = decorator._get_expiration_date(now)

        expected = datetime(2025, 9, 16, 10, 30, 0)
        self.assertEqual(expiration, expected)

    def test_get_expiration_date_exact_time(self):
        """Test expiration date calculation when current time equals invalidation time"""
        decorator = TimeDecorator(invalidate_at="14:30")

        # Current time is exactly 14:30, invalidation at 14:30 tomorrow
        now = datetime(2025, 9, 15, 14, 30, 0)
        expiration = decorator._get_expiration_date(now)

        expected = datetime(2025, 9, 16, 14, 30, 0)
        self.assertEqual(expiration, expected)

    def test_get_expiration_date_midnight(self):
        """Test expiration date calculation for midnight invalidation"""
        decorator = TimeDecorator(invalidate_at="00:00")

        # Current time is 23:30, invalidation at midnight
        now = datetime(2025, 9, 15, 23, 30, 0)
        expiration = decorator._get_expiration_date(now)

        expected = datetime(2025, 9, 16, 0, 0, 0)
        self.assertEqual(expiration, expected)

    def test_calculate_timeout_future_time(self):
        """Test timeout calculation when invalidation time is in the future"""
        decorator = TimeDecorator(invalidate_at="15:30")

        # Current time is 14:00, 1.5 hours until invalidation
        now = datetime(2025, 9, 15, 14, 0, 0)
        timeout = decorator._calculate_timeout(now)

        expected = 90 * 60  # 90 minutes in seconds
        self.assertEqual(timeout, expected)

    def test_calculate_timeout_past_time(self):
        """Test timeout calculation when invalidation time has passed"""
        decorator = TimeDecorator(invalidate_at="10:30")

        # Current time is 14:00, next invalidation is tomorrow
        now = datetime(2025, 9, 15, 14, 0, 0)
        timeout = decorator._calculate_timeout(now)

        # Should be approximately 20.5 hours (until tomorrow 10:30)
        expected = (20 * 60 + 30) * 60  # 20.5 hours in seconds
        self.assertEqual(timeout, expected)

    def test_calculate_timeout_near_midnight(self):
        """Test timeout calculation near midnight"""
        decorator = TimeDecorator(invalidate_at="00:30")

        # Current time is 23:45, 45 minutes until invalidation
        now = datetime(2025, 9, 15, 23, 45, 0)
        timeout = decorator._calculate_timeout(now)

        expected = 45 * 60  # 45 minutes in seconds
        self.assertEqual(timeout, expected)

    def test_integration_with_function_decoration(self):
        """Test that decorator works with actual function decoration"""
        call_count = 0

        @TimeDecorator(invalidate_at="23:59")
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return f"result_{x}_{call_count}"

        # First call should execute function
        result1 = test_function(1)
        self.assertEqual(call_count, 1)
        self.assertIn("result_1_1", result1)

        # Second call with same args should hit cache
        result2 = test_function(1)
        self.assertEqual(call_count, 1)  # Function not called again
        self.assertEqual(result1, result2)

        # Different args should execute function again
        result3 = test_function(2)
        self.assertEqual(call_count, 2)
        self.assertIn("result_2_2", result3)

    def test_docstring_preserved(self):
        """Test that function docstring is preserved after decoration"""

        @TimeDecorator(invalidate_at="12:00")
        def documented_function():
            """This is a test function."""
            return "test"

        self.assertEqual(documented_function.__doc__, "This is a test function.")

    def test_function_name_preserved(self):
        """Test that function name is preserved after decoration"""

        @TimeDecorator(invalidate_at="12:00")
        def named_function():
            return "test"

        self.assertEqual(named_function.__name__, "named_function")

    def test_decorator_attributes_attached(self):
        """Test that decorator attaches its attributes to wrapped function"""

        @TimeDecorator(invalidate_at="12:00")
        def test_function():
            return "test"

        self.assertTrue(hasattr(test_function, "_smart_cache_decorator"))
        self.assertTrue(hasattr(test_function, "_smart_cache_original"))
        self.assertIsInstance(test_function._smart_cache_decorator, TimeDecorator)

    def test_inheritance_from_base_decorator(self):
        """Test that TimeDecorator properly inherits from BaseCacheDecorator"""
        from django_smart_cache.decorators.base import BaseCacheDecorator

        decorator = TimeDecorator(invalidate_at="12:00")
        self.assertIsInstance(decorator, BaseCacheDecorator)

        # Check that base class attributes are available
        self.assertTrue(hasattr(decorator, "config"))
        self.assertTrue(hasattr(decorator, "cache"))
        self.assertTrue(hasattr(decorator, "key_generator"))
        self.assertTrue(hasattr(decorator, "storage"))
        self.assertTrue(hasattr(decorator, "analytics"))
