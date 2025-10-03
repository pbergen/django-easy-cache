"""Tests for object serialization with field exclusion in cache key generation"""

import dataclasses
from datetime import datetime, timezone
from django.test import TestCase
from django.contrib.auth.models import User
from easy_cache.services.key_generator import KeyGenerator


class SimpleObject:
    """Regular Python object for testing"""

    def __init__(self, name: str, value: int, timestamp: datetime):
        self.name = name
        self.value = value
        self.timestamp = timestamp

    def __str__(self):
        # This is stable - no memory address
        return f"SimpleObject(name={self.name}, value={self.value})"


class ObjectWithExclusion:
    """Object that uses _cache_exclude_ protocol"""

    def __init__(self, id: int, data: str, updated_at: datetime):
        self.id = id
        self.data = data
        self.updated_at = updated_at
        # Exclude dynamic field from cache key
        self._cache_exclude_ = ["updated_at"]


@dataclasses.dataclass
class UserProfile:
    """Dataclass for testing dataclass support"""

    user_id: int
    username: str
    created_at: datetime = dataclasses.field(hash=False)  # Exclude from hash
    last_login: datetime = dataclasses.field(hash=False)  # Exclude from hash


class ObjectSerializationTestCase(TestCase):
    """Test that objects are serialized without memory addresses and with field exclusion"""

    def setUp(self):
        self.kg = KeyGenerator()

    @staticmethod
    def _test_function(obj):
        """Simple test function"""
        return obj

    def test_simple_object_produces_stable_key(self):
        """Test that simple objects produce stable cache keys across instances"""
        ts = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        obj1 = SimpleObject("test", 42, ts)
        obj2 = SimpleObject("test", 42, ts)

        key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})

        self.assertEqual(key1, key2, "Same object data should produce identical cache keys")

    def test_cache_exclude_protocol_works(self):
        """Test that _cache_exclude_ protocol excludes dynamic fields from cache key"""
        now1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        now2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)  # Different time

        obj1 = ObjectWithExclusion(1, "data", now1)
        obj2 = ObjectWithExclusion(1, "data", now2)  # Same ID and data, different timestamp

        key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})

        self.assertEqual(
            key1,
            key2,
            "Objects with same cacheable fields should produce identical keys despite different excluded fields",
        )

    def test_cache_exclude_protocol_detects_data_changes(self):
        """Test that _cache_exclude_ doesn't exclude all fields - actual changes are detected"""
        now = datetime.now(timezone.utc)
        obj1 = ObjectWithExclusion(1, "data1", now)
        obj2 = ObjectWithExclusion(1, "data2", now)  # Different data

        key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})

        self.assertNotEqual(key1, key2, "Objects with different cacheable fields should produce different keys")

    def test_dataclass_field_hash_exclusion(self):
        """Test that dataclass field(hash=False) is respected"""
        login1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        login2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)  # Different login time

        profile1 = UserProfile(
            user_id=1, username="alice", created_at=datetime(2024, 1, 1, tzinfo=timezone.utc), last_login=login1
        )
        profile2 = UserProfile(
            user_id=1,
            username="alice",
            created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
            last_login=login2,  # Different login time
        )

        key1 = self.kg.generate_key(func=self._test_function, args=(profile1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(profile2,), kwargs={})

        self.assertEqual(key1, key2, "Dataclasses should respect field(hash=False) for cache key generation")

    def test_dataclass_detects_real_changes(self):
        """Test that dataclass detects changes in non-excluded fields"""
        profile1 = UserProfile(
            user_id=1, username="alice", created_at=datetime.now(timezone.utc), last_login=datetime.now(timezone.utc)
        )
        profile2 = UserProfile(
            user_id=1,
            username="bob",  # Different username
            created_at=datetime.now(timezone.utc),
            last_login=datetime.now(timezone.utc),
        )

        key1 = self.kg.generate_key(func=self._test_function, args=(profile1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(profile2,), kwargs={})

        self.assertNotEqual(key1, key2, "Dataclasses should detect changes in non-excluded fields")

    def test_django_model_uses_stable_identifier(self):
        """Test that Django models use pk instead of memory address"""
        user1 = User.objects.create(username="testuser1")
        user2 = User.objects.get(pk=user1.pk)  # Same user, different object instance

        key1 = self.kg.generate_key(func=self._test_function, args=(user1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(user2,), kwargs={})

        self.assertEqual(
            key1, key2, "Django models should use pk for stable cache keys across different object instances"
        )

    def test_dict_with_objects_using_cache_exclude(self):
        """Test that dicts containing objects with _cache_exclude_ work correctly"""
        now = datetime.now(timezone.utc)
        obj1 = ObjectWithExclusion(1, "data", now)

        later = datetime.now(timezone.utc)
        obj2 = ObjectWithExclusion(1, "data", later)  # Different timestamp

        dict1 = {"object": obj1, "name": "test"}
        dict2 = {"object": obj2, "name": "test"}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Dicts containing objects with _cache_exclude_ should produce stable cache keys")

    def test_nested_objects_with_exclusions(self):
        """Test nested structures with multiple levels of objects"""
        now = datetime.now(timezone.utc)

        nested1 = {
            "user": ObjectWithExclusion(1, "Alice", now),
            "config": {
                "theme": "dark",
                "profile": UserProfile(
                    user_id=1, username="alice", created_at=datetime(2024, 1, 1, tzinfo=timezone.utc), last_login=now
                ),
            },
        }

        later = datetime.now(timezone.utc)
        nested2 = {
            "user": ObjectWithExclusion(1, "Alice", later),  # Different timestamp
            "config": {
                "theme": "dark",
                "profile": UserProfile(
                    user_id=1,
                    username="alice",
                    created_at=datetime(2024, 1, 1, tzinfo=timezone.utc),
                    last_login=later,  # Different login time
                ),
            },
        }

        key1 = self.kg.generate_key(func=self._test_function, args=(nested1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(nested2,), kwargs={})

        self.assertEqual(key1, key2, "Nested structures should respect field exclusions at all levels")

    def test_datetime_in_dict_is_stable(self):
        """Test that datetime objects in dicts are serialized deterministically"""
        ts = datetime(2025, 1, 1, 12, 0, 0, 123456, tzinfo=timezone.utc)
        dict1 = {"timestamp": ts, "value": 42}
        dict2 = {"value": 42, "timestamp": ts}  # Different order

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Datetime objects should be serialized consistently")

    def test_cache_key_does_not_contain_memory_address(self):
        """Test that generated cache keys don't contain memory addresses (0x...)"""
        obj = SimpleObject("test", 42, datetime.now(timezone.utc))

        self.kg.generate_key(func=self._test_function, args=(obj,), kwargs={})

        # Check that original_params doesn't contain hex memory addresses
        self.assertIsNotNone(self.kg.original_params)
        self.assertNotIn("0x", self.kg.original_params.lower(), "Cache key should not contain memory addresses")

    def test_multiple_objects_same_function_different_keys(self):
        """Test that different objects produce different cache keys"""
        obj1 = ObjectWithExclusion(1, "data1", datetime.now(timezone.utc))
        obj2 = ObjectWithExclusion(2, "data2", datetime.now(timezone.utc))

        key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})

        self.assertNotEqual(key1, key2, "Different objects should produce different cache keys")
