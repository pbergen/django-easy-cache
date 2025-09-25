"""Unit tests for Django models"""

from datetime import timedelta

from django.test import TestCase
from django.utils.timezone import localtime

from easy_cache.models import CacheEntry, CacheEventHistory


class TestCacheEntry(TestCase):
    """Test cases for CacheEntry model"""

    def setUp(self):
        """Set up test fixtures"""
        CacheEntry.objects.all().delete()

    def test_create_cache_entry(self):
        """Test creating a basic CacheEntry"""
        entry = CacheEntry.objects.create(
            cache_key="test_key", function_name="test_function", cache_backend="default", timeout=3600
        )

        self.assertEqual(entry.cache_key, "test_key")
        self.assertEqual(entry.function_name, "test_function")
        self.assertEqual(entry.cache_backend, "default")
        self.assertEqual(entry.timeout, 3600)
        self.assertEqual(entry.hit_count, 0)
        self.assertEqual(entry.miss_count, 0)
        self.assertEqual(entry.access_count, 0)
        self.assertIsNotNone(entry.created_at)
        self.assertIsNotNone(entry.last_accessed)

    def test_cache_entry_with_optional_fields(self):
        """Test creating CacheEntry with optional fields"""
        expires_at = localtime() + timedelta(hours=1)

        entry = CacheEntry.objects.create(
            cache_key="test_key",
            function_name="test_function",
            cache_backend="redis",
            original_params="param1=value1&param2=value2",
            timeout=7200,
            expires_at=expires_at,
            hit_count=5,
            miss_count=2,
            access_count=7,
        )

        self.assertEqual(entry.original_params, "param1=value1&param2=value2")
        self.assertEqual(entry.cache_backend, "redis")
        self.assertEqual(entry.timeout, 7200)
        self.assertEqual(entry.expires_at, expires_at)
        self.assertEqual(entry.hit_count, 5)
        self.assertEqual(entry.miss_count, 2)
        self.assertEqual(entry.access_count, 7)

    def test_str_representation(self):
        """Test string representation of CacheEntry"""
        entry = CacheEntry.objects.create(
            cache_key="very_long_cache_key_that_should_be_truncated_in_str_representation",
            function_name="test.module.function_name",
            timeout=3600,
        )

        str_repr = str(entry)
        self.assertIn("test.module.function_name", str_repr)
        self.assertIn("very_long_cache_key_that_should_be_truncated", str_repr)
        self.assertTrue(str_repr.endswith("..."))

    def test_hit_rate_property(self):
        """Test hit_rate property calculation"""
        # Test with no hits or misses
        entry = CacheEntry.objects.create(cache_key="test_key", function_name="test_function", timeout=3600)
        self.assertEqual(entry.hit_rate, 0)

        # Test with only hits
        entry.hit_count = 10
        entry.miss_count = 0
        self.assertEqual(entry.hit_rate, 100.0)

        # Test with only misses
        entry.hit_count = 0
        entry.miss_count = 5
        self.assertEqual(entry.hit_rate, 0.0)

        # Test with mixed hits and misses
        entry.hit_count = 8
        entry.miss_count = 2
        self.assertEqual(entry.hit_rate, 80.0)

        # Test with fractional result
        entry.hit_count = 1
        entry.miss_count = 3
        self.assertEqual(entry.hit_rate, 25.0)

    def test_is_expired_property(self):
        """Test is_expired property"""
        # Test with no expiration date
        entry = CacheEntry.objects.create(cache_key="test_key", function_name="test_function", timeout=3600)
        self.assertFalse(entry.is_expired)

        # Test with future expiration
        future_time = localtime() + timedelta(hours=1)
        entry.expires_at = future_time
        entry.save()
        self.assertFalse(entry.is_expired)

        # Test with past expiration
        past_time = localtime() - timedelta(hours=1)
        entry.expires_at = past_time
        entry.save()
        self.assertTrue(entry.is_expired)

    def test_time_left_property(self):
        """Test time_left property"""
        # Test with no expiration date
        entry = CacheEntry.objects.create(cache_key="test_key", function_name="test_function", timeout=3600)
        self.assertEqual(entry.time_left, timedelta(0))

        # Test with expired entry
        past_time = localtime() - timedelta(hours=1)
        entry.expires_at = past_time
        entry.save()
        self.assertEqual(entry.time_left, timedelta(0))

        # Test with future expiration
        future_time = localtime() + timedelta(hours=1)
        entry.expires_at = future_time
        entry.save()

        time_left = entry.time_left
        self.assertIsInstance(time_left, timedelta)
        self.assertGreater(time_left.total_seconds(), 3500)  # Close to 1 hour
        self.assertLess(time_left.total_seconds(), 3700)  # But not exactly due to execution time

    def test_cache_entry_indexes(self):
        """Test that database indexes are properly defined"""
        # This test ensures indexes are defined in meta
        meta_indexes = CacheEntry._meta.indexes
        self.assertGreater(len(meta_indexes), 0)

        # Check for specific indexes
        index_fields = [list(index.fields) for index in meta_indexes]

        # Verify some key indexes exist
        self.assertIn(["function_name", "created_at"], index_fields)
        self.assertIn(["cache_key", "last_accessed"], index_fields)
        self.assertIn(["expires_at"], index_fields)

    def test_cache_entry_unique_together_behavior(self):
        """Test behavior with multiple entries for same cache key"""
        # Create two entries with same cache key but different functions
        entry1 = CacheEntry.objects.create(cache_key="same_key", function_name="function1", timeout=3600)

        entry2 = CacheEntry.objects.create(cache_key="same_key", function_name="function2", timeout=3600)

        # Both should exist since they have different function names
        self.assertEqual(CacheEntry.objects.filter(cache_key="same_key").count(), 2)
        self.assertNotEqual(entry1.pk, entry2.pk)


