# Object Parameter Caching

## Overview

Django Easy Cache automatically handles methods and functions that receive object instances as parameters, generating stable and unique cache keys without requiring manual serialization. This feature is essential for caching business logic that works with Django models and custom Python objects.

## Why Object Parameter Caching Matters

In traditional caching approaches, passing object instances to cached functions creates unstable cache keys because:

1. **Memory addresses**: Default `repr()` includes memory addresses (e.g., `<User object at 0x7f8b3c4d5e60>`)
2. **Instance variations**: Same logical object creates different instances with different memory addresses
3. **Manual serialization burden**: Developers must manually extract stable identifiers (pk, id, etc.)

Django Easy Cache solves this automatically.

## How It Works

The `KeyGenerator` service intelligently serializes objects using these strategies:

### 1. Django Model Instances

Django models are serialized using their primary key (`pk`) for stable identification:

```python
from django.contrib.auth.models import User
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="14:00")
def get_user_profile(user_obj):
    """Cache user profile calculation using user's pk"""
    return expensive_profile_calculation(user_obj)


# Usage
user = User.objects.get(username="alice")
result = get_user_profile(user)  # Generates key: "...User:123..."

# Different instance, same user = same cache key
same_user = User.objects.get(pk=user.pk)
cached_result = get_user_profile(same_user)  # Cache hit!
```

**Implementation**: `key_generator.py:82-83, 225-227`

### 2. Custom Objects

Custom objects are serialized via their `__dict__` attributes (excluding private attributes starting with `_`):

```python
from easy_cache import easy_cache


class Settings:
    def __init__(self, theme, language):
        self.theme = theme
        self.language = language


@easy_cache.time_based(invalidate_at="00:00")
def get_user_dashboard(user_obj, settings_obj):
    """Cache dashboard with both user and settings objects"""
    return render_dashboard(user_obj, settings_obj)


# Usage
settings = Settings(theme="dark", language="en")
dashboard = get_user_dashboard(user, settings)
# Generates stable key based on user.pk and settings attributes
```

**Implementation**: `key_generator.py:247-252`

### 3. Dataclasses

Dataclasses are supported with respect for `field(hash=False)` exclusions:

```python
import dataclasses
from datetime import datetime
from easy_cache import easy_cache


@dataclasses.dataclass
class UserProfile:
    user_id: int
    username: str
    created_at: datetime = dataclasses.field(hash=False)  # Excluded from cache key
    last_login: datetime = dataclasses.field(hash=False)  # Excluded from cache key


@easy_cache.time_based(invalidate_at="06:00")
def get_profile_analytics(profile):
    return calculate_analytics(profile)


# Usage
profile1 = UserProfile(1, "alice", datetime(2024, 1, 1), datetime(2025, 1, 1))
profile2 = UserProfile(1, "alice", datetime(2024, 1, 1), datetime(2025, 1, 2))

# Same cache key! last_login is excluded via field(hash=False)
analytics1 = get_profile_analytics(profile1)
analytics2 = get_profile_analytics(profile2)  # Cache hit!
```

**Implementation**: `key_generator.py:234-243`

### 4. Enum Types

Enums are serialized using their class name and member name for stability:

```python
from enum import Enum
from easy_cache import easy_cache


class UserRole(Enum):
    ADMIN = 1
    MODERATOR = 2
    USER = 3


@easy_cache.time_based(invalidate_at="12:00")
def get_role_permissions(user, role):
    return fetch_permissions(user, role)


# Usage
permissions = get_role_permissions(user, UserRole.ADMIN)
# Generates key: "...UserRole.ADMIN..."
```

**Implementation**: `key_generator.py:218-219`

## Automatic Exclusion of Unstable Types

Django Easy Cache automatically excludes inherently unstable types from cache keys to prevent cache invalidation on every call:

