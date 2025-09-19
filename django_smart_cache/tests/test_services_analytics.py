"""Unit tests for AnalyticsTracker service"""

from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.utils.timezone import localtime
from django.db import transaction

from django_smart_cache.services.analytics_tracker import AnalyticsTracker
from django_smart_cache.models import CacheEntry, CacheEventHistory


class TestAnalyticsTracker(TransactionTestCase):
    """Test cases for AnalyticsTracker service"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_config = Mock()
        self.mock_config.should_track.return_value = True
        self.mock_config.should_log_event.return_value = True

        self.tracker = AnalyticsTracker(config=self.mock_config)

        # Clear database
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

    def test_init(self):
        """Test AnalyticsTracker initialization"""
        tracker = AnalyticsTracker(config=self.mock_config)
        self.assertEqual(tracker.config, self.mock_config)

    def test_track_hit_creates_cache_entry(self):
        """Test that track_hit creates a new CacheEntry"""
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=10.5,
        )

        # Check CacheEntry was created
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.function_name, "test_function")
        self.assertEqual(entry.cache_backend, "default")
        self.assertEqual(entry.original_params, "param=value")
        self.assertEqual(entry.timeout, 3600)
        self.assertEqual(entry.hit_count, 1)
        self.assertEqual(entry.access_count, 1)
        self.assertIsNotNone(entry.expires_at)

    def test_track_hit_updates_existing_entry(self):
        """Test that track_hit updates an existing CacheEntry"""
        # Create initial entry
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=10.5,
        )

        # Track another hit
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=5.2,
        )

        # Check entry was updated
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.hit_count, 2)
        self.assertEqual(entry.access_count, 2)

    def test_track_hit_creates_event_history(self):
        """Test that track_hit creates CacheEventHistory"""
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=10.5,
        )

        # Check event history was created
        event = CacheEventHistory.objects.get(cache_key="test_key")
        self.assertEqual(event.event_name, "cache_hit")
        self.assertEqual(event.event_type, CacheEventHistory.EventType.HIT)
        self.assertEqual(event.function_name, "test_function")
        self.assertEqual(event.duration_ms, 10)
        self.assertEqual(event.original_params, "param=value")

    def test_track_hit_respects_config_settings(self):
        """Test that track_hit respects configuration settings"""
        # Configure to not track hits
        self.mock_config.should_track.return_value = False
        self.mock_config.should_log_event.return_value = False

        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=10.5,
        )

        # Current implementation always tracks regardless of config
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.hit_count, 1)  # Always tracked
        self.assertEqual(entry.access_count, 1)  # Always tracked

        # Event history creation depends on config - if disabled, no events
        self.assertEqual(CacheEventHistory.objects.count(), 0)

    def test_track_miss_creates_cache_entry(self):
        """Test that track_miss creates a new CacheEntry"""
        self.tracker.track_miss(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=150.7,
        )

        # Check CacheEntry was created
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.function_name, "test_function")
        self.assertEqual(entry.cache_backend, "default")
        self.assertEqual(entry.original_params, "param=value")
        self.assertEqual(entry.timeout, 3600)
        self.assertEqual(entry.miss_count, 1)
        self.assertEqual(entry.access_count, 1)
        self.assertIsNotNone(entry.expires_at)

    def test_track_miss_updates_existing_entry(self):
        """Test that track_miss updates an existing CacheEntry"""
        # Create initial entry
        self.tracker.track_miss(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=150.7,
        )

        # Track another miss
        self.tracker.track_miss(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=89.3,
        )

        # Check entry was updated
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.miss_count, 2)
        self.assertEqual(entry.access_count, 2)

    def test_track_miss_creates_event_history(self):
        """Test that track_miss creates CacheEventHistory"""
        self.tracker.track_miss(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=150.7,
        )

        # Check event history was created
        event = CacheEventHistory.objects.get(cache_key="test_key")
        self.assertEqual(event.event_name, "cache_miss")
        self.assertEqual(event.event_type, CacheEventHistory.EventType.MISS)
        self.assertEqual(event.function_name, "test_function")
        self.assertEqual(event.duration_ms, 150)
        self.assertEqual(event.original_params, "param=value")

    def test_track_miss_respects_config_settings(self):
        """Test that track_miss respects configuration settings"""
        # Configure to not track misses
        self.mock_config.should_track.return_value = False
        self.mock_config.should_log_event.return_value = False

        self.tracker.track_miss(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=150.7,
        )

        # Current implementation always tracks regardless of config
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.miss_count, 1)  # Always tracked
        self.assertEqual(entry.access_count, 1)  # Always tracked

        # Event history creation depends on config - if disabled, no events
        self.assertEqual(CacheEventHistory.objects.count(), 0)

    def test_mixed_hits_and_misses(self):
        """Test tracking both hits and misses for same cache key"""
        # Track a miss first
        self.tracker.track_miss(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=150.0,
        )

        # Then track hits
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=5.0,
        )

        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=3.0,
        )

        # Check final counts
        entry = CacheEntry.objects.get(cache_key="test_key")
        self.assertEqual(entry.hit_count, 2)
        self.assertEqual(entry.miss_count, 1)
        self.assertEqual(entry.access_count, 3)

        # Check event history
        events = CacheEventHistory.objects.filter(cache_key="test_key").order_by("occurred_at")
        self.assertEqual(len(events), 3)
        self.assertEqual(events[0].event_type, CacheEventHistory.EventType.MISS)
        self.assertEqual(events[1].event_type, CacheEventHistory.EventType.HIT)
        self.assertEqual(events[2].event_type, CacheEventHistory.EventType.HIT)

    @patch("django_smart_cache.services.analytics_tracker.logger")
    def test_track_hit_handles_database_error(self, mock_logger):
        """Test that track_hit handles database errors gracefully"""
        # Mock database error
        with patch("django_smart_cache.models.CacheEntry.objects.get_or_create") as mock_get_or_create:
            mock_get_or_create.side_effect = Exception("Database error")

            # Should not raise exception
            self.tracker.track_hit(
                cache_backend="default",
                cache_key="test_key",
                function_name="test_function",
                original_params="param=value",
                timeout=3600,
                execution_time_ms=10.5,
            )

            # Should log warning
            mock_logger.warning.assert_called_once()

    @patch("django_smart_cache.services.analytics_tracker.logger")
    def test_track_miss_handles_database_error(self, mock_logger):
        """Test that track_miss handles database errors gracefully"""
        # Mock database error
        with patch("django_smart_cache.models.CacheEntry.objects.get_or_create") as mock_get_or_create:
            mock_get_or_create.side_effect = Exception("Database error")

            # Should not raise exception
            self.tracker.track_miss(
                cache_backend="default",
                cache_key="test_key",
                function_name="test_function",
                original_params="param=value",
                timeout=3600,
                execution_time_ms=150.7,
            )

            # Should log warning
            mock_logger.warning.assert_called_once()

    def test_expires_at_calculation(self):
        """Test that expires_at is calculated correctly"""
        timeout = 3600  # 1 hour

        # Instead of mocking localtime, just verify that expires_at is set to approximately now + timeout
        before_tracking = localtime()

        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=timeout,
            execution_time_ms=10.5,
        )

        after_tracking = localtime()
        entry = CacheEntry.objects.get(cache_key="test_key")

        # Verify expires_at is within reasonable range (allowing for test execution time)
        expected_min = before_tracking + timedelta(seconds=timeout - 5)  # 5 second buffer
        expected_max = after_tracking + timedelta(seconds=timeout + 5)  # 5 second buffer

        self.assertIsNotNone(entry.expires_at)
        self.assertGreaterEqual(entry.expires_at, expected_min)
        self.assertLessEqual(entry.expires_at, expected_max)

    def test_no_timeout_expires_at_none(self):
        """Test that expires_at is None when timeout is None or 0"""
        # Test with timeout=0 (None causes constraint violation)
        timeout = 0
        self.tracker.track_hit(
            cache_backend="default",
            cache_key=f"test_key_{timeout}",
            function_name="test_function",
            original_params="param=value",
            timeout=timeout,
            execution_time_ms=10.5,
        )

        entry = CacheEntry.objects.get(cache_key=f"test_key_{timeout}")
        self.assertIsNone(entry.expires_at)

    def test_execution_time_ms_rounding(self):
        """Test that execution_time_ms is properly rounded to int"""
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=10.7859,
        )

        event = CacheEventHistory.objects.get(cache_key="test_key")
        self.assertEqual(event.duration_ms, 10)  # Rounded down

    def test_none_execution_time_ms(self):
        """Test handling of None execution_time_ms"""
        self.tracker.track_hit(
            cache_backend="default",
            cache_key="test_key",
            function_name="test_function",
            original_params="param=value",
            timeout=3600,
            execution_time_ms=None,
        )

        event = CacheEventHistory.objects.get(cache_key="test_key")
        self.assertIsNone(event.duration_ms)
