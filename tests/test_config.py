"""Unit tests for EasyCacheConfig"""

from unittest.mock import Mock, patch

from django.test import TestCase, override_settings
from django.core.exceptions import ImproperlyConfigured

from easy_cache.config import EasyCacheConfig, get_config, reload_config


class TestEasyCacheConfig(TestCase):
    """Test cases for EasyCacheConfig"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton instance for each test
        EasyCacheConfig._instance = None

    def test_singleton_pattern(self):
        """Test that EasyCacheConfig implements singleton pattern"""
        config1 = EasyCacheConfig()
        config2 = EasyCacheConfig()

        self.assertIs(config1, config2)

    def test_default_configuration(self):
        """Test default configuration values"""
        config = EasyCacheConfig()

        self.assertEqual(config.get("DEFAULT_BACKEND"), "default")
        self.assertEqual(config.get("KEY_PREFIX"), "easy_cache")
        self.assertEqual(config.get("MAX_VALUE_LENGTH"), 100)
        self.assertTrue(config.get("DEBUG_TOOLBAR_INTEGRATION"))

        # Test tracking settings
        self.assertTrue(config.get("TRACKING.TRACK_CACHE_HITS"))
        self.assertTrue(config.get("TRACKING.TRACK_CACHE_MISSES"))
        self.assertTrue(config.get("TRACKING.TRACK_PERFORMANCE"))

        # Test event settings
        self.assertTrue(config.get("EVENTS.EVENT_CACHE_HITS"))
        self.assertTrue(config.get("EVENTS.EVENT_CACHE_MISSES"))
        self.assertTrue(config.get("EVENTS.EVENT_CACHE_ERRORS"))

    @override_settings(
        easy_cache={
            "DEFAULT_BACKEND": "redis",
            "KEY_PREFIX": "custom_prefix",
            "MAX_VALUE_LENGTH": 200,
            "TRACKING": {
                "TRACK_CACHE_HITS": False,
                "TRACK_PERFORMANCE": True,
            },
            "EVENTS": {
                "EVENT_CACHE_ERRORS": False,
            },
        }
    )
    def test_custom_configuration_override(self):
        """Test configuration override from Django settings"""
        config = EasyCacheConfig()

        # Test overridden values
        self.assertEqual(config.get("DEFAULT_BACKEND"), "redis")
        self.assertEqual(config.get("KEY_PREFIX"), "custom_prefix")
        self.assertEqual(config.get("MAX_VALUE_LENGTH"), 200)

        # Test nested overrides
        self.assertFalse(config.get("TRACKING.TRACK_CACHE_HITS"))
        self.assertTrue(config.get("TRACKING.TRACK_PERFORMANCE"))
        self.assertTrue(config.get("TRACKING.TRACK_CACHE_MISSES"))  # Should remain default

        self.assertFalse(config.get("EVENTS.EVENT_CACHE_ERRORS"))
        self.assertTrue(config.get("EVENTS.EVENT_CACHE_HITS"))  # Should remain default

    def test_get_method_with_dot_notation(self):
        """Test get method with dot notation for nested values"""
        config = EasyCacheConfig()

        # Test existing nested keys
        self.assertTrue(config.get("TRACKING.TRACK_CACHE_HITS"))
        self.assertTrue(config.get("EVENTS.EVENT_CACHE_MISSES"))

        # Test non-existing nested keys
        self.assertIsNone(config.get("TRACKING.NON_EXISTING"))
        self.assertIsNone(config.get("NON_EXISTING.KEY"))

        # Test with default values
        self.assertEqual(config.get("NON_EXISTING.KEY", "default"), "default")
        self.assertEqual(config.get("TRACKING.NON_EXISTING", False), False)

    def test_set_method(self):
        """Test set method for updating configuration"""
        config = EasyCacheConfig()

        # Test setting top-level key
        config.set("NEW_KEY", "new_value")
        self.assertEqual(config.get("NEW_KEY"), "new_value")

        # Test setting nested key
        config.set("NESTED.NEW_KEY", "nested_value")
        self.assertEqual(config.get("NESTED.NEW_KEY"), "nested_value")

        # Test updating existing nested key
        config.set("TRACKING.TRACK_CACHE_HITS", False)
        self.assertFalse(config.get("TRACKING.TRACK_CACHE_HITS"))

    def test_is_enabled_method(self):
        """Test is_enabled method"""
        config = EasyCacheConfig()

        # Test with existing boolean values
        self.assertTrue(config.is_enabled("DEBUG_TOOLBAR_INTEGRATION"))

        # Test with non-existing keys (should return False)
        self.assertFalse(config.is_enabled("NON_EXISTING_FEATURE"))

        # Test after setting custom value
        config.set("CUSTOM_FEATURE", True)
        self.assertTrue(config.is_enabled("CUSTOM_FEATURE"))

        config.set("CUSTOM_FEATURE", False)
        self.assertFalse(config.is_enabled("CUSTOM_FEATURE"))

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            },
            "redis": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            },
        }
    )
    def test_get_cache_backend(self):
        """Test get_cache_backend method"""
        config = EasyCacheConfig()

        # Test default backend
        default_backend = config.get_cache_backend()
        self.assertIsNotNone(default_backend)

        # Test specific backend
        redis_backend = config.get_cache_backend("redis")
        self.assertIsNotNone(redis_backend)

        # Test non-existing backend
        none_backend = config.get_cache_backend("non_existing")
        self.assertIsNone(none_backend)

    def test_get_all_cache_backends(self):
        """Test get_all_cache_backends method"""
        config = EasyCacheConfig()

        backends = config.get_all_cache_backends()
        self.assertIsInstance(backends, dict)
        self.assertIn("default", backends)

    def test_should_track_method(self):
        """Test should_track method"""
        config = EasyCacheConfig()

        # Test existing tracking settings
        self.assertTrue(config.should_track("CACHE_HITS"))
        self.assertTrue(config.should_track("CACHE_MISSES"))
        self.assertTrue(config.should_track("PERFORMANCE"))

        # Test non-existing tracking setting
        self.assertFalse(config.should_track("NON_EXISTING"))

        # Test case insensitivity
        self.assertTrue(config.should_track("cache_hits"))
        self.assertTrue(config.should_track("cache_misses"))

    def test_should_log_event_method(self):
        """Test should_log_event method"""
        config = EasyCacheConfig()

        # Test existing event settings
        self.assertTrue(config.should_log_event("CACHE_HITS"))
        self.assertTrue(config.should_log_event("CACHE_MISSES"))
        self.assertTrue(config.should_log_event("CACHE_ERRORS"))

        # Test non-existing event setting
        self.assertFalse(config.should_log_event("NON_EXISTING"))

        # Test case insensitivity
        self.assertTrue(config.should_log_event("cache_errors"))

    def test_get_tracking_config(self):
        """Test get_tracking_config method"""
        config = EasyCacheConfig()

        tracking_config = config.get_tracking_config()

        self.assertIsInstance(tracking_config, dict)
        self.assertIn("TRACK_CACHE_HITS", tracking_config)
        self.assertIn("TRACK_CACHE_MISSES", tracking_config)
        self.assertIn("TRACK_PERFORMANCE", tracking_config)

        # Should return a copy (not original)
        tracking_config["NEW_KEY"] = "test"
        self.assertNotIn("NEW_KEY", config.get_tracking_config())

    def test_get_event_config(self):
        """Test get_event_config method"""
        config = EasyCacheConfig()

        event_config = config.get_event_config()

        self.assertIsInstance(event_config, dict)
        self.assertIn("EVENT_CACHE_HITS", event_config)
        self.assertIn("EVENT_CACHE_MISSES", event_config)
        self.assertIn("EVENT_CACHE_ERRORS", event_config)

        # Should return a copy (not original)
        event_config["NEW_KEY"] = "test"
        self.assertNotIn("NEW_KEY", config.get_event_config())

    def test_get_full_config(self):
        """Test get_full_config method"""
        config = EasyCacheConfig()

        full_config = config.get_full_config()

        self.assertIsInstance(full_config, dict)
        self.assertIn("DEFAULT_BACKEND", full_config)
        self.assertIn("TRACKING", full_config)
        self.assertIn("EVENTS", full_config)

        # Should return a copy (not original)
        full_config["NEW_KEY"] = "test"
        self.assertNotIn("NEW_KEY", config.get_full_config())

    @override_settings(
        easy_cache={"DEFAULT_BACKEND": "non_existing_backend"},
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        },
    )
    def test_invalid_default_backend_validation(self):
        """Test validation with invalid default backend"""
        with self.assertRaises(ImproperlyConfigured):
            EasyCacheConfig()

    def test_deep_update_functionality(self):
        """Test _deep_update internal method"""
        config = EasyCacheConfig()

        base_dict = {"level1": {"level2": {"key1": "value1", "key2": "value2"}, "key3": "value3"}, "key4": "value4"}

        update_dict = {
            "level1": {
                "level2": {
                    "key1": "updated_value1",  # Should update
                    "key_new": "new_value",  # Should add
                },
                "key_new2": "new_value2",  # Should add
            },
            "key_new3": "new_value3",  # Should add
        }

        config._deep_update(base_dict=base_dict, update_dict=update_dict)

        # Test updates
        self.assertEqual(base_dict["level1"]["level2"]["key1"], "updated_value1")
        self.assertEqual(base_dict["level1"]["level2"]["key2"], "value2")  # Should remain
        self.assertEqual(base_dict["level1"]["key3"], "value3")  # Should remain
        self.assertEqual(base_dict["key4"], "value4")  # Should remain

        # Test additions
        self.assertEqual(base_dict["level1"]["level2"]["key_new"], "new_value")
        self.assertEqual(base_dict["level1"]["key_new2"], "new_value2")
        self.assertEqual(base_dict["key_new3"], "new_value3")

    def test_reload_config_method(self):
        """Test reload_config method"""
        config = EasyCacheConfig()

        # Change a value
        config.set("TEST_KEY", "initial_value")
        self.assertEqual(config.get("TEST_KEY"), "initial_value")

        # Test reload (should reset to Django settings)
        with override_settings(easy_cache={"TEST_KEY": "django_value"}):
            config.reload_config()
            self.assertEqual(config.get("TEST_KEY"), "django_value")

    def test_thread_safety(self):
        """Test thread safety of singleton pattern"""
        import threading

        configs = []

        def create_config():
            config = EasyCacheConfig()
            configs.append(config)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_config)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # All configs should be the same instance
        first_config = configs[0]
        for config in configs[1:]:
            self.assertIs(config, first_config)


class TestConfigHelperFunctions(TestCase):
    """Test cases for config helper functions"""

    def setUp(self):
        """Set up test fixtures"""
        # Reset singleton instance for each test
        EasyCacheConfig._instance = None

    def test_get_config_function(self):
        """Test get_config helper function"""
        config = get_config()

        self.assertIsInstance(config, EasyCacheConfig)

        # Should return same instance on multiple calls
        config2 = get_config()
        self.assertIs(config, config2)

    def test_reload_config_function(self):
        """Test reload_config helper function"""
        config = get_config()

        # Set a test value
        config.set("TEST_RELOAD", "original")
        self.assertEqual(config.get("TEST_RELOAD"), "original")

        # Reload should reset (no custom Django settings, so should be None)
        reload_config()
        self.assertIsNone(config.get("TEST_RELOAD"))

    @patch("django_easy_cache.config.EasyCacheConfig.reload_config")
    def test_reload_config_calls_instance_method(self, mock_reload):
        """Test that reload_config function calls instance reload method"""
        reload_config()

        mock_reload.assert_called_once()

    @override_settings(easy_cache={"CUSTOM_KEY": "custom_value"})
    def test_config_integration_with_django_settings(self):
        """Test integration with Django settings"""
        # Force reload config to pick up override_settings
        reload_config()
        config = get_config()

        self.assertEqual(config.get("CUSTOM_KEY"), "custom_value")

        # Test that defaults are still available
        self.assertEqual(config.get("DEFAULT_BACKEND"), "default")

    def test_config_isolation_between_tests(self):
        """Test that config is properly isolated between tests"""
        # This test should start fresh due to setUp
        config = get_config()

        # Should not have values from previous tests
        self.assertIsNone(config.get("TEST_KEY"))
        self.assertIsNone(config.get("TEST_RELOAD"))
