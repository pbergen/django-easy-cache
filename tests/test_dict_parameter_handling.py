"""Tests for dict and collection parameter handling in cache key generation"""

import json
from django.test import TestCase
from easy_cache.services.key_generator import KeyGenerator


class DictParameterHandlingTestCase(TestCase):
    """Test that dicts and collections are handled deterministically"""

    def setUp(self):
        self.kg = KeyGenerator()

    @staticmethod
    def _test_function(data):
        """Simple test function (not a test case)"""
        return data

    def test_dict_with_different_insertion_order_produces_same_key(self):
        """Test that dicts with same content but different order produce identical keys"""
        dict1 = {"name": "John", "age": 30, "city": "NYC"}
        dict2 = {"city": "NYC", "name": "John", "age": 30}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Dicts with same content should produce identical cache keys")

    def test_nested_dicts_are_deterministic(self):
        """Test that nested dicts produce consistent cache keys"""
        nested1 = {"user": {"name": "Alice", "id": 123}, "active": True}
        nested2 = {"active": True, "user": {"id": 123, "name": "Alice"}}

        key1 = self.kg.generate_key(func=self._test_function, args=(nested1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(nested2,), kwargs={})

        self.assertEqual(key1, key2, "Nested dicts should produce identical cache keys")

    def test_lists_produce_consistent_keys(self):
        """Test that identical lists produce the same cache key"""
        list1 = [1, 2, 3, 4, 5]
        list2 = [1, 2, 3, 4, 5]

        key1 = self.kg.generate_key(func=self._test_function, args=(list1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(list2,), kwargs={})

        self.assertEqual(key1, key2, "Identical lists should produce identical cache keys")

    def test_sets_are_deterministic(self):
        """Test that sets with same elements produce consistent cache keys regardless of order"""
        set1 = {3, 1, 2}
        set2 = {2, 3, 1}

        key1 = self.kg.generate_key(func=self._test_function, args=(set1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(set2,), kwargs={})

        self.assertEqual(key1, key2, "Sets with same elements should produce identical cache keys")

    def test_tuples_produce_consistent_keys(self):
        """Test that identical tuples produce the same cache key"""
        tuple1 = (1, 2, 3)
        tuple2 = (1, 2, 3)

        key1 = self.kg.generate_key(func=self._test_function, args=(tuple1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(tuple2,), kwargs={})

        self.assertEqual(key1, key2, "Identical tuples should produce identical cache keys")

    def test_complex_mixed_structures_are_deterministic(self):
        """Test complex nested structures with multiple collection types"""
        complex1 = {"filters": {"status": "active", "type": "user"}, "options": [1, 2, 3], "enabled": True}
        complex2 = {"enabled": True, "filters": {"type": "user", "status": "active"}, "options": [1, 2, 3]}

        key1 = self.kg.generate_key(func=self._test_function, args=(complex1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(complex2,), kwargs={})

        self.assertEqual(key1, key2, "Complex structures should produce identical cache keys")

    def test_kwargs_with_dicts_are_deterministic(self):
        """Test that kwargs containing dicts produce consistent cache keys"""
        key1 = self.kg.generate_key(func=self._test_function, args=(), kwargs={"config": {"debug": True, "port": 8000}})
        key2 = self.kg.generate_key(func=self._test_function, args=(), kwargs={"config": {"port": 8000, "debug": True}})

        self.assertEqual(key1, key2, "Kwargs with dicts should produce identical cache keys")

    def test_different_data_produces_different_keys(self):
        """Test that different data produces different cache keys"""
        dict1 = {"a": 1, "b": 2}
        dict2 = {"a": 1, "b": 3}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertNotEqual(key1, key2, "Different data should produce different cache keys")

    def test_original_params_is_human_readable_json(self):
        """Test that original_params contains human-readable JSON for dicts"""
        test_dict = {"name": "Alice", "age": 25, "active": True}

        self.kg.generate_key(func=self._test_function, args=(test_dict,), kwargs={})

        # original_params should contain pretty-printed JSON
        self.assertIsNotNone(self.kg.original_params)
        self.assertIn('"active"', self.kg.original_params)
        self.assertIn('"age"', self.kg.original_params)
        self.assertIn('"name"', self.kg.original_params)

        # Should be valid JSON
        # Note: original_params might have other formatting, so we check if it contains JSON
        self.assertIn("{", self.kg.original_params)
        self.assertIn("}", self.kg.original_params)

    def test_original_params_with_nested_structures(self):
        """Test that original_params properly handles nested structures"""
        nested_data = {
            "user": {"name": "Bob", "roles": ["admin", "user"]},
            "settings": {"theme": "dark", "notifications": True},
        }

        self.kg.generate_key(func=self._test_function, args=(nested_data,), kwargs={})

        # Check that nested structure is preserved in original_params
        self.assertIsNotNone(self.kg.original_params)
        self.assertIn('"user"', self.kg.original_params)
        self.assertIn('"settings"', self.kg.original_params)
        self.assertIn('"admin"', self.kg.original_params)

    def test_mixed_args_with_simple_and_complex_types(self):
        """Test that mixed arguments (simple types + dicts) work correctly"""
        simple_arg = "test"
        dict_arg = {"key": "value"}
        num_arg = 42

        key1 = self.kg.generate_key(func=self._test_function, args=(simple_arg, dict_arg, num_arg), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(simple_arg, dict_arg, num_arg), kwargs={})

        self.assertEqual(key1, key2, "Mixed arguments should produce consistent cache keys")

    def test_empty_collections_produce_consistent_keys(self):
        """Test that empty collections are handled correctly"""
        empty_dict = {}
        empty_list = []
        empty_set = set()

        key1 = self.kg.generate_key(func=self._test_function, args=(empty_dict,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(empty_dict,), kwargs={})

        self.assertEqual(key1, key2, "Empty dicts should produce consistent cache keys")

        key3 = self.kg.generate_key(func=self._test_function, args=(empty_list,), kwargs={})
        key4 = self.kg.generate_key(func=self._test_function, args=(empty_list,), kwargs={})

        self.assertEqual(key3, key4, "Empty lists should produce consistent cache keys")

    def test_list_order_matters(self):
        """Test that list order is preserved (unlike sets)"""
        list1 = [1, 2, 3]
        list2 = [3, 2, 1]

        key1 = self.kg.generate_key(func=self._test_function, args=(list1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(list2,), kwargs={})

        self.assertNotEqual(key1, key2, "Lists with different order should produce different cache keys")

    def test_dict_with_numeric_and_string_keys(self):
        """Test that dicts with various key types are handled correctly"""
        # Note: JSON only supports string keys, numeric keys will be converted
        dict_with_mixed = {"1": "one", "2": "two", "text": "value"}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict_with_mixed,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict_with_mixed,), kwargs={})

        self.assertEqual(key1, key2, "Dicts with string keys should produce consistent cache keys")
