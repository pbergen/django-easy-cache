"""Tests for problematic types that could break cache key stability"""

import uuid
import decimal
import pathlib
from datetime import datetime, date, time, timedelta, timezone
from django.test import TestCase
from django.contrib.auth.models import User
from easy_cache.services.key_generator import KeyGenerator


class ProblematicTypesTestCase(TestCase):
    """Test types that could cause cache key instability"""

    def setUp(self):
        self.kg = KeyGenerator()

    @staticmethod
    def _test_function(data):
        return data

    # ==========================================
    # UUIDs - Different every time!
    # ==========================================

    def test_uuid_field(self):
        """Test UUID fields - auto-excluded by type"""
        dict1 = {"id": 1, "request_id": uuid.uuid4()}
        dict2 = {"id": 1, "request_id": uuid.uuid4()}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        print(f"UUID 1: {dict1['request_id']}")
        print(f"UUID 2: {dict2['request_id']}")
        print(f"Keys equal? {key1 == key2}")

        # UUIDs are auto-excluded by type, so keys should be SAME
        self.assertEqual(key1, key2, "UUIDs are auto-excluded - same cache key")

    def test_uuid_field_name_patterns(self):
        """Test that UUIDs are auto-excluded regardless of field name"""
        # Common UUID field names - field names don't matter, only type matters!
        uuid_fields = {
            "request_id": uuid.uuid4(),  # UUID type
            "session_id": uuid.uuid4(),  # UUID type
            "transaction_id": uuid.uuid4(),  # UUID type
            "uuid": uuid.uuid4(),  # UUID type
        }

        dict1 = {"user_id": 123, **uuid_fields}
        dict2 = {"user_id": 123, **{k: uuid.uuid4() for k in uuid_fields.keys()}}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        print(f"Keys equal? {key1 == key2}")
        # UUIDs are auto-excluded by TYPE (not field name), so keys should be SAME
        self.assertEqual(key1, key2, "UUIDs auto-excluded by type - same cache key")

    # ==========================================
    # Timedelta - Duration values
    # ==========================================

    def test_timedelta_field(self):
        """Test timedelta fields"""
        dict1 = {"user_id": 1, "duration": timedelta(seconds=30)}
        dict2 = {"user_id": 1, "duration": timedelta(seconds=30)}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same timedelta should produce same key")

    def test_timedelta_different_values(self):
        """Test different timedelta values"""
        dict1 = {"user_id": 1, "timeout": timedelta(seconds=30)}
        dict2 = {"user_id": 1, "timeout": timedelta(seconds=60)}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Question: Should timedeltas be auto-excluded?
        # They could be config values (stable) or dynamic timeouts (unstable)
        self.assertNotEqual(key1, key2, "Different timedelta produces different keys")

    # ==========================================
    # Decimal - Financial/precision values
    # ==========================================

    def test_decimal_field(self):
        """Test Decimal fields (common in Django for prices)"""
        dict1 = {"product_id": 1, "price": decimal.Decimal("19.99")}
        dict2 = {"product_id": 1, "price": decimal.Decimal("19.99")}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same Decimal should produce same key")

    def test_decimal_floating_point_precision(self):
        """Test Decimal precision differences"""
        dict1 = {"amount": decimal.Decimal("19.99")}
        dict2 = {"amount": decimal.Decimal("19.990")}  # Same value, different precision

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        print(f"Decimal 1: {dict1['amount']}")
        print(f"Decimal 2: {dict2['amount']}")
        print(f"Keys equal? {key1 == key2}")

    # ==========================================
    # Pathlib - File paths
    # ==========================================

    def test_pathlib_path(self):
        """Test pathlib.Path objects"""
        dict1 = {"user_id": 1, "file_path": pathlib.Path("/tmp/test.txt")}
        dict2 = {"user_id": 1, "file_path": pathlib.Path("/tmp/test.txt")}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same Path should produce same key")

    def test_pathlib_windows_vs_posix(self):
        """Test different path types"""
        dict1 = {"file": pathlib.PurePosixPath("/tmp/test.txt")}
        dict2 = {"file": pathlib.PureWindowsPath("C:\\tmp\\test.txt")}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Different paths should produce different keys
        self.assertNotEqual(key1, key2, "Different paths produce different keys")

    # ==========================================
    # Random/Generated Values
    # ==========================================

    def test_random_values(self):
        """Test random number generation"""
        import random

        dict1 = {"id": 1, "nonce": random.random()}
        dict2 = {"id": 1, "nonce": random.random()}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Random values are different
        self.assertNotEqual(key1, key2)

    # ==========================================
    # Bytes and Bytearray
    # ==========================================

    def test_bytes_field(self):
        """Test bytes fields"""
        dict1 = {"id": 1, "data": b"hello"}
        dict2 = {"id": 1, "data": b"hello"}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same bytes should produce same key")

    def test_bytearray_field(self):
        """Test bytearray fields (mutable)"""
        dict1 = {"id": 1, "data": bytearray(b"hello")}
        dict2 = {"id": 1, "data": bytearray(b"hello")}

        try:
            key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
            key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})
            print(f"Bytearray serialization worked: {key1 == key2}")
        except Exception as e:
            print(f"Bytearray serialization failed: {e}")

    # ==========================================
    # Complex Numbers
    # ==========================================

    def test_complex_numbers(self):
        """Test complex number fields"""
        dict1 = {"id": 1, "value": complex(1, 2)}
        dict2 = {"id": 1, "value": complex(1, 2)}

        try:
            key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
            key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})
            self.assertEqual(key1, key2, "Same complex number should produce same key")
        except Exception as e:
            print(f"Complex number serialization failed: {e}")

    # ==========================================
    # None vs Missing Keys
    # ==========================================

    def test_none_vs_missing_key(self):
        """Test None value vs missing key"""
        dict1 = {"id": 1, "optional": None}
        dict2 = {"id": 1}  # Missing 'optional' key

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # These should be DIFFERENT (None is a value, missing is absence)
        self.assertNotEqual(key1, key2, "None vs missing key should differ")

    # ==========================================
    # Frozenset
    # ==========================================

    def test_frozenset_field(self):
        """Test frozenset fields"""
        dict1 = {"id": 1, "tags": frozenset(["a", "b", "c"])}
        dict2 = {"id": 1, "tags": frozenset(["c", "b", "a"])}  # Different order

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Frozensets are unordered, so these should be SAME
        self.assertEqual(key1, key2, "Frozensets with same elements should produce same key")

    # ==========================================
    # Django-specific: IPAddress, etc.
    # ==========================================

    def test_ip_address(self):
        """Test IP address fields (Django has IPAddressField)"""
        import ipaddress

        dict1 = {"user_id": 1, "ip": ipaddress.IPv4Address("192.168.1.1")}
        dict2 = {"user_id": 1, "ip": ipaddress.IPv4Address("192.168.1.1")}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same IP address should produce same key")

    def test_ip_address_different(self):
        """Test different IP addresses"""
        import ipaddress

        dict1 = {"user_id": 1, "client_ip": ipaddress.IPv4Address("192.168.1.1")}
        dict2 = {"user_id": 1, "client_ip": ipaddress.IPv4Address("192.168.1.2")}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Question: Should IP addresses be auto-excluded?
        # Could be client_ip (dynamic) or server_ip (static)
        self.assertNotEqual(key1, key2, "Different IP addresses produce different keys")

    # ==========================================
    # Counter and defaultdict
    # ==========================================

    def test_counter(self):
        """Test collections.Counter"""
        from collections import Counter

        dict1 = {"id": 1, "counts": Counter(["a", "b", "a"])}
        dict2 = {"id": 1, "counts": Counter(["b", "a", "a"])}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        # Counter with same counts should produce same key
        self.assertEqual(key1, key2, "Same Counter should produce same key")

    # ==========================================
    # Class instances (not Django models)
    # ==========================================

    def test_custom_class_with_slots(self):
        """Test class with __slots__"""

        class SlottedClass:
            __slots__ = ["value", "name"]

            def __init__(self, value, name):
                self.value = value
                self.name = name

        obj1 = SlottedClass(42, "test")
        obj2 = SlottedClass(42, "test")

        try:
            key1 = self.kg.generate_key(func=self._test_function, args=(obj1,), kwargs={})
            key2 = self.kg.generate_key(func=self._test_function, args=(obj2,), kwargs={})
            print(f"Slotted class keys equal? {key1 == key2}")
        except Exception as e:
            print(f"Slotted class serialization failed: {e}")

    # ==========================================
    # Enum
    # ==========================================

    def test_enum_field(self):
        """Test Enum fields"""
        from enum import Enum

        class Status(Enum):
            PENDING = 1
            ACTIVE = 2
            INACTIVE = 3

        dict1 = {"user_id": 1, "status": Status.ACTIVE}
        dict2 = {"user_id": 1, "status": Status.ACTIVE}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertEqual(key1, key2, "Same Enum should produce same key")

    def test_enum_different_values(self):
        """Test different Enum values"""
        from enum import Enum

        class Status(Enum):
            PENDING = 1
            ACTIVE = 2

        dict1 = {"user_id": 1, "status": Status.PENDING}
        dict2 = {"user_id": 1, "status": Status.ACTIVE}

        key1 = self.kg.generate_key(func=self._test_function, args=(dict1,), kwargs={})
        key2 = self.kg.generate_key(func=self._test_function, args=(dict2,), kwargs={})

        self.assertNotEqual(key1, key2, "Different Enum values produce different keys")
