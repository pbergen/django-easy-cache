"""Unit tests for StorageHandler service"""

from unittest.mock import Mock, patch

from django.test import TestCase

from django_smart_cache.services.storage_handler import StorageHandler


class TestStorageHandler(TestCase):
    """Test cases for StorageHandler service"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_cache = Mock()
        self.storage = StorageHandler(cache_backend=self.mock_cache)

    def test_init(self):
        """Test StorageHandler initialization"""
        cache_backend = Mock()
        storage = StorageHandler(cache_backend=cache_backend)
        self.assertEqual(storage.cache, cache_backend)

    def test_get_success(self):
        """Test successful cache get operation"""
        # Mock successful cache get
        self.mock_cache.get.return_value = "cached_value"

        result = self.storage.get("test_key")

        self.assertEqual(result, "cached_value")
        self.mock_cache.get.assert_called_once_with("test_key")

    def test_get_cache_miss(self):
        """Test cache get with cache miss (None return)"""
        # Mock cache miss
        self.mock_cache.get.return_value = None

        result = self.storage.get("test_key")

        self.assertIsNone(result)
        self.mock_cache.get.assert_called_once_with("test_key")

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_get_exception_handling(self, mock_logger):
        """Test get operation handles cache exceptions gracefully"""
        # Mock cache exception
        self.mock_cache.get.side_effect = Exception("Cache connection error")

        result = self.storage.get("test_key")

        # Should return None on exception
        self.assertIsNone(result)

        # Should log warning
        mock_logger.warning.assert_called_once()
        self.assertIn("Cache get failed", mock_logger.warning.call_args[0][0])

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_get_connection_error(self, mock_logger):
        """Test get operation with connection error"""
        # Mock connection error
        self.mock_cache.get.side_effect = ConnectionError("Connection failed")

        result = self.storage.get("test_key")

        self.assertIsNone(result)
        mock_logger.warning.assert_called_once()

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_get_timeout_error(self, mock_logger):
        """Test get operation with timeout error"""
        # Mock timeout error
        self.mock_cache.get.side_effect = TimeoutError("Operation timed out")

        result = self.storage.get("test_key")

        self.assertIsNone(result)
        mock_logger.warning.assert_called_once()

    def test_set_success(self):
        """Test successful cache set operation"""
        # Mock successful cache set
        self.mock_cache.set.return_value = True

        result = self.storage.set("test_key", "test_value", 3600)

        self.assertTrue(result)
        self.mock_cache.set.assert_called_once_with("test_key", "test_value", 3600)

    def test_set_failure(self):
        """Test cache set operation failure"""
        # Mock cache set failure
        self.mock_cache.set.return_value = False

        result = self.storage.set("test_key", "test_value", 3600)

        self.assertFalse(result)
        self.mock_cache.set.assert_called_once_with("test_key", "test_value", 3600)

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_set_exception_handling(self, mock_logger):
        """Test set operation handles cache exceptions gracefully"""
        # Mock cache exception
        self.mock_cache.set.side_effect = Exception("Cache write error")

        result = self.storage.set("test_key", "test_value", 3600)

        # Should return False on exception
        self.assertFalse(result)

        # Should log warning
        mock_logger.warning.assert_called_once()
        self.assertIn("Cache set failed", mock_logger.warning.call_args[0][0])

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_set_connection_error(self, mock_logger):
        """Test set operation with connection error"""
        # Mock connection error
        self.mock_cache.set.side_effect = ConnectionError("Connection failed")

        result = self.storage.set("test_key", "test_value", 3600)

        self.assertFalse(result)
        mock_logger.warning.assert_called_once()

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_set_timeout_error(self, mock_logger):
        """Test set operation with timeout error"""
        # Mock timeout error
        self.mock_cache.set.side_effect = TimeoutError("Operation timed out")

        result = self.storage.set("test_key", "test_value", 3600)

        self.assertFalse(result)
        mock_logger.warning.assert_called_once()

    def test_get_different_data_types(self):
        """Test get operation with different data types"""
        test_cases = [
            ("string_value", "string_value"),
            (42, 42),
            (3.14, 3.14),
            (True, True),
            (False, False),
            (None, None),
            ({"key": "value"}, {"key": "value"}),
            ([1, 2, 3], [1, 2, 3]),
        ]

        for expected_value, cache_return in test_cases:
            with self.subTest(value=expected_value):
                self.mock_cache.get.return_value = cache_return

                result = self.storage.get("test_key")

                self.assertEqual(result, expected_value)

    def test_set_different_data_types(self):
        """Test set operation with different data types"""
        test_values = [
            "string_value",
            42,
            3.14,
            True,
            False,
            {"key": "value"},
            [1, 2, 3],
            ("tuple", "data"),
        ]

        self.mock_cache.set.return_value = True

        for value in test_values:
            with self.subTest(value=value):
                result = self.storage.set("test_key", value, 3600)

                self.assertTrue(result)
                # Verify the actual value was passed to cache
                call_args = self.mock_cache.set.call_args
                self.assertEqual(call_args[0][1], value)  # Second argument is the value

    def test_set_with_different_timeouts(self):
        """Test set operation with different timeout values"""
        timeouts = [0, 1, 60, 3600, 86400, None]

        self.mock_cache.set.return_value = True

        for timeout in timeouts:
            with self.subTest(timeout=timeout):
                result = self.storage.set("test_key", "test_value", timeout)

                self.assertTrue(result)
                call_args = self.mock_cache.set.call_args
                self.assertEqual(call_args[0][2], timeout)  # Third argument is timeout

    def test_get_with_special_characters_in_key(self):
        """Test get operation with special characters in cache key"""
        special_keys = [
            "key:with:colons",
            "key_with_underscores",
            "key-with-dashes",
            "key.with.dots",
            "key with spaces",
            "key@with#symbols$",
        ]

        self.mock_cache.get.return_value = "test_value"

        for key in special_keys:
            with self.subTest(key=key):
                result = self.storage.get(key)

                self.assertEqual(result, "test_value")
                self.mock_cache.get.assert_called_with(key)

    def test_set_with_special_characters_in_key(self):
        """Test set operation with special characters in cache key"""
        special_keys = [
            "key:with:colons",
            "key_with_underscores",
            "key-with-dashes",
            "key.with.dots",
        ]

        self.mock_cache.set.return_value = True

        for key in special_keys:
            with self.subTest(key=key):
                result = self.storage.set(key, "test_value", 3600)

                self.assertTrue(result)
                call_args = self.mock_cache.set.call_args
                self.assertEqual(call_args[0][0], key)  # First argument is key

    def test_round_trip_operations(self):
        """Test combined get/set operations"""
        # Set a value
        self.mock_cache.set.return_value = True
        set_result = self.storage.set("test_key", "test_value", 3600)
        self.assertTrue(set_result)

        # Get the same value
        self.mock_cache.get.return_value = "test_value"
        get_result = self.storage.get("test_key")
        self.assertEqual(get_result, "test_value")

        # Verify both operations were called
        self.mock_cache.set.assert_called_once_with("test_key", "test_value", 3600)
        self.mock_cache.get.assert_called_once_with("test_key")

    def test_multiple_operations_on_same_instance(self):
        """Test multiple operations on the same StorageHandler instance"""
        self.mock_cache.set.return_value = True
        self.mock_cache.get.return_value = "cached_value"

        # Perform multiple operations
        self.storage.set("key1", "value1", 3600)
        self.storage.set("key2", "value2", 7200)
        result1 = self.storage.get("key1")
        result2 = self.storage.get("key2")

        # Verify all operations worked
        self.assertEqual(result1, "cached_value")
        self.assertEqual(result2, "cached_value")

        # Verify cache backend was called correctly
        self.assertEqual(self.mock_cache.set.call_count, 2)
        self.assertEqual(self.mock_cache.get.call_count, 2)

    def test_storage_handler_is_stateless(self):
        """Test that StorageHandler doesn't maintain internal state"""
        # Create multiple instances with same cache backend
        storage1 = StorageHandler(self.mock_cache)
        storage2 = StorageHandler(self.mock_cache)

        # Both should work independently
        self.mock_cache.get.return_value = "value1"
        result1 = storage1.get("key1")

        self.mock_cache.get.return_value = "value2"
        result2 = storage2.get("key2")

        self.assertEqual(result1, "value1")
        self.assertEqual(result2, "value2")

        # Both instances should use the same cache backend
        self.assertIs(storage1.cache, storage2.cache)

    @patch("django_smart_cache.services.storage_handler.logger")
    def test_logging_includes_key_information(self, mock_logger):
        """Test that error logging includes key information for debugging"""
        test_key = "test_key_for_debugging"

        # Test get operation logging
        self.mock_cache.get.side_effect = Exception("Get error")
        self.storage.get(test_key)

        # Check that key is included in log message
        mock_logger.warning.assert_called()
        log_message = mock_logger.warning.call_args[0][0]
        self.assertIn(test_key, log_message)

        # Reset mock
        mock_logger.reset_mock()

        # Test set operation logging
        self.mock_cache.set.side_effect = Exception("Set error")
        self.storage.set(test_key, "value", 3600)

        # Check that key is included in log message
        mock_logger.warning.assert_called()
        log_message = mock_logger.warning.call_args[0][0]
        self.assertIn(test_key, log_message)

    def test_integration_with_real_cache_interface(self):
        """Test that StorageHandler works with Django cache interface"""
        from django.core.cache.backends.locmem import LocMemCache

        # Use real cache backend for integration test
        real_cache = LocMemCache("test", {})
        storage = StorageHandler(real_cache)

        # Test set/get cycle
        set_result = storage.set("integration_test", "test_value", 60)
        # Some cache backends may return None for successful operations
        # Just verify storage works by checking the get operation

        get_result = storage.get("integration_test")
        self.assertEqual(get_result, "test_value")

        # Test cache miss
        miss_result = storage.get("nonexistent_key")
        self.assertIsNone(miss_result)
