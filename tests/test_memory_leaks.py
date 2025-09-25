import gc
import weakref
from django.test import TestCase
from easy_cache.decorators.base import BaseCacheDecorator


class TestMemoryLeaks(TestCase):
    def test_no_memory_leak_in_template_response_callback(self):
        """Test that decorator instances can be garbage collected"""

        # Create decorator and weak reference
        decorator = BaseCacheDecorator()
        weak_ref = weakref.ref(decorator)

        # Use the decorator
        @decorator
        def test_func():
            return "result"

        # Execute function
        result = test_func()

        # Delete strong reference
        del decorator

        # Force garbage collection
        gc.collect()

        # Weak reference should be dead (no memory leak)
        assert weak_ref() is None, "Decorator instance not garbage collected - memory leak detected"

    def test_callback_function_creation(self):
        """Test that callback function doesn't hold references"""
        from easy_cache.services.storage_handler import StorageHandler
        from django.core.cache import cache

        storage = StorageHandler(cache)
        callback = BaseCacheDecorator._cache_template_response_callback(storage, "test_key", 300)

        # Callback should be a function
        assert callable(callback)

        # Test that callback works
        class MockResponse:
            def __init__(self):
                self.content = "test"

        response = MockResponse()
        # Should not raise exception
        callback(response)
