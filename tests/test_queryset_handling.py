"""Tests for Django QuerySet handling in cache key generation"""

from datetime import datetime, timezone
from django.test import TestCase
from django.contrib.auth.models import User
from easy_cache.services.key_generator import KeyGenerator


class QuerySetHandlingTestCase(TestCase):
    """Test how QuerySets are handled in cache key generation"""

    def setUp(self):
        self.kg = KeyGenerator()
        # Create test users
        self.user1 = User.objects.create(username="user1", email="user1@test.com")
        self.user2 = User.objects.create(username="user2", email="user2@test.com")
        self.user3 = User.objects.create(username="user3", email="user3@test.com")

    @staticmethod
    def _test_function(data):
        return data

    # ==========================================
    # QUERYSET: Basic Behavior
    # ==========================================

    def test_queryset_as_argument(self):
        """Test passing a QuerySet directly as an argument"""
        qs = User.objects.filter(username__startswith="user")

        try:
            key = self.kg.generate_key(func=self._test_function, args=(qs,), kwargs={})
            print(f"QuerySet key generated: {key}")
            print(f"Original params: {self.kg.original_params}")
        except Exception as e:
            self.fail(f"QuerySet serialization failed: {e}")

    def test_queryset_stability_same_query(self):
        """Test that same query produces same cache key"""
        qs1 = User.objects.filter(username__startswith="user")
        qs2 = User.objects.filter(username__startswith="user")

        key1 = self.kg.generate_key(func=self._test_function, args=(qs1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(qs2,), kwargs={})

        # This might FAIL - QuerySets are complex objects!
        print(f"Key 1: {key1}")
        print(f"Key 2: {key2}")
        print(f"Params 1: {self.kg.original_params}")

        # Let's see what happens...

    def test_queryset_vs_list(self):
        """Test QuerySet vs evaluated list"""
        qs = User.objects.filter(username__startswith="user")
        user_list = list(qs)  # Evaluate to list

        key_qs = self.kg.generate_key(func=self._test_function, args=(qs,), kwargs={})
        key_list = self.kg.generate_key(func=self._test_function, args=(user_list,), kwargs={})

        print(f"QuerySet key: {key_qs}")
        print(f"List key: {key_list}")
        print(f"Are they equal? {key_qs == key_list}")

    # ==========================================
    # QUERYSET: Evaluated vs Unevaluated
    # ==========================================

    def test_evaluated_queryset_list(self):
        """Test evaluated QuerySet as list"""
        users = list(User.objects.filter(username__startswith="user"))

        key1 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})

        self.assertEqual(key1, key2, "Evaluated QuerySet (list) should be stable")

    def test_queryset_values(self):
        """Test QuerySet.values() - returns list of dicts"""
        values = list(User.objects.filter(username__startswith="user").values("id", "username"))

        key1 = self.kg.generate_key(func=self._test_function, args=(values,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(values,), kwargs={})

        self.assertEqual(key1, key2, "QuerySet.values() should be stable")
        print(f"Values: {values}")
        print(f"Key: {key1}")

    def test_queryset_values_list(self):
        """Test QuerySet.values_list() - returns list of tuples"""
        values = list(User.objects.filter(username__startswith="user").values_list("id", "username"))

        key1 = self.kg.generate_key(func=self._test_function, args=(values,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(values,), kwargs={})

        self.assertEqual(key1, key2, "QuerySet.values_list() should be stable")

    # ==========================================
    # QUERYSET: With Timestamps
    # ==========================================

    def test_queryset_values_with_date_joined(self):
        """Test QuerySet.values() including date_joined field"""
        # date_joined is auto-populated on User model
        values = list(User.objects.filter(username__startswith="user").values("id", "username", "date_joined"))

        key1 = self.kg.generate_key(func=self._test_function, args=(values,), kwargs={})

        print(f"Values with date_joined: {values}")
        print(f"Key: {key1}")
        print(f"Original params: {self.kg.original_params}")

        # date_joined should be auto-excluded from cache key
        # Let's verify by checking if it's in original_params

    # ==========================================
    # QUERYSET: Ordering
    # ==========================================

    def test_queryset_different_order(self):
        """Test that different ordering produces different keys (order matters for QuerySets)"""
        qs1 = User.objects.filter(username__startswith="user").order_by("username")
        qs2 = User.objects.filter(username__startswith="user").order_by("-username")

        users1 = list(qs1)
        users2 = list(qs2)

        key1 = self.kg.generate_key(func=self._test_function, args=(users1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(users2,), kwargs={})

        # Order matters in lists, so these should be different
        print(f"Same users, different order:")
        print(f"Users 1 PKs: {[u.pk for u in users1]}")
        print(f"Users 2 PKs: {[u.pk for u in users2]}")
        print(f"Keys equal? {key1 == key2}")

    # ==========================================
    # QUERYSET: Real-World Patterns
    # ==========================================

    def test_common_pattern_filter_dict(self):
        """Test common pattern: filters as dict"""
        filters = {
            "username__startswith": "user",
            "is_active": True,
            "date_joined__gte": datetime(2025, 1, 1, tzinfo=timezone.utc),
        }

        # Simulate what a developer would do
        # QuerySet is created and evaluated in the function
        users = list(User.objects.filter(**filters))

        key1 = self.kg.generate_key(func=self._test_function, args=(filters,), kwargs={})

        # With auto-exclude, date_joined__gte should be excluded
        filters2 = filters.copy()
        filters2["date_joined__gte"] = datetime(2025, 1, 2, tzinfo=timezone.utc)  # Different date

        key2 = self.kg.generate_key(func=self._test_function, args=(filters2,), kwargs={})

        # These should be SAME if date fields are excluded
        print(f"Filter dict keys equal? {key1 == key2}")

    def test_queryset_count_vs_list(self):
        """Test caching QuerySet.count() vs list of objects"""
        qs = User.objects.filter(username__startswith="user")

        count = qs.count()
        users = list(qs)

        key_count = self.kg.generate_key(func=self._test_function, args=(count,), kwargs={})
        key_list = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})

        # These should be DIFFERENT (count is int, list is list of models)
        self.assertNotEqual(key_count, key_list)

    # ==========================================
    # QUERYSET: Edge Cases
    # ==========================================

    def test_empty_queryset(self):
        """Test empty QuerySet"""
        users = list(User.objects.filter(username="nonexistent"))

        key1 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})

        self.assertEqual(key1, key2, "Empty QuerySet should be stable")

    def test_queryset_pk_list(self):
        """Test list of PKs (common pattern)"""
        pks = list(User.objects.filter(username__startswith="user").values_list("pk", flat=True))

        key1 = self.kg.generate_key(func=self._test_function, args=(pks,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(pks,), kwargs={})

        self.assertEqual(key1, key2, "List of PKs should be stable")
        print(f"PKs: {pks}")

    def test_queryset_with_select_related(self):
        """Test QuerySet with select_related"""
        # This is advanced - might not work well
        users = list(User.objects.filter(username__startswith="user").select_related())

        key1 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(users,), kwargs={})

        self.assertEqual(key1, key2, "QuerySet with select_related should be stable")
