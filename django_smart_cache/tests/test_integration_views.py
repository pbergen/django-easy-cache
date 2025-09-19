"""Integration tests for decorator usage in Django views"""

import json
import time
from datetime import datetime
from unittest.mock import patch, Mock

from django.test import TestCase, RequestFactory
from django.http import JsonResponse
from django.views.generic import ListView
from django.utils.timezone import localtime

from django_smart_cache.decorators.smart_cache import smart_cache
from django_smart_cache.models import CacheEntry, CacheEventHistory


class TestFunctionBasedViewsIntegration(TestCase):
    """Integration tests for decorator usage in function-based views"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        # Clear database
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

    def get_json_data(self, response):
        """Helper method to extract JSON data from JsonResponse"""
        return json.loads(response.content.decode())

    def test_time_based_function_view_with_jsonresponse(self):
        """Test time-based decorator on function-based view returning JsonResponse"""

        @smart_cache.time_based(invalidate_at="23:59")
        def test_time_view(request):
            """Test view similar to views.py example"""
            time.sleep(0.01)  # Simulate processing time
            current_time = localtime()

            return JsonResponse(
                {
                    "message": "Time-based cache test successful!",
                    "timestamp": current_time.isoformat(),
                    "cache_status": "MISS (first call)",
                    "test": "time_based_function_view",
                }
            )

        # Create request
        request = self.factory.get("/test/")

        # First call - should be cache miss
        start_time = time.time()
        response1 = test_time_view(request)
        first_call_time = time.time() - start_time

        self.assertIsInstance(response1, JsonResponse)
        self.assertEqual(response1.status_code, 200)

        # Parse JSON response
        response1_data = self.get_json_data(response1)
        self.assertEqual(response1_data["message"], "Time-based cache test successful!")
        self.assertEqual(response1_data["test"], "time_based_function_view")

        # Second call - should be cache hit (faster)
        start_time = time.time()
        response2 = test_time_view(request)
        second_call_time = time.time() - start_time

        self.assertIsInstance(response2, JsonResponse)
        self.assertEqual(response2.status_code, 200)

        # Should return same JSON data (cached)
        response2_data = self.get_json_data(response2)
        self.assertEqual(response1_data, response2_data)

        # Second call should be significantly faster
        self.assertLess(second_call_time, first_call_time)

        # Verify cache entry was created
        cache_entries = CacheEntry.objects.all()
        self.assertEqual(cache_entries.count(), 1)

        cache_entry = cache_entries.first()
        self.assertIn("test_time_view", cache_entry.function_name)
        self.assertGreater(cache_entry.hit_count, 0)

    def test_cron_based_function_view_with_jsonresponse(self):
        """Test cron-based decorator on function-based view returning JsonResponse"""

        @smart_cache.cron_based(cron_expression="*/5 * * * *")
        def test_cron_view(request):
            """Test view similar to views.py example"""
            time.sleep(0.01)  # Simulate processing time
            current_time = localtime()

            return JsonResponse(
                {
                    "message": "Cron-based cache test successful!",
                    "timestamp": current_time.isoformat(),
                    "cache_status": "MISS (first call)",
                    "test": "cron_based_function_view",
                }
            )

        # Create request
        request = self.factory.get("/test/")

        # First call - should be cache miss
        response1 = test_cron_view(request)
        self.assertIsInstance(response1, JsonResponse)

        response1_data = self.get_json_data(response1)
        self.assertEqual(response1_data["message"], "Cron-based cache test successful!")

        # Second call - should be cache hit
        response2 = test_cron_view(request)
        response2_data = self.get_json_data(response2)

        # Should return same cached data
        self.assertEqual(response1_data, response2_data)

        # Verify cache entry was created
        cache_entries = CacheEntry.objects.all()
        self.assertEqual(cache_entries.count(), 1)

        cache_entry = cache_entries.first()
        self.assertIn("test_cron_view", cache_entry.function_name)

    def test_function_view_with_request_parameters(self):
        """Test decorator behavior with request parameters"""

        @smart_cache.time_based(invalidate_at="22:00")
        def parameterized_view(request):
            """View that uses request parameters in response"""
            user_id = request.GET.get("user_id", "anonymous")
            page = request.GET.get("page", "1")

            return JsonResponse(
                {
                    "user_id": user_id,
                    "page": page,
                    "message": f"Data for user {user_id}, page {page}",
                    "timestamp": localtime().isoformat(),
                }
            )

        # Test with different parameters
        request1 = self.factory.get("/test/?user_id=123&page=1")
        request2 = self.factory.get("/test/?user_id=123&page=1")  # Same params
        request3 = self.factory.get("/test/?user_id=456&page=2")  # Different params

        # First call with specific params
        response1 = parameterized_view(request1)
        response1_data = self.get_json_data(response1)

        # Second call with same params - should hit cache
        response2 = parameterized_view(request2)
        response2_data = self.get_json_data(response2)

        # Should return same data (cached)
        self.assertEqual(response1_data, response2_data)

        # Third call with different params - should miss cache
        response3 = parameterized_view(request3)
        response3_data = self.get_json_data(response3)

        # Should return different data
        self.assertNotEqual(response1_data, response3_data)
        self.assertEqual(response3_data["user_id"], "456")
        self.assertEqual(response3_data["page"], "2")

        # Should have multiple cache entries for different parameter combinations
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 1)

    def test_function_view_error_handling(self):
        """Test decorator behavior when view raises exception"""

        @smart_cache.time_based(invalidate_at="20:00")
        def error_view(request):
            """View that raises an exception"""
            should_error = request.GET.get("error", "false") == "true"

            if should_error:
                raise ValueError("Test error")

            return JsonResponse({"success": True})

        # Normal request should work and be cached
        normal_request = self.factory.get("/test/?error=false")
        response1 = error_view(normal_request)
        self.assertEqual(response1.status_code, 200)

        response2 = error_view(normal_request)
        self.assertEqual(self.get_json_data(response1), self.get_json_data(response2))

        # Error request should raise exception (not cached)
        error_request = self.factory.get("/test/?error=true")

        with self.assertRaises(ValueError):
            error_view(error_request)

        # Normal request should still work from cache
        response3 = error_view(normal_request)
        self.assertEqual(self.get_json_data(response1), self.get_json_data(response3))

    def test_multiple_decorated_views(self):
        """Test multiple views with different decorators"""

        @smart_cache.time_based(invalidate_at="12:00")
        def daily_report_view(request):
            return JsonResponse({"report": "daily", "generated_at": localtime().isoformat()})

        @smart_cache.cron_based(cron_expression="0 */1 * * *")
        def hourly_stats_view(request):
            return JsonResponse({"stats": "hourly", "generated_at": localtime().isoformat()})

        @smart_cache.time_based(invalidate_at="00:00")
        def midnight_view(request):
            return JsonResponse({"reset": "midnight", "generated_at": localtime().isoformat()})

        request = self.factory.get("/test/")

        # Call all views
        daily_response = daily_report_view(request)
        hourly_response = hourly_stats_view(request)
        midnight_response = midnight_view(request)

        # All should return JSON responses
        self.assertIsInstance(daily_response, JsonResponse)
        self.assertIsInstance(hourly_response, JsonResponse)
        self.assertIsInstance(midnight_response, JsonResponse)

        # Parse responses
        daily_data = self.get_json_data(daily_response)
        hourly_data = self.get_json_data(hourly_response)
        midnight_data = self.get_json_data(midnight_response)

        self.assertEqual(daily_data["report"], "daily")
        self.assertEqual(hourly_data["stats"], "hourly")
        self.assertEqual(midnight_data["reset"], "midnight")

        # Should have separate cache entries
        cache_entries = CacheEntry.objects.all()
        self.assertEqual(cache_entries.count(), 3)

        # Check function names are different
        function_names = [entry.function_name for entry in cache_entries]
        self.assertIn("daily_report_view", str(function_names))
        self.assertIn("hourly_stats_view", str(function_names))
        self.assertIn("midnight_view", str(function_names))

    def test_view_with_complex_json_response(self):
        """Test decorator with complex JSON response data"""

        @smart_cache.cron_based(cron_expression="*/10 * * * *")
        def complex_data_view(request):
            """View that returns complex nested data"""
            return JsonResponse(
                {
                    "metadata": {"generated_at": localtime().isoformat(), "version": "1.0", "cache_enabled": True},
                    "data": {
                        "users": [
                            {"id": 1, "name": "User 1", "active": True},
                            {"id": 2, "name": "User 2", "active": False},
                        ],
                        "statistics": {"total_users": 2, "active_users": 1, "growth_rate": 15.7},
                    },
                    "pagination": {"page": 1, "per_page": 10, "total_pages": 1, "has_next": False},
                }
            )

        request = self.factory.get("/test/")

        # First call
        response1 = complex_data_view(request)
        data1 = self.get_json_data(response1)

        # Second call - should return exact same complex data
        response2 = complex_data_view(request)
        data2 = self.get_json_data(response2)

        self.assertEqual(data1, data2)

        # Verify complex nested structure is preserved
        self.assertEqual(data1["metadata"]["version"], "1.0")
        self.assertEqual(len(data1["data"]["users"]), 2)
        self.assertEqual(data1["data"]["statistics"]["total_users"], 2)
        self.assertEqual(data1["pagination"]["page"], 1)

        # Verify caching worked
        cache_entry = CacheEntry.objects.first()
        self.assertIsNotNone(cache_entry)
        self.assertGreater(cache_entry.hit_count, 0)


class TestClassBasedViewsIntegration(TestCase):
    """Integration tests for decorator usage in class-based views"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        # Clear database
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

    def get_json_data(self, response):
        """Helper method to extract JSON data from JsonResponse"""
        return json.loads(response.content.decode())

    def test_listview_with_time_based_decorator(self):
        """Test time-based decorator on ListView get method"""

        class TestListView(ListView):
            """Test ListView similar to views.py example"""

            template_name = "test.html"
            context_object_name = "items"

            @smart_cache.time_based(invalidate_at="11:30")
            def get(self, request, *args, **kwargs):
                # Simulate ListView behavior but return JsonResponse for testing
                context = {
                    "items": [
                        {"id": 1, "name": "Item 1"},
                        {"id": 2, "name": "Item 2"},
                    ],
                    "generated_at": localtime().isoformat(),
                    "view_type": "ListView",
                }
                return JsonResponse(context)

        view = TestListView()
        request = self.factory.get("/test/")

        # First call
        response1 = view.get(request)
        self.assertIsInstance(response1, JsonResponse)
        data1 = self.get_json_data(response1)

        # Second call - should be cached
        response2 = view.get(request)
        data2 = self.get_json_data(response2)

        # Should return same data
        self.assertEqual(data1, data2)
        self.assertEqual(data1["view_type"], "ListView")
        self.assertEqual(len(data1["items"]), 2)

        # Verify cache entry
        cache_entry = CacheEntry.objects.first()
        self.assertIsNotNone(cache_entry)
        self.assertIn("get", cache_entry.function_name)

    def test_custom_view_with_cron_decorator(self):
        """Test custom view class with cron-based decorator"""

        class CustomView:
            """Custom view class with cached method"""

            @smart_cache.cron_based(cron_expression="*/15 * * * *")
            def dispatch(self, request, *args, **kwargs):
                """Custom dispatch method with caching"""
                return JsonResponse(
                    {
                        "custom_view": True,
                        "method": request.method,
                        "path": request.path,
                        "processed_at": localtime().isoformat(),
                    }
                )

        view = CustomView()
        request = self.factory.get("/custom/")

        # Test caching behavior
        response1 = view.dispatch(request)
        response2 = view.dispatch(request)

        data1 = self.get_json_data(response1)
        data2 = self.get_json_data(response2)

        self.assertEqual(data1, data2)
        self.assertTrue(data1["custom_view"])
        self.assertEqual(data1["method"], "GET")

    def test_view_with_method_arguments(self):
        """Test view method with additional arguments"""

        class ParameterizedView:
            """View with method that takes additional parameters"""

            @smart_cache.time_based(invalidate_at="14:00")
            def get_data(self, request, category, item_id=None):
                """Method with positional and keyword arguments"""
                return JsonResponse(
                    {"category": category, "item_id": item_id, "request_path": request.path, "method": "get_data"}
                )

        view = ParameterizedView()
        request = self.factory.get("/test/electronics/123/")

        # Test with different parameter combinations
        response1 = view.get_data(request, "electronics", item_id=123)
        response2 = view.get_data(request, "electronics", item_id=123)  # Same params
        response3 = view.get_data(request, "books", item_id=456)  # Different params

        data1 = self.get_json_data(response1)
        data2 = self.get_json_data(response2)
        data3 = self.get_json_data(response3)

        # Same params should return cached data
        self.assertEqual(data1, data2)

        # Different params should return different data
        self.assertNotEqual(data1, data3)
        self.assertEqual(data3["category"], "books")
        self.assertEqual(data3["item_id"], 456)

        # Should have multiple cache entries
        cache_entries = CacheEntry.objects.all()
        self.assertGreater(cache_entries.count(), 1)

    def test_inheritance_with_decorated_methods(self):
        """Test decorator behavior with class inheritance"""

        class BaseView:
            """Base view class"""

            @smart_cache.time_based(invalidate_at="09:00")
            def get_base_data(self, request):
                return JsonResponse({"type": "base", "timestamp": localtime().isoformat()})

        class ChildView(BaseView):
            """Child view inheriting from BaseView"""

            @smart_cache.cron_based(cron_expression="0 */2 * * *")
            def get_child_data(self, request):
                return JsonResponse({"type": "child", "timestamp": localtime().isoformat()})

        base_view = BaseView()
        child_view = ChildView()
        request = self.factory.get("/test/")

        # Test base method caching
        base_response1 = base_view.get_base_data(request)
        base_response2 = base_view.get_base_data(request)

        self.assertEqual(self.get_json_data(base_response1), self.get_json_data(base_response2))

        # Test child method caching
        child_response1 = child_view.get_child_data(request)
        child_response2 = child_view.get_child_data(request)

        self.assertEqual(self.get_json_data(child_response1), self.get_json_data(child_response2))

        # Test inherited method caching
        inherited_response1 = child_view.get_base_data(request)
        inherited_response2 = child_view.get_base_data(request)

        self.assertEqual(self.get_json_data(inherited_response1), self.get_json_data(inherited_response2))

        # Should have separate cache entries for each method
        cache_entries = CacheEntry.objects.all()
        self.assertEqual(cache_entries.count(), 3)  # base, child, inherited

        # Verify function names are tracked correctly
        function_names = [entry.function_name for entry in cache_entries]
        self.assertTrue(any("get_base_data" in name for name in function_names))
        self.assertTrue(any("get_child_data" in name for name in function_names))


