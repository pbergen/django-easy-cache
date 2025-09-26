import pytest
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone

from easy_cache.models import CacheEntry
from easy_cache.decorators.time import TimeDecorator
from easy_cache.decorators.cron import CronDecorator
from easy_cache.services.analytics_tracker import AnalyticsTracker
from easy_cache.config import get_config


class CacheTypeTests(TestCase):
    """Test cache type functionality"""

    def setUp(self):
        self.config = get_config()
        self.analytics = AnalyticsTracker(self.config)

    def test_cache_entry_type_choices(self):
        """Test that all cache type choices are properly defined"""
        expected_types = {"time", "cron", "unknown"}
        actual_types = set(CacheEntry.CacheType.values)
        self.assertEqual(actual_types, expected_types)

    def test_cache_entry_type_property_setter(self):
        """Test the type property setter with valid values"""
        entry = CacheEntry(cache_key="test_key", function_name="test_function", timeout=300)
        entry.type = "cron"
        self.assertEqual(entry.cache_type, "cron")

    def test_cache_entry_type_property_setter_invalid(self):
        """Test the type property setter with invalid values"""
        entry = CacheEntry(cache_key="test_key", function_name="test_function", timeout=300)
        with self.assertRaises(ValueError):
            entry.type = "invalid_type"