class TestCacheEventHistory(TestCase):
    """Test cases for CacheEventHistory model"""

    def setUp(self):
        """Set up test fixtures"""
        CacheEventHistory.objects.all().delete()

    def test_create_cache_event(self):
        """Test creating a basic CacheEventHistory"""
        event = CacheEventHistory.objects.create(
            event_name="cache_hit",
            event_type=CacheEventHistory.EventType.HIT,
            cache_backend="default",
            function_name="test_function",
            cache_key="test_key",
        )

        self.assertEqual(event.event_name, "cache_hit")
        self.assertEqual(event.event_type, CacheEventHistory.EventType.HIT)
        self.assertEqual(event.cache_backend, "default")
        self.assertEqual(event.function_name, "test_function")
        self.assertEqual(event.cache_key, "test_key")
        self.assertIsNotNone(event.occurred_at)

    def test_event_type_choices(self):
        """Test EventType choices"""
        # Test all event types
        hit_event = CacheEventHistory.objects.create(
            event_name="test_hit",
            event_type=CacheEventHistory.EventType.HIT,
            function_name="test_function",
            cache_key="test_key",
        )

        miss_event = CacheEventHistory.objects.create(
            event_name="test_miss",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="test_function",
            cache_key="test_key",
        )

        error_event = CacheEventHistory.objects.create(
            event_name="test_error",
            event_type=CacheEventHistory.EventType.ERROR,
            function_name="test_function",
            cache_key="test_key",
        )

        self.assertEqual(hit_event.event_type, "hit")
        self.assertEqual(miss_event.event_type, "miss")
        self.assertEqual(error_event.event_type, "error")

    def test_event_with_optional_fields(self):
        """Test creating event with optional fields"""
        event = CacheEventHistory.objects.create(
            event_name="cache_miss",
            event_type=CacheEventHistory.EventType.MISS,
            cache_backend="redis",
            function_name="test.module.function",
            cache_key="complex_cache_key",
            duration_ms=150,
            original_params="param1=value1&param2=value2",
        )

        self.assertEqual(event.cache_backend, "redis")
        self.assertEqual(event.duration_ms, 150)
        self.assertEqual(event.original_params, "param1=value1&param2=value2")

    def test_event_ordering(self):
        """Test that events are ordered by occurred_at descending"""
        # Create events - Django will automatically set occurred_at with auto_now_add
        event1 = CacheEventHistory.objects.create(
            event_name="first_event",
            event_type=CacheEventHistory.EventType.HIT,
            function_name="test_function",
            cache_key="test_key1",
        )

        # Small delay to ensure different timestamps
        import time

        time.sleep(0.001)

        event2 = CacheEventHistory.objects.create(
            event_name="second_event",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="test_function",
            cache_key="test_key2",
        )

        # Query should return newest first due to Meta ordering
        events = list(CacheEventHistory.objects.all())
        self.assertEqual(events[0].event_name, "second_event")
        self.assertEqual(events[1].event_name, "first_event")

    def test_event_history_indexes(self):
        """Test that database indexes are properly defined"""
        meta_indexes = CacheEventHistory._meta.indexes
        self.assertGreater(len(meta_indexes), 0)

        # Check for specific indexes
        index_fields = [list(index.fields) for index in meta_indexes]

        # Verify key indexes exist
        self.assertIn(["event_name", "occurred_at"], index_fields)
        self.assertIn(["function_name", "event_type", "occurred_at"], index_fields)

    def test_event_filtering_by_type(self):
        """Test filtering events by type"""
        # Create events of different types
        CacheEventHistory.objects.create(
            event_name="hit1",
            event_type=CacheEventHistory.EventType.HIT,
            function_name="test_function",
            cache_key="key1",
        )

        CacheEventHistory.objects.create(
            event_name="miss1",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="test_function",
            cache_key="key2",
        )

        CacheEventHistory.objects.create(
            event_name="error1",
            event_type=CacheEventHistory.EventType.ERROR,
            function_name="test_function",
            cache_key="key3",
        )

        # Test filtering
        hits = CacheEventHistory.objects.filter(event_type=CacheEventHistory.EventType.HIT)
        misses = CacheEventHistory.objects.filter(event_type=CacheEventHistory.EventType.MISS)
        errors = CacheEventHistory.objects.filter(event_type=CacheEventHistory.EventType.ERROR)

        self.assertEqual(hits.count(), 1)
        self.assertEqual(misses.count(), 1)
        self.assertEqual(errors.count(), 1)

        self.assertEqual(hits.first().event_name, "hit1")
        self.assertEqual(misses.first().event_name, "miss1")
        self.assertEqual(errors.first().event_name, "error1")

    def test_event_filtering_by_function(self):
        """Test filtering events by function name"""
        # Create events for different functions
        CacheEventHistory.objects.create(
            event_name="event1", event_type=CacheEventHistory.EventType.HIT, function_name="function1", cache_key="key1"
        )

        CacheEventHistory.objects.create(
            event_name="event2",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="function2",
            cache_key="key2",
        )

        CacheEventHistory.objects.create(
            event_name="event3", event_type=CacheEventHistory.EventType.HIT, function_name="function1", cache_key="key3"
        )

        # Filter by function name
        function1_events = CacheEventHistory.objects.filter(function_name="function1")
        function2_events = CacheEventHistory.objects.filter(function_name="function2")

        self.assertEqual(function1_events.count(), 2)
        self.assertEqual(function2_events.count(), 1)

    def test_duration_ms_handling(self):
        """Test duration_ms field with various values"""
        test_cases = [
            (None, None),
            (0, 0),
            (1, 1),
            (1500, 1500),
            (999999, 999999),
        ]

        for input_duration, expected_duration in test_cases:
            with self.subTest(duration=input_duration):
                event = CacheEventHistory.objects.create(
                    event_name="duration_test",
                    event_type=CacheEventHistory.EventType.HIT,
                    function_name="test_function",
                    cache_key=f"key_{input_duration}",
                    duration_ms=input_duration,
                )

                self.assertEqual(event.duration_ms, expected_duration)

    def test_large_text_fields(self):
        """Test handling of large text in optional fields"""
        large_params = "param=" + "x" * 1000  # Large parameter string
        large_cache_key = "cache_key_" + "y" * 200  # Long cache key

        event = CacheEventHistory.objects.create(
            event_name="large_data_test",
            event_type=CacheEventHistory.EventType.MISS,
            function_name="test_function",
            cache_key=large_cache_key,
            original_params=large_params,
        )

        self.assertEqual(len(event.original_params), len(large_params))
        self.assertEqual(len(event.cache_key), len(large_cache_key))

    def test_model_verbose_names(self):
        """Test model verbose names"""
        self.assertEqual(CacheEntry._meta.verbose_name, "Cache Entry")
        self.assertEqual(CacheEntry._meta.verbose_name_plural, "Cache Entries")

        self.assertEqual(CacheEventHistory._meta.verbose_name, "Cache Event")
        self.assertEqual(CacheEventHistory._meta.verbose_name_plural, "Cache Events")