class TestViewIntegrationEdgeCases(TestCase):
    """Test edge cases for view integration"""

    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        CacheEntry.objects.all().delete()
        CacheEventHistory.objects.all().delete()

    def get_json_data(self, response):
        """Helper method to extract JSON data from JsonResponse"""
        return json.loads(response.content.decode())

    def test_view_with_post_request(self):
        """Test decorator behavior with POST requests"""

        @smart_cache.time_based(invalidate_at="16:00")
        def post_view(request):
            """View that handles POST requests"""
            if request.method == "POST":
                data = {"received": "POST data", "method": "POST"}
            else:
                data = {"received": "GET data", "method": "GET"}

            data["timestamp"] = localtime().isoformat()
            return JsonResponse(data)

        # Test GET request
        get_request = self.factory.get("/test/")
        get_response1 = post_view(get_request)
        get_response2 = post_view(get_request)

        self.assertEqual(self.get_json_data(get_response1), self.get_json_data(get_response2))

        # Test POST request
        post_request = self.factory.post("/test/", {"data": "test"})
        post_response1 = post_view(post_request)
        post_response2 = post_view(post_request)

        self.assertEqual(self.get_json_data(post_response1), self.get_json_data(post_response2))
        self.assertEqual(self.get_json_data(post_response1)["method"], "POST")

        # GET and POST should have different cache entries
        self.assertNotEqual(self.get_json_data(get_response1), self.get_json_data(post_response1))

    def test_view_with_middleware_simulation(self):
        """Test decorator behavior with simulated middleware"""

        @smart_cache.cron_based(cron_expression="*/20 * * * *")
        def middleware_view(request):
            """View that simulates middleware processing"""
            # Simulate middleware adding attributes
            user_agent = getattr(request, "META", {}).get("HTTP_USER_AGENT", "unknown")

            return JsonResponse({"user_agent": user_agent, "has_user": hasattr(request, "user"), "processed": True})

        # Create request with META data
        request = self.factory.get("/test/")
        request.META["HTTP_USER_AGENT"] = "Test Browser"

        response1 = middleware_view(request)
        response2 = middleware_view(request)

        data1 = self.get_json_data(response1)
        data2 = self.get_json_data(response2)

        self.assertEqual(data1, data2)
        self.assertEqual(data1["user_agent"], "Test Browser")

    def test_concurrent_view_calls(self):
        """Test decorator behavior with concurrent-like calls"""

        @smart_cache.time_based(invalidate_at="18:00")
        def concurrent_view(request):
            """View that might be called concurrently"""
            # Simulate some processing time
            time.sleep(0.001)
            return JsonResponse({"call_time": time.time(), "data": "concurrent test"})

        request = self.factory.get("/test/")

        # Make multiple rapid calls
        responses = []
        for _ in range(5):
            response = concurrent_view(request)
            responses.append(self.get_json_data(response))

        # All responses should be identical (cached after first)
        first_response = responses[0]
        for response in responses[1:]:
            self.assertEqual(first_response, response)

        # Verify only one cache entry was created
        cache_entries = CacheEntry.objects.all()
        self.assertEqual(cache_entries.count(), 1)

        cache_entry = cache_entries.first()
        self.assertGreaterEqual(cache_entry.hit_count, 4)  # First was miss, rest hits
