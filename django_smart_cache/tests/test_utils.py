"""Unit tests for utility functions"""
from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase

from django_smart_cache.utils.format_duration_ms import format_duration_ms
from django_smart_cache.utils.format_time_left import format_time_left


class TestFormatDurationMs(TestCase):
    """Test cases for format_duration_ms utility"""

    def test_none_duration(self):
        """Test format_duration_ms with None input"""
        result = format_duration_ms(None)
        self.assertEqual(result, "N/A")

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
            (1000, "1.00s"),
            (1500, "1.50s"),
            (2750, "2.75s"),
            (5000, "5.00s"),
            (59999, "60.00s"),
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_minute_durations(self):
        """Test format_duration_ms with minute-level durations"""
        test_cases = [
            (60000, "1m 0s"),        # 1 minute
            (90000, "1m 30s"),       # 1.5 minutes
            (120000, "2m 0s"),       # 2 minutes
            (150000, "2m 30s"),      # 2.5 minutes
            (3599000, "59m 59s"),    # Just under 1 hour
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_hour_durations(self):
        """Test format_duration_ms with hour-level durations"""
        test_cases = [
            (3600000, "1h 0m"),      # 1 hour
            (5400000, "1h 30m"),     # 1.5 hours
            (7200000, "2h 0m"),      # 2 hours
            (9000000, "2h 30m"),     # 2.5 hours
            (86399000, "23h 59m"),   # Just under 1 day
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_day_durations(self):
        """Test format_duration_ms with day-level durations"""
        test_cases = [
            (86400000, "1d 0h"),     # 1 day
            (90000000, "1d 1h"),     # 1 day 1 hour
            (172800000, "2d 0h"),    # 2 days
            (604800000, "7d 0h"),    # 1 week
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_float_durations(self):
        """Test format_duration_ms with float inputs"""
        test_cases = [
            (1.5, "1ms"),           # Rounded down
            (1.9, "1ms"),           # Rounded down
            (2.1, "2ms"),           # Rounded down
            (1000.5, "1.00s"),      # Seconds with decimals
            (1500.7, "1.50s"),      # Seconds with decimals
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_negative_durations(self):
        """Test format_duration_ms with negative durations"""
        test_cases = [
            (-1, "-1ms"),
            (-1000, "-1.00s"),
            (-60000, "-1m 0s"),
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)

    def test_edge_case_boundary_values(self):
        """Test format_duration_ms with boundary values"""
        test_cases = [
            (999, "999ms"),      # Just under 1 second
            (1000, "1.00s"),     # Exactly 1 second
            (1001, "1.00s"),     # Just over 1 second
            (59999, "60.00s"),   # Just under 1 minute
            (60000, "1m 0s"),    # Exactly 1 minute
            (60001, "1m 0s"),    # Just over 1 minute
        ]

        for duration, expected in test_cases:
            with self.subTest(duration=duration):
                result = format_duration_ms(duration)
                self.assertEqual(result, expected)


class TestFormatTimeLeft(TestCase):
    """Test cases for format_time_left utility"""

    def test_none_timedelta(self):
        """Test format_time_left with None input"""
        result = format_time_left(None)
        self.assertEqual(result, "N/A")

    def test_zero_timedelta(self):
        """Test format_time_left with zero timedelta"""
        td = timedelta(seconds=0)
        result = format_time_left(td)
        self.assertEqual(result, "0s")

    def test_second_timedeltas(self):
        """Test format_time_left with second-level timedeltas"""
        test_cases = [
            (timedelta(seconds=1), "1s"),
            (timedelta(seconds=30), "30s"),
            (timedelta(seconds=59), "59s"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_minute_timedeltas(self):
        """Test format_time_left with minute-level timedeltas"""
        test_cases = [
            (timedelta(minutes=1), "1m 0s"),
            (timedelta(minutes=1, seconds=30), "1m 30s"),
            (timedelta(minutes=5), "5m 0s"),
            (timedelta(minutes=59, seconds=59), "59m 59s"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_hour_timedeltas(self):
        """Test format_time_left with hour-level timedeltas"""
        test_cases = [
            (timedelta(hours=1), "1h 0m"),
            (timedelta(hours=1, minutes=30), "1h 30m"),
            (timedelta(hours=2), "2h 0m"),
            (timedelta(hours=23, minutes=59), "23h 59m"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_day_timedeltas(self):
        """Test format_time_left with day-level timedeltas"""
        test_cases = [
            (timedelta(days=1), "1d 0h"),
            (timedelta(days=1, hours=5), "1d 5h"),
            (timedelta(days=7), "7d 0h"),
            (timedelta(days=365), "365d 0h"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_complex_timedeltas(self):
        """Test format_time_left with complex timedeltas"""
        test_cases = [
            (timedelta(days=1, hours=2, minutes=3, seconds=4), "1d 2h"),
            (timedelta(hours=5, minutes=30, seconds=45), "5h 30m"),
            (timedelta(minutes=90, seconds=30), "1h 30m"),  # 90 minutes = 1h 30m
            (timedelta(seconds=3661), "1h 1m"),             # 3661 seconds = 1h 1m 1s, but shows 1h 1m
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_microsecond_precision(self):
        """Test format_time_left with microsecond precision"""
        test_cases = [
            (timedelta(microseconds=500000), "0s"),  # 0.5 seconds rounds to 0
            (timedelta(seconds=1, microseconds=500000), "1s"),  # 1.5 seconds rounds to 1
            (timedelta(seconds=1, microseconds=999999), "1s"),  # 1.999999 seconds rounds to 1
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_negative_timedeltas(self):
        """Test format_time_left with negative timedeltas"""
        test_cases = [
            (timedelta(seconds=-1), "-1s"),
            (timedelta(minutes=-5), "-5m 0s"),
            (timedelta(hours=-1), "-1h 0m"),
            (timedelta(days=-1), "-1d 0h"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_edge_case_boundary_values(self):
        """Test format_time_left with boundary values"""
        test_cases = [
            (timedelta(seconds=59), "59s"),
            (timedelta(seconds=60), "1m 0s"),
            (timedelta(seconds=61), "1m 1s"),
            (timedelta(minutes=59), "59m 0s"),
            (timedelta(minutes=60), "1h 0m"),
            (timedelta(hours=23), "23h 0m"),
            (timedelta(hours=24), "1d 0h"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_large_timedeltas(self):
        """Test format_time_left with very large timedeltas"""
        test_cases = [
            (timedelta(days=100), "100d 0h"),
            (timedelta(days=365, hours=12), "365d 12h"),
            (timedelta(days=1000), "1000d 0h"),
        ]

        for td, expected in test_cases:
            with self.subTest(timedelta=td):
                result = format_time_left(td)
                self.assertEqual(result, expected)

    def test_fractional_seconds_rounding(self):
        """Test that fractional seconds are handled correctly"""
        # Test with various fractional seconds
        test_cases = [
            (timedelta(seconds=1.1), "1s"),
            (timedelta(seconds=1.9), "1s"),
            (timedelta(seconds=59.9), "59s"),
            (timedelta(minutes=1, seconds=0.1), "1m 0s"),
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
            (0.5, "0ms"),        # Very fast cache hit
            (2.3, "2ms"),        # Fast cache hit
            (15.7, "15ms"),      # Normal cache hit
            (150.2, "150ms"),    # Cache miss with DB query
            (1250.8, "1.25s"),   # Slow DB operation
            (5000.0, "5.00s"),   # Very slow operation
        ]

        for duration_ms, expected in realistic_durations:
            with self.subTest(duration=duration_ms):
                result = format_duration_ms(duration_ms)
                self.assertEqual(result, expected)

    def test_format_time_left_with_real_cache_timeouts(self):
        """Test format_time_left with realistic cache timeout scenarios"""
        # Simulate real cache timeout scenarios
        realistic_timeouts = [
            (timedelta(seconds=30), "30s"),          # Short cache
            (timedelta(minutes=5), "5m 0s"),         # Medium cache
            (timedelta(minutes=30), "30m 0s"),       # Long cache
            (timedelta(hours=1), "1h 0m"),           # Hourly cache
            (timedelta(hours=24), "1d 0h"),          # Daily cache
            (timedelta(days=7), "7d 0h"),            # Weekly cache
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

        # Both should show hours and minutes
        self.assertIn("1h", duration_ms_1h)
        self.assertIn("1h", timedelta_1h)

        # Test 5 minutes in different formats
        duration_ms_5m = format_duration_ms(300000)  # 5 minutes in ms
        timedelta_5m = format_time_left(timedelta(minutes=5))  # 5 minutes as timedelta

        # Both should show minutes and seconds
        self.assertIn("5m", duration_ms_5m)
        self.assertIn("5m", timedelta_5m)

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
        self.assertNotIn('\n', duration_result)
        self.assertNotIn('\t', duration_result)
        self.assertNotIn('\n', time_result)
        self.assertNotIn('\t', time_result)

        # Should be reasonably short for display purposes
        self.assertLess(len(duration_result), 50)
        self.assertLess(len(time_result), 50)
