from datetime import timedelta
from typing import Optional

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class CacheEntry(models.Model):
    """Model to track cache entries for analytics and management"""

    cache_key = models.CharField(max_length=255, db_index=True)
    original_params = models.TextField(blank=True, null=True)
    function_name = models.CharField(max_length=255, db_index=True)
    cache_backend = models.CharField(max_length=100, default="default")

    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now_add=True)
    access_count = models.PositiveIntegerField(default=0)
    hit_count = models.PositiveIntegerField(default=0)
    miss_count = models.PositiveIntegerField(default=0)

    timeout = models.PositiveIntegerField(help_text="Cache timeout in seconds")
    expires_at = models.DateTimeField(
        null=True, blank=True, db_index=True, help_text="When this cache entry expires and should be considered invalid"
    )

    class Meta:
        verbose_name = "Cache Entry"
        verbose_name_plural = "Cache Entries"
        indexes = [
            models.Index(fields=["function_name", "created_at"]),
            models.Index(fields=["cache_key", "last_accessed"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["hit_count", "miss_count"]),
            models.Index(fields=["cache_backend", "created_at"]),
            models.Index(fields=["last_accessed"]),
        ]

    def __str__(self):
        return f"{self.function_name}: {self.cache_key[:50]}..."

    @property
    def hit_rate(self):
        """Calculate hit rate percentage"""
        total = self.hit_count + self.miss_count
        return (self.hit_count / total * 100) if total > 0 else 0

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()

    @property
    def time_left(self) -> timedelta | None:
        if not self.expires_at or self.is_expired:
            return None
        return self.expires_at - timezone.now()


class CacheEventHistory(models.Model):
    """Store cache-related events for analytics"""

    class EventType(models.TextChoices):
        HIT = "hit", "Hit"
        MISS = "miss", "Miss"
        ERROR = "error", "Error"

    event_name = models.CharField(max_length=200, db_index=True)
    event_type = models.CharField(max_length=50, choices=EventType.choices)

    cache_backend = models.CharField(max_length=100, default="default")
    function_name = models.CharField(max_length=200, db_index=True)
    cache_key = models.CharField(max_length=220)

    occurred_at = models.DateTimeField(auto_now_add=True, db_index=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    original_params = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Cache Event"
        verbose_name_plural = "Cache Events"
        ordering = ["-occurred_at"]
        indexes = [
            models.Index(fields=["event_name", "occurred_at"]),
            models.Index(fields=["function_name", "event_type", "occurred_at"]),
        ]
