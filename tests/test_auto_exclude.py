"""Tests for auto-exclude functionality in cache key generation"""

import uuid
from datetime import datetime, date, time, timezone
from django.test import TestCase
from easy_cache.services.key_generator import KeyGenerator


class AutoExcludeTestCase(TestCase):
    """Test auto-exclude feature that automatically filters unstable types"""

    @staticmethod
    def _test_function(data):
        return data

    # ==========================================
    # AUTO-EXCLUDE: Type-Based (datetime, date, time)
    # ==========================================

    def test_auto_exclude_datetime_type(self):
        """Test that datetime values are auto-excluded regardless of field name"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"id": 1, "any_field_name": datetime.now(timezone.utc)}
        dict2 = {"id": 1, "any_field_name": datetime.now(timezone.utc)}

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "datetime values should be auto-excluded by type")

    def test_auto_exclude_date_type(self):
        """Test that date values are auto-excluded"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"id": 1, "some_date": date(2025, 1, 1)}
        dict2 = {"id": 1, "some_date": date(2025, 1, 2)}

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "date values should be auto-excluded by type")

    def test_auto_exclude_time_type(self):
        """Test that time values are auto-excluded"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"id": 1, "some_time": time(12, 0, 0)}
        dict2 = {"id": 1, "some_time": time(13, 0, 0)}

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "time values should be auto-excluded by type")

    def test_auto_exclude_multiple_datetime_fields(self):
        """Test that multiple datetime fields are auto-excluded"""
        kg = KeyGenerator(auto_exclude=True)

        now1 = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        now2 = datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)

        dict1 = {"id": 1, "data": "test", "created_at": now1, "updated_at": now1, "last_modified": now1}
        dict2 = {
            "id": 1,
            "data": "test",
            "created_at": now2,  # Different
            "updated_at": now2,  # Different
            "last_modified": now2,  # Different
        }

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "All datetime fields should be auto-excluded")

    # ==========================================
    # AUTO-EXCLUDE: UUID Type
    # ==========================================

    def test_auto_exclude_uuid_type(self):
        """Test that UUID values are auto-excluded"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"id": 1, "request_id": uuid.uuid4()}
        dict2 = {"id": 1, "request_id": uuid.uuid4()}

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "UUID values should be auto-excluded by type")

    def test_auto_exclude_multiple_uuid_fields(self):
        """Test that multiple UUID fields are auto-excluded"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"user_id": 123, "request_id": uuid.uuid4(), "session_id": uuid.uuid4(), "trace_id": uuid.uuid4()}
        dict2 = {
            "user_id": 123,
            "request_id": uuid.uuid4(),  # Different
            "session_id": uuid.uuid4(),  # Different
            "trace_id": uuid.uuid4(),  # Different
        }

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "All UUID fields should be auto-excluded")

    # ==========================================
    # AUTO-EXCLUDE: Disabled
    # ==========================================

    def test_auto_exclude_disabled(self):
        """Test that disabling auto-exclude includes all fields"""
        kg = KeyGenerator(auto_exclude=False)

        dict1 = {"id": 1, "timestamp": datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)}
        dict2 = {"id": 1, "timestamp": datetime(2025, 1, 1, 13, 0, 0, tzinfo=timezone.utc)}

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertNotEqual(key1, key2, "With auto_exclude=False, all fields should be included")

    # ==========================================
    # AUTO-EXCLUDE: Non-Dynamic Fields Included
    # ==========================================

    def test_stable_fields_are_included(self):
        """Test that stable fields are still included in cache key"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {
            "user_id": 123,
            "name": "John",
            "timestamp": datetime.now(timezone.utc),  # Excluded
        }
        dict2 = {
            "user_id": 456,  # Different! Should produce different key
            "name": "Jane",  # Different! Should produce different key
            "timestamp": datetime.now(timezone.utc),  # Excluded
        }

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertNotEqual(key1, key2, "Stable fields should still affect cache key")

    # ==========================================
    # AUTO-EXCLUDE: Nested Dictionaries
    # ==========================================

    def test_auto_exclude_nested_dicts(self):
        """Test that auto-exclude works in nested dictionaries"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"id": 1, "metadata": {"created": datetime.now(timezone.utc), "name": "test"}}
        dict2 = {
            "id": 1,
            "metadata": {
                "created": datetime.now(timezone.utc),  # Different, but should be excluded
                "name": "test",
            },
        }

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "datetime in nested dicts should be auto-excluded")

    def test_auto_exclude_deeply_nested(self):
        """Test auto-exclude in deeply nested structures"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {"id": 1, "level1": {"level2": {"level3": {"timestamp": datetime.now(timezone.utc), "data": "stable"}}}}
        dict2 = {
            "id": 1,
            "level1": {
                "level2": {
                    "level3": {
                        "timestamp": datetime.now(timezone.utc),  # Different
                        "data": "stable",
                    }
                }
            },
        }

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "datetime in deeply nested dicts should be auto-excluded")

    # ==========================================
    # AUTO-EXCLUDE: Lists with Unstable Types
    # ==========================================

    def test_auto_exclude_in_lists(self):
        """Test that unstable types in lists are excluded"""
        kg = KeyGenerator(auto_exclude=True)

        dict1 = {
            "id": 1,
            "events": [
                {"name": "event1", "time": datetime.now(timezone.utc)},
                {"name": "event2", "time": datetime.now(timezone.utc)},
            ],
        }
        dict2 = {
            "id": 1,
            "events": [
                {"name": "event1", "time": datetime.now(timezone.utc)},  # Different
                {"name": "event2", "time": datetime.now(timezone.utc)},  # Different
            ],
        }

        key1 = kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "datetime in list items should be auto-excluded")

    # ==========================================
    # AUTO-EXCLUDE: Real-World Scenarios
    # ==========================================

    def test_real_world_api_request(self):
        """Test real-world API request with mixed stable and unstable fields"""
        kg = KeyGenerator(auto_exclude=True)

        request1 = {
            "user_id": 123,
            "action": "view_profile",
            "request_id": uuid.uuid4(),  # Excluded
            "timestamp": datetime.now(timezone.utc),  # Excluded
            "session_id": uuid.uuid4(),  # Excluded
        }
        request2 = {
            "user_id": 123,
            "action": "view_profile",
            "request_id": uuid.uuid4(),  # Different, but excluded
            "timestamp": datetime.now(timezone.utc),  # Different, but excluded
            "session_id": uuid.uuid4(),  # Different, but excluded
        }

        key1 = kg.generate_key(func=self._test_function, args=(request1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(request2,), kwargs={})

        self.assertEqual(key1, key2, "Real-world request with unstable types should work")

    def test_real_world_database_query(self):
        """Test real-world database query filters"""
        kg = KeyGenerator(auto_exclude=True)

        filters1 = {
            "status": "active",
            "category": "premium",
            "created_after": datetime(2025, 1, 1, tzinfo=timezone.utc),  # Excluded
        }
        filters2 = {
            "status": "active",
            "category": "premium",
            "created_after": datetime(2025, 1, 15, tzinfo=timezone.utc),  # Different, excluded
        }

        key1 = kg.generate_key(func=self._test_function, args=(filters1,), kwargs={})
        key2 = kg.generate_key(func=self._test_function, args=(filters2,), kwargs={})

        self.assertEqual(key1, key2, "Database query filters should work with type exclusion")