```python
import uuid
from datetime import datetime
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="13:00")
def process_data(user_id, data):
    """Timestamps and UUIDs in data dict are auto-excluded"""
    return expensive_processing(user_id, data)


# These produce the SAME cache key (timestamp and request_id excluded):
result1 = process_data(
    123,
    {
        "value": 42,
        "timestamp": datetime.now(),  # Auto-excluded
        "request_id": uuid.uuid4(),  # Auto-excluded
    },
)

result2 = process_data(
    123,
    {
        "value": 42,
        "timestamp": datetime.now(),  # Different timestamp, but excluded
        "request_id": uuid.uuid4(),  # Different UUID, but excluded
    },
)  # Cache hit! Only "value" matters for cache key
```

**Default excluded types** (configurable in `settings.py`):
- `datetime.datetime`
- `datetime.date`
- `datetime.time`
- `uuid.UUID`

**Implementation**: `config.py:29`, `key_generator.py:158-168, 170-199`

## Real-World Use Cases

### Use Case 1: User Service with Multiple Objects

```python
from django.contrib.auth.models import User
from easy_cache import easy_cache


class UserService:
    @easy_cache.time_based(invalidate_at="14:00")
    def get_user_profile(self, user_obj, settings_obj):
        """Method with multiple object parameters"""
        profile_data = self._fetch_profile(user_obj)
        customizations = self._apply_settings(profile_data, settings_obj)
        return customizations

    def _fetch_profile(self, user):
        # Expensive database queries
        return {...}

    def _apply_settings(self, profile, settings):
        # Complex business logic
        return {...}


# Usage
service = UserService()
user = User.objects.get(username="bob")
settings = UserSettings(theme="light", notifications=True)
profile = service.get_user_profile(user, settings)  # Cached result
```

### Use Case 2: Product Recommendations

```python
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="03:00")
def get_product_recommendations(user, product, context):
    """Cache recommendations based on user, product, and context objects"""
    return ml_model.predict(user, product, context)


# Usage
from shop.models import User, Product

user = User.objects.get(id=123)
product = Product.objects.get(sku="LAPTOP-001")
context = BrowsingContext(
    category="electronics",
    price_range=(500, 1500),
    session_id=uuid.uuid4(),  # Auto-excluded from cache key
)

recommendations = get_product_recommendations(user, product, context)
```

### Use Case 3: Nested Objects in Collections

```python
from easy_cache import easy_cache


@easy_cache.time_based(invalidate_at="00:00")
def calculate_team_metrics(team_data):
    """Handle complex nested structures with objects"""
    return compute_metrics(team_data)


# Usage
from django.contrib.auth.models import User

team_data = {
    "manager": User.objects.get(id=1),
    "members": [User.objects.get(id=2), User.objects.get(id=3)],
    "settings": TeamSettings(notifications=True, timezone="UTC"),
}

metrics = calculate_team_metrics(team_data)
# All User instances serialized via pk, TeamSettings via __dict__
```

## Method vs Function Handling

Django Easy Cache automatically detects methods and excludes the `self` parameter:

```python
from easy_cache import easy_cache


class ReportGenerator:
    def __init__(self, company):
        self.company = company

    @easy_cache.time_based(invalidate_at="06:00")
    def generate_report(self, user, date_range):
        """self is automatically excluded from cache key"""
        return create_report(self.company, user, date_range)


# Usage
generator = ReportGenerator(company=my_company)
report = generator.generate_report(user_obj, date_range_obj)
# Cache key includes: user, date_range (NOT self/company)
```

**Implementation**: `key_generator.py:66-75`

## Advanced: Custom Object Serialization

For fine-grained control over which object attributes affect cache keys, use the deprecated `_cache_exclude_` protocol (for backward compatibility):

```python
from datetime import datetime
from easy_cache import easy_cache


class AuditedData:
    def __init__(self, id, content, updated_at):
        self.id = id
        self.content = content
        self.updated_at = updated_at  # Dynamic timestamp
        self._cache_exclude_ = ["updated_at"]  # Exclude from cache key


@easy_cache.time_based(invalidate_at="12:00")
def process_audited_data(data):
    return transform(data)


# Usage
data1 = AuditedData(1, "content", datetime(2025, 1, 1, 10, 0))
data2 = AuditedData(1, "content", datetime(2025, 1, 1, 11, 0))

# Same cache key! updated_at is excluded
result1 = process_audited_data(data1)
result2 = process_audited_data(data2)  # Cache hit!
```

