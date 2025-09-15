"""Unit tests for CronDecorator"""
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from django.test import TestCase, override_settings

from django_smart_cache.decorators.cron import CronDecorator
from django_smart_cache.exceptions import InvalidCronExpression


class TestCronDecorator(TestCase):
    """Test cases for CronDecorator"""

    def test_init_valid_cron_expression(self):
        """Test initialization with valid cron expressions"""
        valid_expressions = [
            "*/5 * * * *",     # Every 5 minutes
            "0 */2 * * *",     # Every 2 hours
            "30 14 * * *",     # Daily at 14:30
            "0 0 * * 0",       # Weekly on Sunday
            "0 0 1 * *",       # Monthly on 1st
        ]

        for expression in valid_expressions:
            decorator = CronDecorator(cron_expression=expression)
            self.assertEqual(decorator.cron_expression, expression)

    def test_init_invalid_cron_expression(self):
        """Test initialization with invalid cron expressions"""
        invalid_expressions = [
            "invalid",         # Not a cron expression
            "* * * *",         # Missing field
            "60 * * * *",      # Invalid minute
            "* 25 * * *",      # Invalid hour
            "* * 32 * *",      # Invalid day of month
            "* * * 13 *",      # Invalid month
            "* * * * 8",       # Invalid day of week
        ]

        for expression in invalid_expressions:
            with self.assertRaises(InvalidCronExpression):
                decorator = CronDecorator(cron_expression=expression)
                # Force evaluation by calling _parse_cron_expression
                decorator._parse_cron_expression(expression, datetime.now())

    @override_settings(TIME_ZONE='UTC')
    def test_init_with_timezone(self):
        """Test initialization with custom timezone"""
        decorator = CronDecorator(
            cron_expression="*/5 * * * *",
            timezone_name="Europe/Berlin"
        )
        self.assertEqual(decorator.timezone_name, "Europe/Berlin")

    def test_parse_cron_expression_success(self):
        """Test successful cron expression parsing"""
        now = datetime(2025, 9, 15, 14, 30, 0)
        schedule = CronDecorator._parse_cron_expression("*/5 * * * *", now)

        # Should return a schedule object
        self.assertIsNotNone(schedule)
        self.assertTrue(hasattr(schedule, 'next'))

    def test_parse_cron_expression_failure(self):
        """Test cron expression parsing failure"""
        now = datetime(2025, 9, 15, 14, 30, 0)

        with self.assertRaises(InvalidCronExpression):
            CronDecorator._parse_cron_expression("invalid_cron", now)

    @patch('django_smart_cache.decorators.cron.Cron')
    def test_get_expiration_date(self, mock_cron_class):
        """Test expiration date calculation"""
        # Mock the cron schedule
        mock_schedule = Mock()
        next_execution = datetime(2025, 9, 15, 15, 0, 0)
        mock_schedule.next.return_value = next_execution

        mock_cron = Mock()
        mock_cron.schedule.return_value = mock_schedule
        mock_cron_class.return_value = mock_cron

        decorator = CronDecorator(cron_expression="0 */1 * * *")
        now = datetime(2025, 9, 15, 14, 30, 0)

        expiration = decorator._get_expiration_date(now)
        self.assertEqual(expiration, next_execution)

        # Verify cron was called correctly
        mock_cron_class.assert_called_with("0 */1 * * *")
        mock_cron.schedule.assert_called_with(now)
        mock_schedule.next.assert_called_once()

    @patch('django_smart_cache.decorators.cron.Cron')
    def test_calculate_timeout(self, mock_cron_class):
        """Test timeout calculation"""
        # Mock the cron schedule
        mock_schedule = Mock()
        next_execution = datetime(2025, 9, 15, 15, 0, 0)
        mock_schedule.next.return_value = next_execution

        mock_cron = Mock()
        mock_cron.schedule.return_value = mock_schedule
        mock_cron_class.return_value = mock_cron

        decorator = CronDecorator(cron_expression="0 */1 * * *")
        now = datetime(2025, 9, 15, 14, 30, 0)

        timeout = decorator._calculate_timeout(now)
        expected = 30 * 60  # 30 minutes in seconds
        self.assertEqual(timeout, expected)

    def test_integration_with_function_decoration(self):
        """Test that decorator works with actual function decoration"""
        call_count = 0

        @CronDecorator(cron_expression="*/5 * * * *")
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
        @CronDecorator(cron_expression="0 */1 * * *")
        def documented_function():
            """This is a test function."""
            return "test"

        self.assertEqual(documented_function.__doc__, "This is a test function.")

    def test_function_name_preserved(self):
        """Test that function name is preserved after decoration"""
        @CronDecorator(cron_expression="0 */1 * * *")
        def named_function():
            return "test"

        self.assertEqual(named_function.__name__, "named_function")

    def test_decorator_attributes_attached(self):
        """Test that decorator attaches its attributes to wrapped function"""
        @CronDecorator(cron_expression="0 */1 * * *")
        def test_function():
            return "test"

        self.assertTrue(hasattr(test_function, '_smart_cache_decorator'))
        self.assertTrue(hasattr(test_function, '_smart_cache_original'))
        self.assertIsInstance(test_function._smart_cache_decorator, CronDecorator)

    def test_inheritance_from_base_decorator(self):
        """Test that CronDecorator properly inherits from BaseCacheDecorator"""
        from django_smart_cache.decorators.base import BaseCacheDecorator

        decorator = CronDecorator(cron_expression="0 */1 * * *")
        self.assertIsInstance(decorator, BaseCacheDecorator)

        # Check that base class attributes are available
        self.assertTrue(hasattr(decorator, 'config'))
        self.assertTrue(hasattr(decorator, 'cache'))
        self.assertTrue(hasattr(decorator, 'key_generator'))
        self.assertTrue(hasattr(decorator, 'storage'))
        self.assertTrue(hasattr(decorator, 'analytics'))

    def test_common_cron_expressions(self):
        """Test common cron expressions work correctly"""
        expressions = {
            "*/1 * * * *": "Every minute",
            "*/15 * * * *": "Every 15 minutes",
            "0 */1 * * *": "Every hour",
            "0 */2 * * *": "Every 2 hours",
            "0 9 * * *": "Daily at 9 AM",
            "30 14 * * 1": "Mondays at 2:30 PM",
            "0 0 1 * *": "First day of month",
        }

        for expression, description in expressions.items():
            with self.subTest(expression=expression, description=description):
                # Should not raise exception
                decorator = CronDecorator(cron_expression=expression)
                self.assertEqual(decorator.cron_expression, expression)

    @patch('django_smart_cache.decorators.cron.Cron')
    def test_edge_case_next_execution_same_time(self, mock_cron_class):
        """Test edge case where next execution is the current time"""
        # Mock the cron schedule to return current time
        mock_schedule = Mock()
        now = datetime(2025, 9, 15, 14, 30, 0)
        mock_schedule.next.return_value = now

        mock_cron = Mock()
        mock_cron.schedule.return_value = mock_schedule
        mock_cron_class.return_value = mock_cron

        decorator = CronDecorator(cron_expression="30 14 * * *")

        expiration = decorator._get_expiration_date(now)
        timeout = decorator._calculate_timeout(now)

        self.assertEqual(expiration, now)
        self.assertEqual(timeout, 0)  # No timeout needed

    @patch('django_smart_cache.decorators.cron.Cron')
    def test_error_handling_in_parse_cron(self, mock_cron_class):
        """Test error handling in cron expression parsing"""
        # Mock Cron to raise an exception
        mock_cron_class.side_effect = ValueError("Invalid cron expression")

        with self.assertRaises(InvalidCronExpression):
            CronDecorator._parse_cron_expression("invalid", datetime.now())

    def test_multiple_decorators_different_expressions(self):
        """Test multiple functions with different cron expressions"""
        @CronDecorator(cron_expression="*/5 * * * *")
        def function_5_min():
            return "5min"

        @CronDecorator(cron_expression="0 */1 * * *")
        def function_hourly():
            return "hourly"

        # Both should work independently
        result1 = function_5_min()
        result2 = function_hourly()

        self.assertEqual(result1, "5min")
        self.assertEqual(result2, "hourly")

        # Check they have different cron expressions
        self.assertEqual(
            function_5_min._smart_cache_decorator.cron_expression,
            "*/5 * * * *"
        )
        self.assertEqual(
            function_hourly._smart_cache_decorator.cron_expression,
            "0 */1 * * *"
        )
