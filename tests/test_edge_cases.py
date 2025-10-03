"""Tests for edge cases in object serialization"""

import dataclasses
from datetime import datetime, timezone
from django.test import TestCase
from django.contrib.auth.models import User
from easy_cache.services.key_generator import KeyGenerator


class NestedObject:
    """Object with nested dictionary containing dynamic fields"""

    def __init__(self, id: int, config: dict):
        self.id = id
        self.config = config  # Dict that might contain dynamic fields
        self._cache_exclude_ = []  # We'll exclude specific nested paths


class ObjectWithDictProperty:
    """Object with dict property containing timestamps"""

    def __init__(self, name: str, metadata: dict):
        self.name = name
        self.metadata = metadata  # Contains dynamic fields like 'updated_at'


class DeeplyNestedStructure:
    """Object with multiple levels of nesting"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.settings = {
            "preferences": {
                "theme": "dark",
                "notifications": {
                    "email": True,
                    "timestamp": datetime.now(timezone.utc),  # Dynamic!
                },
            }
        }


@dataclasses.dataclass
class Company:
    """Dataclass with relations to other objects"""

    id: int
    name: str
    employees: list  # List of User objects (Django models)
    metadata: dict
    created_at: datetime = dataclasses.field(hash=False)


class EdgeCaseTestCase(TestCase):
    """Test edge cases in cache key generation"""

    def setUp(self):
        self.kg = KeyGenerator()

    @staticmethod
    def _test_function(obj):
        return obj

    # ==========================================
    # EDGE CASE 1: Dicts with dynamic fields
    # ==========================================

    def test_dict_with_timestamp_field(self):
        """Test that dicts with timestamps create different keys (no exclusion)"""
        # Disable auto-exclude to test raw behavior
        kg_no_auto = KeyGenerator(auto_exclude=False)

        now1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        now2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        dict1 = {"id": 1, "data": "test", "updated_at": now1}
        dict2 = {"id": 1, "data": "test", "updated_at": now2}

        key1 = kg_no_auto.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg_no_auto.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Without exclusion mechanism, these WILL be different
        self.assertNotEqual(
            key1, key2, "Dicts with different timestamps should produce different keys without exclusion"
        )

    def test_dict_timestamp_serialized_deterministically(self):
        """Test that same dict+timestamp produces same key"""
        ts = datetime(2025, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        dict1 = {"id": 1, "updated_at": ts}
        dict2 = {"updated_at": ts, "id": 1}  # Different order

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same dict data should produce same key regardless of key order")

    # ==========================================
    # EDGE CASE 2: Objects with dict properties
    # ==========================================

    def test_object_with_dict_containing_timestamps(self):
        """Test object with dict property containing dynamic fields"""
        # With auto-exclude ON, timestamps in nested dicts are excluded
        now1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        now2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        obj1 = ObjectWithDictProperty("test", {"key": "value", "updated_at": now1})
        obj2 = ObjectWithDictProperty("test", {"key": "value", "updated_at": now2})

        key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})

        # With auto-exclude, these should be SAME (updated_at is auto-excluded)
        self.assertEqual(
            key1, key2, "Objects with dicts containing different auto-excluded timestamps should produce same keys"
        )

    # ==========================================
    # EDGE CASE 3: Multi-level nesting
    # ==========================================

    def test_deeply_nested_dict_structure(self):
        """Test that deeply nested structures are serialized deterministically"""
        nested = {"level1": {"level2": {"level3": {"data": "value", "items": [1, 2, 3]}}}}

        key1 = self.kg.generate_key(func=self._test_function, args=(nested,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(nested,), kwargs={})

        self.assertEqual(key1, key2, "Deeply nested structures should be deterministic")

    def test_deeply_nested_with_different_order(self):
        """Test that nested dicts with different key order produce same key"""
        nested1 = {"outer": {"a": 1, "b": 2, "inner": {"x": 10, "y": 20}}}
        nested2 = {"outer": {"inner": {"y": 20, "x": 10}, "b": 2, "a": 1}}

        key1 = self.kg.generate_key(func=self._test_function, args=(nested1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(nested2,), kwargs={})

        self.assertEqual(key1, key2, "Nested dicts should produce same key regardless of key order at any level")

    # ==========================================
    # EDGE CASE 4: Relations & Django models
    # ==========================================

    def test_object_with_django_model_relations(self):
        """Test object containing Django model instances"""
        user1 = User.objects.create(username="alice")
        user2 = User.objects.create(username="bob")

        obj1 = {"user": user1, "data": "test"}
        obj2 = {"user": user1, "data": "test"}  # Same user
        obj3 = {"user": user2, "data": "test"}  # Different user

        key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})
        key3 = self.kg.generate_key(func=self._test_function, args=(obj3,), kwargs={})

        self.assertEqual(key1, key2, "Same user should produce same key")
        self.assertNotEqual(key1, key3, "Different users should produce different keys")

    def test_dataclass_with_list_of_models(self):
        """Test dataclass containing list of Django models"""
        user1 = User.objects.create(username="emp1")
        user2 = User.objects.create(username="emp2")

        company = Company(
            id=1,
            name="TechCorp",
            employees=[user1, user2],
            metadata={"industry": "tech"},
            created_at=datetime.now(timezone.utc),
        )

        key1 = self.kg.generate_key(func=self._test_function, args=(company,), kwargs={})

        # Create same company again (created_at will be different but excluded)
        company2 = Company(
            id=1,
            name="TechCorp",
            employees=[user1, user2],
            metadata={"industry": "tech"},
            created_at=datetime.now(timezone.utc),  # Different time
        )

        key2 = self.kg.generate_key(func=self._test_function, args=(company2,), kwargs={})

        self.assertEqual(key1, key2, "Dataclass with model lists should respect field(hash=False)")

    # ==========================================
    # EDGE CASE 5: Mixed collections
    # ==========================================

    def test_set_containing_tuples(self):
        """Test set containing tuples"""
        set1 = {(1, 2), (3, 4), (5, 6)}
        set2 = {(5, 6), (1, 2), (3, 4)}  # Different order

        key1 = self.kg.generate_key(func=self._test_function, args=(set1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(set2,), kwargs={})

        self.assertEqual(key1, key2, "Sets with same tuples should produce same key")

    def test_list_of_dicts_with_different_orders(self):
        """Test list of dicts where each dict has different key order"""
        list1 = [{"a": 1, "b": 2}, {"x": 10, "y": 20}]
        list2 = [{"b": 2, "a": 1}, {"y": 20, "x": 10}]

        key1 = self.kg.generate_key(func=self._test_function, args=(list1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(list2,), kwargs={})

        self.assertEqual(key1, key2, "List of dicts should sort keys within each dict")

    def test_dict_with_set_values(self):
        """Test dict with set as value"""
        dict1 = {"tags": {3, 1, 2}, "name": "test"}
        dict2 = {"tags": {2, 3, 1}, "name": "test"}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Dict with set values should be deterministic")

    # ==========================================
    # EDGE CASE 6: Circular references (potential issue)
    # ==========================================

    def test_self_referential_dict_raises_error(self):
        """Test that circular references in dicts raise an appropriate error"""
        circular_dict = {"a": 1}
        circular_dict["self"] = circular_dict  # Circular reference!

        with self.assertRaises(Exception) as context:
            self.kg.generate_key(func=self._test_function, args=(circular_dict,), kwargs={})

        # Should raise ValueError from JSON encoder
        self.assertTrue(
            "Circular reference" in str(context.exception) or "maximum recursion" in str(context.exception).lower()
        )

    # ==========================================
    # EDGE CASE 7: Very deep nesting
    # ==========================================

    def test_very_deep_nesting(self):
        """Test handling of very deeply nested structures"""
        deep = {"level": 1}
        current = deep
        for i in range(2, 20):  # 20 levels deep
            current["next"] = {"level": i}
            current = current["next"]

        key1 = self.kg.generate_key(func=self._test_function, args=(deep,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(deep,), kwargs={})

        self.assertEqual(key1, key2, "Very deep nesting should be handled consistently")

    # ==========================================
    # EDGE CASE 8: Unicode and special chars
    # ==========================================

    def test_dict_with_unicode_keys_and_values(self):
        """Test that unicode in dicts is handled properly"""
        dict1 = {"name": "测试", "emoji": "🚀", "special": "café"}
        dict2 = {"emoji": "🚀", "special": "café", "name": "测试"}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Unicode should be handled deterministically")

    # ==========================================
    # EDGE CASE 9: None and empty values
    # ==========================================

    def test_dict_with_none_values(self):
        """Test handling of None in dicts"""
        dict1 = {"a": 1, "b": None, "c": 3}
        dict2 = {"c": 3, "a": 1, "b": None}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "None values should be handled consistently")

    def test_nested_empty_collections(self):
        """Test nested empty collections"""
        nested1 = {"empty_dict": {}, "empty_list": [], "data": "value"}
        nested2 = {"data": "value", "empty_list": [], "empty_dict": {}}

        key1 = self.kg.generate_key(func=self._test_function, args=(nested1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(nested2,), kwargs={})

        self.assertEqual(key1, key2, "Empty collections should be handled consistently")

    # ==========================================
    # EDGE CASE 10: Large collections
    # ==========================================

    def test_very_large_dict(self):
        """Test that very large dicts are handled (and hashed if too long)"""
        large_dict = {f"key_{i}": f"value_{i}" for i in range(1000)}

        key1 = self.kg.generate_key(func=self._test_function, args=(large_dict,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(large_dict,), kwargs={})

        self.assertEqual(key1, key2, "Large dicts should be handled consistently")
        # Check that it got hashed (should be relatively short)
        self.assertIsNotNone(self.kg.original_params)

    def test_list_of_many_models(self):
        """Test list containing many Django models"""
        users = [User.objects.create(username=f"user{i}") for i in range(50)]

        key1 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})

        self.assertEqual(key1, key2, "Lists of many models should be deterministic")