**Note**: This protocol is deprecated. Prefer using dataclasses with `field(hash=False)` for modern code.

## Thread Safety

All object serialization is thread-safe. The `KeyGenerator` service uses deterministic JSON serialization without maintaining object references, ensuring:

- No race conditions
- No memory leaks from retained object references
- Safe for concurrent requests in Django applications

**Implementation**: `config.py:20-21` (thread-safe configuration singleton)

## Performance Characteristics

### Serialization Performance

Object serialization uses Python's built-in `json` module with custom encoders:

- **Django models**: O(1) - just extracts `pk`
- **Simple objects**: O(n) where n = number of public attributes
- **Nested structures**: Recursive with automatic hashing for large payloads (>100 chars)

### Memory Efficiency

- No persistent object references stored
- Large serializations (>100 chars) are hashed to 16-character SHA256 digest
- Automatic cleanup after key generation

**Implementation**: `key_generator.py:289-290`

## Configuration

Customize auto-excluded types in your Django settings:

```python
# settings.py
from datetime import datetime, date, time
import uuid

easy_cache = {
    "DEFAULT_EXCLUDE_TYPES": (
        datetime,
        date,
        time,
        uuid.UUID,
        # Add your custom types here
    ),
}
```

## Best Practices

### ✅ DO

1. **Use Django models directly** - Let the package handle pk extraction
2. **Use dataclasses with `field(hash=False)`** - For modern, explicit exclusions
3. **Keep object attributes stable** - Avoid dynamic/random values in object attributes
4. **Test cache key stability** - Verify same logical objects produce same keys

### ❌ DON'T

1. **Don't use `_cache_exclude_` for new code** - Prefer dataclass field exclusions
2. **Don't include file handles or connections in objects** - Not serializable
3. **Don't rely on `__repr__`** - Package ignores custom repr methods
4. **Don't use circular references** - Will raise serialization errors

## Troubleshooting

### Problem: Different cache keys for same logical object

**Solution**: Ensure object attributes are stable. Check for:
- Timestamp fields (should be auto-excluded or use `field(hash=False)`)
- UUID fields (should be auto-excluded)
- Random/generated values

### Problem: UncachableArgumentError

**Solution**: Object contains non-serializable attributes. Options:
- Mark with `field(hash=False)` in dataclasses
- Add type to `DEFAULT_EXCLUDE_TYPES` configuration
- Restructure object to separate cacheable from uncacheable data

### Problem: Unexpected cache misses

Solution: Enable debug logging to see generated cache keys:

```python
# Check what's being included in cache keys
from easy_cache.services.key_generator import KeyGenerator

kg = KeyGenerator()
kg.generate_key(func=your_function, args=(obj,), kwargs={})
print(kg.original_params)  # Shows serialized parameters
```

## Testing Object Parameter Caching

Test coverage includes:
- `tests/test_object_cache_exclusion.py` - Core object serialization tests
- `tests/test_edge_cases.py` - Edge cases and nested structures
- `tests/test_problematic_types.py` - Unstable type handling

Example test pattern:

```python
from django.test import TestCase
from easy_cache.services.key_generator import KeyGenerator


class MyObjectCachingTest(TestCase):
    def test_same_object_data_same_key(self):
        kg = KeyGenerator()

        obj1 = MyObject(id=1, data="test")
        obj2 = MyObject(id=1, data="test")

        key1 = kg.generate_key(func=my_function, args=(obj1,), kwargs={})
        key2 = kg.generate_key(func=my_function, args=(obj2,), kwargs={})

        self.assertEqual(key1, key2)
```

## Related Documentation

- [Time-Based Caching](../README.md#time-based-caching)
- [Configuration Guide](../README.md#configuration)
- [API Reference](../README.md#api-reference)
