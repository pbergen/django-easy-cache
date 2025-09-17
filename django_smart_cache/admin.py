from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime

from .models import CacheEntry, CacheEventHistory
from .utils.format_time_left import format_time_left
from .utils import format_duration_ms


@admin.register(CacheEntry)
class CacheEntryAdmin(admin.ModelAdmin):
    list_display = [
        "function_name",
        "cache_key_short",
        "expires_at_display",
        "hit_rate_display",
        "access_count",
        "last_accessed",
        "cache_backend",
    ]
    list_filter = ["function_name", "cache_backend", "created_at", "last_accessed", "expires_at"]
    search_fields = ["cache_key", "function_name"]
    readonly_fields = [
        "cache_key",
        "created_at",
        "last_accessed",
        "expires_at",
        "access_count",
        "hit_count",
        "miss_count",
        "hit_rate_display",
    ]

    @admin.display(description="Cache Key")
    def cache_key_short(self, obj):
        return obj.cache_key[:50] + "..." if len(obj.cache_key) > 50 else obj.cache_key

    @admin.display(
        description="Expires At",
        ordering="expires_at",
    )
    def expires_at_display(self, obj):
        """Display expiration time with human-readable time left."""
        if not obj.expires_at:
            return "-"

        expires_at_local = localtime(obj.expires_at)
        if obj.is_expired:
            return format_html(
                '<span style="color: red;">{} (expired)</span>', expires_at_local.strftime("%Y-%m-%d %H:%M")
            )

        time_left_str = format_time_left(obj.time_left)

        # Color based on remaining time
        total_seconds = obj.time_left.total_seconds()
        if total_seconds > 86400:  # More than 1 day
            color = "green"
        elif total_seconds > 3600:  # More than 1 hour
            color = "orange"
        else:  # Less than 1 hour
            color = "red"

        return format_html(
            '<span style="color: {};">{} ({} left)</span>',
            color,
            expires_at_local.strftime("%Y-%m-%d %H:%M"),
            time_left_str,
        )

    @admin.display(
        description="Hit Rate",
        ordering="hit_count",
    )
    def hit_rate_display(self, obj):
        # return obj.hit_count
        rate = obj.hit_rate
        color = "green" if rate >= 80 else "orange" if rate >= 60 else "red"
        return format_html('<span style="color: {};">{}</span>', color, format(rate, ".1f") + "%")


@admin.register(CacheEventHistory)
class CacheEventHistoryAdmin(admin.ModelAdmin):
    list_display = [
        "event_name",
        "event_type_display",
        "function_name",
        "occurred_at",
        "duration_display",
    ]
    list_filter = ["event_type", "event_name", "function_name", "occurred_at"]
    search_fields = ["event_name", "function_name", "cache_key"]
    readonly_fields = ["occurred_at"]
    date_hierarchy = "occurred_at"

    @admin.display(
        description="Event Type",
        ordering="event_type",
    )
    def event_type_display(self, obj):
        colors = {
            CacheEventHistory.EventType.HIT: "green",
            CacheEventHistory.EventType.MISS: "orange",
            CacheEventHistory.EventType.ERROR: "red",
        }
        icons = {
            CacheEventHistory.EventType.HIT: "✓",
            CacheEventHistory.EventType.MISS: "○",
            CacheEventHistory.EventType.ERROR: "✗",
        }
        color = colors.get(obj.event_type, "black")
        icon = icons.get(obj.event_type, "")
        return format_html('<span style="color: {};">{} {}</span>', color, icon, obj.get_event_type_display())

    def duration_display(self, obj):
        if obj.duration_ms:
            color = "green" if obj.duration_ms < 100 else "orange" if obj.duration_ms < 500 else "red"
            return format_html('<span style="color: {};">{}</span>', color, format_duration_ms(obj.duration_ms))
        return "-"
