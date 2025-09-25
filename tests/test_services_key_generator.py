"""Unit tests for KeyGenerator service"""

from datetime import datetime
from unittest.mock import Mock, patch

from django.test import TestCase
from django.http import HttpRequest

from easy_cache.services.key_generator import KeyGenerator
from easy_cache.exceptions import CacheKeyValidationError


class TestKeyGenerator(TestCase):
    """Test cases for KeyGenerator service"""

    def setUp(self):
        """Set up test fixtures"""
        self.generator = KeyGenerator()

    def test_init_default_prefix(self):
        """Test initialization with default prefix"""
        generator = KeyGenerator()
        self.assertEqual(generator.prefix, "easy_cache")

    def test_init_custom_prefix(self):
        """Test initialization with custom prefix"""
        generator = KeyGenerator(prefix="custom_prefix")
        self.assertEqual(generator.prefix, "custom_prefix")

    def test_generate_key_basic(self):
        """Test basic cache key generation"""

        def test_function(x, y):
            return x + y

        key = self.generator.generate_key(func=test_function, args=(1, 2), kwargs={}, expiration_date=None)

        # Should contain function name and hashed params
        self.assertIn("test_function", key)
        self.assertTrue(key.startswith("easy_cache:"))

        # Verify function name and params are stored
        self.assertIn("test_function", self.generator.function_name)
        self.assertIsNotNone(self.generator.original_params)

    def test_generate_key_with_expiration_date(self):
        """Test cache key generation with expiration date"""

        def test_function():
            return "test"

        expiration = datetime(2025, 9, 15, 14, 30, 0)

        key = self.generator.generate_key(func=test_function, args=(), kwargs={}, expiration_date=expiration)

        # Should contain expiration date in formatted form
        self.assertIn("20250915_143000", key)

    def test_generate_key_with_kwargs(self):
        """Test cache key generation with keyword arguments"""

        def test_function(x, y=None, z=None):
            return x

        key = self.generator.generate_key(func=test_function, args=(1,), kwargs={"y": 2, "z": 3}, expiration_date=None)

        # Should generate consistent key
        self.assertTrue(key.startswith("easy_cache:"))
        self.assertIn("test_function", key)

    def test_generate_key_consistency(self):
        """Test that same inputs generate same key"""

        def test_function(x, y):
            return x + y

        key1 = self.generator.generate_key(func=test_function, args=(1, 2), kwargs={}, expiration_date=None)

        key2 = self.generator.generate_key(func=test_function, args=(1, 2), kwargs={}, expiration_date=None)

        self.assertEqual(key1, key2)

    def test_generate_key_different_args(self):
        """Test that different args generate different keys"""

        def test_function(x, y):
            return x + y

        key1 = self.generator.generate_key(func=test_function, args=(1, 2), kwargs={}, expiration_date=None)

        key2 = self.generator.generate_key(func=test_function, args=(1, 3), kwargs={}, expiration_date=None)

        self.assertNotEqual(key1, key2)

    def test_simple_params_with_allowed_types(self):
        """Test _simple_params with allowed types"""

        def test_function(s, i, f, b, n):
            return s

        params = self.generator._simple_params(func=test_function, args=("string", 42, 3.14, True, None), kwargs={})

        # Should include all allowed types except None
        self.assertIn("string", params)
        self.assertIn("42", params)
        self.assertIn("3.14", params)
        self.assertIn("True", params)

    def test_simple_params_with_method_self_filtering(self):
        """Test _simple_params filters out 'self' parameter for methods"""

        class TestClass:
            def test_method(self, x, y):
                return x + y

        instance = TestClass()

        params = self.generator._simple_params(func=instance.test_method, args=(instance, 1, 2), kwargs={})

        # Should not include 'self' in parameters
        self.assertNotIn("TestClass", params)
        self.assertIn("1", params)
        self.assertIn("2", params)

    def test_simple_params_with_django_model(self):
        """Test _simple_params with Django model objects"""
        # Mock Django model
        mock_model = Mock()
        mock_model.__class__.__name__ = "TestModel"
        mock_model.pk = 123

        def test_function(model):
            return model

        params = self.generator._simple_params(func=test_function, args=(mock_model,), kwargs={})

        # Should include model class name and pk
        self.assertIn("TestModel:123", params)

    def test_simple_params_with_request_object(self):
        """Test _simple_params with Django HttpRequest"""
        request = HttpRequest()
        request.method = "GET"
        request.GET = {"param1": "value1", "param2": "value2"}

        def test_view(request):
            return "response"

        params = self.generator._simple_params(func=test_view, args=(request,), kwargs={})

        # Should include GET parameters
        self.assertIn("param1=value1", params)
        self.assertIn("param2=value2", params)

    def test_simple_params_with_kwargs_filtering(self):
        """Test _simple_params filters out certain kwargs"""

        def test_function(**kwargs):
            return "test"

        params = self.generator._simple_params(
            func=test_function,
            args=(),
            kwargs={
                "request": Mock(),  # Should be filtered out
                "args": (1, 2),  # Should be filtered out
                "kwargs": {},  # Should be filtered out
                "valid_param": "value",  # Should be included
            },
        )

        self.assertNotIn("request", params)
        self.assertNotIn("args", params)
        self.assertNotIn("kwargs", params)
        self.assertIn("valid_param=value", params)

    def test_process_value_none(self):
        """Test _process_value with None"""
        result = self.generator._process_value(None)
        self.assertIsNone(result)

    def test_process_value_string_cleaning(self):
        """Test _process_value cleans strings"""
        test_cases = [
            ("hello world", "hello_world"),
            ("line1\nline2", "line1_line2"),
            ("carriage\rreturn", "carriage_return"),
            ("null\0char", "null_char"),
        ]

        for input_str, expected in test_cases:
            with self.subTest(input_str=input_str):
                result = self.generator._process_value(input_str)
                self.assertEqual(result, expected)

    def test_process_value_long_string_hashing(self):
        """Test _process_value hashes long strings"""
        long_string = "x" * 200  # Longer than MAX_VALUE_LENGTH

        result = self.generator._process_value(long_string)

        # Should be hashed and start with underscore
        self.assertTrue(result.startswith("_"))
        self.assertEqual(len(result), 9)  # 1 underscore + 8 hash chars

    def test_process_value_non_string_types(self):
        """Test _process_value with non-string types"""
        test_cases = [
            (42, "42"),
            (3.14, "3.14"),
            (True, "True"),
            (False, "False"),
        ]

        for input_val, expected in test_cases:
            with self.subTest(input_val=input_val):
                result = self.generator._process_value(input_val)
                self.assertEqual(result, expected)

    def test_validate_cache_key_valid(self):
        """Test cache key validation with valid keys"""
        valid_keys = [
            "easy_cache:simple_key",
            "prefix:function_name_hash123",
            "cache:test_" + "x" * 200,  # Within length limit
        ]

        for key in valid_keys:
            with self.subTest(key=key):
                # Should not raise exception
                self.generator.validate_cache_key(key)

    def test_validate_cache_key_too_long(self):
        """Test cache key validation with too long keys"""
        long_key = "easy_cache:" + "x" * 300  # Exceeds 250 char limit

        with self.assertRaises(CacheKeyValidationError) as cm:
            self.generator.validate_cache_key(long_key)

        self.assertIn("too long", str(cm.exception))

    def test_validate_cache_key_problematic_chars(self):
        """Test cache key validation with problematic characters"""
        problematic_keys = [
            "easy_cache:key\nwith_newline",
            "easy_cache:key\rwith_carriage",
            "easy_cache:key\0with_null",
        ]

        for key in problematic_keys:
            with self.subTest(key=key):
                with self.assertRaises(CacheKeyValidationError) as cm:
                    self.generator.validate_cache_key(key)

                self.assertIn("problematic character", str(cm.exception))

    def test_function_name_generation(self):
        """Test function name generation for different function types"""

        # Regular function
        def regular_function():
            pass

        key1 = self.generator.generate_key(func=regular_function, args=(), kwargs={}, expiration_date=None)

        self.assertIn("regular_function", self.generator.function_name)

        # Method
        class TestClass:
            def test_method(self):
                pass

        instance = TestClass()
        key2 = self.generator.generate_key(func=instance.test_method, args=(instance,), kwargs={}, expiration_date=None)

        self.assertIn("TestClass.test_method", self.generator.function_name)

    def test_hash_consistency(self):
        """Test that parameter hashing is consistent"""

        def test_function(x, y):
            return x + y

        # Generate key twice with same params
        key1 = self.generator.generate_key(func=test_function, args=(1, 2), kwargs={}, expiration_date=None)

        key2 = self.generator.generate_key(func=test_function, args=(1, 2), kwargs={}, expiration_date=None)

        # Should have same hash part
        hash1 = key1.split("_")[-1]
        hash2 = key2.split("_")[-1]
        self.assertEqual(hash1, hash2)

    def test_complex_parameter_handling(self):
        """Test handling of complex parameter combinations"""

        def complex_function(pos1, pos2, kw1=None, kw2=None):
            return "test"

        # Test with mixed positional and keyword args
        key = self.generator.generate_key(
            func=complex_function,
            args=(1, "string"),
            kwargs={"kw1": True, "kw2": 3.14},
            expiration_date=datetime(2025, 9, 15, 12, 0, 0),
        )

        # Should generate valid key
        self.assertTrue(key.startswith("easy_cache:"))
        self.assertIn("complex_function", key)
        self.assertIn("20250915_120000", key)

        # Should not raise validation error
        self.generator.validate_cache_key(key)

    def test_edge_case_empty_params(self):
        """Test edge case with no parameters"""

        def no_params_function():
            return "test"

        key = self.generator.generate_key(func=no_params_function, args=(), kwargs={}, expiration_date=None)

        # Should still generate valid key
        self.assertTrue(key.startswith("easy_cache:"))
        self.assertIn("no_params_function", key)

    @patch("django_easy_cache.services.key_generator.get_config")
    def test_max_value_length_config(self, mock_get_config):
        """Test that MAX_VALUE_LENGTH is respected from config"""
        mock_config = Mock()
        mock_config.get.return_value = 50  # Custom max length
        mock_get_config.return_value = mock_config

        generator = KeyGenerator()

        # Test with string longer than custom max length
        long_string = "x" * 60
        result = generator._process_value(long_string)

        # Should be hashed because it exceeds config limit
        self.assertTrue(result.startswith("_"))
        mock_config.get.assert_called_with("MAX_VALUE_LENGTH")

    def test_repr_fallback_for_unknown_objects(self):
        """Test repr() fallback for unknown object types"""

        class CustomClass:
            def __repr__(self):
                return "CustomClass(value=42)"

        custom_obj = CustomClass()

        def test_function(obj):
            return obj

        params = self.generator._simple_params(func=test_function, args=(custom_obj,), kwargs={})

        # Should include repr() result
        self.assertIn("CustomClass(value=42)", params)
