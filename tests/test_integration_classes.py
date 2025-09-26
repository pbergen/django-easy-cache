"""Integration tests for decorator usage in regular class methods"""

import time

from django.test import TestCase
from django.utils.timezone import localtime

from easy_cache.decorators.easy_cache import easy_cache
from easy_cache.models import CacheEntry, CacheEventHistory


class TestClassMethodIntegration(TestCase):
    """Integration tests for decorator usage in regular class methods"""

    def setUp(self):
        """Set up test fixtures"""
        # Clear database
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

    def test_dataprocessor_like_class_integration(self):
        """Test decorator usage in DataProcessor-like class similar to views.py"""

        class DataProcessor:
            """Test class similar to views.py DataProcessor"""

            def __init__(self, user_id: int):
                self.user_id = user_id

            @easy_cache.time_based(invalidate_at="02:00")
            def get_user_stats(self):
                """User statistics with daily invalidation at 2 AM"""
                time.sleep(0.01)  # Simulate DB query
                return {
                    "user_id": self.user_id,
                    "stats": {"views": 1234, "clicks": 567},
                    "calculated_at": localtime().isoformat(),
                }

            @easy_cache.cron_based(cron_expression="*/1 * * * *")
            def get_live_metrics(self, metric_type: str):
                """Live metrics updated every minute"""
                time.sleep(0.02)  # Simulate API call
                return {
                    "user_id": self.user_id,
                    "metric_type": metric_type,
                    "value": time.time(),
                    "updated_at": localtime().isoformat(),
                }

            @easy_cache.time_based(invalidate_at="00:00")
            def generate_daily_report(self, date_str: str):
                """Daily report - invalidated at midnight"""
                time.sleep(0.03)  # Simulate heavy computation
                return {
                    "user_id": self.user_id,
                    "date": date_str,
                    "report_data": f"Report for {date_str}",
                    "generated_at": localtime().isoformat(),
                }

            def get_user_stats_simple(self):
                """Simple method WITHOUT cache decorator for comparison"""
                time.sleep(0.01)
                return {
                    "user_id": self.user_id,
                    "stats": {"views": 1234, "clicks": 567},
                    "calculated_at": localtime().isoformat(),
                }

        # Test with user ID 1
        processor = DataProcessor(user_id=1)

        # Test get_user_stats caching
        start_time = time.time()
        stats1 = processor.get_user_stats()
        first_call_time = time.time() - start_time

        start_time = time.time()
        stats2 = processor.get_user_stats()
        second_call_time = time.time() - start_time

        # Should return same data (cached)
        self.assertEqual(stats1, stats2)
        self.assertEqual(stats1["user_id"], 1)
        self.assertIn("calculated_at", stats1)

        # Second call should be faster
        self.assertLess(second_call_time, first_call_time)

        # Test get_live_metrics with parameters
        metrics1 = processor.get_live_metrics("page_views")
        metrics2 = processor.get_live_metrics("page_views")  # Same params
        metrics3 = processor.get_live_metrics("clicks")  # Different params

        # Same params should return cached data
        self.assertEqual(metrics1, metrics2)
        self.assertEqual(metrics1["metric_type"], "page_views")

        # Different params should return different data
        self.assertNotEqual(metrics1, metrics3)
        self.assertEqual(metrics3["metric_type"], "clicks")

        # Test generate_daily_report
        report1 = processor.generate_daily_report("2025-09-15")
        report2 = processor.generate_daily_report("2025-09-15")  # Same date
        report3 = processor.generate_daily_report("2025-09-16")  # Different date

        # Same date should return cached data
        self.assertEqual(report1, report2)
        self.assertEqual(report1["date"], "2025-09-15")

        # Different date should return different data
        self.assertNotEqual(report1, report3)
        self.assertEqual(report3["date"], "2025-09-16")

        # Verify cache entries were created for different methods
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 3)  # At least 3 different method calls

        # Check that different methods have separate cache entries
        function_names = [entry.function_name for entry in cache_entries]
        self.assertTrue(any("get_user_stats" in name for name in function_names))
        self.assertTrue(any("get_live_metrics" in name for name in function_names))
        self.assertTrue(any("generate_daily_report" in name for name in function_names))

    def test_multiple_instances_same_class(self):
        """Test caching behavior with multiple instances of the same class"""

        class UserProcessor:
            """Test class for multiple instances"""

            @easy_cache.time_based(invalidate_at="10:00")
            def get_profile(self, user_id: int):
                """Get user profile data"""
                return {
                    "user_id": user_id,
                    "profile": f"Profile for user {user_id}",
                    "loaded_at": localtime().isoformat(),
                }

        # Create multiple instances
        processor1 = UserProcessor()
        processor2 = UserProcessor()
        processor3 = UserProcessor()  # Same user_id as processor1

        # Get profiles
        profile1_a = processor1.get_profile(user_id=1)
        profile2_a = processor2.get_profile(user_id=2)
        profile3_a = processor3.get_profile(user_id=1)  # Different instance, same user_id

        # Second calls should hit cache
        profile1_b = processor1.get_profile(user_id=1)
        profile2_b = processor2.get_profile(user_id=2)
        profile3_b = processor3.get_profile(user_id=1)

        # Same instance calls should return same data
        self.assertEqual(profile1_a, profile1_b)
        self.assertEqual(profile2_a, profile2_b)
        self.assertEqual(profile3_a, profile3_b)

        # Different user_ids should return different data
        self.assertNotEqual(profile1_a, profile2_a)
        self.assertEqual(profile1_a["user_id"], 1)
        self.assertEqual(profile2_a["user_id"], 2)

        # Different instances with same parameters should return same cached data
        # because caching is based on method and parameters, not instance identity
        self.assertEqual(profile1_a, profile3_a)

        # Verify cache entries
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 1)  # At least 2 different parameter sets

    def test_class_method_with_complex_parameters(self):
        """Test class method caching with complex parameter types"""

        class AnalyticsProcessor:
            """Test class with complex parameters"""

            def __init__(self, service_name: str):
                self.service_name = service_name

            @easy_cache.cron_based(cron_expression="*/5 * * * *")
            def analyze_data(self, data_type: str, filters: dict = None, options: list = None):
                """Method with complex parameters"""
                filters = filters or {}
                options = options or []

                return {
                    "service": self.service_name,
                    "data_type": data_type,
                    "filters": filters,
                    "options": options,
                    "result": f"Analysis for {data_type}",
                    "processed_at": localtime().isoformat(),
                }

        processor = AnalyticsProcessor("test_service")

        # Test with different parameter combinations
        result1 = processor.analyze_data("users", {"active": True}, ["sort_by_date"])
        result2 = processor.analyze_data("users", {"active": True}, ["sort_by_date"])  # Same
        result3 = processor.analyze_data("users", {"active": False}, ["sort_by_date"])  # Different filter
        result4 = processor.analyze_data("orders", {"active": True}, ["sort_by_date"])  # Different type

        # Same parameters should return cached data
        self.assertEqual(result1, result2)

        # Different parameters should return different data
        self.assertNotEqual(result1, result3)
        self.assertNotEqual(result1, result4)

        self.assertEqual(result1["data_type"], "users")
        self.assertEqual(result1["filters"]["active"], True)
        self.assertEqual(result3["filters"]["active"], False)
        self.assertEqual(result4["data_type"], "orders")

    def test_inheritance_with_cached_methods(self):
        """Test caching behavior with class inheritance"""

        class BaseProcessor:
            """Base class with cached method"""

            @easy_cache.time_based(invalidate_at="15:00")
            def get_base_data(self, base_id: int):
                """Base method with caching"""
                return {
                    "base_id": base_id,
                    "type": "base",
                    "data": "base_data",
                    "timestamp": localtime().isoformat(),
                }

        class ExtendedProcessor(BaseProcessor):
            """Extended class with additional cached method"""

            @easy_cache.cron_based(cron_expression="*/2 * * * *")
            def get_extended_data(self, base_id: int, extended_id: int):
                """Extended method with caching"""
                return {
                    "base_id": base_id,
                    "extended_id": extended_id,
                    "type": "extended",
                    "data": "extended_data",
                    "timestamp": localtime().isoformat(),
                }

        # Test base class
        base_proc = BaseProcessor()
        base_data1 = base_proc.get_base_data(base_id=1)
        base_data2 = base_proc.get_base_data(base_id=1)

        self.assertEqual(base_data1, base_data2)
        self.assertEqual(base_data1["type"], "base")

        # Test extended class
        ext_proc = ExtendedProcessor()

        # Test inherited method
        inherited_data1 = ext_proc.get_base_data(base_id=2)
        inherited_data2 = ext_proc.get_base_data(base_id=2)

        self.assertEqual(inherited_data1, inherited_data2)
        self.assertEqual(inherited_data1["base_id"], 2)

        # Test extended method
        extended_data1 = ext_proc.get_extended_data(base_id=2, extended_id=20)
        extended_data2 = ext_proc.get_extended_data(base_id=2, extended_id=20)

        self.assertEqual(extended_data1, extended_data2)
        self.assertEqual(extended_data1["extended_id"], 20)

        # Different instances should have different cached data
        self.assertNotEqual(base_data1, inherited_data1)

        # Verify separate cache entries
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 2)

        function_names = [entry.function_name for entry in cache_entries]
        self.assertTrue(any("get_base_data" in name for name in function_names))
        self.assertTrue(any("get_extended_data" in name for name in function_names))

    def test_method_caching_with_side_effects(self):
        """Test that caching works correctly with methods that have side effects"""

        class CounterProcessor:
            """Test class with side effects"""

            def __init__(self):
                self.call_count = 0
                self.side_effect_count = 0

            @easy_cache.time_based(invalidate_at="20:00")
            def get_data_with_side_effects(self, data_id: int):
                """Method that has side effects (should only execute once when cached)"""
                self.call_count += 1
                self.side_effect_count += 1

                return {
                    "data_id": data_id,
                    "call_count": self.call_count,
                    "side_effect_count": self.side_effect_count,
                    "timestamp": localtime().isoformat(),
                }

        processor = CounterProcessor()

        # First call - should execute method
        result1 = processor.get_data_with_side_effects(1)
        self.assertEqual(processor.call_count, 1)
        self.assertEqual(processor.side_effect_count, 1)
        self.assertEqual(result1["call_count"], 1)

        # Second call with same parameters - should return cached result
        result2 = processor.get_data_with_side_effects(1)
        self.assertEqual(processor.call_count, 1)  # Should not increment
        self.assertEqual(processor.side_effect_count, 1)  # Should not increment
        self.assertEqual(result1, result2)  # Should return exact same data

        # Third call with different parameters - should execute method again
        result3 = processor.get_data_with_side_effects(2)
        self.assertEqual(processor.call_count, 2)  # Should increment
        self.assertEqual(processor.side_effect_count, 2)  # Should increment
        self.assertEqual(result3["call_count"], 2)
        self.assertNotEqual(result1, result3)

    def test_class_method_error_handling(self):
        """Test error handling in cached class methods"""

        class ErrorProcessor:
            """Test class with methods that can raise errors"""

            def __init__(self):
                self.success_calls = 0

            @easy_cache.cron_based(cron_expression="*/3 * * * *")
            def risky_operation(self, should_fail: bool = False):
                """Method that might raise an exception"""
                if should_fail:
                    raise ValueError("Simulated error")

                self.success_calls += 1
                return {"success": True, "call_number": self.success_calls, "timestamp": localtime().isoformat()}

        processor = ErrorProcessor()

        # Successful operation should be cached
        result1 = processor.risky_operation(should_fail=False)
        result2 = processor.risky_operation(should_fail=False)

        self.assertEqual(result1, result2)
        self.assertEqual(processor.success_calls, 1)  # Only called once due to caching

        # Failed operation should raise exception (not cached)
        with self.assertRaises(ValueError):
            processor.risky_operation(should_fail=True)

        # Successful operation should still return cached result
        result3 = processor.risky_operation(should_fail=False)
        self.assertEqual(result1, result3)
        self.assertEqual(processor.success_calls, 1)  # Still only called once

    def test_performance_comparison_cached_vs_uncached(self):
        """Test performance difference between cached and uncached methods"""

        class PerformanceTestProcessor:
            """Test class for performance comparison"""

            @easy_cache.time_based(invalidate_at="23:00")
            def slow_cached_method(self, work_amount: int):
                """Cached method that simulates slow work"""
                time.sleep(0.01 * work_amount)  # Simulate work
                return {
                    "work_amount": work_amount,
                    "result": f"Processed {work_amount} units",
                    "timestamp": localtime().isoformat(),
                }

            def slow_uncached_method(self, work_amount: int):
                """Uncached method that simulates slow work"""
                time.sleep(0.01 * work_amount)  # Simulate work
                return {
                    "work_amount": work_amount,
                    "result": f"Processed {work_amount} units",
                    "timestamp": localtime().isoformat(),
                }

        processor = PerformanceTestProcessor()

        # Test cached method performance
        start_time = time.time()
        cached_result1 = processor.slow_cached_method(5)  # First call (miss)
        first_cached_time = time.time() - start_time

        start_time = time.time()
        cached_result2 = processor.slow_cached_method(5)  # Second call (hit)
        second_cached_time = time.time() - start_time

        # Test uncached method performance
        start_time = time.time()
        uncached_result1 = processor.slow_uncached_method(5)  # Always slow
        first_uncached_time = time.time() - start_time

        start_time = time.time()
        uncached_result2 = processor.slow_uncached_method(5)  # Always slow
        second_uncached_time = time.time() - start_time

        # Cached method should return same result
        self.assertEqual(cached_result1["work_amount"], cached_result2["work_amount"])
        self.assertEqual(cached_result1["timestamp"], cached_result2["timestamp"])  # Same timestamp due to caching

        # Uncached method should have different timestamps
        self.assertNotEqual(uncached_result1["timestamp"], uncached_result2["timestamp"])

        # Second cached call should be much faster than first
        self.assertLess(second_cached_time, first_cached_time * 0.5)  # At least 50% faster

        # Uncached calls should take similar time
        self.assertAlmostEqual(first_uncached_time, second_uncached_time, delta=0.01)

        # Second cached call should be faster than uncached calls
        self.assertLess(second_cached_time, first_uncached_time * 0.5)
        self.assertLess(second_cached_time, second_uncached_time * 0.5)

    def test_class_methods_with_different_invalidation_strategies(self):
        """Test class with multiple methods using different invalidation strategies"""

        class MixedStrategyProcessor:
            """Test class with different caching strategies"""

            def __init__(self, processor_id: int):
                self.processor_id = processor_id

            @easy_cache.time_based(invalidate_at="06:00")
            def get_morning_report(self):
                """Report updated every morning at 6 AM"""
                return {
                    "processor_id": self.processor_id,
                    "report_type": "morning",
                    "generated_at": localtime().isoformat(),
                }

            @easy_cache.cron_based(cron_expression="0 */4 * * *")
            def get_quarterly_stats(self):
                """Stats updated every 4 hours"""
                return {
                    "processor_id": self.processor_id,
                    "stats_type": "quarterly",
                    "generated_at": localtime().isoformat(),
                }

            @easy_cache.time_based(invalidate_at="00:00")
            def get_daily_summary(self, include_details: bool = False):
                """Summary updated daily at midnight"""
                return {
                    "processor_id": self.processor_id,
                    "summary_type": "daily",
                    "include_details": include_details,
                    "generated_at": localtime().isoformat(),
                }

        processor = MixedStrategyProcessor(processor_id=42)

        # Test all methods
        morning1 = processor.get_morning_report()
        morning2 = processor.get_morning_report()

        quarterly1 = processor.get_quarterly_stats()
        quarterly2 = processor.get_quarterly_stats()

        summary1 = processor.get_daily_summary(include_details=True)
        summary2 = processor.get_daily_summary(include_details=True)
        summary3 = processor.get_daily_summary(include_details=False)

        # All cached calls should return same data
        self.assertEqual(morning1, morning2)
        self.assertEqual(quarterly1, quarterly2)
        self.assertEqual(summary1, summary2)

        # Different parameters should return different data
        self.assertNotEqual(summary1, summary3)

        # All methods should have different results
        self.assertNotEqual(morning1, quarterly1)
        self.assertNotEqual(morning1, summary1)
        self.assertNotEqual(quarterly1, summary1)

        # Verify all methods have correct processor_id
        self.assertEqual(morning1["processor_id"], 42)
        self.assertEqual(quarterly1["processor_id"], 42)
        self.assertEqual(summary1["processor_id"], 42)

        # Verify cache entries for different strategies
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 3)  # At least 4 different cached calls

        # Check that all methods are represented
        function_names = [entry.function_name for entry in cache_entries]
        self.assertTrue(any("get_morning_report" in name for name in function_names))
        self.assertTrue(any("get_quarterly_stats" in name for name in function_names))
        self.assertTrue(any("get_daily_summary" in name for name in function_names))
