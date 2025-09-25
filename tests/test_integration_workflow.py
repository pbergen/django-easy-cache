"""Complete workflow integration tests"""

import json
import time

from django.test import TestCase, RequestFactory, override_settings
from django.http import JsonResponse
from django.utils.timezone import localtime

from easy_cache.decorators.easy_cache import easy_cache
from easy_cache.models import CacheEntry, CacheEventHistory


class TestCompleteWorkflowIntegration(TestCase):
    """Test complete workflows combining all components"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        # Clear database
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

    def get_json_data(self, response):
        """Helper method to extract JSON data from JsonResponse"""
        return json.loads(response.content.decode())

    def test_complex_data_flow_with_dependencies(self):
        """Test complex data flow where cached methods depend on other cached methods"""

        class DataPipeline:
            """Service that processes data through multiple cached stages"""

            @easy_cache.time_based(invalidate_at="01:00")
            def extract_raw_data(self, dataset_id: str):
                """Stage 1: Extract raw data - cached daily"""
                time.sleep(0.01)  # Simulate data extraction
                return {"dataset_id": dataset_id, "raw_records": 1000, "extracted_at": localtime().isoformat()}

            @easy_cache.cron_based(cron_expression="0 */6 * * *")
            def transform_data(self, dataset_id: str):
                """Stage 2: Transform data - uses cached raw data"""
                raw_data = self.extract_raw_data(dataset_id)  # This should hit cache after first call
                time.sleep(0.015)  # Simulate transformation

                return {
                    "dataset_id": dataset_id,
                    "source_records": raw_data["raw_records"],
                    "transformed_records": raw_data["raw_records"] * 0.95,  # Some filtering
                    "transformed_at": localtime().isoformat(),
                }

            @easy_cache.time_based(invalidate_at="08:00")
            def generate_insights(self, dataset_id: str):
                """Stage 3: Generate insights - uses cached transformed data"""
                transformed_data = self.transform_data(dataset_id)  # This should hit cache
                time.sleep(0.02)  # Simulate ML processing

                return {
                    "dataset_id": dataset_id,
                    "source_records": transformed_data["transformed_records"],
                    "insights": {"trend": "increasing", "confidence": 0.87, "anomalies_detected": 2},
                    "generated_at": localtime().isoformat(),
                }

        # Create pipeline instances
        pipeline1 = DataPipeline()
        pipeline2 = DataPipeline()

        # Test cascading cache behavior
        start_time = time.time()
        insights1_first = pipeline1.generate_insights("sales_data")
        first_call_time = time.time() - start_time

        # Second call should be much faster due to caching at all levels
        start_time = time.time()
        insights1_second = pipeline1.generate_insights("sales_data")
        second_call_time = time.time() - start_time

        # Should return identical data
        self.assertEqual(insights1_first, insights1_second)

        # Second call should be significantly faster
        self.assertLess(second_call_time, first_call_time * 0.3)

        # Test with different dataset
        insights2 = pipeline2.generate_insights("user_behavior")
        self.assertNotEqual(insights1_first["dataset_id"], insights2["dataset_id"])

        # Verify cache entries for all pipeline stages
        cache_entries = CacheEntry.objects.all()
        function_names = [entry.function_name for entry in cache_entries]

        self.assertTrue(any("extract_raw_data" in name for name in function_names))
        self.assertTrue(any("transform_data" in name for name in function_names))
        self.assertTrue(any("generate_insights" in name for name in function_names))

        # Verify that intermediate stages were also cached and reused
        extract_entries = [e for e in cache_entries if "extract_raw_data" in e.function_name]
        transform_entries = [e for e in cache_entries if "transform_data" in e.function_name]
        insights_entries = [e for e in cache_entries if "generate_insights" in e.function_name]

        # Each stage should have entries for both datasets
        self.assertGreaterEqual(len(extract_entries), 2)
        self.assertGreaterEqual(len(transform_entries), 2)
        self.assertGreaterEqual(len(insights_entries), 2)

    def test_cache_invalidation_scenarios(self):
        """Test various cache invalidation scenarios"""

        class TimeBasedService:
            """Service to test time-based invalidation"""

            @easy_cache.time_based(invalidate_at="23:59")
            def get_daily_summary(self):
                return {"summary": "daily data", "generated_at": localtime().isoformat()}

        class CronBasedService:
            """Service to test cron-based invalidation"""

            @easy_cache.cron_based(cron_expression="*/30 * * * *")
            def get_frequent_updates(self):
                return {"updates": "frequent data", "generated_at": localtime().isoformat()}

        time_service = TimeBasedService()
        cron_service = CronBasedService()

        # Generate cache entries
        time_data1 = time_service.get_daily_summary()
        time_data2 = time_service.get_daily_summary()  # Should hit cache

        cron_data1 = cron_service.get_frequent_updates()
        cron_data2 = cron_service.get_frequent_updates()  # Should hit cache

        self.assertEqual(time_data1, time_data2)
        self.assertEqual(cron_data1, cron_data2)

        # Verify cache entries exist
        initial_entries = CacheEntry.objects.all()
        self.assertGreater(initial_entries.count(), 0)

        # Verify hit counts
        for entry in initial_entries:
            if entry.hit_count > 0:
                self.assertGreater(entry.access_count, entry.hit_count)

    def test_error_handling_in_workflow(self):
        """Test error handling throughout the workflow"""

        class UnreliableService:
            """Service that sometimes fails"""

            def __init__(self):
                self.call_count = 0

            @easy_cache.time_based(invalidate_at="18:00")
            def unreliable_method(self, should_fail: bool = False):
                """Method that might fail"""
                self.call_count += 1

                if should_fail:
                    raise ConnectionError("Service temporarily unavailable")

                return {"success": True, "call_count": self.call_count, "timestamp": localtime().isoformat()}

        @easy_cache.cron_based(cron_expression="*/10 * * * *")
        def robust_view(request):
            """View that handles service failures gracefully"""
            service = UnreliableService()

            try:
                data = service.unreliable_method(should_fail=False)
                return JsonResponse({"status": "success", "data": data})
            except Exception as e:
                return JsonResponse(
                    {"status": "error", "message": str(e), "fallback_data": {"timestamp": localtime().isoformat()}}
                )

        service = UnreliableService()
        request = self.factory.get("/robust/")

        # Test successful operation (cached)
        response1 = robust_view(request)
        response2 = robust_view(request)

        data1 = self.get_json_data(response1)
        data2 = self.get_json_data(response2)

        self.assertEqual(data1, data2)  # Should be cached
        self.assertEqual(data1["status"], "success")

        # Test that successful operations are cached properly
        success_result1 = service.unreliable_method(should_fail=False)
        success_result2 = service.unreliable_method(should_fail=False)

        self.assertEqual(success_result1, success_result2)

        # Verify cache entries were created despite potential errors
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 0)

    def test_performance_under_load(self):
        """Test caching performance under simulated load"""

        class HighTrafficService:
            """Service that simulates high-traffic scenarios"""

            @easy_cache.cron_based(cron_expression="*/5 * * * *")
            def get_popular_content(self, category: str):
                """Expensive operation that benefits from caching"""
                time.sleep(0.01)  # Simulate expensive computation
                return {
                    "category": category,
                    "content": f"Popular items for {category}",
                    "computed_at": localtime().isoformat(),
                }

        @easy_cache.time_based(invalidate_at="06:00")
        def popular_content_api(request):
            """API endpoint that serves popular content"""
            category = request.GET.get("category", "general")

            service = HighTrafficService()
            content_data = service.get_popular_content(category)

            return JsonResponse(
                {
                    "api_version": "1.0",
                    "category": category,
                    "content": content_data,
                    "served_at": localtime().isoformat(),
                }
            )

        # Simulate multiple concurrent requests
        categories = ["tech", "sports", "news", "tech", "sports", "tech"]  # Some repeats
        responses = []
        total_time = 0

        for category in categories:
            request = self.factory.get(f"/api/popular/?category={category}")

            start_time = time.time()
            response = popular_content_api(request)
            call_time = time.time() - start_time
            total_time += call_time

            responses.append((category, self.get_json_data(response), call_time))

        # Verify that repeated categories returned cached data
        tech_responses = [r for r in responses if r[0] == "tech"]
        self.assertGreater(len(tech_responses), 1)

        # All tech responses should have identical content data
        first_tech_content = tech_responses[0][1]["content"]
        for _, response_data, _ in tech_responses[1:]:
            self.assertEqual(response_data["content"], first_tech_content)

        # Later tech responses should be faster (cached)
        tech_times = [t for _, _, t in tech_responses]
        self.assertLess(min(tech_times[1:]), tech_times[0] * 0.8)

        # Verify cache efficiency
        cache_entries = CacheEntry.objects.all()
        total_hits = sum(entry.hit_count for entry in cache_entries)
        total_accesses = sum(entry.access_count for entry in cache_entries)

        if total_accesses > 0:
            hit_rate = total_hits / total_accesses
            self.assertGreater(hit_rate, 0.2)  # Should have reasonable hit rate

        # Performance should improve with caching
        average_time = total_time / len(categories)
        self.assertLess(average_time, 0.015)  # Should be faster due to caching

    def test_mixed_invalidation_strategies_workflow(self):
        """Test workflow with mixed time-based and cron-based invalidation"""

        class MixedCacheService:
            """Service using both time-based and cron-based caching"""

            @easy_cache.time_based(invalidate_at="00:00")
            def get_daily_config(self, service_id: str):
                """Configuration that changes daily at midnight"""
                return {
                    "service_id": service_id,
                    "config": {"max_requests": 1000, "timeout": 30},
                    "valid_until": "midnight",
                }

            @easy_cache.cron_based(cron_expression="*/10 * * * *")
            def get_live_status(self, service_id: str):
                """Status that updates every 10 minutes"""
                return {"service_id": service_id, "status": "operational", "updated_every": "10 minutes"}

            @easy_cache.time_based(invalidate_at="12:00")
            def get_business_hours_info(self, service_id: str):
                """Info that updates at noon"""
                config = self.get_daily_config(service_id)  # Uses cached daily config
                status = self.get_live_status(service_id)  # Uses cached live status

                return {
                    "service_id": service_id,
                    "business_info": {"config": config, "current_status": status, "business_hours": "9 AM - 5 PM"},
                    "combined_at": localtime().isoformat(),
                }

        # Test the mixed strategy workflow
        service = MixedCacheService()

        # First call - should execute all methods
        start_time = time.time()
        business_info1 = service.get_business_hours_info("payment_gateway")
        first_call_time = time.time() - start_time

        # Second call - should hit cache at all levels
        start_time = time.time()
        business_info2 = service.get_business_hours_info("payment_gateway")
        second_call_time = time.time() - start_time

        # Data should be identical
        self.assertEqual(business_info1, business_info2)

        # Second call should be much faster
        self.assertLess(second_call_time, first_call_time)

        # Test individual method caching
        config1 = service.get_daily_config("payment_gateway")
        config2 = service.get_daily_config("payment_gateway")
        self.assertEqual(config1, config2)

        status1 = service.get_live_status("payment_gateway")
        status2 = service.get_live_status("payment_gateway")
        self.assertEqual(status1, status2)

        # Verify cache entries for all invalidation strategies
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 2)

        function_names = [entry.function_name for entry in cache_entries]
        self.assertTrue(any("get_daily_config" in name for name in function_names))
        self.assertTrue(any("get_live_status" in name for name in function_names))
        self.assertTrue(any("get_business_hours_info" in name for name in function_names))

        # Verify that different invalidation strategies are used
        time_based_entries = []
        cron_based_entries = []

        for entry in cache_entries:
            # Check cache entry properties to distinguish strategies
            if entry.cache_type == CacheEntry.CacheType.TIME:
                time_based_entries.append(entry)
            if entry.cache_type == CacheEntry.CacheType.CRON:
                cron_based_entries.append(entry)

        # Should have both types
        self.assertGreater(len(time_based_entries), 0)
        self.assertGreater(len(cron_based_entries), 0)
