"""Unit tests for utility functions"""

from datetime import timedelta

from django.test import TestCase

from easy_cache.utils.format_duration_ms import format_duration_ms
from easy_cache.utils.format_time_left import format_time_left


class TestFormatDurationMs(TestCase):
    """Test cases for format_duration_ms utility"""

    def test_none_duration(self):
        """Test format_duration_ms with None input"""
        # The implementation doesn't handle None - test should expect TypeError
        with self.assertRaises(TypeError):
            format_duration_ms(None)

    def test_zero_duration(self):
        """Test format_duration_ms with zero duration"""
        result = format_duration_ms(0)
        self.assertEqual(result, "0ms")

    def test_millisecond_durations(self):
        """Test format_duration_ms with small millisecond durations"""
        test_cases = [
            (1, "1ms"),
            (5, "5ms"),
            (99, "99ms"),
            (123, "123ms"),
            (999, "999ms"),
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_second_durations(self):
        """Test format_duration_ms with second-level durations"""
        test_cases = [
            (1000, "1s"),
            (1500, "1.5s"),
            (2750, "2.8s"),
            (5000, "5s"),
            (59999, "60.0s"),
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_minute_durations(self):
        """Test format_duration_ms with minute-level durations"""
        test_cases = [
            (60000, "1m"),  # 1 minute
            (90000, "1m 30s"),  # 1.5 minutes
            (120000, "2m"),  # 2 minutes
            (150000, "2m 30s"),  # 2.5 minutes
            (3599000, "59m 59s"),  # Just under 1 hour
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_hour_durations(self):
        """Test format_duration_ms with hour-level durations"""
        test_cases = [
            (3600000, "60m"),  # 1 hour
            (5400000, "90m"),  # 1.5 hours
            (7200000, "120m"),  # 2 hours
            (9000000, "150m"),  # 2.5 hours
            (86399000, "1439m 59s"),  # Just under 1 day
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_day_durations(self):
        """Test format_duration_ms with day-level durations"""
        test_cases = [
            (86400000, "1440m"),  # 1 day
            (90000000, "1500m"),  # 1 day 1 hour
            (172800000, "2880m"),  # 2 days
            (604800000, "10080m"),  # 1 week
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_float_durations(self):
        """Test format_duration_ms with float inputs"""
        test_cases = [
            (1.5, "1ms"),  # Rounded down
            (1.9, "1ms"),  # Rounded down
            (2.1, "2ms"),  # Rounded down
            (1000.5, "1.0s"),  # Seconds with decimals
            (1500.7, "1.5s"),  # Seconds with decimals
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_negative_durations(self):
        """Test format_duration_ms with negative durations"""
        test_cases = [
            (-1, "-1ms"),
            (-1000, "-1000ms"),
            (-60000, "-60000ms"),
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_edge_case_boundary_values(self):
        """Test format_duration_ms with boundary values"""
        test_cases = [
            (999, "999ms"),  # Just under 1 second
            (1000, "1s"),  # Exactly 1 second
            (1001, "1.0s"),  # Just over 1 second
            (59999, "60.0s"),  # Just under 1 minute
            (60000, "1m"),  # Exactly 1 minute
            (60001, "1m"),  # Just over 1 minute
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)


class TestFormatTimeLeft(TestCase):
    """Test cases for format_time_left utility"""

    def test_none_timedelta(self):
        """Test format_time_left with None input"""
        # The implementation doesn't handle None - test should expect AttributeError
        with self.assertRaises(AttributeError):
            format_time_left(None)

    def test_zero_timedelta(self):
        """Test format_time_left with zero timedelta"""
        td = timedelta(seconds=0)
        result = format_time_left(td)
        self.assertEqual(result, "expired")

    def test_second_timedeltas(self):
        """Test format_time_left with second-level timedeltas"""
        test_cases = [
            (timedelta(seconds=1), "1 second"),
            (timedelta(seconds=30), "30 seconds"),
            (timedelta(seconds=59), "59 seconds"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_minute_timedeltas(self):
        """Test format_time_left with minute-level timedeltas"""
        test_cases = [
            (timedelta(minutes=1), "1 minute"),
            (timedelta(minutes=1, seconds=30), "1 minute 30 seconds"),
            (timedelta(minutes=5), "5 minutes"),
            (timedelta(minutes=59, seconds=59), "59 minutes 59 seconds"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_hour_timedeltas(self):
        """Test format_time_left with hour-level timedeltas"""
        test_cases = [
            (timedelta(hours=1), "1 hour"),
            (timedelta(hours=1, minutes=30), "1 hour 30 minutes"),
            (timedelta(hours=2), "2 hours"),
            (timedelta(hours=23, minutes=59), "23 hours 59 minutes"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_day_timedeltas(self):
        """Test format_time_left with day-level timedeltas"""
        test_cases = [
            (timedelta(days=1), "1 day"),
            (timedelta(days=1, hours=5), "1 day 5 hours"),
            (timedelta(days=7), "1 week"),
            (timedelta(days=365), "1 year"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_complex_timedeltas(self):
        """Test format_time_left with complex timedeltas"""
        test_cases = [
            (timedelta(days=1, hours=2, minutes=3, seconds=4), "1 day 2 hours"),
            (timedelta(hours=5, minutes=30, seconds=45), "5 hours 30 minutes"),
            (timedelta(minutes=90, seconds=30), "1 hour 30 minutes"),  # 90 minutes = 1h 30m
            (timedelta(seconds=3661), "1 hour 1 minute"),  # 3661 seconds = 1h 1m 1s, but shows 1h 1m
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_microsecond_precision(self):
        """Test format_time_left with microsecond precision"""
        test_cases = [
            (timedelta(microseconds=500000), "expired"),  # 0.5 seconds rounds to 0
            (timedelta(seconds=1, microseconds=500000), "1 second"),  # 1.5 seconds rounds to 1
            (timedelta(seconds=1, microseconds=999999), "1 second"),  # 1.999999 seconds rounds to 1
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_negative_timedeltas(self):
        """Test format_time_left with negative timedeltas"""
        test_cases = [
            (timedelta(seconds=-1), "expired"),
            (timedelta(minutes=-5), "expired"),
            (timedelta(hours=-1), "expired"),
            (timedelta(days=-1), "expired"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_edge_case_boundary_values(self):
        """Test format_time_left with boundary values"""
        test_cases = [
            (timedelta(seconds=59), "59 seconds"),
            (timedelta(seconds=60), "1 minute"),
            (timedelta(seconds=61), "1 minute 1 second"),
            (timedelta(minutes=59), "59 minutes"),
            (timedelta(minutes=60), "1 hour"),
            (timedelta(hours=23), "23 hours"),
            (timedelta(hours=24), "1 day"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_large_timedeltas(self):
        """Test format_time_left with very large timedeltas"""
        test_cases = [
            (timedelta(days=100), "3 months 1 week"),
            (timedelta(days=365, hours=12), "1 year 12 hours"),
            (timedelta(days=1000), "2 years 8 months"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_fractional_seconds_rounding(self):
        """Test that fractional seconds are handled correctly"""
        # Test with various fractional seconds
        test_cases = [
            (timedelta(seconds=1.1), "1 second"),
            (timedelta(seconds=1.9), "1 second"),
            (timedelta(seconds=59.9), "59 seconds"),
            (timedelta(minutes=1, seconds=0.1), "1 minute"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)


class TestUtilityFunctionsIntegration(TestCase):
    """Integration tests for utility functions"""

    def test_format_duration_ms_with_real_measurements(self):
        """Test format_duration_ms with realistic performance measurements"""
        # Simulate real cache operation durations
        realistic_durations = [
            (0.5, "0ms"),  # Very fast cache hit
            (2.3, "2ms"),  # Fast cache hit
            (15.7, "15ms"),  # Normal cache hit
            (150.2, "150ms"),  # Cache miss with DB query
            (1250.8, "1.3s"),  # Slow DB operation
            (5000.0, "5s"),  # Very slow operation
        ]

        for duration_ms, expected in realistic_durations:
            with self.subTest(duration=duration_ms):
                result = format_duration_ms(duration_ms)
                self.assertEqual(result, expected)

    def test_format_time_left_with_real_cache_timeouts(self):
        """Test format_time_left with realistic cache timeout scenarios"""
        # Simulate real cache timeout scenarios
        realistic_timeouts = [
            (timedelta(seconds=30), "30 seconds"),  # Short cache
            (timedelta(minutes=5), "5 minutes"),  # Medium cache
            (timedelta(minutes=30), "30 minutes"),  # Long cache
            (timedelta(hours=1), "1 hour"),  # Hourly cache
            (timedelta(hours=24), "1 day"),  # Daily cache
            (timedelta(days=7), "1 week"),  # Weekly cache
        ]

        for timeout, expected in realistic_timeouts:
            with self.subTest(timeout=timeout):
                result = format_time_left(timeout)
                self.assertEqual(result, expected)

    def test_consistency_between_utilities(self):
        """Test consistency between format_duration_ms and format_time_left"""
        # Both should handle similar time ranges consistently

        # Test 1 hour in different formats
        duration_ms_1h = format_duration_ms(3600000)  # 1 hour in ms
        timedelta_1h = format_time_left(timedelta(hours=1))  # 1 hour as timedelta

        # Both should show hours (duration_ms shows "60m", time_left shows "1 hour")
        self.assertIn("60m", duration_ms_1h)
        self.assertIn("1 hour", timedelta_1h)

        # Test 5 minutes in different formats
        duration_ms_5m = format_duration_ms(300000)  # 5 minutes in ms
        timedelta_5m = format_time_left(timedelta(minutes=5))  # 5 minutes as timedelta

        # Both should show minutes (duration_ms shows "5m", time_left shows "5 minutes")
        self.assertIn("5m", duration_ms_5m)
        self.assertIn("5 minutes", timedelta_5m)

    def test_utility_functions_error_handling(self):
        """Test error handling in utility functions"""
        # Test with invalid types (should not crash)
        try:
            result = format_duration_ms("invalid")
            # If it doesn't crash, it should return something reasonable
            self.assertIsInstance(result, str)
        except (TypeError, ValueError):
            # It's acceptable to raise an exception for invalid types
            pass

        try:
            result = format_time_left("invalid")
            self.assertIsInstance(result, str)
        except (TypeError, ValueError, AttributeError):
            # It's acceptable to raise an exception for invalid types
            pass

    def test_utility_functions_with_extreme_values(self):
        """Test utility functions with extreme values"""
        # Test with very large numbers
        large_duration = 999999999999  # Very large millisecond value
        result = format_duration_ms(large_duration)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

        # Test with very large timedelta
        large_timedelta = timedelta(days=999999)
        result = format_time_left(large_timedelta)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_utility_functions_output_format(self):
        """Test that utility functions produce consistent output format"""
        # All outputs should be strings
        self.assertIsInstance(format_duration_ms(1000), str)
        self.assertIsInstance(format_time_left(timedelta(seconds=60)), str)

        # Outputs should not contain unexpected characters
        duration_result = format_duration_ms(1500)
        time_result = format_time_left(timedelta(minutes=2, seconds=30))

        # Should not contain newlines or tabs
        self.assertNotIn("\n", duration_result)
        self.assertNotIn("\t", duration_result)
        self.assertNotIn("\n", time_result)
        self.assertNotIn("\t", time_result)

        # Should be reasonably short for display purposes
        self.assertLess(len(duration_result), 50)
        self.assertLess(len(time_result), 50)
