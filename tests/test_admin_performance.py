from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from easy_cache.admin import CacheEntryAdmin
from easy_cache.models import CacheEntry
from django.utils import timezone
from datetime import timedelta
import time


class TestAdminPerformance(TestCase):
    def setUp(self):
        # Create test data
        for i in range(100):
            CacheEntry.objects.create(
                cache_key=f"test_key_{i}",
                function_name=f"test_func_{i}",
                hit_count=i,
                miss_count=i // 2,
                expires_at=timezone.now() + timedelta(hours=1),
                timeout=3600,
            )

    def test_admin_list_performance(self):
        """Test that admin list view performs well with many entries"""
        admin = CacheEntryAdmin(CacheEntry, AdminSite())

        start_time = time.time()

        # Simulate admin list view
        queryset = admin.get_queryset(None)
        list(queryset)  # Force evaluation

        end_time = time.time()
        execution_time = end_time - start_time

        # Should complete in under 100ms for 100 entries
        assert execution_time < 0.1, f"Admin list too slow: {execution_time:.3f}s"

    def test_queryset_optimization(self):
        """Test that queryset is optimized with annotations"""
        admin = CacheEntryAdmin(CacheEntry, AdminSite())
        queryset = admin.get_queryset(None)

        # Check that queryset has the time_remaining annotation
        entry = queryset.first()
        assert hasattr(entry, "time_remaining"), "Queryset missing time_remaining annotation"

    def test_expires_at_display_performance(self):
        """Test that expires_at_display method is performant"""
        admin = CacheEntryAdmin(CacheEntry, AdminSite())
        queryset = admin.get_queryset(None)
        entry = queryset.first()

        # Warm up to avoid cold start effects
        admin.expires_at_display(entry)

        start_time = time.perf_counter()

        # Call display method multiple times
        for _ in range(100):
            admin.expires_at_display(entry)

        end_time = time.perf_counter()
        execution_time = end_time - start_time

        # More reasonable threshold - 100ms for 100 calls (1ms per call)
        assert execution_time < 0.1, f"expires_at_display too slow: {execution_time:.3f}s for 100 calls"
