"""Unit tests for EasyCacheDecorator"""

from django.test import TestCase, override_settings

from easy_cache.decorators.easy_cache import EasyCacheDecorator
from easy_cache.decorators.time import TimeDecorator
from easy_cache.decorators.cron import CronDecorator


class TestEasyCacheDecorator(TestCase):
    """Test cases for EasyCacheDecorator"""

    def test_init_default_values(self):
        """Test initialization with default values"""
        decorator = EasyCacheDecorator()
        self.assertEqual(decorator.key_template, "{function_name}_{args_hash}")
        self.assertEqual(decorator.cache_name, "default")
        self.assertIsNotNone(decorator.cache)

    def test_init_custom_values(self):
        """Test initialization with custom values"""
        decorator = EasyCacheDecorator(key_template="{function_name}_{custom}", cache_backend="custom_cache")
        self.assertEqual(decorator.key_template, "{function_name}_{custom}")
        self.assertEqual(decorator.cache_name, "custom_cache")

    def test_time_based_classmethod_returns_time_decorator(self):
        """Test that time_based classmethod returns TimeDecorator"""
        decorator = EasyCacheDecorator.time_based(invalidate_at="14:30")
        self.assertIsInstance(decorator, TimeDecorator)
        self.assertEqual(decorator.invalidate_at, "14:30")

    def test_time_based_with_timezone(self):
        """Test time_based with custom timezone"""
        decorator = EasyCacheDecorator.time_based(invalidate_at="14:30", timezone_name="Europe/Berlin")
        self.assertIsInstance(decorator, TimeDecorator)
        self.assertEqual(decorator.invalidate_at, "14:30")
        self.assertEqual(decorator.timezone_name, "Europe/Berlin")

    def test_time_based_with_kwargs(self):
        """Test time_based with additional kwargs"""
        decorator = EasyCacheDecorator.time_based(invalidate_at="14:30", cache_backend="test_cache")
        self.assertIsInstance(decorator, TimeDecorator)
        self.assertEqual(decorator.invalidate_at, "14:30")
        self.assertEqual(decorator.cache_name, "test_cache")

    def test_cron_based_classmethod_returns_cron_decorator(self):
        """Test that cron_based classmethod returns CronDecorator"""
        decorator = EasyCacheDecorator.cron_based(cron_expression="*/5 * * * *")
        self.assertIsInstance(decorator, CronDecorator)
        self.assertEqual(decorator.cron_expression, "*/5 * * * *")

    def test_cron_based_with_timezone(self):
        """Test cron_based with custom timezone"""
        decorator = EasyCacheDecorator.cron_based(cron_expression="*/5 * * * *", timezone_name="America/New_York")
        self.assertIsInstance(decorator, CronDecorator)
        self.assertEqual(decorator.cron_expression, "*/5 * * * *")
        self.assertEqual(decorator.timezone_name, "America/New_York")

    def test_cron_based_with_kwargs(self):
        """Test cron_based with additional kwargs"""
        decorator = EasyCacheDecorator.cron_based(cron_expression="*/5 * * * *", cache_backend="custom_cache")
        self.assertIsInstance(decorator, CronDecorator)
        self.assertEqual(decorator.cron_expression, "*/5 * * * *")
        self.assertEqual(decorator.cache_name, "custom_cache")

    def test_global_easy_cache_instance(self):
        """Test that the global easy_cache instance exists"""
        from easy_cache.decorators.easy_cache import easy_cache

        self.assertIsInstance(easy_cache, EasyCacheDecorator)

    def test_global_instance_time_based_usage(self):
        """Test using global instance for time_based decoration"""
        from easy_cache.decorators.easy_cache import easy_cache

        @easy_cache.time_based(invalidate_at="12:00")
        def test_function():
            return "test_result"

        # Should work without errors
        result = test_function()
        self.assertEqual(result, "test_result")

        # Check decorator attributes
        self.assertTrue(hasattr(test_function, "_easy_cache_decorator"))
        self.assertIsInstance(test_function._easy_cache_decorator, TimeDecorator)

    def test_global_instance_cron_based_usage(self):
        """Test using global instance for cron_based decoration"""
        from easy_cache.decorators.easy_cache import easy_cache

        @easy_cache.cron_based(cron_expression="0 */1 * * *")
        def test_function():
            return "test_result"

        # Should work without errors
        result = test_function()
        self.assertEqual(result, "test_result")

        # Check decorator attributes
        self.assertTrue(hasattr(test_function, "_easy_cache_decorator"))
        self.assertIsInstance(test_function._easy_cache_decorator, CronDecorator)

    def test_multiple_decorators_independent(self):
        """Test that multiple decorators work independently"""
        from easy_cache.decorators.easy_cache import easy_cache

        @easy_cache.time_based(invalidate_at="12:00")
        def time_function():
            return "time_result"

        @easy_cache.cron_based(cron_expression="*/5 * * * *")
        def cron_function():
            return "cron_result"

        # Both should work independently
        time_result = time_function()
        cron_result = cron_function()

        self.assertEqual(time_result, "time_result")
        self.assertEqual(cron_result, "cron_result")

        # Check they have different decorator types
        self.assertIsInstance(time_function._easy_cache_decorator, TimeDecorator)
        self.assertIsInstance(cron_function._easy_cache_decorator, CronDecorator)

    def test_decorator_preserves_function_attributes(self):
        """Test that decorators preserve function attributes"""
        from easy_cache.decorators.easy_cache import easy_cache

        @easy_cache.time_based(invalidate_at="12:00")
        def documented_function(x, y=None):
            """A well documented function.

            Args:
                x: First parameter
                y: Second parameter (optional)

            Returns:
                str: A test result
            """
            return f"result_{x}_{y}"

        # Check function attributes are preserved
        self.assertEqual(documented_function.__name__, "documented_function")
        self.assertIn("A well documented function", documented_function.__doc__)

        # Check function works correctly
        result = documented_function(1, y=2)
        self.assertEqual(result, "result_1_2")

    def test_easy_cache_instance_cache_backend_initialization(self):
        """Test cache backend initialization in EasyCacheDecorator"""
        from django.core.cache import caches

        decorator = EasyCacheDecorator(cache_backend="default")

        # Should initialize cache backend
        self.assertIsNotNone(decorator.cache)
        self.assertEqual(decorator.cache, caches["default"])

    @override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            },
            "test_cache": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            },
        }
    )
    def test_easy_cache_custom_cache_backend(self):
        """Test EasyCacheDecorator with custom cache backend"""
        from django.core.cache import caches

        decorator = EasyCacheDecorator(cache_backend="test_cache")

        self.assertEqual(decorator.cache_name, "test_cache")
        self.assertEqual(decorator.cache, caches["test_cache"])

    def test_classmethod_inheritance_pattern(self):
        """Test that classmethods properly create and return decorator instances"""
        # Test that classmethods don't affect the class itself
        original_class = EasyCacheDecorator

        time_decorator = EasyCacheDecorator.time_based(invalidate_at="12:00")
        cron_decorator = EasyCacheDecorator.cron_based(cron_expression="*/5 * * * *")

        # Original class should be unchanged
        self.assertIs(EasyCacheDecorator, original_class)

        # Returned decorators should be different instances
        self.assertIsInstance(time_decorator, TimeDecorator)
        self.assertIsInstance(cron_decorator, CronDecorator)
        self.assertIsNot(time_decorator, cron_decorator)

    def test_parameter_forwarding_to_decorators(self):
        """Test that parameters are properly forwarded to specific decorators"""
        # Test time_based parameter forwarding
        time_decorator = EasyCacheDecorator.time_based(
            invalidate_at="14:30", timezone_name="Europe/London", cache_backend="test_cache"
        )

        self.assertEqual(time_decorator.invalidate_at, "14:30")
        self.assertEqual(time_decorator.timezone_name, "Europe/London")
        self.assertEqual(time_decorator.cache_name, "test_cache")

        # Test cron_based parameter forwarding
        cron_decorator = EasyCacheDecorator.cron_based(
            cron_expression="0 */2 * * *", timezone_name="Asia/Tokyo", cache_backend="redis_cache"
        )

        self.assertEqual(cron_decorator.cron_expression, "0 */2 * * *")
        self.assertEqual(cron_decorator.timezone_name, "Asia/Tokyo")
        self.assertEqual(cron_decorator.cache_name, "redis_cache")

    def test_usage_patterns_from_views(self):
        """Test usage patterns as seen in the views.py file"""
        from easy_cache.decorators.easy_cache import easy_cache

        # Pattern 1: Simple time-based function decorator
        @easy_cache.time_based(invalidate_at="22:40")
        def simple_view():
            return {"message": "test"}

        # Pattern 2: Cron-based function decorator
        @easy_cache.cron_based(cron_expression="*/5 * * * *")
        def cron_view():
            return {"message": "cron_test"}

        # Both should work
        result1 = simple_view()
        result2 = cron_view()

        self.assertEqual(result1["message"], "test")
        self.assertEqual(result2["message"], "cron_test")

        # Verify decorator types
        self.assertIsInstance(simple_view._easy_cache_decorator, TimeDecorator)
        self.assertIsInstance(cron_view._easy_cache_decorator, CronDecorator)
